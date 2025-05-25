import streamlit as st
import pandas as pd

# Custom CSS for styling, background, animations, and layout
st.markdown(
    """
    <style>
    @keyframes fadeIn {
        0% {opacity: 0;}
        100% {opacity: 1;}
    }

    .stApp {
        background: linear-gradient(135deg, #e0f7fa, #fce4ec);
        color: #333;
        font-family: 'Segoe UI', sans-serif;
        animation: fadeIn 2s ease-in;
    }

    .header-container {
        display: flex;
        align-items: center;
        gap: 20px;
        animation: fadeIn 2s ease-in;
        margin-bottom: 30px;
    }

    .logo {
        height: 60px;
    }

    .main-title {
        font-size: 40px;
        font-weight: 800;
        color: #6a1b9a;
        margin: 0;
    }

    .stRadio > div {
        flex-direction: row;
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Logo and main title
st.markdown(
    """
    <div class="header-container">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/HD_transparent_picture.png/600px-HD_transparent_picture.png" class="logo">
        <h1 class="main-title">NextRead</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Load the dataset
df = pd.read_csv('required.csv')

# Function to get books by author
def get_books_by_author(author_name):
    matching_books = df[df['authors'].str.lower().str.contains(author_name.lower())]
    if not matching_books.empty:
        return matching_books[['title', 'average_ratings']]
    else:
        return None

# Function to get books by title
def get_rating_by_title(book_title):
    matching_books = df[df['title'].str.lower().str.contains(book_title.lower())]
    if not matching_books.empty:
        return matching_books[['title', 'authors', 'average_ratings']]
    else:
        return None

# Search UI
search_option = st.radio("Search by:", ['authors', 'title'])

if search_option == 'authors':
    author_input = st.text_input("Enter author name:")
    if author_input:
        results = get_books_by_author(author_input)
        if results is not None:
            st.success(f"Books by '{author_input}':")
            st.dataframe(results.reset_index(drop=True), use_container_width=True)
        else:
            st.warning(f"No books found for author '{author_input}'.")

elif search_option == 'title':
    title_input = st.text_input("Enter book title:")
    if title_input:
        results = get_rating_by_title(title_input)
        if results is not None:
            st.success(f"Book(s) matching '{title_input}':")
            st.dataframe(results.reset_index(drop=True), use_container_width=True)
        else:
            st.warning(f"No books found with title '{title_input}'.")
