from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.db import public_client
from app.auth import get_current_user, get_user_client
from app.templating import render
from app.moderation import get_report_counts, HIDE_THRESHOLD

router = APIRouter()


@router.get("/")
def home(request: Request, q: str = ""):
    user = get_current_user(request)

    if q:
        books = (
            public_client.table("books")
            .select("*")
            .or_(f"title.ilike.%{q}%,author.ilike.%{q}%")
            .limit(24)
            .execute()
            .data
        )
    else:
        books = (
            public_client.table("books")
            .select("*")
            .order("created_at", desc=True)
            .limit(12)
            .execute()
            .data
        )

    # Build the activity feed from two sources: reviews, and activity_posts
    # (manual "share something" posts + auto-logged started/finished-reading
    # milestones), merged and sorted together by time.
    recent_reviews = (
        public_client.table("reviews")
        .select("*, profiles!reviews_user_id_fkey(username,avatar_url), books(id,title,author,cover_url)")
        .order("created_at", desc=True)
        .limit(12)
        .execute()
        .data
    )
    recent_posts = (
        public_client.table("activity_posts")
        .select("*, profiles(username,avatar_url), books(id,title,author,cover_url)")
        .order("created_at", desc=True)
        .limit(12)
        .execute()
        .data
    )

    feed_items = []
    for r in recent_reviews:
        feed_items.append({"kind": "review", "created_at": r["created_at"], "data": r})
    for p in recent_posts:
        feed_items.append({"kind": p["type"], "created_at": p["created_at"], "data": p})
    feed_items.sort(key=lambda x: x["created_at"], reverse=True)
    feed_items = feed_items[:15]

    return render(
        request, "index.html", books=books, q=q, feed_items=feed_items, hero_reviews=recent_reviews[:3]
    )


@router.post("/posts/new")
def create_post(request: Request, body: str = Form(...), redirect_to: str = Form("/")):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    body = body.strip()
    if body:
        client = get_user_client(request)
        client.table("activity_posts").insert(
            {"user_id": user["id"], "type": "post", "body": body}
        ).execute()

    return RedirectResponse(redirect_to, status_code=303)


@router.post("/posts/{post_id}/delete")
def delete_post(request: Request, post_id: str, redirect_to: str = Form("/")):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    client.table("activity_posts").delete().eq("id", post_id).eq("user_id", user["id"]).execute()

    return RedirectResponse(redirect_to, status_code=303)


@router.get("/books/add")
def add_book_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/login", status_code=303)
    return render(request, "add_book.html")


def _to_int(value: str) -> int | None:
    """Blank number inputs arrive as '' — coerce safely instead of 500ing."""
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


@router.post("/books/add")
def add_book(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(""),
    genre: str = Form(""),
    page_count: str = Form(""),
    published_year: str = Form(""),
    cover_url: str = Form(""),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    result = (
        client.table("books")
        .insert(
            {
                "title": title,
                "author": author,
                "description": description or None,
                "genre": genre or None,
                "page_count": _to_int(page_count),
                "published_year": _to_int(published_year),
                "cover_url": cover_url or None,
                "added_by": user["id"],
            }
        )
        .execute()
    )
    book_id = result.data[0]["id"]
    return RedirectResponse(f"/books/{book_id}", status_code=303)


@router.get("/books/{book_id}")
def book_detail(request: Request, book_id: str):
    user = get_current_user(request)

    book = public_client.table("books").select("*").eq("id", book_id).single().execute().data
    reviews = (
        public_client.table("reviews")
        .select(
            "*, profiles!reviews_user_id_fkey(username,avatar_url), "
            "review_comments(*, profiles(username,avatar_url))"
        )
        .eq("book_id", book_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    for r in reviews:
        r["review_comments"] = sorted(
            r.get("review_comments") or [], key=lambda c: c.get("created_at") or ""
        )

    my_shelf = None
    my_review = None
    my_lists = []
    lists_with_book = set()
    if user:
        try:
            client = get_user_client(request)
            shelf_res = (
                client.table("user_books")
                .select("*")
                .eq("book_id", book_id)
                .eq("user_id", user["id"])
                .execute()
                .data
            )
            my_shelf = shelf_res[0] if shelf_res else None
            review_res = (
                client.table("reviews")
                .select("*")
                .eq("book_id", book_id)
                .eq("user_id", user["id"])
                .execute()
                .data
            )
            my_review = review_res[0] if review_res else None

            my_lists = (
                client.table("custom_lists")
                .select("*")
                .eq("user_id", user["id"])
                .order("created_at", desc=True)
                .execute()
                .data
            )
            if my_lists:
                list_ids = [l["id"] for l in my_lists]
                membership = (
                    client.table("list_books")
                    .select("list_id")
                    .eq("book_id", book_id)
                    .in_("list_id", list_ids)
                    .execute()
                    .data
                )
                lists_with_book = {m["list_id"] for m in membership}
        except Exception:
            # Dead/expired session token, most likely — degrade to showing
            # the book with no personal shelf/review/list state rather than
            # crashing the whole page.
            my_shelf = None
            my_review = None
            my_lists = []
            lists_with_book = set()

    avg_rating = None
    ratings = [r["rating"] for r in reviews if r.get("rating")]
    if ratings:
        avg_rating = round(sum(ratings) / len(ratings), 1)

    report_counts = get_report_counts(public_client, "review", [r["id"] for r in reviews])

    return render(
        request,
        "book_detail.html",
        book=book,
        reviews=reviews,
        my_shelf=my_shelf,
        my_review=my_review,
        avg_rating=avg_rating,
        rating_count=len(ratings),
        my_lists=my_lists,
        lists_with_book=lists_with_book,
        report_counts=report_counts,
        hide_threshold=HIDE_THRESHOLD,
    )
