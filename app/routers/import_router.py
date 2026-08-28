import csv
import io
import re
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from app.db import public_client
from app.auth import get_current_user, get_user_client
from app.templating import render

router = APIRouter()

# Goodreads' "Exclusive Shelf" column values -> our shelf statuses
SHELF_MAP = {
    "read": "read",
    "currently-reading": "reading",
    "to-read": "want_to_read",
}

CHUNK_SIZE = 200  # keep individual bulk requests small enough to stay fast/reliable


def _clean(value) -> str:
    """Strips whitespace and Goodreads' ="123" spreadsheet-formula wrapping
    (used on ISBN columns so Excel doesn't mangle leading zeros)."""
    if not value:
        return ""
    value = str(value).strip()
    m = re.match(r'^="?(.*?)"?$', value)
    if m:
        value = m.group(1)
    return value.strip()


def _to_int(value):
    value = _clean(value)
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _cover_from_isbn(isbn: str) -> str | None:
    """
    Open Library serves cover images directly from an ISBN with no API call
    needed — just a predictable URL. Goodreads exports include ISBNs but
    never cover images, so this is how imported books get artwork.
    """
    isbn = (isbn or "").strip()
    if not isbn:
        return None
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"


@router.get("/import")
def import_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/login", status_code=303)
    return render(request, "import.html", covers_updated=None, error=None)


@router.post("/import/goodreads")
async def import_goodreads(request: Request, file: UploadFile = File(...)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    raw = await file.read()
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    client = get_user_client(request)

    # --- Parse + clean every row first (no network calls yet) ---
    parsed = []
    skipped = []
    seen_in_file = set()  # dedupe re-read rows within the same export
    for row in reader:
        title = _clean(row.get("Title", ""))
        author = _clean(row.get("Author", ""))
        if not title or not author:
            skipped.append(title or "(row missing a title)")
            continue
        key = (title.lower(), author.lower())
        if key in seen_in_file:
            continue
        seen_in_file.add(key)
        parsed.append(
            {
                "key": key,
                "title": title,
                "author": author,
                "isbn": _clean(row.get("ISBN13") or row.get("ISBN") or ""),
                "page_count": _to_int(row.get("Number of Pages")),
                "published_year": _to_int(
                    row.get("Original Publication Year") or row.get("Year Published")
                ),
                "status": SHELF_MAP.get(
                    _clean(row.get("Exclusive Shelf", "")).lower(), "want_to_read"
                ),
                "rating": _to_int(row.get("My Rating")),
                "review_body": _clean(row.get("My Review", "")),
            }
        )

    if not parsed:
        return render(
            request,
            "import_result.html",
            added_books=0,
            matched_existing=0,
            shelved=0,
            reviewed=0,
            skipped=skipped,
        )

    # --- One bulk read to find which of these already exist in the catalog ---
    # (fetch id/title/author in pages rather than filtering per-row)
    existing_lookup = {}
    page_size = 1000
    start = 0
    while True:
        page = (
            public_client.table("books")
            .select("id,title,author")
            .range(start, start + page_size - 1)
            .execute()
            .data
        )
        for b in page:
            existing_lookup[(b["title"].lower(), b["author"].lower())] = b["id"]
        if len(page) < page_size:
            break
        start += page_size

    matched_existing = 0
    to_insert = []
    for row in parsed:
        if row["key"] in existing_lookup:
            row["book_id"] = existing_lookup[row["key"]]
            matched_existing += 1
        else:
            to_insert.append(row)

    # --- Bulk-insert new books, chunked ---
    added_books = 0
    for chunk in _chunks(to_insert, CHUNK_SIZE):
        payload = [
            {
                "title": r["title"],
                "author": r["author"],
                "isbn": r["isbn"] or None,
                "cover_url": _cover_from_isbn(r["isbn"]),
                "page_count": r["page_count"],
                "published_year": r["published_year"],
                "added_by": user["id"],
            }
            for r in chunk
        ]
        try:
            result = client.table("books").insert(payload).execute()
        except Exception:
            # fall back to skipping this chunk rather than failing the whole import
            skipped.extend(r["title"] for r in chunk)
            continue
        for r, inserted in zip(chunk, result.data):
            r["book_id"] = inserted["id"]
            added_books += 1

    all_shelved_rows = [r for r in parsed if r.get("book_id")]

    # --- Bulk upsert shelves ---
    shelved = 0
    for chunk in _chunks(all_shelved_rows, CHUNK_SIZE):
        payload = [
            {"user_id": user["id"], "book_id": r["book_id"], "status": r["status"]}
            for r in chunk
        ]
        client.table("user_books").upsert(payload, on_conflict="user_id,book_id").execute()
        shelved += len(chunk)

    # --- Bulk upsert reviews (only rows with a real rating) ---
    reviewed = 0
    reviewable = [r for r in all_shelved_rows if r["rating"] and r["rating"] > 0]
    for chunk in _chunks(reviewable, CHUNK_SIZE):
        payload = [
            {
                "user_id": user["id"],
                "book_id": r["book_id"],
                "rating": r["rating"],
                "body": r["review_body"] or None,
            }
            for r in chunk
        ]
        client.table("reviews").upsert(payload, on_conflict="user_id,book_id").execute()
        reviewed += len(chunk)

    return render(
        request,
        "import_result.html",
        added_books=added_books,
        matched_existing=matched_existing,
        shelved=shelved,
        reviewed=reviewed,
        skipped=skipped,
    )


@router.post("/tools/backfill-covers")
def backfill_covers(request: Request):
    """
    Fills in cover_url for any catalog book that has an ISBN but no cover —
    typically books that came in through a Goodreads import before this
    feature existed. No external API calls: Open Library's cover URLs are
    deterministic from the ISBN alone.
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    client = get_user_client(request)

    to_update = []
    page_size = 1000
    start = 0
    while True:
        page = (
            public_client.table("books")
            .select("id,isbn")
            .is_("cover_url", "null")
            .not_.is_("isbn", "null")
            .range(start, start + page_size - 1)
            .execute()
            .data
        )
        to_update.extend(page)
        if len(page) < page_size:
            break
        start += page_size

    updated = 0
    try:
        for chunk in _chunks(to_update, CHUNK_SIZE):
            payload = [
                {"id": b["id"], "cover_url": _cover_from_isbn(b["isbn"])}
                for b in chunk
                if b.get("isbn")
            ]
            if payload:
                client.table("books").upsert(payload, on_conflict="id").execute()
                updated += len(payload)
    except Exception as e:
        return render(request, "import.html", error=f"Couldn't backfill covers: {e}")

    return render(request, "import.html", covers_updated=updated)

