import httpx
from fastapi import APIRouter, Query

router = APIRouter()

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


def _parse_volumes(items):
    results = []
    for item in items:
        info = item.get("volumeInfo", {})
        image_links = info.get("imageLinks", {})
        cover = image_links.get("thumbnail") or image_links.get("smallThumbnail")
        if cover:
            cover = cover.replace("http://", "https://")
        published = info.get("publishedDate", "")
        year = None
        if published[:4].isdigit():
            year = int(published[:4])

        results.append(
            {
                "title": info.get("title", ""),
                "author": ", ".join(info.get("authors", [])) or "Unknown",
                "description": info.get("description", ""),
                "cover_url": cover or "",
                "page_count": info.get("pageCount") or "",
                "published_year": year or "",
                "genre": (info.get("categories") or [""])[0],
            }
        )
    return results


@router.get("/api/book-search")
def book_search(q: str = Query(..., min_length=2)):
    """
    Proxies a search to the Google Books API (no key required for basic
    volume search) so /books/add can offer live results as the person types,
    instead of requiring fully manual entry.
    """
    try:
        resp = httpx.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": q, "maxResults": 8},
            timeout=8.0,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception as e:
        return {"results": [], "error": str(e)}

    return {"results": _parse_volumes(items)}


@router.get("/api/mood-search")
def mood_search(mood: str = Query(...)):
    """Book recommendations for the Discover page's mood picker."""
    query = MOOD_QUERIES.get(mood.lower())
    if not query:
        return {"results": [], "error": f"unknown mood: {mood}"}
    try:
        resp = httpx.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": query, "maxResults": 9, "orderBy": "relevance"},
            timeout=8.0,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception as e:
        return {"results": [], "error": str(e)}

    return {"results": _parse_volumes(items)}
