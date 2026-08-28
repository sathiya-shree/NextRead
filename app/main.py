import os
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from app.routers import auth_router, books, shelves, reviews, clubs, users, book_search, import_router, lists

load_dotenv()

logger = logging.getLogger("shelfie")

app = FastAPI(title="Shelfie")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-secret-change-me"),
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.exception_handler(Exception)
async def catch_all(request: Request, exc: Exception):
    """
    Surfaces the real error instead of a blank crash. Vercel's function logs
    (Project -> Deployments -> your deployment -> Functions -> Logs) also show
    this traceback, which is the fastest way to diagnose a 500 in production.
    """
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    traceback.print_exc()
    return HTMLResponse(
        f"""
        <div style="font-family: monospace; max-width: 700px; margin: 60px auto; padding: 24px;
                    background:#F2ECDC; border-radius:4px; color:#17231C;">
          <h2 style="margin-top:0;">Something broke on this page</h2>
          <p style="opacity:.7">{request.method} {request.url.path}</p>
          <pre style="white-space:pre-wrap; background:#E4DACB; padding:12px; border-radius:4px; font-size:12px;">{exc}</pre>
          <p><a href="/" style="color:#A67C2E;">&larr; Back home</a></p>
        </div>
        """,
        status_code=500,
    )

app.include_router(auth_router.router)
app.include_router(books.router)
app.include_router(book_search.router)
app.include_router(shelves.router)
app.include_router(reviews.router)
app.include_router(clubs.router)
app.include_router(users.router)
app.include_router(import_router.router)
app.include_router(lists.router)
