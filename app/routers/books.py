from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.db import public_client
from app.auth import get_current_user, get_user_client
from app.templating import render

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

    # Recent reviews from anyone, newest first, for the activity feed
    recent_reviews = (
        public_client.table("reviews")
        .select("*, profiles!reviews_user_id_fkey(username,avatar_url), books(title,author,cover_url)")
        .order("created_at", desc=True)
        .limit(10)
        .execute()
        .data
    )

    return render(
        request, "index.html", books=books, q=q, recent_reviews=recent_reviews
    )


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
        .select("*, profiles!reviews_user_id_fkey(username,avatar_url)")
        .eq("book_id", book_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    my_shelf = None
    my_review = None
    my_lists = []
    lists_with_book = set()
    if user:
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

    avg_rating = None
    ratings = [r["rating"] for r in reviews if r.get("rating")]
    if ratings:
        avg_rating = round(sum(ratings) / len(ratings), 2)

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
    )
