import streamlit as st
import pandas as pd

st.markdown(
    """
    <style>
    body {
        background-color: #f0f2f6;
    }
    .stApp {
        background: linear-gradient(135deg, #e0f7fa, #fce4ec);
        color: #333;
        font-family: 'Arial', sans-serif;
    }
    .stRadio > div {
        flex-direction: row;
    }
    .title {
        font-size: 36px;
        font-weight: bold;
        color: #6a1b9a;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
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

# Streamlit UI
st.title("📚 Book Info Finder")

search_option = st.radio("Search by:", ['authors', 'title'])

if search_option == 'authors':
    author_input = st.text_input("Enter author name:")
    if author_input:
        results = get_books_by_author(author_input)
        if results is not None:
            st.write(f"Books by '{author_input}':")
            st.dataframe(results, use_container_width=True)
        else:
            st.warning(f"No books found for author '{author_input}'.")

elif search_option == 'title':
    title_input = st.text_input("Enter book title:")
    if title_input:
        results = get_rating_by_title(title_input)
        if results is not None:
            st.write(f"Book(s) matching '{title_input}':")
            st.dataframe(results, use_container_width=True)
        else:
            st.warning(f"No books found with title '{title_input}'.")
