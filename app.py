import streamlit as st
import pandas as pd

# Load your dataset
df = pd.read_csv('required.csv')  # Make sure this file is uploaded in Colab

# Function to get books by author
def get_books_by_author(author_name):
    matching_books = df[df['authors'].str.lower().str.contains(author_name.lower())]
    if not matching_books.empty:
        return matching_books[['title', 'authors', 'average_ratings']]
    else:
        return None

# Function to get rating by book title
def get_rating_by_title(book_title):
    matching_books = df[df['title'].str.lower().str.contains(book_title.lower())]
    if not matching_books.empty:
        return matching_books[['title', 'authors', 'average_ratings']]
    else:
        return None

# Streamlit UI
st.title("📚 Book Info Finder")

search_option = st.radio("Search by:", ['Author Name', 'Book Title'])

if search_option == 'Author Name':
    author_input = st.text_input("Enter author name:")
    if author_input:
        results = get_books_by_author(author_input)
        if results is not None:
            st.write(f"Books by '{author_input}':")
            st.dataframe(results)
        else:
            st.warning(f"No books found for author '{author_input}'.")

elif search_option == 'Book Title':
    title_input = st.text_input("Enter book title:")
    if title_input:
        results = get_rating_by_title(title_input)
        if results is not None:
            st.write(f"Book(s) matching '{title_input}':")
            st.dataframe(results)
        else:
            st.warning(f"No books found with title '{title_input}'.")
