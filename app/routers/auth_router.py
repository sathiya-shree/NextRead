from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.db import public_client, client_for_user
from app.templating import render

router = APIRouter()


@router.get("/login")
def login_page(request: Request):
    return render(request, "login.html")


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        result = public_client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        request.session["auth"] = {
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "user_id": result.user.id,
        }
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        return render(request, "login.html", error=str(e))


@router.get("/signup")
def signup_page(request: Request):
    return render(request, "signup.html")


@router.post("/signup")
def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(...),
):
    try:
        result = public_client.auth.sign_up({"email": email, "password": password})
        if result.user is None:
            raise Exception("Signup failed")

        # Update the auto-created profile with the chosen username
        if result.session:
            request.session["auth"] = {
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
                "user_id": result.user.id,
            }
            try:
                # Must use a client authenticated as this user — RLS blocks
                # the update otherwise, which silently left usernames unset.
                authed_client = client_for_user(result.session.access_token)
                authed_client.table("profiles").update(
                    {"username": username, "display_name": username}
                ).eq("id", result.user.id).execute()
            except Exception:
                pass
            return RedirectResponse("/", status_code=303)
        else:
            # Email confirmation required by Supabase project settings
            return render(
                request,
                "login.html",
                error="Check your email to confirm your account, then log in.",
            )
    except Exception as e:
        return render(request, "signup.html", error=str(e))


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
