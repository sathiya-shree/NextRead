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
    """Supabase client authenticated as the current user (for RLS-protected writes)."""
    session = get_session(request)
    token = session["access_token"] if session else None
    return client_for_user(token)
