from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.auth import get_current_user, get_user_client

router = APIRouter()


@router.post("/books/{book_id}/shelve")
def shelve(request: Request, book_id: str, status: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    client.table("user_books").upsert(
        {"user_id": user["id"], "book_id": book_id, "status": status},
        on_conflict="user_id,book_id",
    ).execute()
    return RedirectResponse(f"/books/{book_id}", status_code=303)


@router.post("/books/{book_id}/unshelve")
def unshelve(request: Request, book_id: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    client.table("user_books").delete().eq("book_id", book_id).eq(
        "user_id", user["id"]
    ).execute()
    return RedirectResponse(f"/books/{book_id}", status_code=303)
