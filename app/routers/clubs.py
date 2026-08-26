from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.db import public_client
from app.auth import get_current_user, get_user_client
from app.templating import render

router = APIRouter()


@router.get("/clubs")
def clubs_list(request: Request):
    clubs = (
        public_client.table("clubs")
        .select("*, club_members(count)")
        .order("created_at", desc=True)
        .execute()
        .data
    )
    return render(request, "clubs.html", clubs=clubs)


@router.get("/clubs/new")
def new_club_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/login", status_code=303)
    return render(request, "new_club.html")


@router.post("/clubs/new")
def create_club(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    is_private: bool = Form(False),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    result = (
        client.table("clubs")
        .insert(
            {
                "name": name,
                "description": description,
                "is_private": is_private,
                "owner_id": user["id"],
            }
        )
        .execute()
    )
    club_id = result.data[0]["id"]
    client.table("club_members").insert(
        {"club_id": club_id, "user_id": user["id"], "role": "owner"}
    ).execute()
    return RedirectResponse(f"/clubs/{club_id}", status_code=303)


@router.get("/clubs/{club_id}")
def club_detail(request: Request, club_id: str):
    user = get_current_user(request)

    club = public_client.table("clubs").select("*").eq("id", club_id).single().execute().data
    members = (
        public_client.table("club_members")
        .select("*, profiles(username,avatar_url)")
        .eq("club_id", club_id)
        .execute()
        .data
    )
    current_book_rows = (
        public_client.table("club_books")
        .select("*, books(*)")
        .eq("club_id", club_id)
        .eq("is_current", True)
        .execute()
        .data
    )
    current_book = current_book_rows[0] if current_book_rows else None

    discussions = []
    if current_book:
        discussions = (
            public_client.table("discussions")
            .select("*, profiles(username,avatar_url)")
            .eq("club_book_id", current_book["id"])
            .order("created_at", desc=True)
            .execute()
            .data
        )

    is_member = bool(user) and any(m["user_id"] == user["id"] for m in members)

    # Books available to assign (any book in the catalog)
    all_books = public_client.table("books").select("id,title,author").limit(100).execute().data

    return render(
        request,
        "club_detail.html",
        club=club,
        members=members,
        current_book=current_book,
        discussions=discussions,
        is_member=is_member,
        all_books=all_books,
    )


@router.post("/clubs/{club_id}/join")
def join_club(request: Request, club_id: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    client.table("club_members").upsert(
        {"club_id": club_id, "user_id": user["id"], "role": "member"},
        on_conflict="club_id,user_id",
    ).execute()
    return RedirectResponse(f"/clubs/{club_id}", status_code=303)


@router.post("/clubs/{club_id}/leave")
def leave_club(request: Request, club_id: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    client.table("club_members").delete().eq("club_id", club_id).eq(
        "user_id", user["id"]
    ).execute()
    return RedirectResponse(f"/clubs/{club_id}", status_code=303)


@router.post("/clubs/{club_id}/assign-book")
def assign_book(request: Request, club_id: str, book_id: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    # retire the currently active book
    client.table("club_books").update({"is_current": False}).eq(
        "club_id", club_id
    ).eq("is_current", True).execute()
    client.table("club_books").insert(
        {"club_id": club_id, "book_id": book_id, "is_current": True}
    ).execute()
    return RedirectResponse(f"/clubs/{club_id}", status_code=303)


@router.post("/clubs/{club_id}/discussions/new")
def new_discussion(
    request: Request,
    club_id: str,
    club_book_id: str = Form(...),
    title: str = Form(...),
    body: str = Form(""),
    page_marker: int = Form(0),
    spoiler: bool = Form(False),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    client.table("discussions").insert(
        {
            "club_id": club_id,
            "club_book_id": club_book_id,
            "user_id": user["id"],
            "title": title,
            "body": body,
            "page_marker": page_marker or None,
            "spoiler": spoiler,
        }
    ).execute()
    return RedirectResponse(f"/clubs/{club_id}", status_code=303)


@router.get("/discussions/{discussion_id}")
def discussion_detail(request: Request, discussion_id: str):
    discussion = (
        public_client.table("discussions")
        .select("*, profiles(username,avatar_url), clubs(name,id)")
        .eq("id", discussion_id)
        .single()
        .execute()
        .data
    )
    comments = (
        public_client.table("discussion_comments")
        .select("*, profiles(username,avatar_url)")
        .eq("discussion_id", discussion_id)
        .order("created_at")
        .execute()
        .data
    )
    return render(request, "discussion_detail.html", discussion=discussion, comments=comments)


@router.post("/discussions/{discussion_id}/comment")
def comment_discussion(request: Request, discussion_id: str, body: str = Form(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    client.table("discussion_comments").insert(
        {"discussion_id": discussion_id, "user_id": user["id"], "body": body}
    ).execute()
    return RedirectResponse(f"/discussions/{discussion_id}", status_code=303)
