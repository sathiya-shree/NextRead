import streamlit as st
import pandas as pd
import random

# --- Page Setup ---
st.set_page_config(page_title="NextRead", layout="wide")

# --- Load Data ---
df = pd.read_csv("required.csv", on_bad_lines='skip', encoding='utf-8')

# --- Bookmarks ---
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# --- Starry Night CSS with Moon & Shooting Stars ---
st.markdown("""
<style>
/* Basic Reset */
html, body, [class*="css"] {
    background: black !important;
    color: white !important;
}

/* Starry Sky */
body::before {
    content: '';
    position: fixed;
    width: 100%;
    height: 100%;
    background: black;
    z-index: -3;
}

/* Twinkling Stars */
@keyframes twinkle {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 0.2; }
}
.star {
    position: fixed;
    width: 2px;
    height: 2px;
    background: white;
    animation: twinkle 2s infinite;
    z-index: -2;
}
""", unsafe_allow_html=True)

# Add stars dynamically
for _ in range(100):
    top = random.randint(0, 100)
    left = random.randint(0, 100)
    st.markdown(f"""
    <div class="star" style="top: {top}vh; left: {left}vw;"></div>
    """, unsafe_allow_html=True)

# Add moon
st.markdown("""
<style>
.moon {
    position: fixed;
    top: 50px;
    right: 100px;
    width: 100px;
    height: 100px;
    background: radial-gradient(circle at 30% 30%, #fdfcdc, #dcdcdc);
    border-radius: 50%;
    box-shadow: 0 0 60px #fdfcdc;
    z-index: -1;
}
</style>
<div class="moon"></div>
""", unsafe_allow_html=True)

# Add shooting stars
st.markdown("""
<style>
@keyframes shoot {
  0% { transform: translateX(0) translateY(0); opacity: 1; }
  100% { transform: translateX(-100vw) translateY(100vh); opacity: 0; }
}
.shooting-star {
    position: fixed;
    top: 10%;
    left: 90%;
    width: 2px;
    height: 100px;
    background: linear-gradient(white, transparent);
    transform: rotate(-45deg);
    animation: shoot 3s infinite linear;
    z-index: -2;
}
</style>
<div class="shooting-star"></div>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<h1 style='text-align: center;'>📚 NextRead</h1>", unsafe_allow_html=True)

# --- Helper Functions ---
def get_books_by_author(author_name):
    matches = df[df['authors'].str.lower().str.contains(author_name.lower(), na=False)]
    return matches[['title', 'average_ratings', 'authors']] if not matches.empty else None

def get_rating_by_title(book_title):
    matches = df[df['title'].str.lower().str.contains(book_title.lower(), na=False)]
    return matches[['title', 'authors', 'average_ratings']] if not matches.empty else None

def display_books(books):
    for _, row in books.iterrows():
        book_id = f"{row['title']}|{row['authors']}"
        is_bookmarked = book_id in st.session_state.bookmarks
        bookmark_text = "🔖 Remove Bookmark" if is_bookmarked else "⭐ Bookmark"
        st.markdown(f"""
            <div style="background-color: #1e1e1ecc; padding: 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(255,255,255,0.2);">
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

# --- Search UI ---
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
st.markdown("---")
if st.button("🎲 Surprise Me!"):
    random_book = df.sample(1).iloc[0]
    book_id = f"{random_book['title']}|{random_book['authors']}"
    is_bookmarked = book_id in st.session_state.bookmarks
    bookmark_text = "🔖 Remove Bookmark" if is_bookmarked else "⭐ Bookmark"
    st.markdown(f"""
        <div style="background-color: #1e1e1ecc; padding: 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(255,255,255,0.2);">
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

# --- Bookmarks ---
if st.session_state.bookmarks:
    st.markdown("---")
    st.markdown("### 🔖 Your Bookmarks")
    for bm in st.session_state.bookmarks:
        title, author = bm.split("|")
        bm_data = df[(df['title'] == title) & (df['authors'] == author)].iloc[0]
        st.markdown(f"""
            <div style="background-color: #1e1e1ecc; padding: 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(255,255,255,0.2);">
                <strong>📖 {bm_data['title']}</strong><br>
                ✍️ Author: {bm_data['authors']}<br>
                ⭐ Average Rating: {bm_data['average_ratings']}
            </div>
        """, unsafe_allow_html=True)
