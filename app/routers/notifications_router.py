from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.auth import get_current_user, get_user_client
from app.templating import render

router = APIRouter()


@router.get("/notifications")
def notifications_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)
    try:
        items = (
            client.table("notifications")
            .select("*, actor:profiles!notifications_actor_id_fkey(username,avatar_url)")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
            .limit(100)
            .execute()
            .data
        )
    except Exception:
        # Most commonly: the session's refresh_token was already dead and
        # get_user_client() had to fall back to an anonymous client, so this
        # RLS-scoped query has nothing to return. Degrade to an empty inbox
        # rather than a raw error page — if the person is truly logged out
        # now, the nav will reflect that on their next click anyway.
        items = []

    unread_ids = [n["id"] for n in items if not n["is_read"]]
    if unread_ids:
        try:
            client.table("notifications").update({"is_read": True}).in_("id", unread_ids).execute()
        except Exception:
            pass

    return render(request, "notifications.html", items=items)
