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

    Supabase access tokens expire (default ~1 hour). If we just reused the
    token stored at login time, every write would start failing with a 500
    once it expired, even though the person is still "logged in". So we
    proactively refresh using the stored refresh_token before every
    authenticated write, and update the session with the new tokens.
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
        # Refresh token itself is dead (long expired / revoked) — fall back
        # to the old access token; the caller's request will fail cleanly
        # with a Postgrest auth error instead of us crashing here.
         request.session.pop("auth", None)
    return client_for_user(None)
