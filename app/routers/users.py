import datetime
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from app.db import public_client, client_for_user
from app.auth import get_current_user, get_user_client, get_session
from app.templating import render
from app.notifications import notify, compute_streak
from app.badges import compute_badges

router = APIRouter()


@router.get("/settings")
def settings_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return render(request, "settings.html")


@router.post("/settings")
async def update_settings(
    request: Request,
    username: str = Form(...),
    display_name: str = Form(""),
    bio: str = Form(""),
    avatar: UploadFile = File(None),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    updates = {
        "username": username.strip(),
        "display_name": display_name.strip() or username.strip(),
        "bio": bio.strip(),
    }

    error = None

    # Optional avatar upload — stored under a per-user folder in the
    # public "avatars" bucket so storage RLS can scope write access.
    if avatar is not None and avatar.filename:
        try:
            contents = await avatar.read()
            ext = (avatar.filename.rsplit(".", 1)[-1] or "jpg").lower()
            if ext not in {"jpg", "jpeg", "png", "webp", "gif"}:
                ext = "jpg"
            path = f"{user['id']}/avatar.{ext}"
            session = get_session(request)
            storage_client = client_for_user(session["access_token"] if session else None)
            storage_client.storage.from_("avatars").upload(
                path,
                contents,
                {"content-type": avatar.content_type or "image/jpeg", "upsert": "true"},
            )
            public_url = storage_client.storage.from_("avatars").get_public_url(path)
            # cache-bust so the browser picks up the new image immediately
            updates["avatar_url"] = f"{public_url}?v={__import__('time').time_ns()}"
        except Exception as e:
            error = f"Photo upload failed: {e}"

    try:
        client.table("profiles").update(updates).eq("id", user["id"]).execute()
    except Exception as e:
        return render(request, "settings.html", error=str(e))

    if error:
        return render(request, "settings.html", error=error)

    return RedirectResponse(f"/u/{updates['username']}", status_code=303)


@router.get("/people")
def people_directory(request: Request, q: str = ""):
    viewer = get_current_user(request)

    query = public_client.table("profiles").select("*")
    if q:
        query = query.ilike("username", f"%{q}%")
    people = query.order("created_at", desc=True).limit(60).execute().data

    following_ids = set()
    if viewer:
        rows = (
            public_client.table("follows")
            .select("following_id")
            .eq("follower_id", viewer["id"])
            .execute()
            .data
        )
        following_ids = {r["following_id"] for r in rows}

    return render(
        request,
        "people.html",
        people=people,
        q=q,
        following_ids=following_ids,
        viewer=viewer,
    )


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

    # Lists: use the viewer's authed client if logged in, so their own
    # private lists show on their own profile (RLS still hides other
    # people's private lists automatically either way).
    lists = []
    list_previews = {}
    try:
        lists_client = get_user_client(request) if viewer else public_client
        lists = (
            lists_client.table("custom_lists")
            .select("*")
            .eq("user_id", profile_data["id"])
            .order("created_at", desc=True)
            .execute()
            .data
        )
        if lists:
            list_ids = [l["id"] for l in lists]
            entries = (
                lists_client.table("list_books")
                .select("list_id, books(cover_url)")
                .in_("list_id", list_ids)
                .order("added_at", desc=True)
                .execute()
                .data
            )
            counts = {}
            for e in entries:
                lid = e["list_id"]
                counts[lid] = counts.get(lid, 0) + 1
                if lid not in list_previews:
                    list_previews[lid] = []
                if len(list_previews[lid]) < 4 and e.get("books"):
                    list_previews[lid].append(e["books"].get("cover_url"))
            for l in lists:
                l["book_count"] = counts.get(l["id"], 0)
    except Exception:
        # Most likely an expired/dead session token — degrade to showing no
        # lists rather than crashing the whole profile page.
        lists = []
        list_previews = {}

    is_own = bool(viewer) and viewer["id"] == profile_data["id"]
    reviews_total = len(reviews)

    # --- Streak: derived from logged reading-activity days ---
    activity_rows = (
        public_client.table("reading_activity")
        .select("activity_date")
        .eq("user_id", profile_data["id"])
        .order("activity_date", desc=True)
        .limit(400)
        .execute()
        .data
    )
    activity_dates = set()
    for row in activity_rows:
        try:
            activity_dates.add(datetime.date.fromisoformat(row["activity_date"]))
        except (ValueError, TypeError):
            pass
    streak = compute_streak(activity_dates)

    # --- Yearly reading goal (private — only meaningful/visible on your own profile) ---
    current_year = datetime.date.today().year
    books_read_this_year = sum(
        1
        for row in shelves_by_status["read"]
        if row.get("finished_at") and str(row["finished_at"])[:4] == str(current_year)
    )
    goal = None
    if is_own:
        try:
            goal_client = get_user_client(request)
            goal_rows = (
                goal_client.table("reading_goals")
                .select("*")
                .eq("user_id", profile_data["id"])
                .eq("year", current_year)
                .execute()
                .data
            )
            goal = goal_rows[0] if goal_rows else None
        except Exception:
            goal = None

    # --- Badges ---
    clubs_count = (
        public_client.table("club_members")
        .select("*", count="exact")
        .eq("user_id", profile_data["id"])
        .limit(1)
        .execute()
        .count
    )
    badges = compute_badges(
        {
            "books_read": len(shelves_by_status["read"]),
            "reviews_count": reviews_total,
            "followers_count": followers.count,
            "streak": streak,
            "clubs_count": clubs_count or 0,
        }
    )

    return render(
        request,
        "profile.html",
        profile=profile_data,
        shelves_by_status=shelves_by_status,
        reviews=reviews[:5],
        reviews_total=reviews_total,
        followers_count=followers.count,
        following_count=following.count,
        is_following=is_following,
        is_own=is_own,
        lists=lists,
        list_previews=list_previews,
        streak=streak,
        goal=goal,
        current_year=current_year,
        books_read_this_year=books_read_this_year,
        badges=badges,
    )


@router.get("/u/{username}/shelf/{status}")
def shelf_view(request: Request, username: str, status: str):
    if status not in ("want_to_read", "reading", "read"):
        return RedirectResponse(f"/u/{username}", status_code=303)

    profile_data = (
        public_client.table("profiles").select("*").eq("username", username).single().execute().data
    )
    rows = (
        public_client.table("user_books")
        .select("*, books(*)")
        .eq("user_id", profile_data["id"])
        .eq("status", status)
        .order("updated_at", desc=True)
        .execute()
        .data
    )
    labels = {"want_to_read": "Want to read", "reading": "Currently reading", "read": "Read"}
    return render(
        request, "shelf_view.html", profile=profile_data, rows=rows, label=labels[status]
    )


@router.post("/goals/set")
def set_reading_goal(request: Request, target: int = Form(...), redirect_to: str = Form("/")):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    target = max(1, min(target, 1000))
    client = get_user_client(request)
    client.table("reading_goals").upsert(
        {"user_id": user["id"], "year": datetime.date.today().year, "target": target},
        on_conflict="user_id,year",
    ).execute()
    return RedirectResponse(redirect_to, status_code=303)


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
    notify(
        client,
        user_id=target["id"],
        actor_id=viewer["id"],
        type_="follow",
        message=f"{viewer['username']} started following you",
        link=f"/u/{viewer['username']}",
    )
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
