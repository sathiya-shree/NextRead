import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from app.routers import auth_router, books, shelves, reviews, clubs, users

load_dotenv()

app = FastAPI(title="Shelfie")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-secret-change-me"),
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router.router)
app.include_router(books.router)
app.include_router(shelves.router)
app.include_router(reviews.router)
app.include_router(clubs.router)
app.include_router(users.router)
