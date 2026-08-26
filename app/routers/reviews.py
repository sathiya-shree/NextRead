from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.auth import get_current_user, get_user_client

router = APIRouter()


@router.post("/books/{book_id}/review")
def write_review(
    request: Request,
    book_id: str,
    rating: int = Form(...),
    body: str = Form(""),
    spoiler: bool = Form(False),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

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

    return RedirectResponse(f"/books/{book_id}", status_code=303)
