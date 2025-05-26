import streamlit as st
import pandas as pd
import random

# Set up Streamlit page
st.set_page_config(page_title="NextRead", layout="wide", page_icon="📚")

# Load dataset
df = pd.read_csv("required.csv", on_bad_lines='skip', encoding='utf-8')
df = df[['title', 'authors', 'genre', 'average_ratings']].dropna()
df = df.sample(frac=1).reset_index(drop=True)

# Initialize bookmarks
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# CSS for background and layout
css = """
<style>
body {
    background: linear-gradient(to right, #1e1e2f, #2a2a3b, #1e1e2f);
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.main-title {
    color: #FFD700;
    font-size: 3.2em;
    font-weight: bold;
    text-align: center;
    margin-top: 30px;
    margin-bottom: 10px;
}
.search-container {
    background: rgba(255, 255, 255, 0.05);
    padding: 20px;
    border-radius: 15px;
    margin: 0 auto 40px auto;
    max-width: 700px;
    box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
}
.card {
    background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
    color: white;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 25px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    transition: 0.3s ease;
}
.card:hover {
    transform: scale(1.01);
    box-shadow: 0 10px 20px rgba(255,255,255,0.15);
}
.bookmark-btn {
    background-color: #FFD700;
    color: black;
    padding: 7px 12px;
    border-radius: 5px;
    margin-top: 10px;
    font-weight: bold;
    border: none;
    cursor: pointer;
}
.bookmark-btn:hover {
    background-color: #e6c200;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# App title
st.markdown("<h1 class='main-title'>📚 NextRead</h1>", unsafe_allow_html=True)

# Search section
st.markdown("<div class='search-container'>", unsafe_allow_html=True)
search_type = st.radio("Search by:", ['authors', 'title'], horizontal=True)
if search_type == 'authors':
    author = st.text_input("Enter author name:")
elif search_type == 'title':
    title = st.text_input("Enter book title:")
st.markdown("</div>", unsafe_allow_html=True)

# Helper functions
def display_books(book_data):
    for _, row in book_data.iterrows():
        with st.container():
            st.markdown(f"""
                <div class="card">
                <h3>📖 {row['title']}</h3>
                <p><strong>✍️ Author:</strong> {row['authors']}</p>
                <p><strong>📚 Genre:</strong> {row['genre']}</p>
                <p><strong>⭐ Average Rating:</strong> {row['average_ratings']}</p>
                </div>
            """, unsafe_allow_html=True)

            if st.button("🔖 Bookmark", key=f"bookmark_{row['title']}"):
                st.session_state.bookmarks.append(row)

def get_books_by_author(author_name):
    return df[df['authors'].str.lower().str.contains(author_name.lower(), na=False)]

def get_books_by_title(title_name):
    return df[df['title'].str.lower().str.contains(title_name.lower(), na=False)]

# Search Results
if search_type == 'authors' and author:
    results = get_books_by_author(author)
    if not results.empty:
        st.markdown("### 📘 Books by Author:")
        display_books(results)
    else:
        st.warning(f"No books found for '{author}'.")

if search_type == 'title' and title:
    results = get_books_by_title(title)
    if not results.empty:
        st.markdown("### 📘 Books by Title:")
        display_books(results)
    else:
        st.warning(f"No books found for '{title}'.")

# Bookmarks section
if st.session_state.bookmarks:
    st.markdown("### 🔖 Bookmarked Books")
    for book in st.session_state.bookmarks:
        st.markdown(f"""
            <div class="card">
            <h3>📖 {book['title']}</h3>
            <p><strong>✍️ Author:</strong> {book['authors']}</p>
            <p><strong>📚 Genre:</strong> {book['genre']}</p>
            <p><strong>⭐ Average Rating:</strong> {book['average_ratings']}</p>
            </div>
        """, unsafe_allow_html=True)
