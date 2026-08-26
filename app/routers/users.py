from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.db import public_client
from app.auth import get_current_user, get_user_client
from app.templating import render

router = APIRouter()


@router.get("/u/{username}")
def profile(request: Request, username: str):
    viewer = get_current_user(request)

    profile_data = (
        public_client.table("profiles")
        .select("*")
        .eq("username", username)
        .single()
        .execute()
        .data
    )

    shelf = (
        public_client.table("user_books")
        .select("*, books(*)")
        .eq("user_id", profile_data["id"])
        .order("updated_at", desc=True)
        .execute()
        .data
    )
    reviews = (
        public_client.table("reviews")
        .select("*, books(title,author,cover_url)")
        .eq("user_id", profile_data["id"])
        .order("created_at", desc=True)
        .execute()
        .data
    )
    followers = (
        public_client.table("follows")
        .select("*", count="exact")
        .eq("following_id", profile_data["id"])
        .execute()
    )
    following = (
        public_client.table("follows")
        .select("*", count="exact")
        .eq("follower_id", profile_data["id"])
        .execute()
    )

    is_following = False
    if viewer and viewer["id"] != profile_data["id"]:
        rel = (
            public_client.table("follows")
            .select("*")
            .eq("follower_id", viewer["id"])
            .eq("following_id", profile_data["id"])
            .execute()
            .data
        )
        is_following = bool(rel)

    shelves_by_status = {"want_to_read": [], "reading": [], "read": []}
    for row in shelf:
        shelves_by_status.setdefault(row["status"], []).append(row)

    return render(
        request,
        "profile.html",
        profile=profile_data,
        shelves_by_status=shelves_by_status,
        reviews=reviews,
        followers_count=followers.count,
        following_count=following.count,
        is_following=is_following,
        is_own=bool(viewer) and viewer["id"] == profile_data["id"],
    )


@router.post("/u/{username}/follow")
def follow(request: Request, username: str):
    viewer = get_current_user(request)
    if not viewer:
        return RedirectResponse("/login", status_code=303)

    target = (
        public_client.table("profiles")
        .select("id")
        .eq("username", username)
        .single()
        .execute()
        .data
    )
    client = get_user_client(request)
    client.table("follows").upsert(
        {"follower_id": viewer["id"], "following_id": target["id"]},
        on_conflict="follower_id,following_id",
    ).execute()
    return RedirectResponse(f"/u/{username}", status_code=303)


@router.post("/u/{username}/unfollow")
def unfollow(request: Request, username: str):
    viewer = get_current_user(request)
    if not viewer:
        return RedirectResponse("/login", status_code=303)

    target = (
        public_client.table("profiles")
        .select("id")
        .eq("username", username)
        .single()
        .execute()
        .data
    )
    client = get_user_client(request)
    client.table("follows").delete().eq("follower_id", viewer["id"]).eq(
        "following_id", target["id"]
    ).execute()
    return RedirectResponse(f"/u/{username}", status_code=303)
