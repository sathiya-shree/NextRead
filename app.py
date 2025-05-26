import streamlit as st
import pandas as pd
import random

# --- Page Config ---
st.set_page_config(page_title="NextRead", layout="wide", page_icon="📚")

# --- Load Data ---
df = pd.read_csv("required.csv", on_bad_lines='skip', encoding='utf-8')
df = df[['title', 'authors', 'genres', 'average_ratings']]
df.dropna(subset=['title', 'authors', 'genres', 'average_ratings'], inplace=True)

# --- Shuffle the dataset to avoid fixed order ---
df = df.sample(frac=1).reset_index(drop=True)

# --- Initialize bookmarks ---
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# --- CSS Styling ---
css = """
<style>
body {
    background: linear-gradient(135deg, #1e1e2f 0%, #121212 100%);
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.main-title {
    color: #FFD700;
    font-size: 3.2em;
    font-weight: bold;
    text-align: center;
    margin-top: 30px;
    margin-bottom: 40px;
    text-shadow: none;
}

.card {
    background: linear-gradient(145deg, #2a2a3b, #1a1a2f);
    color: white;
    box-shadow: 0 6px 15px rgba(255,255,255,0.05);
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 25px;
    animation: fadeIn 1s ease;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.card:hover {
    transform: scale(1.02);
    box-shadow: 0 10px 25px rgba(255,255,255,0.15);
}

@keyframes fadeIn {
    0% { opacity: 0; transform: translateY(10px); }
    100% { opacity: 1; transform: translateY(0); }
}

.bookmark-btn {
    background-color: #FFD700;
    color: black;
    padding: 7px 12px;
    border-radius: 5px;
    border: none;
    cursor: pointer;
    margin-top: 10px;
    font-weight: bold;
    box-shadow: 0 0 5px #FFD700;
    transition: all 0.3s ease;
}
.bookmark-btn:hover {
    background-color: #daa520;
    box-shadow: 0 0 15px #FFD700;
}

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

# --- Title ---
st.markdown("<h1 class='main-title'>📚 NextRead</h1>", unsafe_allow_html=True)

# --- Filter Functions ---
def get_books_by_author(author_name):
    matches = df[df['authors'].str.lower().str.contains(author_name.lower(), na=False)]
    return matches[['title', 'authors', 'genres', 'average_ratings']] if not matches.empty else None

def get_rating_by_title(book_title):
    matches = df[df['title'].str.lower().str.contains(book_title.lower(), na=False)]
    return matches[['title', 'authors', 'genres', 'average_ratings']] if not matches.empty else None

# --- Display Function ---
def display_books(books):
    for _, row in books.iterrows():
        book_id = f"{row['title']}|{row['authors']}"
        is_bookmarked = book_id in st.session_state.bookmarks
        bookmark_text = "🔖 Remove Bookmark" if is_bookmarked else "⭐ Bookmark"
        st.markdown(f"""
            <div class='card'>
                <strong>📖 {row['title']}</strong><br>
                ✍️ Author: {row['authors']}<br>
                📚 Genre: {row['genres']}<br>
                ⭐ Average Rating: {row['average_ratings']}
            </div>
        """, unsafe_allow_html=True)
        if st.button(bookmark_text, key=book_id):
            if is_bookmarked:
                st.session_state.bookmarks.remove(book_id)
            else:
                st.session_state.bookmarks.append(book_id)
            st.experimental_rerun()

# --- Reader's Picks ---
st.markdown("### 🔥 Reader’s Picks")
readers_picks = df.sample(5)
display_books(readers_picks)

# --- Search Section ---
st.markdown("<hr>", unsafe_allow_html=True)
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
            📚 Genre: {random_book['genres']}<br>
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
                📚 Genre: {bm_data['genres']}<br>
                ⭐ Average Rating: {bm_data['average_ratings']}
            </div>
        """, unsafe_allow_html=True)
