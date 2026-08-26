import os
import random
import re
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st


# ============================================================
# BOOKISH — YOUR VIVID READING JOURNAL
# ============================================================

st.set_page_config(
    page_title="Bookish",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bookish.db")
CSV_PATH = os.path.join(BASE_DIR, "required.csv")


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=15,
        check_same_thread=False,
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=15000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS shelves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_key TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                authors TEXT,
                shelf TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                added_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_key TEXT NOT NULL,
                rating REAL NOT NULL,
                review TEXT,
                reaction TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS discussions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_key TEXT NOT NULL,
                username TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quest TEXT UNIQUE NOT NULL,
                completed INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                username TEXT DEFAULT 'Reader',
                bio TEXT DEFAULT 'currently lost in fiction ♡'
            );

            INSERT OR IGNORE INTO profile
            (id, username, bio)
            VALUES (1, 'Reader', 'currently lost in fiction ♡');

            CREATE TABLE IF NOT EXISTS challenge (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                target INTEGER DEFAULT 30
            );

            INSERT OR IGNORE INTO challenge
            (id, target)
            VALUES (1, 30);

            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                book_key TEXT,
                log_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT 'purple',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS list_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_name TEXT NOT NULL,
                book_key TEXT NOT NULL,
                title TEXT NOT NULL,
                authors TEXT,
                added_at TEXT NOT NULL,
                UNIQUE(list_name, book_key)
            );
            """
        )


init_db()


# ============================================================
# DATA
# ============================================================

@st.cache_data
def load_books():
    if not os.path.exists(CSV_PATH):
        st.error(
            "required.csv was not found. Put required.csv in the same "
            "folder as app.py."
        )
        st.stop()

    data = pd.read_csv(
        CSV_PATH,
        encoding="utf-8",
        on_bad_lines="skip",
    )

    data.columns = [str(c).strip() for c in data.columns]

    for column in ["title", "authors", "genre", "average_ratings"]:
        if column not in data.columns:
            data[column] = "Unknown"

    for column in ["title", "authors", "genre"]:
        data[column] = data[column].fillna("Unknown").astype(str)

    data["rating_num"] = pd.to_numeric(
        data["average_ratings"],
        errors="coerce",
    ).fillna(0)

    data = data[data["title"].str.strip() != ""]
    data = data.drop_duplicates(subset=["title", "authors"])

    return data.reset_index(drop=True)


books = load_books()


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "Home",
    "selected_book": None,
    "mood": None,
    "roulette_book": None,
    "search_query": "",
    "flash": None,
    "active_list": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================

def book_key(book):
    return f"{book['title']}||{book['authors']}"


def get_profile():
    with get_connection() as conn:
        return conn.execute(
            "SELECT username, bio FROM profile WHERE id = 1"
        ).fetchone()


def update_profile(username, bio):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE profile
            SET username = ?, bio = ?
            WHERE id = 1
            """,
            (username.strip() or "Reader", bio.strip()),
        )


def log_activity(action, book_key_value=None):
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO activity_log (action, book_key, log_date)
            VALUES (?, ?, ?)
            """,
            (action, book_key_value, today),
        )


def get_active_dates():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT log_date FROM activity_log ORDER BY log_date DESC"
        ).fetchall()
    return {row[0] for row in rows}


def compute_streak():
    dates = get_active_dates()
    if not dates:
        return 0, 0

    today = datetime.now().date()

    current = 0
    cursor = today
    if cursor.strftime("%Y-%m-%d") not in dates:
        cursor = cursor - timedelta(days=1)

    while cursor.strftime("%Y-%m-%d") in dates:
        current += 1
        cursor -= timedelta(days=1)

    sorted_dates = sorted(
        datetime.strptime(d, "%Y-%m-%d").date() for d in dates
    )
    longest = 1
    running = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            running += 1
        else:
            running = 1
        longest = max(longest, running)
    longest = max(longest, current)

    return current, longest


def get_shelf(book):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT shelf, progress
            FROM shelves
            WHERE book_key = ?
            """,
            (book_key(book),),
        ).fetchone()


def save_shelf(book, shelf, progress=None):
    key = book_key(book)

    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT progress FROM shelves
            WHERE book_key = ?
            """,
            (key,),
        ).fetchone()

        current_progress = (
            existing[0] if existing and progress is None else (progress or 0)
        )

        conn.execute(
            """
            INSERT INTO shelves
            (book_key, title, authors, shelf, progress, added_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(book_key) DO UPDATE SET
                title = excluded.title,
                authors = excluded.authors,
                shelf = excluded.shelf,
                progress = excluded.progress
            """,
            (
                key,
                str(book["title"]),
                str(book["authors"]),
                shelf,
                int(current_progress),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

    log_activity(f"shelf:{shelf}", key)


def delete_shelf(book):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM shelves WHERE book_key = ?",
            (book_key(book),),
        )


def get_shelf_books(shelf):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT book_key, title, authors, progress
            FROM shelves
            WHERE shelf = ?
            ORDER BY id DESC
            """,
            (shelf,),
        ).fetchall()


def get_all_shelves():
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT book_key, title, authors, shelf, progress
            FROM shelves
            ORDER BY id DESC
            """
        ).fetchall()


def save_review(book, rating, review, reaction):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO reviews
            (book_key, rating, review, reaction, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                book_key(book),
                float(rating),
                review.strip(),
                reaction,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
    log_activity("review", book_key(book))


def get_reviews(book):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT rating, review, reaction, created_at
            FROM reviews
            WHERE book_key = ?
            ORDER BY id DESC
            """,
            (book_key(book),),
        ).fetchall()


def count_reviews():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]


def add_discussion(book, message, username):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO discussions
            (book_key, username, message, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                book_key(book),
                username,
                message.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
    log_activity("discussion", book_key(book))


def get_discussions(book):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT username, message, created_at
            FROM discussions
            WHERE book_key = ?
            ORDER BY id DESC
            """,
            (book_key(book),),
        ).fetchall()


def get_quest_status(quest):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT completed FROM quests WHERE quest = ?",
            (quest,),
        ).fetchone()
    return bool(row[0]) if row else False


def set_quest_status(quest, completed):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO quests (quest, completed)
            VALUES (?, ?)
            ON CONFLICT(quest) DO UPDATE SET
                completed = excluded.completed
            """,
            (quest, int(completed)),
        )
    if completed:
        log_activity("quest", None)


def get_challenge_target():
    with get_connection() as conn:
        return conn.execute(
            "SELECT target FROM challenge WHERE id = 1"
        ).fetchone()[0]


def set_challenge_target(target):
    with get_connection() as conn:
        conn.execute(
            "UPDATE challenge SET target = ? WHERE id = 1",
            (int(target),),
        )


# ---- Lists (Goodreads-style custom shelves) ----

LIST_COLORS = ["purple", "teal", "coral", "gold"]


def create_list(name, color=None):
    name = name.strip()
    if not name:
        return False
    color = color or random.choice(LIST_COLORS)
    with get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO lists (name, color, created_at) VALUES (?, ?, ?)",
                (name, color, datetime.now().isoformat(timespec="seconds")),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def delete_list(name):
    with get_connection() as conn:
        conn.execute("DELETE FROM lists WHERE name = ?", (name,))
        conn.execute("DELETE FROM list_items WHERE list_name = ?", (name,))


def get_all_lists():
    with get_connection() as conn:
        return conn.execute(
            "SELECT name, color, created_at FROM lists ORDER BY id DESC"
        ).fetchall()


