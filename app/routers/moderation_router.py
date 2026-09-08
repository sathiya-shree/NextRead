from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.auth import get_current_user, get_user_client

router = APIRouter()

VALID_TARGET_TYPES = {"review", "discussion", "discussion_comment", "review_comment", "activity_post"}


@router.post("/reports/new")
def create_report(
    request: Request,
    target_type: str = Form(...),
    target_id: str = Form(...),
    reason: str = Form(""),
    redirect_to: str = Form("/"),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if target_type not in VALID_TARGET_TYPES:
        return RedirectResponse(redirect_to, status_code=303)

    client = get_user_client(request)
    try:
        client.table("reports").insert(
            {
                "reporter_id": user["id"],
                "target_type": target_type,
                "target_id": target_id,
                "reason": reason.strip() or None,
            }
        ).execute()
    except Exception:
        pass  # reporting should never itself throw a 500 at the user

    sep = "&" if "?" in redirect_to else "?"
    return RedirectResponse(f"{redirect_to}{sep}reported=1", status_code=303)
