import datetime


def notify(client, user_id: str, actor_id: str, type_: str, message: str, link: str):
    """
    Creates a notification for `user_id`, attributed to `actor_id`.
    Never raises — a failed notification should never break the action that
    triggered it (a follow, a comment, etc. should still succeed either way).
    """
    if not user_id or user_id == actor_id:
        return  # don't notify people about their own actions
    try:
        client.table("notifications").insert(
            {
                "user_id": user_id,
                "actor_id": actor_id,
                "type": type_,
                "message": message,
                "link": link,
            }
        ).execute()
    except Exception:
        pass


def log_activity(client, user_id: str):
    """
    Marks today as an active reading day for this user — the basis for
    streaks. Idempotent (upsert), so calling it repeatedly in one day is
    harmless. Never raises for the same reason as notify().
    """
    try:
        today = datetime.date.today().isoformat()
        client.table("reading_activity").upsert(
            {"user_id": user_id, "activity_date": today},
            on_conflict="user_id,activity_date",
        ).execute()
    except Exception:
        pass


def compute_streak(activity_dates: set) -> int:
    """
    Given a set of datetime.date objects, returns the current streak length.
    A streak is still "alive" if today hasn't been logged yet but yesterday
    was — it only breaks once a full day is skipped.
    """
    today = datetime.date.today()
    cursor = today
    if cursor not in activity_dates:
        cursor = cursor - datetime.timedelta(days=1)
        if cursor not in activity_dates:
            return 0
    streak = 0
    while cursor in activity_dates:
        streak += 1
        cursor -= datetime.timedelta(days=1)
    return streak
