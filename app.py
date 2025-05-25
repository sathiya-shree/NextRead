import streamlit as st
import pandas as pd

# Custom CSS for styling and animation
st.markdown(
    """
    <style>
    @keyframes fadeIn {
        0% {opacity: 0; transform: translateY(-10px);}
        100% {opacity: 1; transform: translateY(0);}
    }

    .stApp {
        background: linear-gradient(to right, #e0c3fc, #8ec5fc);
        font-family: 'Segoe UI', sans-serif;
        animation: fadeIn 2s ease-in;
    }

    .title-container {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        text-align: center;
        animation: fadeIn 2s ease-in-out;
        padding-top: 30px;
        padding-bottom: 20px;
    }

    .main-title {
        font-size: 48px;
        font-weight: 900;
        color: #4a148c;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px #ddd;
        letter-spacing: 2px;
    }

    .logo {
        height: 60px;
        margin-bottom: 10px;
    }

    .stRadio > div {
        flex-direction: row;
        justify-content: center;
    }

    .stTextInput input {
        border-radius: 8px;
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Centered title and logo (optional)
st.markdown(
    """
    <div class="title-container">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/HD_transparent_picture.png/600px-HD_transparent_picture.png" class="logo">
        <div class="main-title">NextRead</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Load the dataset
df = pd.read_csv("required.csv")

# Function to get books by author
def get_books_by_author(author_name):
    matching_books = df[df['authors'].str.lower().str.contains(author_name.lower())]
    if not matching_books.empty:
        return matching_books[['title', 'average_ratings']]
    return None

# Function to get books by title
def get_rating_by_title(book_title):
    matching_books = df[df['title'].str.lower().str.contains(book_title.lower())]
    if not matching_books.empty:
        return matching_books[['title', 'authors', 'average_ratings']]
    return None

# Streamlit search UI
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
