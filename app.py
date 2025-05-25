import streamlit as st
import pandas as pd
from streamlit_lottie import st_lottie
import requests
import random

# --- Page Config ---
st.set_page_config(page_title="NextRead", layout="wide")

# --- Load Data ---
df = pd.read_csv("required.csv", on_bad_lines='skip', encoding='utf-8')

# --- Session State ---
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# --- Helper Functions ---
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def get_books_by_author(author_name):
    matches = df[df['authors'].str.lower().str.contains(author_name.lower())]
    return matches[['title', 'average_ratings', 'authors']] if not matches.empty else None

def get_rating_by_title(book_title):
    matches = df[df['title'].str.lower().str.contains(book_title.lower())]
    return matches[['title', 'authors', 'average_ratings']] if not matches.empty else None

def get_rating_badge(rating):
    rating = float(rating)
    if rating >= 4.5:
        color = "#43a047"  # Green
    elif rating >= 3.5:
        color = "#fb8c00"  # Orange
    else:
        color = "#e53935"  # Red
    return f"<span style='color:white;background-color:{color};padding:4px 8px;border-radius:5px;font-weight:bold'>{rating}</span>"

# --- CSS Styling ---
css = """
<style>
  section.main {
      background: linear-gradient(45deg, #ffe4e1, #e0f7fa, #fff9c4, #ffe4e1);
      background-size: 400% 400%;
      animation: bg-animation 15s ease infinite;
      padding: 2rem;
  }

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
      font-size: 3.5em;
      font-weight: 900;
      text-align: left;
      background: linear-gradient(90deg, #8e24aa, #00acc1, #ffb300);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: shine 3s linear infinite;
  }

  @keyframes shine {
      0% {background-position: -500%;}
      100% {background-position: 500%;}
  }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- Load Lottie Animation ---
lottie_book = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_jtkhrafv.json")

# --- Header with Animation ---
with st.container():
    left, right = st.columns(2)
    with left:
        st.markdown("<h1 class='main-title'>NextRead 📚</h1>", unsafe_allow_html=True)
        st.markdown("#### Find your next favorite book with ease and style!")
    with right:
        st_lottie(lottie_book, height=200, key="book")

# --- Tabs Layout ---
tab1, tab2 = st.tabs(["🔍 Search", "🔖 Bookmarks"])

# --- Search Tab ---
with tab1:
    search_type = st.radio("Search by:", ['authors', 'title'], horizontal=True)

    def display_books(books):
        for i, row in books.iterrows():
            book_id = f"{row['title']}|{row['authors']}"
            is_bookmarked = book_id in st.session_state.bookmarks
            bookmark_text = "🔖 Remove Bookmark" if is_bookmarked else "📌 Bookmark This"
            with st.expander(f"📖 {row['title']} by {row['authors']}"):
                st.markdown(f"⭐ Average Rating: {get_rating_badge(row['average_ratings'])}", unsafe_allow_html=True)
                if st.button(bookmark_text, key=book_id):
                    if is_bookmarked:
                        st.session_state.bookmarks.remove(book_id)
                    else:
                        st.session_state.bookmarks.append(book_id)
                    st.experimental_rerun()

    if search_type == 'authors':
        author = st.text_input("Enter author name:")
        if author:
            with st.spinner('🔍 Searching books by author...'):
                books = get_books_by_author(author)
            if books is not None:
                st.subheader("Books by Author")
                display_books(books)
            else:
                st.warning(f"No books found for '{author}'.")

    elif search_type == 'title':
        title = st.text_input("Enter book title:")
        if title:
            with st.spinner('🔍 Searching books by title...'):
                books = get_rating_by_title(title)
            if books is not None:
                st.subheader("Matching Book(s)")
                display_books(books)
            else:
                st.warning(f"No books found with title '{title}'.")

    # --- Surprise Me ---
    st.markdown("---")
    if st.button("🎲 Surprise Me!"):
        random_book = df.sample(1).iloc[0]
        book_id = f"{random_book['title']}|{random_book['authors']}"
        is_bookmarked = book_id in st.session_state.bookmarks
        bookmark_text = "🔖 Remove Bookmark" if is_bookmarked else "📌 Bookmark This"
        with st.expander(f"📖 {random_book['title']} by {random_book['authors']}"):
            st.markdown(f"⭐ Average Rating: {get_rating_badge(random_book['average_ratings'])}", unsafe_allow_html=True)
            if st.button(bookmark_text, key="surprise_" + book_id):
                if is_bookmarked:
                    st.session_state.bookmarks.remove(book_id)
                else:
                    st.session_state.bookmarks.append(book_id)
                st.experimental_rerun()
        random.choice([st.balloons(), st.snow()])

# --- Bookmarks Tab ---
with tab2:
    if st.session_state.bookmarks:
        st.subheader("Your Bookmarks")
        for bm in st.session_state.bookmarks:
            title, author = bm.split("|")
            bm_data = df[(df['title'] == title) & (df['authors'] == author)].iloc[0]
            with st.expander(f"📖 {bm_data['title']} by {bm_data['authors']}"):
                st.markdown(f"⭐ Average Rating: {get_rating_badge(bm_data['average_ratings'])}", unsafe_allow_html=True)
    else:
        st.info("You haven't bookmarked any books yet!")
