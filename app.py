import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Bookish",
    page_icon="🌷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATABASE
# ============================================================

DB_NAME = "bookish.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shelves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_key TEXT UNIQUE,
            shelf TEXT,
            progress INTEGER DEFAULT 0,
            added_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_key TEXT,
            rating REAL,
            review TEXT,
            reaction TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discussions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_key TEXT,
            username TEXT,
            message TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_name TEXT,
            target INTEGER,
            completed INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


create_database()


# ============================================================
# LOAD BOOK DATA
# ============================================================

@st.cache_data
def load_books():

    try:

        data = pd.read_csv(
            "required.csv",
            encoding="utf-8",
            on_bad_lines="skip"
        )

        data.columns = data.columns.str.strip()

        required_columns = [
            "title",
            "authors",
            "average_ratings",
            "genre"
        ]

        for column in required_columns:

            if column not in data.columns:
                data[column] = "Unknown"

        return data

    except FileNotFoundError:

        st.error(
            "required.csv was not found. "
            "Place it in the same folder as app.py."
        )

        st.stop()


books = load_books()


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "random_book" not in st.session_state:
    st.session_state.random_book = None

if "selected_book" not in st.session_state:
    st.session_state.selected_book = None


# ============================================================
# STYLING
# ============================================================

st.markdown("""
<style>

@import url(
'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&
family=Playfair+Display:wght@500;600;700&
family=Pacifico&display=swap'
);

* {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at 10% 10%,
            #ffeaf2 0,
            transparent 25%
        ),
        radial-gradient(
            circle at 90% 20%,
            #e9f2ff 0,
            transparent 25%
        ),
        #fffaf7;
}

/* SIDEBAR */

[data-testid="stSidebar"] {

    background:
        linear-gradient(
            180deg,
            #fff4f7,
            #f7f1ff
        );

    border-right: 1px solid #f1dce5;
}

[data-testid="stSidebar"] * {
    color: #44353b !important;
}

/* BRAND */

.logo {

    font-family: 'Pacifico', cursive;

    font-size: 38px;

    color: #c66b91;

    text-align: center;

    margin-bottom: 0;
}

.tagline {

    text-align: center;

    color: #927985;

    font-size: 13px;

    margin-bottom: 25px;
}

/* HERO */

.hero {

    background:
        linear-gradient(
            135deg,
            #fff0f5,
            #f5efff
        );

    border-radius: 28px;

    padding: 42px;

    margin-bottom: 28px;

    border: 1px solid #f3dfe9;

    box-shadow:
        0 15px 45px
        rgba(180, 120, 150, 0.08);
}

.hero h1 {

    font-family: 'Playfair Display', serif;

    color: #49363f;

    font-size: 45px;

    margin-bottom: 5px;
}

.hero p {

    color: #806f78;

    font-size: 17px;
}

/* SECTION */

.section-title {

    font-family: 'Playfair Display', serif;

    color: #49363f;

    font-size: 29px;

    margin-top: 30px;

    margin-bottom: 15px;
}

/* BOOK CARD */

.book-card {

    background: rgba(255,255,255,0.9);

    border: 1px solid #f0e3e7;

    border-radius: 22px;

    padding: 23px;

    margin-bottom: 18px;

    box-shadow:
        0 8px 30px
        rgba(100,70,80,0.06);

    transition: 0.25s;
}

.book-card:hover {

    transform: translateY(-4px);

    box-shadow:
        0 15px 35px
        rgba(100,70,80,0.10);
}

.book-title {

    font-family: 'Playfair Display', serif;

    font-size: 22px;

    font-weight: 700;

    color: #46343b;
}

.book-author {

    color: #a07889;

    margin: 5px 0 15px;
}

.book-meta {

    color: #75666c;

    font-size: 14px;

    line-height: 1.8;
}

/* MOOD CARD */

.mood-card {

    background: white;

    border-radius: 20px;

    padding: 22px;

    text-align: center;

    border: 1px solid #f0e2e8;

    min-height: 120px;
}

.mood-card:hover {

    border-color: #d99ab4;

}

/* STAT CARD */

.stat-card {

    background: white;

    border-radius: 20px;

    padding: 20px;

    text-align: center;

    border: 1px solid #f0e2e8;
}

.stat-number {

    font-size: 30px;

    font-weight: 700;

    color: #c06b91;
}

.stat-label {

    font-size: 13px;

    color: #8b7b82;
}

/* BUTTON */

.stButton > button {

    border-radius: 12px;

    border: 1px solid #e4ccd7;

    background: white;

    color: #704f5d;

    font-weight: 600;

    transition: 0.2s;
}

.stButton > button:hover {

    border-color: #c66b91;

    color: #c66b91;

    transform: translateY(-1px);
}

/* FOOTER */

.footer {

    text-align: center;

    color: #a18f97;

    padding: 40px 0 20px;

    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE HELPERS
# ============================================================

def make_key(book):

    return (
        str(book["title"])
        + "||"
        + str(book["authors"])
    )


def get_shelf(book_key):

    conn = get_connection()

    result = conn.execute(
        """
        SELECT shelf, progress
        FROM shelves
        WHERE book_key = ?
        """,
        (book_key,)
    ).fetchone()

    conn.close()

    if result:
        return result[0], result[1]

    return None, 0


def save_to_shelf(book, shelf):

    key = make_key(book)

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO shelves
        (book_key, shelf, added_at)
        VALUES (?, ?, ?)

        ON CONFLICT(book_key)
        DO UPDATE SET shelf = excluded.shelf
        """,
        (
            key,
            shelf,
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()


def remove_from_shelf(book):

    key = make_key(book)

    conn = get_connection()

    conn.execute(
        "DELETE FROM shelves WHERE book_key = ?",
        (key,)
    )

    conn.commit()
    conn.close()


def get_shelf_books(shelf):

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT book_key
        FROM shelves
        WHERE shelf = ?
        """,
        (shelf,)
    ).fetchall()

    conn.close()

    return [row[0] for row in rows]


def save_review(book, rating, review, reaction):

    key = make_key(book)

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO reviews
        (book_key, rating, review, reaction, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            key,
            rating,
            review,
            reaction,
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()


def add_discussion(book, message):

    key = make_key(book)

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO discussions
        (book_key, username, message, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            key,
            "Reader",
            message,
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()


# ============================================================
# BOOK CARD
# ============================================================

def display_book(book, key_prefix):

    title = str(book["title"])

    author = str(book["authors"])

    genre = str(book["genre"])

    rating = str(book["average_ratings"])

    book_key = make_key(book)

    shelf, progress = get_shelf(book_key)

    st.markdown(
        f"""
        <div class="book-card">

            <div class="book-title">
                📖 {title}
            </div>

            <div class="book-author">
                by {author}
            </div>

            <div class="book-meta">

                ⭐ <b>{rating}</b>

                &nbsp;&nbsp; • &nbsp;&nbsp;

                🏷️ {genre}

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        shelf_option = st.selectbox(
            "Shelf",
            [
                "Not added",
                "Want to Read",
                "Currently Reading",
                "Read"
            ],
            index=(
                [
                    "Not added",
                    "Want to Read",
                    "Currently Reading",
                    "Read"
                ].index(shelf)
                if shelf in [
                    "Want to Read",
                    "Currently Reading",
                    "Read"
                ]
                else 0
            ),
            key=f"shelf_{key_prefix}_{book_key}"
        )

    with c2:

        if st.button(
            "💾 Save",
            key=f"save_{key_prefix}_{book_key}"
        ):

            if shelf_option == "Not added":

                remove_from_shelf(book)

            else:

                save_to_shelf(
                    book,
                    shelf_option
                )

            st.success("Shelf updated!")

            st.rerun()

    with c3:

        if st.button(
            "💭 Review",
            key=f"review_{key_prefix}_{book_key}"
        ):

            st.session_state.selected_book = book

            st.session_state.page = "Reviews"

            st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="logo">Bookish</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="tagline">your little reading corner ♡</div>',
        unsafe_allow_html=True
    )

    st.divider()

    pages = [
        "🏠 Home",
        "🔎 Discover",
        "📚 My Books",
        "💬 Book Rooms",
        "🎯 Challenges",
        "📊 Reading Wrapped",
        "👤 Profile"
    ]

    selected_page = st.radio(
        "Explore",
        pages,
        label_visibility="collapsed"
    )

    st.session_state.page = selected_page.replace(
        "🏠 ", ""
    ).replace(
        "🔎 ", ""
    ).replace(
        "📚 ", ""
    ).replace(
        "💬 ", ""
    ).replace(
        "🎯 ", ""
    ).replace(
        "📊 ", ""
    ).replace(
        "👤 ", ""
    )

    st.divider()

    st.caption("Made for people who read with their whole heart ♡")


# ============================================================
# HOME
# ============================================================

if st.session_state.page == "Home":

    st.markdown(
        """
        <div class="hero">

            <h1>Good evening, reader 🌙</h1>

            <p>
            Your next favorite story might be one click away.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">'
        'What kind of story do you need today?'
        '</div>',
        unsafe_allow_html=True
    )

    moods = [
        ("🌧️", "I need comfort"),
        ("🥀", "Make me cry"),
        ("🧠", "Make me think"),
        ("🕯️", "Something dark"),
        ("💌", "Give me butterflies"),
        ("🌱", "I need a fresh start")
    ]

    mood_cols = st.columns(3)

    for index, (emoji, mood) in enumerate(moods):

        with mood_cols[index % 3]:

            st.markdown(
                f"""
                <div class="mood-card">

                    <div style="font-size:32px;">
                        {emoji}
                    </div>

                    <b>{mood}</b>

                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "Explore",
                key=f"mood_{index}",
                use_container_width=True
            ):

                st.session_state.page = "Discover"

                st.rerun()

    st.markdown(
        '<div class="section-title">'
        '✨ A little pick for you'
        '</div>',
        unsafe_allow_html=True
    )

    recommendation = books.sample(1).iloc[0]

    display_book(
        recommendation,
        "home_recommendation"
    )


# ============================================================
# DISCOVER
# ============================================================

elif st.session_state.page == "Discover":

    st.markdown(
        '<div class="section-title">'
        '🔎 Find your next obsession'
        '</div>',
        unsafe_allow_html=True
    )

    query = st.text_input(
        "Search",
        placeholder="Search by title or author..."
    )

    col1, col2 = st.columns(2)

    with col1:

        genre_options = ["All"]

        if "genre" in books.columns:

            genre_options += sorted(
                books["genre"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        selected_genre = st.selectbox(
            "Genre",
            genre_options
        )

    with col2:

        minimum_rating = st.slider(
            "Minimum rating",
            0.0,
            5.0,
            0.0,
            0.1
        )

    filtered = books.copy()

    if query:

        mask = (
            filtered["title"]
            .astype(str)
            .str.contains(
                query,
                case=False,
                na=False
            )
            |
            filtered["authors"]
            .astype(str)
            .str.contains(
                query,
                case=False,
                na=False
            )
        )

        filtered = filtered[mask]

    if selected_genre != "All":

        filtered = filtered[
            filtered["genre"]
            .astype(str)
            .str.contains(
                selected_genre,
                case=False,
                na=False
            )
        ]

    filtered["rating_numeric"] = pd.to_numeric(
        filtered["average_ratings"],
        errors="coerce"
    )

    filtered = filtered[
        filtered["rating_numeric"]
        .fillna(0)
        >= minimum_rating
    ]

    st.write(
        f"**{len(filtered):,} books found**"
    )

    for index, (_, book) in enumerate(
        filtered.head(30).iterrows()
    ):

        display_book(
            book,
            f"discover_{index}"
        )


# ============================================================
# MY BOOKS
# ============================================================

elif st.session_state.page == "My Books":

    st.markdown(
        '<div class="section-title">'
        '📚 My Books'
        '</div>',
        unsafe_allow_html=True
    )

    shelf_tabs = st.tabs(
        [
            "♡ Want to Read",
            "📖 Currently Reading",
            "✓ Read"
        ]
    )

    shelves = [
        "Want to Read",
        "Currently Reading",
        "Read"
    ]

    for tab, shelf_name in zip(
        shelf_tabs,
        shelves
    ):

        with tab:

            saved_keys = get_shelf_books(
                shelf_name
            )

            found = False

            for index, (_, book) in enumerate(
                books.iterrows()
            ):

                if make_key(book) in saved_keys:

                    found = True

                    display_book(
                        book,
                        f"{shelf_name}_{index}"
                    )

            if not found:

                st.info(
                    "Nothing here yet. "
                    "Go discover something beautiful ♡"
                )


# ============================================================
# BOOK ROOMS
# ============================================================

elif st.session_state.page == "Book Rooms":

    st.markdown(
        '<div class="section-title">'
        '💬 Book Rooms'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "A cozy little corner to talk about books."
    )

    selected_title = st.selectbox(
        "Choose a book",
        books["title"].dropna().astype(str).unique()
    )

    selected = books[
        books["title"].astype(str)
        == selected_title
    ].iloc[0]

    st.markdown(
        f"""
        <div class="book-card">

            <div class="book-title">
                📖 {selected["title"]}
            </div>

            <div class="book-author">
                by {selected["authors"]}
            </div>

            <p>
                💭 What did you think about this book?
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    message = st.text_area(
        "Share your thoughts",
        placeholder="This ending completely broke me..."
    )

    if st.button("💌 Post to the room"):

        if message.strip():

            add_discussion(
                selected,
                message
            )

            st.success(
                "Your thought has been added 💗"
            )

            st.rerun()

    conn = get_connection()

    discussions = conn.execute(
        """
        SELECT username, message, created_at
        FROM discussions
        WHERE book_key = ?
        ORDER BY id DESC
        """,
        (make_key(selected),)
    ).fetchall()

    conn.close()

    for username, message, date in discussions:

        st.markdown(
            f"""
            <div class="book-card">

                <b>🌷 {username}</b>

                <p>{message}</p>

                <small>
                    {date[:10]}
                </small>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# CHALLENGES
# ============================================================

elif st.session_state.page == "Challenges":

    st.markdown(
        '<div class="section-title">'
        '🎯 Reading Challenges'
        '</div>',
        unsafe_allow_html=True
    )

    read_books = get_shelf_books("Read")

    completed = len(read_books)

    target = 30

    progress = min(
        completed / target,
        1
    )

    st.markdown(
        f"""
        <div class="book-card">

            <h2>
                🌷 My 2026 Reading Challenge
            </h2>

            <h1>
                {completed} / {target}
            </h1>

            <p>
                books completed
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.progress(progress)

    st.markdown(
        '<div class="section-title">'
        '✨ Monthly quests'
        '</div>',
        unsafe_allow_html=True
    )

    quests = [
        "Read a book under 200 pages.",
        "Read a book published before 2000.",
        "Read a book you've owned for over a year.",
        "Read a book with a blue cover.",
        "Read a book outside your usual genre.",
        "Read a book recommended by a friend."
    ]

    for quest in quests:

        st.checkbox(
            quest,
            key=f"quest_{quest}"
        )


# ============================================================
# READING WRAPPED
# ============================================================

elif st.session_state.page == "Reading Wrapped":

    st.markdown(
        '<div class="section-title">'
        '📊 Your Reading Wrapped'
        '</div>',
        unsafe_allow_html=True
    )

    read_keys = get_shelf_books("Read")

    read_books = []

    for _, book in books.iterrows():

        if make_key(book) in read_keys:

            read_books.append(book)

    total_read = len(read_books)

    if total_read == 0:

        st.info(
            "Finish your first book to unlock your reading stats ✨"
        )

    else:

        col1, col2, col3 = st.columns(3)

        with col1:

            st.markdown(
                f"""
                <div class="stat-card">

                    <div class="stat-number">
                        {total_read}
                    </div>

                    <div class="stat-label">
                        Books Read
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        ratings = pd.to_numeric(
            [
                book["average_ratings"]
                for book in read_books
            ],
            errors="coerce"
        )

        average_rating = ratings.mean()

        with col2:

            st.markdown(
                f"""
                <div class="stat-card">

                    <div class="stat-number">
                        {average_rating:.1f}
                    </div>

                    <div class="stat-label">
                        Average Rating
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:

            genres = [
                str(book["genre"])
                for book in read_books
            ]

            favorite_genre = (
                pd.Series(genres)
                .value_counts()
                .index[0]
            )

            st.markdown(
                f"""
                <div class="stat-card">

                    <div class="stat-number">
                        {favorite_genre}
                    </div>

                    <div class="stat-label">
                        Favorite Genre
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            '<div class="section-title">'
            '📚 Your reading history'
            '</div>',
            unsafe_allow_html=True
        )

        genre_counts = pd.Series(
            [
                str(book["genre"])
                for book in read_books
            ]
        ).value_counts()

        st.bar_chart(
            genre_counts
        )

        st.success(
            "Apparently, you have excellent taste. "
            "Or excellent emotional damage. 🥀"
        )


# ============================================================
# PROFILE
# ============================================================

elif st.session_state.page == "Profile":

    st.markdown(
        '<div class="section-title">'
        '👤 Your Reader Profile'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero">

            <h1>
                🌷 The Quiet Reader
            </h1>

            <p>
                You like stories that stay with you
                long after the final page.
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Books saved",
            len(
                get_shelf_books(
                    "Want to Read"
                )
            )
        )

    with col2:

        st.metric(
            "Currently reading",
            len(
                get_shelf_books(
                    "Currently Reading"
                )
            )
        )

    with col3:

        st.metric(
            "Books finished",
            len(
                get_shelf_books(
                    "Read"
                )
            )
        )

    st.markdown(
        '<div class="section-title">'
        '💭 Your reading vibe'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "🌙 Emotional stories"
    )

    st.write(
        "☕ Character-driven fiction"
    )

    st.write(
        "🥀 Books that hurt a little"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">

        made with 📚 + ☕ + a little emotional damage

        <br><br>

        <b>Bookish</b> · your little reading corner ♡

    </div>
    """,
    unsafe_allow_html=True
)
