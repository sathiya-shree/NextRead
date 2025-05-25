import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(page_title="NextRead", layout="wide")

# Load data
df = pd.read_csv("required.csv", on_bad_lines='skip', encoding='utf-8')

# Inject starry night CSS
st.markdown("""
<style>
body {
    background-color: black !important;
    color: white;
}

.starry-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: black;
    overflow: hidden;
    z-index: -1;
}

.star {
    position: absolute;
    width: 2px;
    height: 2px;
    background: white;
    border-radius: 50%;
    animation: twinkle 2s infinite;
}

@keyframes twinkle {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.2; }
}

.moon {
    position: absolute;
    top: 40px;
    right: 60px;
    width: 80px;
    height: 80px;
    background: radial-gradient(circle at 30% 30%, #fdfcdc, #dcdcdc);
    border-radius: 50%;
    box-shadow: 0 0 60px #fdfcdc;
    z-index: -1;
}

.shooting-star {
    position: absolute;
    top: 20%;
    left: 80%;
    width: 2px;
    height: 100px;
    background: linear-gradient(white, transparent);
    transform: rotate(-45deg);
    animation: shoot 4s infinite linear;
}

@keyframes shoot {
    0% { transform: translateX(0) translateY(0) rotate(-45deg); opacity: 1; }
    100% { transform: translateX(-500px) translateY(500px) rotate(-45deg); opacity: 0; }
}
</style>

<div class="starry-bg">
    <div class="moon"></div>
    <div class="shooting-star"></div>
    """ +
    "".join([f'<div class="star" style="top: {i*5 % 100}vh; left: {(i*11) % 100}vw;"></div>' for i in range(100)]) +
    "</div>", unsafe_allow_html=True)



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
