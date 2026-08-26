from fastapi.templating import Jinja2Templates
from app.auth import get_current_user

templates = Jinja2Templates(directory="app/templates")


def render(request, name: str, **context):
    """Shortcut that always injects the current_user into the template context."""
    context["request"] = request
    context["current_user"] = get_current_user(request)
    return templates.TemplateResponse(name, context)
