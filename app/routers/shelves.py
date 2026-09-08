import datetime
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.auth import get_current_user, get_user_client
from app.notifications import log_activity

router = APIRouter()


@router.post("/books/{book_id}/shelve")
def shelve(request: Request, book_id: str, status: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)

    existing = (
        client.table("user_books")
        .select("started_at,finished_at")
        .eq("user_id", user["id"])
        .eq("book_id", book_id)
        .execute()
        .data
    )
    existing_row = existing[0] if existing else None
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    payload = {"user_id": user["id"], "book_id": book_id, "status": status}
    if status in ("reading", "read") and not (existing_row and existing_row.get("started_at")):
        payload["started_at"] = now
    if status == "read" and not (existing_row and existing_row.get("finished_at")):
        payload["finished_at"] = now

    client.table("user_books").upsert(payload, on_conflict="user_id,book_id").execute()
    log_activity(client, user["id"])

    return RedirectResponse(f"/books/{book_id}", status_code=303)


@router.post("/books/{book_id}/progress")
def update_progress(request: Request, book_id: str, progress_pages: str = Form("")):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    try:
        pages = max(0, int(progress_pages))
    except ValueError:
        pages = 0

    client = get_user_client(request)
    existing = (
        client.table("user_books")
        .select("status,started_at")
        .eq("user_id", user["id"])
        .eq("book_id", book_id)
        .execute()
        .data
    )
    existing_row = existing[0] if existing else None

    payload = {"user_id": user["id"], "book_id": book_id, "progress_pages": pages}
    # Logging progress implies you're reading it, unless already marked read
    if not existing_row or existing_row.get("status") not in ("reading", "read"):
        payload["status"] = "reading"
    if not (existing_row and existing_row.get("started_at")):
        payload["started_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    client.table("user_books").upsert(payload, on_conflict="user_id,book_id").execute()
    log_activity(client, user["id"])

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
