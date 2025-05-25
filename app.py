import streamlit as st
import pandas as pd

# --- Load Data ---
df = pd.read_csv("required.csv")

# --- Book Filter Functions ---
def get_books_by_author(author_name):
    matches = df[df['authors'].str.lower().str.contains(author_name.lower())]
    return matches[['title', 'average_ratings']] if not matches.empty else None

def get_rating_by_title(book_title):
    matches = df[df['title'].str.lower().str.contains(book_title.lower())]
    return matches[['title', 'authors', 'average_ratings']] if not matches.empty else None

# --- Theme Switcher ---
theme = st.selectbox("Choose Theme", ["Light", "Dark"])

light_css = """
    <style>
    body { background: #f9f9f9; color: #333; }
    .main-title { color: #4a148c; }
    .card { background-color: #fff; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 12px; padding: 20px; transition: transform 0.3s ease; }
    .card:hover { transform: scale(1.03); }
    </style>
"""

dark_css = """
    <style>
    body { background: #121212; color: #e0e0e0; }
    .main-title { color: #bb86fc; }
    .card { background-color: #1f1f1f; box-shadow: 0 4px 8px rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; transition: transform 0.3s ease; }
    .card:hover { transform: scale(1.03); }
    </style>
"""

st.markdown(dark_css if theme == "Dark" else light_css, unsafe_allow_html=True)

# --- Animated Title ---
st.markdown("""
    <div style='text-align: center; padding-top: 20px;'>
        <h1 class='main-title' style='font-size: 3em;'>📖 NextRead</h1>
    </div>
""", unsafe_allow_html=True)

# --- Search Feature ---
search_type = st.radio("Search by:", ['authors', 'title'], horizontal=True)

if search_type == 'authors':
    author = st.text_input("Enter author name:")
    if author:
        books = get_books_by_author(author)
        if books is not None:
            st.markdown("<h3>Books by Author:</h3>", unsafe_allow_html=True)
            for _, row in books.iterrows():
                st.markdown(f"""
                    <div class='card'>
                        <strong>📚 {row['title']}</strong><br>
                        ⭐ Average Rating: {row['average_ratings']}
                    </div><br>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"No books found for '{author}'.")

elif search_type == 'title':
    title = st.text_input("Enter book title:")
    if title:
        books = get_rating_by_title(title)
        if books is not None:
            st.markdown("<h3>Matching Book(s):</h3>", unsafe_allow_html=True)
            for _, row in books.iterrows():
                st.markdown(f"""
                    <div class='card'>
                        <strong>📖 {row['title']}</strong><br>
                        ✍️ Author: {row['authors']}<br>
                        ⭐ Average Rating: {row['average_ratings']}
                    </div><br>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"No books found with title '{title}'.")
