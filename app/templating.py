from fastapi.templating import Jinja2Templates
from app.auth import get_current_user, get_session
from app.db import client_for_user

templates = Jinja2Templates(directory="app/templates")


def render(request, name: str, **context):
    """Shortcut that always injects the current_user (and, if logged in,
    their unread notification count for the nav bell) into every template."""
    context["request"] = request
    user = get_current_user(request)
    context["current_user"] = user

    unread_count = 0
    if user:
        try:
            # Notifications are RLS-scoped to the owner (auth.uid() = user_id),
            # so this needs to run as the authenticated user — but unlike a
            # real write, it's fine if the token happens to be stale (worst
            # case the badge briefly under-counts), so we deliberately use
            # the session's existing token rather than get_user_client(),
            # which refreshes the token on every call. Doing that on every
            # single page render would hammer Supabase's auth endpoint and
            # risks refresh-token rotation conflicts between concurrent tabs.
            session = get_session(request)
            token = session["access_token"] if session else None
            unread_count = (
                client_for_user(token)
                .table("notifications")
                .select("id", count="exact")
                .eq("user_id", user["id"])
                .eq("is_read", False)
                .limit(1)
                .execute()
                .count
            ) or 0
        except Exception:
            unread_count = 0
    context["unread_notifications"] = unread_count

    return templates.TemplateResponse(name, context)
