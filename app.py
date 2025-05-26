import streamlit as st
import pandas as pd
import random

# --- Page Config ---
st.set_page_config(page_title="NextRead", layout="wide", page_icon="📚")

# --- Load Data ---
df = pd.read_csv("required.csv", on_bad_lines='skip', encoding='utf-8')

# --- Initialize bookmarks ---
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# --- CSS Styling (Gradient bg, dark mode, colors, animations) ---
css = """
<style>
/* Full gradient background for the entire app */
body {
    margin: 0;
    min-height: 100vh;
    background: linear-gradient(135deg, #1e1e2f, #2a2a3b, #1e1e2f);
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Streamlit app container transparent to show bg */
.stApp {
    background: transparent !important;
    padding: 20px 40px 40px 40px;
}

/* Title without glow */
.main-title {
    color: #FFD700;  /* Gold */
    font-size: 3.2em;
    font-weight: bold;
    text-align: center;
    margin-top: 30px;
    margin-bottom: 20px;
    text-shadow: none;
}

/* Search input container */
.search-container {
    max-width: 600px;
    margin: 0 auto 40px auto;
}

/* Card styles with subtle gradient and shadow */
.card {
    background: linear-gradient(135deg, #2b2b3c, #1f1f2a);
    color: white;
    box-shadow: 0 6px 15px rgba(255, 215, 0, 0.3);
    border-radius: 15px;
    padding: 20px 25px;
    margin-bottom: 25px;
    animation: fadeIn 1s ease;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.card:hover {
    transform: scale(1.03);
    box-shadow: 0 12px 25px rgba(255, 215, 0, 0.6);
}

/* Fade in effect */
@keyframes fadeIn {
    0% { opacity: 0; transform: translateY(10px); }
    100% { opacity: 1; transform: translateY(0); }
}

/* Bookmark button */
.bookmark-btn {
    background-color: #FFD700;
    color: black;
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    margin-top: 12px;
    font-weight: bold;
    box-shadow: 0 0 6px #FFD700;
    transition: all 0.3s ease;
}
.bookmark-btn:hover {
    background-color: #daa520;
    box-shadow: 0 0 18px #FFD700;
}

/* Divider */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, #FFD700, #FF8C00, #FFD700);
    margin-top: 40px;
    margin-bottom: 40px;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- App Title ---
st.markdown("<h1 class='main-title'>📚 NextRead</h1>", unsafe_allow_html=True)

# --- Search Bar Container ---
with st.container():
    search_type = st.radio("Search by:", ['authors', 'title'], horizontal=True, label_visibility="collapsed")
    if search_type == 'authors':
        author = st.text_input("Enter author name:")
    else:
        title = st.text_input("Enter book title:")

# --- Book Filter Functions ---
def get_books_by_author(author_name):
    matches = df[df['authors'].str.lower().str.contains(author_name.lower(), na=False)]
    return matches[['title', 'average_ratings', 'authors', 'genre']] if not matches.empty else None

def get_rating_by_title(book_title):
    matches = df[df['title'].str.lower().str.contains(book_title.lower(), na=False)]
    return matches[['title', 'authors', 'average_ratings', 'genre']] if not matches.empty else None

# --- Display Book Cards ---
def display_books(books):
    for i, row in books.iterrows():
        book_id = f"{row['title']}|{row['authors']}"
        is_bookmarked = book_id in st.session_state.bookmarks
        bookmark_text = "🔖 Remove Bookmark" if is_bookmarked else "⭐ Bookmark"
        st.markdown(f"""
            <div class='card'>
                <strong>📖 {row['title']}</strong><br>
                ✍️ Author: {row['authors']}<br>
                📚 Genre: {row['genre']}<br>
                ⭐ Average Rating: {row['average_ratings']}
            </div>
        """, unsafe_allow_html=True)
        if st.button(bookmark_text, key=book_id):
            if is_bookmarked:
                st.session_state.bookmarks.remove(book_id)
            else:
                st.session_state.bookmarks.append(book_id)
            st.experimental_rerun()

# --- Search Results ---
if search_type == 'authors' and author:
    with st.spinner('🔍 Searching books by author...'):
        books = get_books_by_author(author)
    if books is not None:
        st.markdown("### 📘 Books by Author:")
        display_books(books)
    else:
        st.warning(f"No books found for '{author}'.")
elif search_type == 'title' and title:
    with st.spinner('🔍 Searching books by title...'):
        books = get_rating_by_title(title)
    if books is not None:
        st.markdown("### 📘 Matching Book(s):")
        display_books(books)
    else:
        st.warning(f"No books found with title '{title}'.")

# --- Surprise Me ---
st.markdown("<hr>", unsafe_allow_html=True)
if st.button("🎲 Surprise Me!"):
    random_book = df.sample(1).iloc[0]
    book_id = f"{random_book['title']}|{random_book['authors']}"
    is_bookmarked = book_id in st.session_state.bookmarks
    bookmark_text = "🔖 Remove Bookmark" if is_bookmarked else "⭐ Bookmark"
    st.markdown(f"""
        <div class='card'>
            <strong>📖 {random_book['title']}</strong><br>
            ✍️ Author: {random_book['authors']}<br>
            📚 Genre: {random_book['genre']}<br>
            ⭐ Average Rating: {random_book['average_ratings']}
        </div>
    """, unsafe_allow_html=True)
    if st.button(bookmark_text, key="surprise_" + book_id):
        if is_bookmarked:
            st.session_state.bookmarks.remove(book_id)
        else:
            st.session_state.bookmarks.append(book_id)
        st.experimental_rerun()

# --- Bookmarks Section ---
if st.session_state.bookmarks:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🔖 Your Bookmarks")
    for bm in st.session_state.bookmarks:
        title, author = bm.split("|")
        bm_data = df[(df['title'] == title) & (df['authors'] == author)].iloc[0]
        st.markdown(f"""
            <div class='card'>
                <strong>📖 {bm_data['title']}</strong><br>
                ✍️ Author: {bm_data['authors']}<br>
                📚 Genre: {bm_data['genre']}<br>
                ⭐ Average Rating: {bm_data['average_ratings']}
            </div>
        """, unsafe_allow_html=True)
