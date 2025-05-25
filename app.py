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
theme = st.selectbox("🎨 Choose Theme", ["Light", "Dark"])

# --- Custom CSS ---
light_css = """
    <style>
    @keyframes bg-gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    section[data-testid="stAppViewContainer"] {
        background: linear-gradient(-45deg, #ffecd2, #fcb69f, #ffecd2, #fcb69f);
        background-size: 400% 400%;
        animation: bg-gradient 20s ease infinite;
        color: #333 !important;
    }
    .main-title {
        font-size: 3em;
        color: #4a148c;
        font-weight: 800;
        text-shadow: 2px 2px 4px #fff;
        animation: fade-in 2s ease-in;
    }
    .card {
        background-color: #ffffffcc;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        margin: 10px 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: fade-in 1s ease-in-out;
    }
    .card:hover {
        transform: scale(1.03);
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    @keyframes fade-in {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    </style>
"""

dark_css = """
    <style>
    @keyframes bg-gradient-dark {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    section[data-testid="stAppViewContainer"] {
        background: linear-gradient(-45deg, #232526, #414345, #232526, #414345);
        background-size: 400% 400%;
        animation: bg-gradient-dark 20s ease infinite;
        color: #e0e0e0 !important;
    }
    .main-title {
        font-size: 3em;
        color: #bb86fc;
        font-weight: 800;
        text-shadow: 2px 2px 4px #000;
        animation: fade-in 2s ease-in;
    }
    .card {
        background-color: #2c2c2cdd;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 16px rgba(255,255,255,0.05);
        margin: 10px 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        animation: fade-in 1s ease-in-out;
    }
    .card:hover {
        transform: scale(1.03);
        box-shadow: 0 8px 32px rgba(255,255,255,0.1);
    }
    @keyframes fade-in {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    </style>
"""

# Apply selected theme
st.markdown(dark_css if theme == "Dark" else light_css, unsafe_allow_html=True)

# --- Title Section ---
st.markdown("""
    <div style='text-align: center; padding-top: 30px;'>
        <h1 class='main-title'>📚 NextRead</h1>
        <p style='font-size: 1.1em;'>Your cozy book companion</p>
    </div>
""", unsafe_allow_html=True)

# --- Search Mode ---
st.markdown("### 🔍 Search by Author or Title")
search_type = st.radio("Search by:", ['authors', 'title'], horizontal=True)

# --- Author Search ---
if search_type == 'authors':
    author = st.text_input("✍️ Enter author name:")
    if author:
        books = get_books_by_author(author)
        if books is not None:
            st.markdown("### 📚 Books by Author:")
            for _, row in books.iterrows():
                st.markdown(f"""
                    <div class='card'>
                        <strong>{row['title']}</strong><br>
                        ⭐ Average Rating: {row['average_ratings']}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"No books found for '{author}'.")

# --- Title Search ---
elif search_type == 'title':
    title = st.text_input("📖 Enter book title:")
    if title:
        books = get_rating_by_title(title)
        if books is not None:
            st.markdown("### 🔎 Matching Book(s):")
            for _, row in books.iterrows():
                st.markdown(f"""
                    <div class='card'>
                        <strong>{row['title']}</strong><br>
                        ✍️ Author: {row['authors']}<br>
                        ⭐ Average Rating: {row['average_ratings']}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"No books found with title '{title}'.")
