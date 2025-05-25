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

# --- Inject CSS for smooth animated gradient and styling ---
st.markdown("""
<style>
/* Smooth infinite gradient animation */
section.main {
    background: linear-gradient(270deg, #f6d365, #fda085, #fbc7a4, #f6d365);
    background-size: 800% 800%;
    animation: gradientAnimation 30s ease infinite;
    padding: 2rem;
    border-radius: 12px;
}

/* Main container background */
div[data-testid="stAppViewContainer"] {
    background: linear-gradient(270deg, #f6d365, #fda085, #fbc7a4, #f6d365);
    background-size: 800% 800%;
    animation: gradientAnimation 30s ease infinite;
    min-height: 100vh;
    padding-top: 3rem;
    padding-bottom: 3rem;
}

/* Gradient keyframes */
@keyframes gradientAnimation {
    0%{background-position:0% 50%}
    50%{background-position:100% 50%}
    100%{background-position:0% 50%}
}

/* Title styling */
.main-title {
    color: #4B0082;
    font-size: 3.5rem;
    font-weight: 900;
    text-align: center;
    margin-bottom: 2rem;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.2);
}

/* Card styling */
.card {
    background-color: rgba(255, 255, 255, 0.85);
    border-radius: 16px;
    padding: 20px 25px;
    box-shadow: 0 6px 15px rgba(0,0,0,0.12);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    margin-bottom: 1rem;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(0,0,0,0.2);
}

/* Subheadings */
h3 {
    color: #4B0082;
    font-weight: 700;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

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
                    </div>
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
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"No books found with title '{title}'.")
