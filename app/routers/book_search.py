import datetime
from collections import Counter
import httpx
from fastapi import APIRouter, Query, Request

from app.auth import get_current_user, get_user_client

router = APIRouter()

# Identify ourselves per Open Library's usage guidelines — helps avoid
# being rate-limited as an anonymous/unidentified client.
HEADERS = {"User-Agent": "Shelfie/1.0 (https://github.com/; contact via app)"}

MOOD_QUERIES = {
    "cozy": "cozy heartwarming comfort read fiction",
    "thrilling": "thriller suspense page turner",
    "heartbreaking": "literary fiction emotional heartbreaking",
    "funny": "humor funny witty novel",
    "mind-bending": "mind bending science fiction philosophical",
    "romantic": "romance love story",
    "spooky": "horror gothic supernatural spooky",
    "inspiring": "inspiring memoir nonfiction",
}


def _parse_ol_docs(docs):
    """
    Parses Open Library's search.json 'docs' into the shape the frontend
    expects. Used for both /api/book-search and /api/mood-search — Open
    Library requires no API key and (unlike Google Books) has been reliable
    from serverless hosts, so both features run through it.
    """
    results = []
    for d in docs:
        cover_i = d.get("cover_i")
        cover = f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg" if cover_i else ""
        results.append(
            {
                "title": d.get("title", ""),
                "author": ", ".join(d.get("author_name", []) or []) or "Unknown",
                "description": "",  # search.json doesn't include descriptions
                "cover_url": cover,
                "page_count": d.get("number_of_pages_median") or "",
                "published_year": d.get("first_publish_year") or "",
                "genre": (d.get("subject") or [""])[0],
            }
        )
    return results


def _ol_search(query: str, limit: int, sort: str | None = None):
    params = {
        "q": query,
        "limit": limit,
        "fields": "title,author_name,cover_i,first_publish_year,subject,number_of_pages_median,edition_count",
    }
    if sort:
        params["sort"] = sort
    resp = httpx.get(
        "https://openlibrary.org/search.json",
        params=params,
        headers=HEADERS,
        timeout=8.0,
    )
    resp.raise_for_status()
    return resp.json().get("docs", [])


@router.get("/api/book-search")
def book_search(q: str = Query(..., min_length=2)):
    """
    Live search-as-you-type results for /books/add, so people aren't
    stuck typing every field manually. Left un-biased by recency/popularity
    since someone might genuinely be looking for an old or obscure title.
    """
    try:
        docs = _ol_search(q, 8)
    except Exception as e:
        return {"results": [], "error": str(e)}

    return {"results": _parse_ol_docs(docs)}


@router.get("/api/mood-search")
def mood_search(request: Request, mood: str = Query(...)):
    """
    Book recommendations for the Discover page's mood picker. Unlike plain
    search, this is meant to surface things people would actually recognize
    — so it's restricted to books first published in roughly the last 25
    years and sorted by edition count (how many times a book has been
    reprinted/re-edited), which is a solid crowd-sourced proxy for "this is
    a widely-read, still-in-print book" rather than an obscure backlist title.

    When someone's logged in, this also leans on their own reading history:
    their most-read genres get folded into the query, so "Cozy" for a
    fantasy reader and "Cozy" for a romance reader don't return the same
    nine books.
    """
    query = MOOD_QUERIES.get(mood.lower())
    if not query:
        return {"results": [], "error": f"unknown mood: {mood}"}

    user = get_current_user(request)
    if user:
        top_genres = _top_genres_for_user(request, user["id"])
        if top_genres:
            query = f"{query} {' '.join(top_genres)}"

    current_year = datetime.date.today().year
    earliest_year = current_year - 25
    scoped_query = f"{query} first_publish_year:[{earliest_year} TO {current_year}]"

    try:
        docs = _ol_search(scoped_query, 9, sort="editions")
    except Exception as e:
        return {"results": [], "error": str(e)}

    return {"results": _parse_ol_docs(docs)}


def _top_genres_for_user(request: Request, user_id: str, limit: int = 2) -> list:
    """The 1-2 genres that show up most often among books this person has
    marked read — a lightweight taste signal for personalizing mood search."""
    try:
        client = get_user_client(request)  # user_books is RLS-scoped to its owner
        rows = (
            client.table("user_books")
            .select("books(genre)")
            .eq("user_id", user_id)
            .eq("status", "read")
            .limit(200)
            .execute()
            .data
        )
        counter = Counter()
        for r in rows:
            genre = (r.get("books") or {}).get("genre")
            if genre:
                counter[genre] += 1
        return [g for g, _ in counter.most_common(limit)]
    except Exception:
        return []
