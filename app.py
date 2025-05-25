import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="NextRead", layout="wide")

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
  st.markdown("""
    <style>
    /* This targets the main content area */
    section.main {
        background: linear-gradient(45deg, #ffe4e1, #e0f7fa, #fff9c4, #ffe4e1);
        background-size: 400% 400%;
        animation: bg-animation 15s ease infinite;
        padding: 2rem;
    }

    /* Optional: Customize the entire app container */
    div[data-testid="stAppViewContainer"] {
        background: linear-gradient(45deg, #ffe4e1, #e0f7fa, #fff9c4, #ffe4e1);
        background-size: 400% 400%;
        animation: bg-animation 15s ease infinite;
    }

    @keyframes bg-animation {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .main-title {
        color: #6a1b9a;
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        margin-top: 30px;
    }

    .card {
        background-color: #ffffffcc;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-radius: 15px;
        padding: 20px;
        transition: transform 0.3s ease;
    }

    .card:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

"""

st.markdown(dark_css if theme == "Dark" else light_css, unsafe_allow_html=True)

# --- App Title ---
st.markdown("<h1 class='main-title'>NextRead 📚</h1>", unsafe_allow_html=True)

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
                        <strong>📘 {row['title']}</strong><br>
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
