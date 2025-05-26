import streamlit as st
import pandas as pd
import random

# --- Page Config ---
st.set_page_config(page_title="NextRead", layout="wide", page_icon="📚")

# --- Load Data ---
df = pd.read_csv("required.csv", on_bad_lines='skip', encoding='utf-8')

# Add genre column if not available
if "genres" not in df.columns:
    df["genres"] = random.choices(
        ["Fiction", "Romance", "Mystery", "Fantasy", "Science", "Young Adult", "Thriller", "Biography"],
        k=len(df)
    )

# --- Initialize bookmarks ---
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# --- CSS Styling with Gradient Background ---
css = """
<style>
body {
    background: linear-gradient(to right, #141E30, #243B55);
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
    animation: glow 2s infinite alternate;
}
@keyframes glow {
    from {
        text-shadow: 0 0 10px #FFD700;
    }
    to {
        text-shadow: 0 0 20px #FF8C00;
    }
}
.card {
    background: linear-gradient(145deg, #1f1f1f, #2e2e2e);
    color: white;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 25px;
    box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    animation: fadeIn 1s ease;
}
.card:hover {
    transform: scale(1.02);
    box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
}
.bookmark-btn {
    background-color: #FFD700;
    color: black;
    padding: 7px 12px;
    border-radius: 5px;
    font-weight: bold;
    border: none;
    cursor: pointer;
    margin-top: 10px;
}
.bookmark-btn:hover {
    background-color: #e6c200;
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

# --- Book Card Display ---
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

# --- Search Section ---
search_type = st.radio("Search by:", ['Author', 'Title', 'Genre'], horizontal=True)

if search_type == 'Author':
    author = st.text_input("Enter author name:")
    if author:
        matches = df[df['authors'].str.lower().str.contains(author.lower())]
        if not matches.empty:
            st.markdown("### 📘 Books by Author:")
            display_books(matches)
        else:
            st.warning("No books found for that author.")

elif search_type == 'Title':
    title = st.text_input("Enter book title:")
    if title:
        matches = df[df['title'].str.lower().str.contains(title.lower())]
        if not matches.empty:
            st.markdown("### 📘 Matching Titles:")
            display_books(matches)
        else:
            st.warning("No books found with that title.")

elif search_type == 'Genre':
    genres = df['genres'].unique()
    selected_genre = st.selectbox("Choose a genre:", genres)
    filtered = df[df['genres'] == selected_genre]
    st.markdown(f"### 📚 Books in {selected_genre} Genre")
    display_books(filtered)

# --- Surprise Me ---
st.markdown("<hr>", unsafe_allow_html=True)
if st.button("🎲 Surprise Me!"):
    random_book = df.sample(1).iloc[0]
    display_books(pd.DataFrame([random_book]))

# --- Top Rated ---
top_books = df.sort_values(by='average_ratings', ascending=False).head(5)
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("### 🏆 Top Rated Books")
display_books(top_books)

# --- New Arrivals (Random subset) ---
new_arrivals = df.sample(5)
st.markdown("### 🌟 New Arrivals")
display_books(new_arrivals)

# --- Bookmarks ---
if st.session_state.bookmarks:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🔖 Your Bookmarks")
    for bm in st.session_state.bookmarks:
        title, author = bm.split("|")
        result = df[(df['title'] == title) & (df['authors'] == author)]
        if not result.empty:
            display_books(result)
