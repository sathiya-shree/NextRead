from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.db import public_client
from app.auth import get_current_user, get_user_client
from app.templating import render

router = APIRouter()


@router.post("/lists/new")
def create_list(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    is_public: bool = Form(True),
    book_id: str = Form(""),
    redirect_to: str = Form("/"),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    result = (
        client.table("custom_lists")
        .insert(
            {
                "user_id": user["id"],
                "name": name.strip(),
                "description": description.strip(),
                "is_public": is_public,
            }
        )
        .execute()
    )
    list_id = result.data[0]["id"]

    if book_id:
        client.table("list_books").upsert(
            {"list_id": list_id, "book_id": book_id}, on_conflict="list_id,book_id"
        ).execute()
        return RedirectResponse(redirect_to, status_code=303)

    return RedirectResponse(f"/lists/{list_id}", status_code=303)


@router.get("/lists/{list_id}")
def view_list(request: Request, list_id: str):
    viewer = get_current_user(request)
    client = get_user_client(request) if viewer else public_client

    lst = (
        client.table("custom_lists")
        .select("*, profiles(username,avatar_url)")
        .eq("id", list_id)
        .single()
        .execute()
        .data
    )
    entries = (
        client.table("list_books")
        .select("*, books(*)")
        .eq("list_id", list_id)
        .order("added_at", desc=True)
        .execute()
        .data
    )
    is_owner = bool(viewer) and lst and viewer["id"] == lst["user_id"]

    return render(request, "list_detail.html", lst=lst, entries=entries, is_owner=is_owner)


@router.post("/lists/{list_id}/add-book")
def add_book_to_list(
    request: Request, list_id: str, book_id: str = Form(...), redirect_to: str = Form("/")
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    client.table("list_books").upsert(
        {"list_id": list_id, "book_id": book_id}, on_conflict="list_id,book_id"
    ).execute()
    return RedirectResponse(redirect_to, status_code=303)


@router.post("/lists/{list_id}/remove-book")
def remove_book_from_list(
    request: Request, list_id: str, book_id: str = Form(...), redirect_to: str = Form("/")
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    client.table("list_books").delete().eq("list_id", list_id).eq("book_id", book_id).execute()
    return RedirectResponse(redirect_to, status_code=303)
