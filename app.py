import streamlit as st
import pandas as pd
import random

# ============================================================
# APP CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="BookNest",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM DESIGN
# ============================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #f7f5f2;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #24201d;
}

[data-testid="stSidebar"] * {
    color: #f5f1eb !important;
}

/* Main heading */
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 54px;
    font-weight: 700;
    color: #29231f;
    margin-bottom: 0;
}

.hero-subtitle {
    color: #756d66;
    font-size: 18px;
    margin-top: 5px;
    margin-bottom: 35px;
}

/* Section heading */
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    color: #302923;
    margin-top: 20px;
}

/* Book card */
.book-card {
    background: white;
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 18px;
    border: 1px solid #e9e3dc;
    box-shadow: 0 5px 20px rgba(50, 40, 30, 0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.book-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(50, 40, 30, 0.10);
}

.book-title {
    font-family: 'Playfair Display', serif;
    font-size: 23px;
    font-weight: 700;
    color: #2d2621;
}

.book-author {
    color: #7a6d62;
    margin-top: 5px;
    margin-bottom: 15px;
}

.book-info {
    color: #554b44;
    font-size: 14px;
    line-height: 1.8;
}

/* Metric cards */
.metric-box {
    background: white;
    padding: 18px;
    border-radius: 15px;
    text-align: center;
    border: 1px solid #e9e3dc;
}

.metric-number {
    font-size: 28px;
    font-weight: 700;
    color: #7c5c45;
}

.metric-label {
    font-size: 13px;
    color: #81766d;
}

/* Buttons */
.stButton > button {
    border-radius: 10px;
    border: 1px solid #d8cfc6;
    background: #fff;
    color: #4b4038;
    font-weight: 600;
}

.stButton > button:hover {
    border-color: #8b6a51;
    color: #8b6a51;
}

/* Search inputs */
.stTextInput input {
    border-radius: 12px;
    border: 1px solid #ddd5cd;
    background: white;
}

/* Select boxes */
.stSelectbox div[data-baseweb="select"] > div {
    border-radius: 12px;
}

/* Footer */
.footer {
    text-align: center;
    color: #8b8179;
    margin-top: 60px;
    padding: 25px;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_books():
    try:
        books = pd.read_csv(
            "required.csv",
            encoding="utf-8",
            on_bad_lines="skip"
        )

        books.columns = books.columns.str.strip()

        return books

    except FileNotFoundError:
        st.error("required.csv could not be found.")
        st.stop()

    except Exception as error:
        st.error(f"Unable to load the book database: {error}")
        st.stop()


books_df = load_books()


# ============================================================
# SESSION STATE
# ============================================================

if "saved_books" not in st.session_state:
    st.session_state.saved_books = []

if "random_book" not in st.session_state:
    st.session_state.random_book = None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def book_key(book):
    """Create a unique identifier for a book."""
    return f"{book['title']}::{book['authors']}"


def search_books(keyword, column):
    """Search the database using a selected column."""

    if not keyword.strip():
        return pd.DataFrame()

    search_value = keyword.strip().lower()

    matches = books_df[
        books_df[column]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.contains(search_value, na=False)
    ]

    return matches


def toggle_saved(book):
    """Add or remove a book from saved books."""

    identifier = book_key(book)

    if identifier in st.session_state.saved_books:
        st.session_state.saved_books.remove(identifier)
    else:
        st.session_state.saved_books.append(identifier)


def is_saved(book):
    return book_key(book) in st.session_state.saved_books


def show_book(book, button_prefix="book"):
    """Display one book as a card."""

    title = str(book.get("title", "Unknown Title"))
    author = str(book.get("authors", "Unknown Author"))
    genre = str(book.get("genre", "Not specified"))
    rating = str(book.get("average_ratings", "N/A"))

    saved = is_saved(book)

    st.markdown(
        f"""
        <div class="book-card">

            <div class="book-title">
                {title}
            </div>

            <div class="book-author">
                by {author}
            </div>

            <div class="book-info">
                📚 <b>Genre:</b> {genre}<br>
                ⭐ <b>Average Rating:</b> {rating}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    button_label = "💔 Remove from Library" if saved else "♡ Save to Library"

    if st.button(
        button_label,
        key=f"{button_prefix}_{book_key(book)}"
    ):
        toggle_saved(book)
        st.rerun()


def get_book_count():
    return len(books_df)


def get_genre_count():
    if "genre" not in books_df.columns:
        return 0

    return books_df["genre"].dropna().nunique()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <h1 style="font-family: 'Playfair Display';">
        📚 BookNest
        </h1>
        """,
        unsafe_allow_html=True
    )

    st.caption("Find your next favorite read.")

    st.divider()

    page = st.radio(
        "Navigate",
        [
            "🔎 Discover",
            "🎲 Random Pick",
            "🔖 My Library"
        ]
    )

    st.divider()

    st.markdown("### Database")

    st.write(f"📚 {get_book_count():,} books")

    st.write(f"🏷️ {get_genre_count():,} genres")

    st.write(
        f"🔖 {len(st.session_state.saved_books)} saved"
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<div class="hero-title">Find a book worth getting lost in.</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="hero-subtitle">'
    'Search the collection, discover something unexpected, '
    'and build your personal reading shelf.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# DISCOVER PAGE
# ============================================================

if page == "🔎 Discover":

    # Statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-number">
                    {len(books_df):,}
                </div>
                <div class="metric-label">
                    Books Available
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-number">
                    {get_genre_count():,}
                </div>
                <div class="metric-label">
                    Genres
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-number">
                    {len(st.session_state.saved_books)}
                </div>
                <div class="metric-label">
                    In Your Library
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        '<div class="section-title">Search the collection</div>',
        unsafe_allow_html=True
    )

    search_column = st.selectbox(
        "Search using",
        ["title", "authors"],
        format_func=lambda value: {
            "title": "📖 Book Title",
            "authors": "✍️ Author"
        }[value]
    )

    query = st.text_input(
        "Search",
        placeholder="Start typing a book or author's name..."
    )

    if query:

        results = search_books(query, search_column)

        if results.empty:

            st.warning(
                f"No books found for **{query}**."
            )

        else:

            st.success(
                f"Found {len(results)} matching book(s)."
            )

            for index, (_, book) in enumerate(results.iterrows()):

                show_book(
                    book,
                    button_prefix=f"search_{index}"
                )


# ============================================================
# RANDOM PAGE
# ============================================================

elif page == "🎲 Random Pick":

    st.markdown(
        '<div class="section-title">Let the bookshelf decide.</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Not sure what to read? Pick a book completely at random."
    )

    if st.button("✨ Pick a Book", use_container_width=True):

        st.session_state.random_book = (
            books_df.sample(1).iloc[0]
        )

        st.rerun()

    if st.session_state.random_book is not None:

        st.markdown("### Your random pick")

        show_book(
            st.session_state.random_book,
            button_prefix="random"
        )


# ============================================================
# MY LIBRARY
# ============================================================

elif page == "🔖 My Library":

    st.markdown(
        '<div class="section-title">My Reading Library</div>',
        unsafe_allow_html=True
    )

    saved_ids = st.session_state.saved_books

    if not saved_ids:

        st.info(
            "Your library is empty. Search for a book and save it here."
        )

    else:

        saved_data = []

        for identifier in saved_ids:

            title, author = identifier.split("::", 1)

            match = books_df[
                (books_df["title"].astype(str) == title) &
                (books_df["authors"].astype(str) == author)
            ]

            if not match.empty:
                saved_data.append(match.iloc[0])

        if saved_data:

            st.write(
                f"You have saved **{len(saved_data)} book(s)**."
            )

            for index, book in enumerate(saved_data):

                show_book(
                    book,
                    button_prefix=f"library_{index}"
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        BookNest · Your next story is waiting 📖
    </div>
    """,
    unsafe_allow_html=True
)
