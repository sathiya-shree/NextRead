import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="NextRead", layout="wide")

# --- Load Data ---
df = pd.read_csv("required.csv", error_bad_lines=False, warn_bad_lines=True)
df = pd.read_csv("required.csv", on_bad_lines='skip')
df = pd.read_csv("required.csv", encoding='utf-8')


# --- Initialize bookmarks in session state ---
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# --- Book Filter Functions ---
def get_books_by_author(author_name):
    matches = df[df['authors'].str.lower().str.contains(author_name.lower())]
    return matches[['title', 'average_ratings', 'authors']] if not matches.empty else None

def get_rating_by_title(book_title):
    matches = df[df['title'].str.lower().str.contains(book_title.lower())]
    return matches[['title', 'authors', 'average_ratings']] if not matches.empty else None

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
      color: #6a1b9a;
      font-size: 3em;
      font-weight: bold;
      text-align: center;
      margin-top: 30px;
      margin-bottom: 40px;
  }

  .card {
      background-color: #ffffffcc;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      border-radius: 15px;
      padding: 20px;
      margin-bottom: 20px;
      transition: transform 0.3s ease;
  }

  .card:hover {
      transform: scale(1.05);
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
  }

  .bookmark-btn {
      background-color: #6a1b9a;
      color: white;
      padding: 5px 10px;
      border-radius: 5px;
      border: none;
      cursor: pointer;
      margin-top: 10px;
      font-weight: bold;
  }

  .bookmark-btn:hover {
      background-color: #4a148c;
  }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- App Title ---
st.markdown("<h1 class='main-title'>NextRead 📚</h1>", unsafe_allow_html=True)

# --- Search Feature ---
search_type = st.radio("Search by:", ['authors', 'title'], horizontal=True)

def display_books(books):
    for i, row in books.iterrows():
        book_id = f"{row['title']}|{row['authors']}"
        is_bookmarked = book_id in st.session_state.bookmarks
        bookmark_text = "Remove Bookmark" if is_bookmarked else "Bookmark"
        st.markdown(f"""
            <div class='card'>
                <strong>📖 {row['title']}</strong><br>
                ✍️ Author: {row['authors']}<br>
                ⭐ Average Rating: {row['average_ratings']}
            </div>
        """, unsafe_allow_html=True)

        # Bookmark button
        if st.button(bookmark_text, key=book_id):
            if is_bookmarked:
                st.session_state.bookmarks.remove(book_id)
            else:
                st.session_state.bookmarks.append(book_id)
            st.experimental_rerun()

# --- Searching with spinner ---
if search_type == 'authors':
    author = st.text_input("Enter author name:")
    if author:
        with st.spinner('Searching books by author...'):
            books = get_books_by_author(author)
        if books is not None:
            st.markdown("<h3>Books by Author:</h3>", unsafe_allow_html=True)
            display_books(books)
        else:
            st.warning(f"No books found for '{author}'.")

elif search_type == 'title':
    title = st.text_input("Enter book title:")
    if title:
        with st.spinner('Searching books by title...'):
            books = get_rating_by_title(title)
        if books is not None:
            st.markdown("<h3>Matching Book(s):</h3>", unsafe_allow_html=True)
            display_books(books)
        else:
            st.warning(f"No books found with title '{title}'.")

# --- Surprise Me Button ---
st.markdown("---")
if st.button("🎲 Surprise Me!"):
    random_book = df.sample(1).iloc[0]
    book_id = f"{random_book['title']}|{random_book['authors']}"
    is_bookmarked = book_id in st.session_state.bookmarks
    bookmark_text = "Remove Bookmark" if is_bookmarked else "Bookmark"
    st.markdown(f"""
      <div class='card'>
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

# --- Show Bookmarks ---
if st.session_state.bookmarks:
    st.markdown("---")
    st.markdown("### 🔖 Your Bookmarks")
    for bm in st.session_state.bookmarks:
        title, author = bm.split("|")
        bm_data = df[(df['title'] == title) & (df['authors'] == author)].iloc[0]
        st.markdown(f"""
          <div class='card'>
            <strong>📖 {bm_data['title']}</strong><br>
            ✍️ Author: {bm_data['authors']}<br>
            ⭐ Average Rating: {bm_data['average_ratings']}
          </div>
        """, unsafe_allow_html=True)
