from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.db import public_client
from app.auth import get_current_user, get_user_client
from app.templating import render
from app.notifications import notify, log_activity

router = APIRouter()


@router.get("/reviews")
def reviews_page(request: Request, q: str = "", user: str = ""):
    """A dedicated, searchable feed of reviews — either site-wide or, when
    ?user=username is set (linked from a profile page), just that person's."""
    query = (
        public_client.table("reviews")
        .select("*, profiles!reviews_user_id_fkey(username,avatar_url), books(id,title,author,cover_url)")
        .order("created_at", desc=True)
        .limit(300)
    )

    filter_profile = None
    if user:
        target = (
            public_client.table("profiles").select("*").eq("username", user).limit(1).execute().data
        )
        filter_profile = target[0] if target else None
        if filter_profile:
            query = query.eq("user_id", filter_profile["id"])
        else:
            # unknown username — show nothing rather than error
            query = query.eq("user_id", "00000000-0000-0000-0000-000000000000")

    all_reviews = query.execute().data

    if q:
        ql = q.lower()
        all_reviews = [
            r
            for r in all_reviews
            if ql in (r.get("body") or "").lower()
            or ql in ((r.get("books") or {}).get("title") or "").lower()
            or ql in ((r.get("books") or {}).get("author") or "").lower()
            or ql in ((r.get("profiles") or {}).get("username") or "").lower()
        ]

    return render(
        request,
        "reviews.html",
        reviews=all_reviews,
        q=q,
        filter_user=user,
        filter_profile=filter_profile,
    )


@router.post("/books/{book_id}/review")
def write_review(
    request: Request,
    book_id: str,
    rating: float = Form(...),
    body: str = Form(""),
    spoiler: bool = Form(False),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    # Clamp to 1-5 and snap to the nearest half-star, defensively —
    # the picker UI already does this, but never trust the client alone.
    rating = round(max(1.0, min(5.0, rating)) * 2) / 2

    client = get_user_client(request)
    client.table("reviews").upsert(
        {
            "user_id": user["id"],
            "book_id": book_id,
            "rating": rating,
            "body": body,
            "spoiler": spoiler,
        },
        on_conflict="user_id,book_id",
    ).execute()

    # Also mark the book as read
    client.table("user_books").upsert(
        {"user_id": user["id"], "book_id": book_id, "status": "read"},
        on_conflict="user_id,book_id",
    ).execute()
    log_activity(client, user["id"])

    return RedirectResponse(f"/books/{book_id}", status_code=303)


@router.post("/books/{book_id}/review/delete")
def delete_review(request: Request, book_id: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    # RLS (reviews_cud_own) already scopes this to the caller's own review —
    # the eq(user_id) here is belt-and-suspenders, not the only guard.
    client.table("reviews").delete().eq("book_id", book_id).eq("user_id", user["id"]).execute()

    return RedirectResponse(f"/books/{book_id}", status_code=303)


@router.post("/reviews/{review_id}/like")
def like_review(request: Request, review_id: str, book_id: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    existing = (
        client.table("review_likes")
        .select("*")
        .eq("review_id", review_id)
        .eq("user_id", user["id"])
        .execute()
        .data
    )
    if existing:
        client.table("review_likes").delete().eq("review_id", review_id).eq(
            "user_id", user["id"]
        ).execute()
    else:
        client.table("review_likes").insert(
            {"review_id": review_id, "user_id": user["id"]}
        ).execute()
        # Only notify on the "add" side of the toggle, not on unlike
        review_row = (
            public_client.table("reviews").select("user_id").eq("id", review_id).limit(1).execute().data
        )
        if review_row:
            notify(
                client,
                user_id=review_row[0]["user_id"],
                actor_id=user["id"],
                type_="review_like",
                message=f"{user['username']} liked your review",
                link=f"/books/{book_id}",
            )

    return RedirectResponse(f"/books/{book_id}", status_code=303)


@router.post("/reviews/{review_id}/comment")
def comment_review(
    request: Request, review_id: str, book_id: str = Form(...), body: str = Form(...)
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    client.table("review_comments").insert(
        {"review_id": review_id, "user_id": user["id"], "body": body}
    ).execute()

    review_row = (
        public_client.table("reviews").select("user_id").eq("id", review_id).limit(1).execute().data
    )
    if review_row:
        notify(
            client,
            user_id=review_row[0]["user_id"],
            actor_id=user["id"],
            type_="review_comment",
            message=f"{user['username']} commented on your review",
            link=f"/books/{book_id}",
        )

    return RedirectResponse(f"/books/{book_id}", status_code=303)
