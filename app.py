import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="NextRead", layout="wide", page_icon="📚")

df = pd.read_csv("required.csv", on_bad_lines='skip', encoding='utf-8')

if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# --- Enhanced CSS ---
css = """
<style>
body {
    background: linear-gradient(135deg, #1e1e2f, #121212);
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

.main-title {
    color: #ffdd57;
    font-size: 3.5em;
    font-weight: bold;
    text-align: center;
    margin-top: 30px;
    margin-bottom: 40px;
    animation: fadeIn 1s ease;
}

/* Card styles */
.card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 25px;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    backdrop-filter: blur(10px);
    transition: transform 0.4s ease, box-shadow 0.4s ease;
}
.card:hover {
    transform: scale(1.02);
    box-shadow: 0 15px 30px rgba(255, 215, 0, 0.2);
}

/* Buttons */
button[kind="primary"] {
    background: linear-gradient(to right, #FFD700, #FF8C00);
    color: black !important;
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 0 8px #ffd700;
}
button[kind="primary"]:hover {
    background: linear-gradient(to right, #FF8C00, #FFD700);
    box-shadow: 0 0 15px #ffd700;
    transform: scale(1.05);
}

/* Divider */
hr {
    border: none;
    height: 3px;
    background: linear-gradient(90deg, #FFD700, #FF8C00, #FFD700);
    border-radius: 3px;
    margin-top: 50px;
    margin-bottom: 40px;
    animation: pulseLine 4s infinite;
}

@keyframes pulseLine {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- App Title ---
st.markdown("<h1 class='main-title'>📚 NextRead</h1>", unsafe_allow_html=True)

# --- Book Filter Functions ---
def get_books_by_author(author_name):
    matches = df[df['authors'].str.lower().str.contains(author_name.lower(), na=False)]
    return matches[['title', 'average_ratings', 'authors']] if not matches.empty else None

def get_rating_by_title(book_title):
    matches = df[df['title'].str.lower().str.contains(book_title.lower(), na=False)]
    return matches[['title', 'authors', 'average_ratings']] if not matches.empty else None

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
                ⭐ Average Rating: {row['average_ratings']}
            </div>
        """, unsafe_allow_html=True)
        if st.button(bookmark_text, key=book_id):
            if is_bookmarked:
                st.session_state.bookmarks.remove(book_id)
            else:
                st.session_state.bookmarks.append(book_id)
            st.experimental_rerun()

# --- Search Feature ---
search_type = st.radio("Search by:", ['authors', 'title'], horizontal=True)

if search_type == 'authors':
    author = st.text_input("Enter author name:")
    if author:
        with st.spinner('🔍 Searching books by author...'):
            books = get_books_by_author(author)
        if books is not None:
            st.markdown("### 📘 Books by Author:")
            display_books(books)
        else:
            st.warning(f"No books found for '{author}'.")

elif search_type == 'title':
    title = st.text_input("Enter book title:")
    if title:
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
                ⭐ Average Rating: {bm_data['average_ratings']}
            </div>
        """, unsafe_allow_html=True)
