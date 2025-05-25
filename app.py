import streamlit as st
import pandas as pd
import random

# --- Page Config ---
st.set_page_config(page_title="NextRead 📚", layout="wide")

# --- Load Data ---
df = pd.read_csv("required.csv", on_bad_lines='skip', encoding='utf-8')

# --- Initialize bookmarks ---
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# --- CSS Styling ---
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Quicksand', sans-serif;
}

section.main {
    animation: gradient 15s ease infinite;
    background: linear-gradient(-45deg, #4facfe, #00f2fe, #fbc1cc, #f8b500);
    background-size: 400% 400%;
}

@keyframes gradient {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

.main-title {
    color: #6a1b9a;
    font-size: 3.2em;
    font-weight: bold;
    text-align: center;
    margin: 20px 0;
    text-shadow: 2px 2px 4px #ccc;
}

.card {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    padding: 20px;
    transition: 0.4s ease;
    margin: 10px;
}
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(0,0,0,0.15);
}

.bookmark-btn {
    background: linear-gradient(to right, #8e2de2, #4a00e0);
    color: white;
    padding: 8px 15px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    margin-top: 12px;
    font-weight: bold;
}
.bookmark-btn:hover {
    background: linear-gradient(to right, #4a00e0, #8e2de2);
    transform: scale(1.02);
}

input[type="text"] {
    border-radius: 8px !important;
    padding: 8px;
}

hr {
    border: none;
    height: 2px;
    background: #ddd;
    margin: 30px 0;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- App Title ---
st.markdown("<h1 class='main-title'>📚 NextRead</h1>", unsafe_allow_html=True)

# --- Book Filter Functions ---
def get_books_by_author(author_name):
    matches = df[df['authors'].str.lower().str.contains(author_name.lower())]
    return matches[['title', 'average_ratings', 'authors']] if not matches.empty else None

def get_rating_by_title(book_title):
    matches = df[df['title'].str.lower().str.contains(book_title.lower())]
    return matches[['title', 'authors', 'average_ratings']] if not matches.empty else None

# --- Display Book Cards ---
def display_books(books):
    cols = st.columns(2)
    for i, row in books.iterrows():
        col = cols[i % 2]
        with col:
            book_id = f"{row['title']}|{row['authors']}"
            is_bookmarked = book_id in st.session_state.bookmarks
            bookmark_text = "🔖 Remove Bookmark" if is_bookmarked else "⭐ Bookmark"
            st.markdown(f"""
                <div class='card'>
                    <strong>📖 {row['title']}</strong><br>
                    ✍️ <b>Author:</b> {row['authors']}<br>
                    ⭐ <b>Average Rating:</b> {row['average_ratings']}
                </div>
            """, unsafe_allow_html=True)
            if st.button(bookmark_text, key=book_id):
                if is_bookmarked:
                    st.session_state.bookmarks.remove(book_id)
                else:
                    st.session_state.bookmarks.append(book_id)
                st.experimental_rerun()

# --- Search Feature ---
search_type = st.radio("🔍 Search by:", ['authors', 'title'], horizontal=True)

if search_type == 'authors':
    author = st.text_input("Type author name here:")
    if author:
        with st.spinner('🔎 Finding books by that author...'):
            books = get_books_by_author(author)
        if books is not None:
            st.markdown("### ✨ Books by Author")
            display_books(books)
        else:
            st.warning(f"❌ No books found for **{author}**.")

elif search_type == 'title':
    title = st.text_input("Type book title here:")
    if title:
        with st.spinner('🔎 Searching for that book...'):
            books = get_rating_by_title(title)
        if books is not None:
            st.markdown("### ✨ Matching Book(s)")
            display_books(books)
        else:
            st.warning(f"❌ No books found with title **{title}**.")

# --- Surprise Me Feature ---
st.markdown("<hr>", unsafe_allow_html=True)
if st.button("🎲 Surprise Me!"):
    random_book = df.sample(1).iloc[0]
    book_id = f"{random_book['title']}|{random_book['authors']}"
    is_bookmarked = book_id in st.session_state.bookmarks
    bookmark_text = "🔖 Remove Bookmark" if is_bookmarked else "⭐ Bookmark"
    st.markdown(f"""
        <div class='card'>
            <strong>📖 {random_book['title']}</strong><br>
            ✍️ <b>Author:</b> {random_book['authors']}<br>
            ⭐ <b>Average Rating:</b> {random_book['average_ratings']}
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
                ✍️ <b>Author:</b> {bm_data['authors']}<br>
                ⭐ <b>Average Rating:</b> {bm_data['average_ratings']}
            </div>
        """, unsafe_allow_html=True)