def add_to_list(list_name, book):
    with get_connection() as conn:
        try:
            conn.execute(
                """
                INSERT INTO list_items (list_name, book_key, title, authors, added_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    list_name,
                    book_key(book),
                    str(book["title"]),
                    str(book["authors"]),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            log_activity("list_add", book_key(book))
            return True
        except sqlite3.IntegrityError:
            return False


def remove_from_list(list_name, key):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM list_items WHERE list_name = ? AND book_key = ?",
            (list_name, key),
        )


def get_list_items(list_name):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT book_key, title, authors
            FROM list_items
            WHERE list_name = ?
            ORDER BY id DESC
            """,
            (list_name,),
        ).fetchall()


def get_list_count(list_name):
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM list_items WHERE list_name = ?",
            (list_name,),
        ).fetchone()[0]


def get_lists_for_book(key):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT list_name FROM list_items WHERE book_key = ?",
            (key,),
        ).fetchall()
    return {row[0] for row in rows}


# ---- Achievements ----

def compute_achievements():
    read_count = len(get_shelf_books("Read"))
    review_count = count_reviews()
    current_streak, longest_streak = compute_streak()
    list_count = len(get_all_lists())

    all_shelves = get_all_shelves()
    read_keys = {row[0] for row in all_shelves if row[3] == "Read"}
    read_data = books[books.apply(book_key, axis=1).isin(read_keys)]
    genres_explored = (
        read_data["genre"].str.split(",").explode().str.strip().nunique()
        if not read_data.empty
        else 0
    )

    badges = [
        {
            "icon": "🌱",
            "name": "First Page",
            "desc": "Finish your first book",
            "unlocked": read_count >= 1,
            "color": "teal",
        },
        {
            "icon": "📚",
            "name": "Bookworm",
            "desc": "Finish 5 books",
            "unlocked": read_count >= 5,
            "color": "purple",
        },
        {
            "icon": "🏆",
            "name": "Bibliophile",
            "desc": "Finish 20 books",
            "unlocked": read_count >= 20,
            "color": "gold",
        },
        {
            "icon": "🔥",
            "name": "On a Roll",
            "desc": "3-day reading streak",
            "unlocked": longest_streak >= 3,
            "color": "coral",
        },
        {
            "icon": "🔥🔥",
            "name": "Unstoppable",
            "desc": "7-day reading streak",
            "unlocked": longest_streak >= 7,
            "color": "coral",
        },
        {
            "icon": "🔥🔥🔥",
            "name": "Legendary Streak",
            "desc": "30-day reading streak",
            "unlocked": longest_streak >= 30,
            "color": "coral",
        },
        {
            "icon": "🌈",
            "name": "Genre Explorer",
            "desc": "Read across 5+ genres",
            "unlocked": genres_explored >= 5,
            "color": "teal",
        },
        {
            "icon": "✍️",
            "name": "Reviewer",
            "desc": "Write 5 reviews",
            "unlocked": review_count >= 5,
            "color": "purple",
        },
        {
            "icon": "📝",
            "name": "Wordsmith",
            "desc": "Write 20 reviews",
            "unlocked": review_count >= 20,
            "color": "gold",
        },
        {
            "icon": "🗂️",
            "name": "Curator",
            "desc": "Create 3 custom lists",
            "unlocked": list_count >= 3,
            "color": "teal",
        },
    ]
    return badges


def find_book_by_key(key):
    matches = books[
        books.apply(book_key, axis=1) == key
    ]
    if matches.empty:
        return None
    return matches.iloc[0]


def select_book(book):
    st.session_state.selected_book = book_key(book)
    st.session_state.page = "Book"


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def get_cover_url(title, authors):
    """Look up a real cover image via the free Open Library API.
    Tries title+author first, then falls back to title alone (Goodreads-style
    author strings like 'Author A, Author B' often don't match exactly).
    Returns None if nothing is found, so the caller can fall back gracefully."""
    headers = {"User-Agent": "BookishReadingApp/1.0 (personal reading journal)"}
    first_author = re.split(r"[,/&]| and ", str(authors))[0].strip()

    attempts = [
        {"title": str(title), "author": first_author},
        {"title": str(title)},
    ]

    for query in attempts:
        try:
            resp = requests.get(
                "https://openlibrary.org/search.json",
                params={**query, "limit": 1, "fields": "cover_i"},
                headers=headers,
                timeout=5,
            )
            if resp.status_code == 200:
                docs = resp.json().get("docs", [])
                if docs and docs[0].get("cover_i"):
                    return (
                        f"https://covers.openlibrary.org/b/id/"
                        f"{docs[0]['cover_i']}-L.jpg"
                    )
        except Exception:
            continue

    return None


def cover_monogram(title):
    words = [w for w in str(title).split() if w and w[0].isalpha()]
    letters = "".join(w[0] for w in words[:2]).upper()
    return letters or "📖"


def cover_html(title, authors, genre, cover_class="", min_height=230):
    """Render just the cover art: a real photo when we find one (clean,
    no text on top of it — Fable/Goodreads style), otherwise a jewel-tone
    monogram card as a graceful fallback. Title/author render separately,
    above the cover, wherever this is called."""
    cover_url = get_cover_url(title, authors)

    if cover_url:
        safe_title = str(title).replace('"', "&quot;")
        return f"""
        <div class="book-cover has-image {cover_class}" style="min-height:{min_height}px;">
            <img
                src="{cover_url}"
                alt="{safe_title}"
                class="cover-photo"
                loading="lazy"
                onerror="this.parentElement.classList.add('img-failed'); this.style.display='none';"
            />
        </div>
        """

    return f"""
    <div class="book-cover {cover_class}" style="min-height:{min_height}px;">
        <div class="cover-monogram">{cover_monogram(title)}</div>
        <div class="cover-small">{genre}</div>
    </div>
    """


def book_heading(title, authors, level="normal"):
    """Title + author, rendered above the cover — Goodreads/Fable style."""
    if level == "large":
        st.markdown(f"### {title}")
    else:
        st.markdown(f"**{title}**")
    st.caption(f"by {authors}")


def show_notice():
    if st.session_state.flash:
        message, kind = st.session_state.flash
        if kind == "success":
            st.success(message)
        elif kind == "info":
            st.info(message)
        elif kind == "warning":
            st.warning(message)
        st.session_state.flash = None


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

MOODS = {
    "🌧️ Comfort": {
        "words": ["fiction", "family", "friendship", "hope", "life", "love", "contemporary"],
        "genres": ["fiction", "contemporary", "literary"],
    },
    "🥀 Make me cry": {
        "words": ["loss", "grief", "family", "love", "life", "sad", "war", "death"],
        "genres": ["fiction", "literary", "historical"],
    },
    "💌 Give me butterflies": {
        "words": ["romance", "love", "relationship", "marriage", "heart"],
        "genres": ["romance", "romantic"],
    },
    "🕯️ Something dark": {
        "words": ["mystery", "crime", "dark", "death", "thriller", "murder", "horror"],
        "genres": ["mystery", "thriller", "horror", "crime"],
    },
    "🧠 Make me think": {
        "words": ["philosophy", "psychology", "society", "politics", "history", "science"],
        "genres": ["literary", "philosophy", "history", "nonfiction"],
    },
    "🌱 Fresh start": {
        "words": ["growth", "change", "journey", "life", "hope", "healing", "self"],
        "genres": ["fiction", "self-help", "memoir", "contemporary"],
    },
}


def mood_score(row, mood_name):
    config = MOODS[mood_name]
    text = f"{row['title']} {row['authors']} {row['genre']}".lower()

    score = 0

    for word in config["words"]:
        if word in text:
            score += 2

    for genre in config["genres"]:
        if genre in str(row["genre"]).lower():
            score += 3

    score += min(float(row["rating_num"]), 5) * 0.4

    return score


