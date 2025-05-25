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
    /* Animate background gradient */
    @keyframes bg-gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    section[data-testid="stAppViewContainer"] {
        background: linear-gradient(-45deg, #ff9a9e, #fad0c4, #fad0c4, #ff9a9e);
        background-size: 400% 400%;
        animation: bg-gradient 15s ease infinite;
        color: #333 !important;
        transition: background 0.5s ease;
    }
    .main-title { 
        color: #4a148c; 
        font-weight: 700;
        margin-bottom: 20px;
    }
    .card { 
        background-color: #fff; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
        border-radius: 12px; 
        padding: 20px; 
        transition: transform 0.3s ease; 
    }
    .card:hover { 
        transform: scale(1.03); 
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
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
        background: linear-gradient(-45deg, #2a2a72, #009ffd, #2a2a72, #009ffd);
        background-size: 400% 400%;
        animation: bg-gradient-dark 15s ease infinite;
        color: #e0e0e0 !important;
        transition: background 0.5s ease;
    }
    .main-title { 
        color: #bb86fc; 
        font-weight: 700;
        margin-bottom: 20px;
    }
    .card { 
        background-color: #1f1f1f; 
        box-shadow: 0 4px 12px rgba(255,255,255,0.05); 
        border-radius: 12px; 
        padding: 20px; 
        transition: transform 0.3s ease; 
    }
    .card:hover { 
        transform: scale(1.03); 
        box-shadow: 0 8px 24px rgba(255,255,255,0.15);
    }
    </style>
"""

st.markdown(dark_css if theme == "Dark" else light_css, unsafe_allow_html=True)

# --- Static Title ---
st.markdown("""
    <div style='text-align: center; padding-top: 20px;'>
        <h1 class='main-title'>📖 NextRead</h1>
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
