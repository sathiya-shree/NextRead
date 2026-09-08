from fastapi import Request
from app.db import client_for_user, public_client


def get_session(request: Request) -> dict | None:
    """Returns {'access_token', 'refresh_token', 'user_id', 'username'} or None."""
    return request.session.get("auth")


def get_current_user(request: Request) -> dict | None:
    """Convenience: returns the profile dict for the logged-in user, or None."""
    session = get_session(request)
    if not session:
        return None
    try:
        res = (
            public_client.table("profiles")
            .select("*")
            .eq("id", session["user_id"])
            .single()
            .execute()
        )
        return res.data
    except Exception:
        return None


def get_user_client(request: Request):
    """
    Supabase client authenticated as the current user (for RLS-protected writes).

    Supabase access tokens expire (default ~1 hour), and refresh_tokens are
    single-use — once refreshed, the old refresh_token is invalidated. If the
    refresh call itself fails (stale/already-used refresh_token), falling
    back to the original access_token is pointless: it's already expired,
    so the caller's query would just fail again with the identical
    "JWT expired" error, uncaught, one function call later.

    Instead, when refresh fails, we clear the dead session and return an
    anonymous client. Read queries then simply return empty/RLS-scoped
    results instead of crashing; the person effectively appears logged out
    for this request, which is a safe, honest state (their refresh token
    really is dead) rather than a raw error page.
    """
    session = get_session(request)
    if not session:
        return client_for_user(None)

    try:
        refreshed = public_client.auth.refresh_session(session["refresh_token"])
        request.session["auth"] = {
            "access_token": refreshed.session.access_token,
            "refresh_token": refreshed.session.refresh_token,
            "user_id": refreshed.user.id,
        }
        return client_for_user(refreshed.session.access_token)
    except Exception:
        request.session.pop("auth", None)
        return client_for_user(None)