def mood_recommendations(mood_name, limit=6):
    if mood_name not in MOODS:
        return books.sample(min(limit, len(books)))

    scored = books.copy()
    scored["_mood_score"] = scored.apply(
        lambda row: mood_score(row, mood_name),
        axis=1,
    )

    if scored["_mood_score"].max() <= 0:
        return scored.sample(min(limit, len(scored)))

    top = scored.sort_values(
        ["_mood_score", "rating_num"],
        ascending=False,
    ).head(max(limit * 3, limit))

    return top.sample(min(limit, len(top)))


def general_recommendations(limit=6):
    return books.sort_values(
        "rating_num",
        ascending=False,
    ).head(max(limit * 3, limit)).sample(
        min(limit, len(books))
    )


def similar_books(book, limit=4):
    genre = str(book["genre"]).split(",")[0].strip().lower()
    if not genre:
        return books.sample(min(limit, len(books)))

    pool = books[
        books["genre"].str.lower().str.contains(genre, na=False)
        & (books["title"] != book["title"])
    ]
    if pool.empty:
        pool = books[books["title"] != book["title"]]

    pool = pool.sort_values("rating_num", ascending=False).head(max(limit * 3, limit))
    return pool.sample(min(limit, len(pool)))


# ============================================================
# CSS — VIBRANT JEWEL-TONE THEME
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap');

    :root {
        --purple: #6C2BD9;
        --purple-deep: #3E1671;
        --purple-soft: #EFE3FF;
        --teal: #0E9594;
        --teal-deep: #0A5C5C;
        --teal-soft: #DDF6F1;
        --coral: #FF6152;
        --coral-deep: #C23B2E;
        --coral-soft: #FFE3DE;
        --gold: #F2A93B;
        --gold-deep: #B5720E;
        --gold-soft: #FFEFD3;
        --ink: #221733;
        --ink-soft: #5B5170;
    }

    .stApp, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 8% 8%, rgba(108,43,217,.22), transparent 32%),
            radial-gradient(circle at 92% 6%, rgba(14,149,148,.24), transparent 34%),
            radial-gradient(circle at 50% 100%, rgba(255,97,82,.20), transparent 42%),
            radial-gradient(circle at 30% 60%, rgba(242,169,59,.14), transparent 36%),
            #FBF7FF !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #3E1671 0%, #21123F 100%);
        border-right: none;
    }

    [data-testid="stSidebar"] * {
        font-family: "DM Sans", sans-serif;
        color: #F1E9FF !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,.06);
        border: 1px solid rgba(255,255,255,.12);
        color: #F1E9FF !important;
        text-align: left;
        border-radius: 12px;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(90deg, var(--coral), var(--gold));
        border-color: transparent;
        color: #221733 !important;
        transform: translateX(2px);
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, var(--coral), var(--gold)) !important;
        border-color: transparent !important;
        color: #221733 !important;
        font-weight: 800;
        box-shadow: 0 6px 16px rgba(255,97,82,.35);
    }

    .bookish-brand {
        font-family: "Fraunces", serif;
        font-size: 40px;
        font-weight: 700;
        background: linear-gradient(90deg, #FFB4A8, #FFD98E);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
        margin-bottom: -5px;
    }

    .bookish-tagline {
        color: #C9B8ED !important;
        font-size: 13px;
        margin-bottom: 22px;
    }

    .streak-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(90deg, var(--coral), var(--gold));
        color: #221733 !important;
        font-weight: 800;
        border-radius: 999px;
        padding: 6px 14px;
        font-size: 13px;
        margin-bottom: 10px;
    }

    .eyebrow {
        color: var(--coral-deep);
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.9px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .hero-title {
        font-family: "Fraunces", serif;
        color: var(--ink);
        font-size: clamp(38px, 5vw, 64px);
        line-height: 1.02;
        letter-spacing: -2px;
        margin: 0;
        background: linear-gradient(100deg, var(--purple-deep) 10%, var(--coral-deep) 60%, var(--gold-deep) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-copy {
        color: var(--ink-soft);
        font-size: 16px;
        margin-top: 12px;
        max-width: 620px;
    }

    .section-title {
        font-family: "Fraunces", serif;
        color: var(--ink);
        font-size: 28px;
        font-weight: 600;
        margin-top: 30px;
        margin-bottom: 8px;
    }

    .section-copy {
        color: var(--ink-soft);
        font-size: 14px;
        margin-bottom: 16px;
    }

    .book-cover {
        min-height: 230px;
        border-radius: 18px;
        padding: 25px 18px;
        background: linear-gradient(145deg, #8A4FE8, var(--purple-deep));
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 16px 32px rgba(62,22,113,.28);
        position: relative;
        overflow: hidden;
    }

    .book-cover::after {
        content: "";
        position: absolute;
        top: -40%;
        right: -30%;
        width: 140%;
        height: 140%;
        background: radial-gradient(circle, rgba(255,255,255,.16), transparent 60%);
    }

    .book-cover.alt1 {
        background: linear-gradient(145deg, #16B8B4, var(--teal-deep));
        box-shadow: 0 16px 32px rgba(10,92,92,.28);
    }

    .book-cover.alt2 {
        background: linear-gradient(145deg, #FF8A73, var(--coral-deep));
        box-shadow: 0 16px 32px rgba(194,59,46,.28);
    }

    .book-cover.alt3 {
        background: linear-gradient(145deg, #FFC55C, var(--gold-deep));
        box-shadow: 0 16px 32px rgba(181,114,14,.28);
    }

    .book-cover.has-image {
        background: none;
        box-shadow: 0 16px 32px rgba(34,23,51,.18);
        padding: 0;
        overflow: hidden;
    }

    .book-cover.has-image::after {
        display: none;
    }

    .cover-photo {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
        border-radius: 18px;
    }

    .book-cover.has-image.img-failed {
        background: linear-gradient(145deg, #8A4FE8, var(--purple-deep));
        padding: 25px 18px;
    }

    .cover-monogram {
        font-family: "Fraunces", serif;
        font-size: 40px;
        font-weight: 700;
        opacity: .95;
    }

    .cover-scrim {
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(20,10,40,.08) 35%, rgba(20,10,40,.92) 100%);
    }

    .cover-content {
        position: relative;
        z-index: 2;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        gap: 10px;
    }

    .cover-small {
        font-size: 10px;
        letter-spacing: 2px;
        text-transform: uppercase;
        opacity: .9;
        font-weight: 700;
    }

    .cover-title {
        font-family: "Fraunces", serif;
        font-size: 25px;
        line-height: 1.08;
        font-weight: 700;
    }

    .cover-author {
        font-size: 12px;
        opacity: .92;
    }

    .quote {
        background: var(--purple-soft);
        border-left: 4px solid var(--purple);
        padding: 14px 17px;
        border-radius: 0 14px 14px 0;
        color: var(--purple-deep);
        font-style: italic;
        margin: 10px 0 20px;
    }

    .tiny {
        color: var(--ink-soft);
        font-size: 12px;
    }

    .pill {
        display: inline-block;
        color: white;
        border-radius: 999px;
        padding: 5px 12px;
        font-size: 11px;
        font-weight: 700;
        margin-right: 6px;
        margin-bottom: 4px;
    }

    .mood-card {
        border-radius: 16px;
        padding: 18px 16px;
        margin-bottom: 10px;
        color: white;
    }

    .mood-card.purple { background: linear-gradient(135deg, #8A4FE8, var(--purple-deep)); }
    .mood-card.teal { background: linear-gradient(135deg, #16B8B4, var(--teal-deep)); }
    .mood-card.coral { background: linear-gradient(135deg, #FF8A73, var(--coral-deep)); }
    .mood-card.gold { background: linear-gradient(135deg, #FFC55C, var(--gold-deep)); }

    .mood-card-emoji {
        font-family: "Fraunces", serif;
        font-size: 19px;
        font-weight: 700;
    }

    .mood-card-desc {
        font-size: 12.5px;
        opacity: .92;
        margin-top: 4px;
    }

    .topnav-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 6px;
        padding-bottom: 14px;
        border-bottom: 1px solid #EADFFB;
    }

    .topnav-wrap .stButton > button {
        border-radius: 999px !important;
        font-size: 13.5px;
    }

    .fact-banner {
        background: linear-gradient(100deg, var(--purple-deep), var(--teal-deep) 60%, var(--coral-deep));
        color: white;
        border-radius: 18px;
        padding: 18px 22px;
        margin: 14px 0 6px;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .fact-banner b {
        color: #FFE9A8;
    }

    .stat-strip {
        display: flex;
        gap: 14px;
        margin: 6px 0 4px;
    }

    .stat-chip {
        flex: 1;
        border-radius: 16px;
        padding: 14px 16px;
        color: white;
        text-align: center;
    }

    .stat-chip .num {
        font-family: "Fraunces", serif;
        font-size: 26px;
        font-weight: 700;
        display: block;
    }

    .stat-chip .lbl {
        font-size: 11px;
        opacity: .9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .pill.purple { background: var(--purple); }
    .pill.teal { background: var(--teal); }
    .pill.coral { background: var(--coral); }
    .pill.gold { background: var(--gold-deep); }

    .badge-card {
        border-radius: 18px;
        padding: 18px;
        text-align: center;
        border: 2px solid transparent;
    }

    .badge-card.locked {
        background: #F1ECFB;
        opacity: .45;
        filter: grayscale(70%);
    }

    .badge-card.unlocked.purple { background: linear-gradient(160deg, var(--purple-soft), #fff); border-color: var(--purple); }
    .badge-card.unlocked.teal { background: linear-gradient(160deg, var(--teal-soft), #fff); border-color: var(--teal); }
    .badge-card.unlocked.coral { background: linear-gradient(160deg, var(--coral-soft), #fff); border-color: var(--coral); }
    .badge-card.unlocked.gold { background: linear-gradient(160deg, var(--gold-soft), #fff); border-color: var(--gold); }

    .badge-icon { font-size: 32px; }
    .badge-name { font-family: "Fraunces", serif; font-weight: 700; color: var(--ink); margin-top: 4px; }
    .badge-desc { font-size: 11px; color: var(--ink-soft); }

    .big-number {
        font-family: "Fraunces", serif;
        font-size: 40px;
        background: linear-gradient(90deg, var(--purple), var(--coral));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }

    .muted {
        color: var(--ink-soft);
    }

    .footer-copy {
        text-align: center;
        color: #9C8FBD;
        font-size: 12px;
        padding: 42px 0 20px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 20px !important;
        border-color: #E9DDFB !important;
        background: rgba(255,255,255,.86);
        box-shadow: 0 8px 24px rgba(62,22,113,.08);
        transition: transform .18s ease, box-shadow .18s ease;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 16px 32px rgba(108,43,217,.16);
    }

    @keyframes bookishFadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    section.main > div.block-container {
        animation: bookishFadeIn .45s ease;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }

    .streak-chip {
        animation: float 2.4s ease-in-out infinite;
    }

    .stButton > button {
        border-radius: 12px;
        border: 1px solid #E2D3F7;
        background: #fff;
        color: var(--purple-deep);
        font-weight: 700;
        min-height: 40px;
        transition: all .18s ease;
    }

    .stButton > button:hover {
        border-color: transparent;
        background: linear-gradient(90deg, var(--purple), var(--coral));
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(108,43,217,.28);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, var(--coral), var(--gold));
        border: none;
        color: #221733;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 12px !important;
        border-color: #E2D3F7 !important;
        background: #fff !important;
    }

    .stProgress > div > div {
        background: linear-gradient(90deg, var(--teal), var(--purple));
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 700;
        color: var(--ink-soft);
    }

    .stTabs [aria-selected="true"] {
        color: var(--purple-deep) !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

profile = get_profile()
username = profile[0] if profile else "Reader"
current_streak, longest_streak = compute_streak()

with st.sidebar:
    st.markdown('<div class="bookish-brand">Bookish</div>', unsafe_allow_html=True)
    st.markdown('<div class="bookish-tagline">your vivid reading journal ♡</div>', unsafe_allow_html=True)

    if current_streak > 0:
        st.markdown(
            f'<div class="streak-chip">🔥 {current_streak}-day streak</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    nav = {
        "Home": "🏠",
        "Discover": "🔎",
        "My Books": "📚",
        "Lists": "🗂️",
        "Streaks & Badges": "🔥",
        "Book Rooms": "💬",
        "Challenges": "🎯",
        "Reading Wrapped": "📊",
        "Profile": "👤",
    }

    current_page = st.session_state.page
    detail_pages = {"Book": "Discover"}
    highlighted_page = detail_pages.get(current_page, current_page)

    for page_name, icon in nav.items():
        is_active = page_name == highlighted_page
        if st.button(
            f"{'👉' if is_active else icon}  {page_name}",
            key=f"nav_{page_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.page = page_name
            st.rerun()

    st.divider()

    want_count = len(get_shelf_books("Want to Read"))
    reading_count = len(get_shelf_books("Currently Reading"))
    read_count = len(get_shelf_books("Read"))

    st.caption(f"♡ {want_count} books on your TBR")
    st.caption(f"📖 {reading_count} currently reading")
    st.caption(f"✓ {read_count} finished")

    st.divider()

    st.caption("Made for people who read with their whole heart ♡")


# ============================================================
# TOP NAVIGATION — quick, elegant page switching
# ============================================================

def render_topnav():
    topnav_pages = [
        ("Home", "🏠"),
        ("Discover", "🔎"),
        ("My Books", "📚"),
        ("Lists", "🗂️"),
        ("Streaks & Badges", "🔥"),
        ("Profile", "👤"),
    ]

    current = st.session_state.page
    highlighted = {"Book": "Discover"}.get(current, current)

    st.markdown('<div class="topnav-wrap">', unsafe_allow_html=True)
    cols = st.columns(len(topnav_pages))
    for i, (name, icon) in enumerate(topnav_pages):
        with cols[i]:
            active = name == highlighted
            if st.button(
                f"{icon} {name}",
                key=f"topnav_{name}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.page = name
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


render_topnav()


# ============================================================
# COMMON BOOK DETAIL
# ============================================================

def book_detail(book):
    if book is None:
        st.warning("That book is no longer available.")
        return

    key = book_key(book)

    st.markdown(
        f'<div class="eyebrow">Bookish book room</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"## {book['title']}"
    )

    st.caption(f"by {book['authors']}")

    genre_tags = [g.strip() for g in str(book["genre"]).split(",") if g.strip()]
    tag_colors = ["purple", "teal", "coral", "gold"]
    tag_html = "".join(
        f'<span class="pill {tag_colors[i % 4]}">{tag}</span>'
        for i, tag in enumerate(genre_tags[:5])
    )
    if tag_html:
        st.markdown(tag_html, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 2])

    with c1:
        cover_class = random.choice(["", "alt1", "alt2", "alt3"])
        st.markdown(
            cover_html(
                book["title"], book["authors"], book["genre"],
                cover_class, min_height=280,
            ),
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"### ⭐ {float(book['rating_num']):.2f} average rating"
        )
        st.write(f"**Genre:** {book['genre']}")

        shelf_info = get_shelf(book)
        current_shelf = shelf_info[0] if shelf_info else "Not added"
        current_progress = shelf_info[1] if shelf_info else 0

        shelf = st.selectbox(
            "Add to shelf",
            ["Not added", "Want to Read", "Currently Reading", "Read"],
            index=[
                "Not added",
                "Want to Read",
                "Currently Reading",
                "Read",
            ].index(current_shelf),
            key=f"detail_shelf_{key}",
        )

        progress = 100
        if shelf == "Currently Reading":
            progress = st.slider(
                "Reading progress",
                0,
                100,
                int(current_progress),
                key=f"detail_progress_{key}",
            )

        b1, b2 = st.columns(2)

        with b1:
            if st.button(
                "Save to my shelf",
                key=f"detail_save_{key}",
                use_container_width=True,
            ):
                if shelf == "Not added":
                    delete_shelf(book)
                else:
                    save_shelf(book, shelf, progress)
                if shelf == "Read" and current_shelf != "Read":
                    st.session_state.flash = ("You finished it! 🎉", "success")
                    st.balloons()
                else:
                    st.session_state.flash = ("Shelf updated ♡", "success")
                st.rerun()

        with b2:
            if st.button(
                "← Back",
                key="detail_back",
                use_container_width=True,
            ):
                st.session_state.page = "Discover"
                st.session_state.selected_book = None
                st.rerun()

        all_lists = get_all_lists()
        if all_lists:
            list_names = [row[0] for row in all_lists]
            already_in = get_lists_for_book(key)
            picked = st.multiselect(
                "Add to your lists",
                list_names,
                default=[name for name in list_names if name in already_in],
                key=f"detail_lists_{key}",
            )

            if st.button("Update lists", key=f"detail_lists_save_{key}"):
                for name in list_names:
                    if name in picked and name not in already_in:
                        add_to_list(name, book)
                    elif name not in picked and name in already_in:
                        remove_from_list(name, key)
                st.session_state.flash = ("Lists updated ♡", "success")
                st.rerun()
        else:
            st.caption("You don't have any lists yet — create one on the Lists page ♡")

    st.divider()

    review_tab, discuss_tab, similar_tab = st.tabs(
        ["💭 Reviews", "💬 Discussion", "✨ You might also like"]
    )

    with review_tab:
        reviews = get_reviews(book)

        if reviews:
            for rating, review, reaction, date in reviews[:5]:
                with st.container(border=True):
                    st.write(f"{reaction}  **{rating:.1f} / 5**")
                    if review:
                        st.write(f"“{review}”")
                    st.caption(date[:10])
        else:
            st.caption("No reviews yet. Be the first reader to leave one ♡")

        with st.expander("✍️ Leave a review"):
            rating = st.slider(
                "Your rating",
                0.5,
                5.0,
                4.0,
                0.5,
                key=f"rating_{key}",
            )

            reaction = st.selectbox(
                "How did it make you feel?",
                ["🥹", "😭", "❤️", "🤍", "😮", "🤯", "🌱", "🕯️"],
                key=f"reaction_{key}",
            )

            review = st.text_area(
                "Your thoughts",
                placeholder="I wasn't ready for that ending...",
                key=f"review_{key}",
            )

            if st.button(
                "Post review",
                key=f"post_review_{key}",
            ):
                save_review(book, rating, review, reaction)
                st.success("Your review is now part of the room ♡")
                st.rerun()

    with discuss_tab:
        st.markdown(
            '<div class="quote">⚠️ Spoiler warning: discussions may contain spoilers.</div>',
            unsafe_allow_html=True,
        )

        message = st.text_area(
            "Join the conversation",
            placeholder="Tell the room what stayed with you...",
            key=f"detail_room_message_{key}",
        )

        if st.button("💌 Post to the room", key=f"detail_post_room_{key}"):
            if message.strip():
                add_discussion(book, message, username)
                st.session_state.flash = ("Your thought is in the room ♡", "success")
                st.rerun()

        discussions = get_discussions(book)
        if discussions:
            for room_user, msg, date in discussions[:8]:
                with st.container(border=True):
                    st.markdown(f"**🌷 {room_user}**")
                    st.write(f"“{msg}”")
                    st.caption(date[:10])
        else:
            st.caption("No one has started the conversation yet. You could be first ♡")

    with similar_tab:
        recs = similar_books(book, 4)
        rec_cols = st.columns(4)
        for i, (_, rec) in enumerate(recs.iterrows()):
            with rec_cols[i % 4]:
                cover_class = ["", "alt1", "alt2", "alt3"][i % 4]
                book_heading(rec["title"], rec["authors"])
                st.markdown(
                    cover_html(
                        rec["title"], rec["authors"], rec["genre"],
                        cover_class, min_height=150,
                    ),
                    unsafe_allow_html=True,
                )
                if st.button("Open", key=f"similar_{key}_{i}", use_container_width=True):
                    select_book(rec)
                    st.rerun()


# ============================================================
# HOME
# ============================================================

if st.session_state.page == "Home":

    st.markdown(
        '<div class="eyebrow">Welcome back</div>',
        unsafe_allow_html=True,
    )

    hour = datetime.now().hour
    if hour < 5:
        greeting, greeting_emoji = "Still up", "🌙"
    elif hour < 12:
        greeting, greeting_emoji = "Good morning", "☀️"
    elif hour < 17:
        greeting, greeting_emoji = "Good afternoon", "🌤️"
    elif hour < 21:
        greeting, greeting_emoji = "Good evening", "🌇"
    else:
        greeting, greeting_emoji = "Good night", "🌙"

    st.markdown(
        f'<div class="hero-title">{greeting}, {username} {greeting_emoji}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero-copy">'
        "Your next favorite story might be one click away."
        "</div>",
        unsafe_allow_html=True,
    )

    FUN_FACTS = [
        "The world's oldest known library, the Library of Ashurbanipal, is over 2,600 years old.",
        "The word “bookworm” originally described insects that literally ate through old books.",
        "Agatha Christie is the best-selling novelist of all time, with over 2 billion copies sold.",
        "The longest novel ever published, “In Search of Lost Time,” has roughly 1.2 million words.",
        "Reading for just 6 minutes can reduce stress levels by up to 68%, according to one Sussex study.",
        "The first novel ever written on a typewriter was “The Adventures of Tom Sawyer.”",
        "“Don Quixote” is considered the best-selling novel of all time across all languages.",
        "Shakespeare invented over 1,700 English words we still use today.",
        "The Codex Sinaiticus, a 4th-century manuscript, is one of the oldest surviving books.",
        "Reading fiction has been shown to increase empathy by helping you simulate others' minds.",
    ]
    fact_index = int(datetime.now().strftime("%Y%m%d")) % len(FUN_FACTS)

    st.markdown(
        f'<div class="fact-banner">📚 <div><b>Did you know?</b> {FUN_FACTS[fact_index]}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="stat-strip">
            <div class="stat-chip" style="background:linear-gradient(135deg,#8A4FE8,var(--purple-deep));">
                <span class="num">{want_count}</span>
                <span class="lbl">On your TBR</span>
            </div>
            <div class="stat-chip" style="background:linear-gradient(135deg,#16B8B4,var(--teal-deep));">
                <span class="num">{reading_count}</span>
                <span class="lbl">Currently reading</span>
            </div>
            <div class="stat-chip" style="background:linear-gradient(135deg,#FF8A73,var(--coral-deep));">
                <span class="num">{read_count}</span>
                <span class="lbl">Finished</span>
            </div>
            <div class="stat-chip" style="background:linear-gradient(135deg,#FFC55C,var(--gold-deep));">
                <span class="num">🔥 {current_streak}</span>
                <span class="lbl">Day streak</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if current_streak == 0:
        with st.container(border=True):
            st.markdown("**🔥 Start a streak today** — update a shelf, write a review, or drop a thought in a book room.")

    st.markdown(
        '<div class="section-title">What kind of story do you need today?</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-copy">'
        "Tell us the feeling. We'll find the story."
        "</div>",
        unsafe_allow_html=True,
    )

    mood_cols = st.columns(3)

    mood_descriptions = {
        "🌧️ Comfort": "warm blankets in book form",
        "🥀 Make me cry": "bring the tissues",
        "💌 Give me butterflies": "soft hearts & slow burns",
        "🕯️ Something dark": "for your questionable era",
        "🧠 Make me think": "stories that linger",
        "🌱 Fresh start": "a little hope for today",
    }

    mood_card_colors = ["purple", "teal", "coral", "gold"]

    for index, mood in enumerate(MOODS):
        with mood_cols[index % 3]:
            with st.container(border=True):
                st.markdown(
                    f'<div class="mood-card {mood_card_colors[index % 4]}">'
                    f'<div class="mood-card-emoji">{mood}</div>'
                    f'<div class="mood-card-desc">{mood_descriptions[mood]}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Explore ✨",
                    key=f"home_mood_{index}",
                    use_container_width=True,
                ):
                    st.session_state.mood = mood
                    st.session_state.page = "Discover"
                    st.rerun()

    st.markdown(
        '<div class="section-title">✨ A little pick for you</div>',
        unsafe_allow_html=True,
    )

    recommendation = (
        mood_recommendations(st.session_state.mood, 1).iloc[0]
        if st.session_state.mood
        else general_recommendations(1).iloc[0]
    )

    with st.container(border=True):
        c1, c2 = st.columns([1, 2])

        with c1:
            cover_class = random.choice(["", "alt1", "alt2", "alt3"])
            st.markdown(
                cover_html(
                    recommendation["title"], recommendation["authors"],
                    recommendation["genre"], cover_class,
                ),
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(f"### {recommendation['title']}")
            st.caption(f"by {recommendation['authors']}")
            st.write(
                f"⭐ **{float(recommendation['rating_num']):.2f}**"
                f"  ·  🏷️ **{recommendation['genre']}**"
            )

            if st.session_state.mood:
                st.markdown(
                    f'<div class="quote">'
                    f"Picked for your “{st.session_state.mood}” mood."
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="quote">'
                    "A little story for a quiet moment."
                    "</div>",
                    unsafe_allow_html=True,
                )

            cta1, cta2 = st.columns(2)

            with cta1:
                if st.button(
                    "♡ Add to my shelf",
                    key="home_add",
                    use_container_width=True,
                ):
                    save_shelf(
                        recommendation,
                        "Want to Read",
                    )
                    st.success("Added to your TBR ♡")

            with cta2:
                if st.button(
                    "↗ Open book",
                    key="home_open",
                    use_container_width=True,
                ):
                    select_book(recommendation)
                    st.rerun()

    if st.button(
        "↻ Give me another",
        key="home_another",
    ):
        if st.session_state.mood:
            st.session_state.roulette_book = (
                mood_recommendations(
                    st.session_state.mood,
                    1,
                ).iloc[0]
            )
        else:
            st.session_state.roulette_book = (
                general_recommendations(1).iloc[0]
            )
        st.rerun()

    if st.session_state.roulette_book is not None:
        rb = st.session_state.roulette_book
        with st.container(border=True):
            st.markdown("### 🎲 Your next little obsession")
            st.markdown(f"**{rb['title']}**")
            st.caption(f"by {rb['authors']} · ⭐ {float(rb['rating_num']):.2f}")
            if st.button("♡ Save it", key="save_roulette"):
                save_shelf(rb, "Want to Read")
                st.success("Saved to your TBR ♡")

    st.markdown(
        '<div class="section-title">🔥 Trending in your reading world</div>',
        unsafe_allow_html=True,
    )

    trending = books.sort_values(
        "rating_num",
        ascending=False,
    ).head(6)

    cols = st.columns(3)

    for index, (_, book) in enumerate(trending.iterrows()):
        with cols[index % 3]:
            with st.container(border=True):
                cover_class = ["", "alt1", "alt2", "alt3"][index % 4]
                book_heading(book["title"], book["authors"])
                st.markdown(
                    cover_html(
                        book["title"], book["authors"], book["genre"],
                        cover_class, min_height=190,
                    ),
                    unsafe_allow_html=True,
                )
                st.write(f"⭐ {float(book['rating_num']):.2f}")
                if st.button(
                    "Open",
                    key=f"trend_{index}",
                    use_container_width=True,
                ):
                    select_book(book)
                    st.rerun()


# ============================================================
# DISCOVER
# ============================================================

elif st.session_state.page == "Discover":

    st.markdown(
        '<div class="eyebrow">Explore</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-title">Find your next obsession</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-copy">'
        "Search by title, author, mood or genre."
        "</div>",
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Search books",
        value=st.session_state.search_query,
        placeholder="Try “Jane Austen”, “love”, “mystery”...",
        key="discover_search",
    )

    st.session_state.search_query = query

    genres = sorted(
        {
            part.strip()
            for value in books["genre"].dropna().astype(str)
            for part in value.split(",")
            if part.strip()
        }
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        genre = st.selectbox(
            "Genre",
            ["All genres"] + genres,
        )

    with c2:
        min_rating = st.slider(
            "Minimum rating",
            0.0,
            5.0,
            0.0,
            0.1,
        )

    with c3:
        sort_by = st.selectbox(
            "Sort",
            ["Best rated", "A–Z", "Random"],
        )

    with c4:
        view_cols = st.selectbox(
            "Layout",
            ["Grid", "List"],
        )

    if st.session_state.mood:
        clear1, clear2 = st.columns([3, 1])
        with clear1:
            st.info(f"Showing books around your mood: {st.session_state.mood}")
        with clear2:
            if st.button("✕ Clear mood", use_container_width=True):
                st.session_state.mood = None
                st.rerun()

    result = books.copy()

    if query.strip():
        q = query.strip()
        result = result[
            result["title"].str.contains(q, case=False, na=False)
            | result["authors"].str.contains(q, case=False, na=False)
            | result["genre"].str.contains(q, case=False, na=False)
        ]

    if genre != "All genres":
        result = result[
            result["genre"].str.contains(
                genre,
                case=False,
                na=False,
            )
        ]

    result = result[result["rating_num"] >= min_rating]

    if st.session_state.mood and not query.strip() and genre == "All genres":
        result = mood_recommendations(st.session_state.mood, 12)
    elif sort_by == "Best rated":
        result = result.sort_values("rating_num", ascending=False)
    elif sort_by == "A–Z":
        result = result.sort_values("title")
    else:
        result = result.sample(frac=1)

    st.write(f"**{len(result):,} books found**")

    tag_colors = ["purple", "teal", "coral", "gold"]

    if view_cols == "Grid":
        grid = st.columns(3)
        for index, (_, book) in enumerate(result.head(30).iterrows()):
            with grid[index % 3]:
                with st.container(border=True):
                    cover_class = ["", "alt1", "alt2", "alt3"][index % 4]
                    st.markdown(f"**{book['title']}**")
                    st.caption(f"by {book['authors']}")
                    st.markdown(
                        cover_html(
                            book["title"], book["authors"], book["genre"],
                            cover_class, min_height=190,
                        ),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<span class="pill {tag_colors[index % 4]}">⭐ {float(book["rating_num"]):.2f}</span>',
                        unsafe_allow_html=True,
                    )

                    o1, o2 = st.columns(2)
                    with o1:
                        if st.button("Open", key=f"discover_open_{index}", use_container_width=True):
                            select_book(book)
                            st.rerun()
                    with o2:
                        if st.button("♡ Save", key=f"discover_save_{index}", use_container_width=True):
                            save_shelf(book, "Want to Read")
                            st.success("Saved ♡")
    else:
        for index, (_, book) in enumerate(result.head(30).iterrows()):
            with st.container(border=True):
                c1, c2, c3 = st.columns([1.2, 3, 1])

                with c1:
                    cover_class = ["", "alt1", "alt2", "alt3"][index % 4]
                    st.markdown(
                        cover_html(
                            book["title"], book["authors"], book["genre"],
                            cover_class, min_height=170,
                        ),
                        unsafe_allow_html=True,
                    )

                with c2:
                    st.markdown(f"### {book['title']}")
                    st.caption(f"by {book['authors']}")
                    st.write(
                        f"⭐ **{float(book['rating_num']):.2f}**"
                        f"  ·  🏷️ **{book['genre']}**"
                    )

                with c3:
                    if st.button(
                        "Open",
                        key=f"discover_open_list_{index}",
                        use_container_width=True,
                    ):
                        select_book(book)
                        st.rerun()

                    if st.button(
                        "♡ Save",
                        key=f"discover_save_list_{index}",
                        use_container_width=True,
                    ):
                        save_shelf(book, "Want to Read")
                        st.success("Saved ♡")


# ============================================================
# BOOK DETAIL
# ============================================================

elif st.session_state.page == "Book":

    selected = find_book_by_key(
        st.session_state.selected_book
    )

    if selected is None:
        st.session_state.page = "Discover"
        st.rerun()

    book_detail(selected)


# ============================================================
# MY BOOKS
# ============================================================

elif st.session_state.page == "My Books":

    st.markdown(
        '<div class="eyebrow">Your shelves</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-title">My Books</div>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "♡ Want to Read",
            "📖 Currently Reading",
            "✓ Read",
        ]
    )

    for tab, shelf_name in zip(
        tabs,
        ["Want to Read", "Currently Reading", "Read"],
    ):
        with tab:
            rows = get_shelf_books(shelf_name)

            if not rows:
                st.info(
                    "This shelf is waiting for a story ♡"
                )
                continue

            for index, row in enumerate(rows):
                found = find_book_by_key(row[0])

                with st.container(border=True):
                    if found is not None:
                        c1, c2 = st.columns([4, 1])

                        with c1:
                            st.markdown(f"### 📖 {row[1]}")
                            st.caption(f"by {row[2]}")

                            if shelf_name == "Currently Reading":
                                st.progress(
                                    max(0, min(row[3], 100)) / 100
                                )
                                st.caption(
                                    f"{row[3]}% read"
                                )

                        with c2:
                            if st.button(
                                "Open",
                                key=f"mybook_open_{shelf_name}_{index}",
                                use_container_width=True,
                            ):
                                select_book(found)
                                st.rerun()

                            if st.button(
                                "Remove",
                                key=f"mybook_remove_{shelf_name}_{index}",
                                use_container_width=True,
                            ):
                                delete_shelf(found)
                                st.rerun()


# ============================================================
# LISTS — GOODREADS-STYLE CUSTOM SHELVES
# ============================================================

elif st.session_state.page == "Lists":

    st.markdown(
        '<div class="eyebrow">Your own curation</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-title">Lists</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-copy">'
        "Build your own shelves — beach reads, comfort rereads, "
        "books that wrecked you. Whatever your heart wants to group."
        "</div>",
        unsafe_allow_html=True,
    )

    with st.expander("➕ Create a new list", expanded=len(get_all_lists()) == 0):
        new_list_name = st.text_input("List name", placeholder="e.g. Beach Reads 🏖️")
        new_list_color = st.selectbox("Color", LIST_COLORS, format_func=str.title)

        if st.button("Create list"):
            if create_list(new_list_name, new_list_color):
                st.success(f"“{new_list_name.strip()}” is ready ♡")
                st.rerun()
            else:
                st.warning("Give it a name, or that list already exists.")

    all_lists = get_all_lists()

    if not all_lists:
        st.caption("You haven't created any lists yet. Start one above ♡")
    else:
        if st.session_state.active_list not in [row[0] for row in all_lists]:
            st.session_state.active_list = all_lists[0][0]

        chip_cols = st.columns(len(all_lists))
        for i, (name, color, _created) in enumerate(all_lists):
            with chip_cols[i]:
                count = get_list_count(name)
                if st.button(
                    f"{name} ({count})",
                    key=f"list_chip_{name}",
                    use_container_width=True,
                ):
                    st.session_state.active_list = name
                    st.rerun()

        active = st.session_state.active_list
        active_color = next((c for n, c, _ in all_lists if n == active), "purple")

        st.markdown(
            f'<div class="section-title">🗂️ {active}</div>',
            unsafe_allow_html=True,
        )

        items = get_list_items(active)

        if not items:
            st.info("No books in this list yet — add some from Discover or a book's detail page ♡")
        else:
            item_cols = st.columns(3)
            for i, (item_key, title, authors) in enumerate(items):
                with item_cols[i % 3]:
                    with st.container(border=True):
                        cover_class = ["", "alt1", "alt2", "alt3"][i % 4]
                        found = find_book_by_key(item_key)
                        genre_label = found["genre"] if found is not None else "list pick"
                        book_heading(title, authors)
                        st.markdown(
                            cover_html(
                                title, authors, genre_label,
                                cover_class, min_height=160,
                            ),
                            unsafe_allow_html=True,
                        )
                        b1, b2 = st.columns(2)
                        with b1:
                            if found is not None and st.button(
                                "Open", key=f"list_open_{active}_{i}", use_container_width=True
                            ):
                                select_book(found)
                                st.rerun()
                        with b2:
                            if st.button(
                                "Remove", key=f"list_remove_{active}_{i}", use_container_width=True
                            ):
                                remove_from_list(active, item_key)
                                st.rerun()

        with st.expander("🗑️ Delete this list"):
            st.caption("This can't be undone.")
            if st.button(f"Delete “{active}”", key=f"delete_list_{active}"):
                delete_list(active)
                st.session_state.active_list = None
                st.rerun()


# ============================================================
# STREAKS & BADGES
# ============================================================

elif st.session_state.page == "Streaks & Badges":

    st.markdown(
        '<div class="eyebrow">Your reading momentum</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-title">Streaks & Badges</div>',
        unsafe_allow_html=True,
    )

    s1, s2 = st.columns(2)

    with s1:
        with st.container(border=True):
            st.markdown(
                f'<div class="big-number">🔥 {current_streak}</div>',
                unsafe_allow_html=True,
            )
            st.caption("current streak (days)")

    with s2:
        with st.container(border=True):
            st.markdown(
                f'<div class="big-number">🏆 {longest_streak}</div>',
                unsafe_allow_html=True,
            )
            st.caption("longest streak ever")

    st.markdown(
        '<div class="section-copy">'
        "Your streak grows any day you update a shelf, post a review, "
        "or join a book room discussion."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">🎖️ Badges</div>',
        unsafe_allow_html=True,
    )

    badges = compute_achievements()
    unlocked_count = sum(1 for b in badges if b["unlocked"])
    st.caption(f"{unlocked_count} / {len(badges)} unlocked")

    badge_cols = st.columns(5)
    for i, badge in enumerate(badges):
        state_class = "unlocked" if badge["unlocked"] else "locked"
        with badge_cols[i % 5]:
            st.markdown(
                f"""
                <div class="badge-card {state_class} {badge['color']}">
                    <div class="badge-icon">{badge['icon']}</div>
                    <div class="badge-name">{badge['name']}</div>
                    <div class="badge-desc">{badge['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write("")

elif st.session_state.page == "Book Rooms":

    st.markdown(
        '<div class="eyebrow">Community</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-title">Book Rooms</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-copy">'
        "Every book deserves a room where readers can talk."
        "</div>",
        unsafe_allow_html=True,
    )

    selected_title = st.selectbox(
        "Choose a book",
        books["title"].unique(),
    )

    selected = books[
        books["title"] == selected_title
    ].iloc[0]

    with st.container(border=True):
        st.markdown(f"### 📖 {selected['title']}")
        st.caption(f"by {selected['authors']} · {selected['genre']}")

        st.markdown(
            '<div class="quote">'
            "⚠️ Spoiler warning: discussions may contain spoilers."
            "</div>",
            unsafe_allow_html=True,
        )

        message = st.text_area(
            "Join the conversation",
            placeholder="Tell the room what stayed with you...",
            key="room_message",
        )

        if st.button(
            "💌 Post to the room",
            key="post_room",
        ):
            if message.strip():
                add_discussion(
                    selected,
                    message,
                    username,
                )
                st.success("Your thought is in the room ♡")
                st.rerun()

    discussions = get_discussions(selected)

    if discussions:
        for room_user, message, date in discussions:
            with st.container(border=True):
                st.markdown(f"**🌷 {room_user}**")
                st.write(f"“{message}”")
                st.caption(date[:10])
    else:
        st.caption(
            "No one has started the conversation yet. "
            "You could be first ♡"
        )


elif st.session_state.page == "Challenges":

    st.markdown(
        '<div class="eyebrow">Keep reading</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-title">Reading Challenges</div>',
        unsafe_allow_html=True,
    )

    read_count = len(get_shelf_books("Read"))
    target = get_challenge_target()
    progress = min(read_count / max(target, 1), 1)

    with st.container(border=True):
        st.markdown("### 🌷 My 2026 Reading Challenge")
        st.markdown(
            f'<span class="big-number">{read_count}</span>'
            f' <span class="muted">/ {target} books</span>',
            unsafe_allow_html=True,
        )
        st.progress(progress)
        remaining = max(target - read_count, 0)
        st.caption(
            f"{remaining} more to go. One page at a time ♡"
        )

    with st.expander("⚙️ Change my reading goal"):
        new_target = st.number_input(
            "Books this year",
            min_value=1,
            max_value=500,
            value=int(target),
        )

        if st.button("Save goal"):
            set_challenge_target(new_target)
            st.success("Your goal has been updated ♡")
            st.rerun()

    st.markdown(
        '<div class="section-title">✨ Little reading quests</div>',
        unsafe_allow_html=True,
    )

    quests = [
        "Read a book under 200 pages.",
        "Read a book published before 2000.",
        "Read outside your usual genre.",
        "Finish a book you've abandoned.",
        "Read a friend's favorite book.",
        "Read a book with a one-word title.",
        "Read a book that makes you cry.",
        "Read a book you've owned for over a year.",
    ]

    for index, quest in enumerate(quests):
        current = get_quest_status(quest)
        value = st.checkbox(
            quest,
            value=current,
            key=f"quest_{index}",
        )
        if value != current:
            set_quest_status(quest, value)
elif st.session_state.page == "Reading Wrapped":

    st.markdown(
        '<div class="eyebrow">Your year in books</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-title">Reading Wrapped</div>',
        unsafe_allow_html=True,
    )

    all_shelves = get_all_shelves()

    read_rows = [
        row for row in all_shelves
        if row[3] == "Read"
    ]

    if not read_rows:
        with st.container(border=True):
            st.markdown("### Your story is just beginning 🌱")
            st.write(
                "Finish your first book and your reading stats "
                "will start taking shape here."
            )
    else:
        read_keys = {row[0] for row in read_rows}

        read_data = books[
            books.apply(book_key, axis=1).isin(read_keys)
        ].copy()

        total = len(read_data)
        average = read_data["rating_num"].mean()

        genre_counts = (
            read_data["genre"]
            .str.split(",")
            .explode()
            .str.strip()
            .value_counts()
        )

        favorite_genre = (
            genre_counts.index[0]
            if not genre_counts.empty
            else "Fiction"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            with st.container(border=True):
                st.markdown(
                    f'<div class="big-number">{total}</div>',
                    unsafe_allow_html=True,
                )
                st.caption("books read")

        with c2:
            with st.container(border=True):
                st.markdown(
                    f'<div class="big-number">{average:.1f}</div>',
                    unsafe_allow_html=True,
                )
                st.caption("average rating")

        with c3:
            with st.container(border=True):
                st.markdown(
                    f'<div class="big-number">{favorite_genre}</div>',
                    unsafe_allow_html=True,
                )
                st.caption("favorite genre")

        st.markdown(
            '<div class="section-title">Your reading mood</div>',
            unsafe_allow_html=True,
        )

        st.bar_chart(genre_counts.head(8))

        if average >= 4.3:
            personality = "The Enthusiastic Reader"
            description = (
                "You fall hard for books and apparently "
                "have no intention of hiding it."
            )
        elif favorite_genre.lower() in {"romance", "romantic"}:
            personality = "The Soft-Hearted Reader"
            description = (
                "Give you a good love story and you'll "
                "disappear for the afternoon."
            )
        elif favorite_genre.lower() in {"mystery", "thriller", "crime"}:
            personality = "The Midnight Detective"
            description = (
                "You trust suspicious characters approximately zero percent."
            )
        else:
            personality = "The Quiet Observer"
            description = (
                "You like stories that stay with you "
                "long after the final page."
            )

        with st.container(border=True):
            st.markdown(f"### 🌙 {personality}")
            st.write(description)

        st.success(
            "Apparently, you have excellent taste. "
            "Or excellent emotional damage. 🥀"
        )


elif st.session_state.page == "Profile":

    st.markdown(
        '<div class="eyebrow">Your reading identity</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-title">Reader Profile</div>',
        unsafe_allow_html=True,
    )

    profile = get_profile()

    with st.container(border=True):
        st.markdown("### 🌷 Your little reading corner")
        st.write(f"**{profile[0]}**")
        st.caption(profile[1])

        if current_streak > 0:
            st.markdown(
                f'<div class="streak-chip">🔥 {current_streak}-day streak</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        want = len(get_shelf_books("Want to Read"))
        reading = len(get_shelf_books("Currently Reading"))
        read = len(get_shelf_books("Read"))
        badges_unlocked = sum(1 for b in compute_achievements() if b["unlocked"])

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric("TBR", want)

        with c2:
            st.metric("Reading", reading)

        with c3:
            st.metric("Finished", read)

        with c4:
            st.metric("Badges", badges_unlocked)

    with st.expander("✏️ Edit profile"):
        new_username = st.text_input(
            "Name",
            value=profile[0],
        )
        new_bio = st.text_input(
            "Bio",
            value=profile[1],
        )

        if st.button("Save profile"):
            update_profile(new_username, new_bio)
            st.success("Profile updated ♡")
            st.rerun()

    st.markdown(
        '<div class="section-title">💭 Your reading vibe</div>',
        unsafe_allow_html=True,
    )

    st.write("🌙 Stories that linger")
    st.write("☕ Character-driven worlds")
    st.write("🥀 A healthy appreciation for emotional damage")
    st.write("📖 Always one more chapter")

st.markdown(
    '<div class="footer-copy">'
    "made with 📚 + 💜 + a little emotional damage"
    "<br><br>"
    "<b>Bookish</b> · your vivid reading journal ♡"
    "</div>",
    unsafe_allow_html=True,
)

show_notice()