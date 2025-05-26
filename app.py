import streamlit as st

# --- Set Page Config ---
st.set_page_config(page_title="Book Finder App", layout="wide")

# --- Apply Custom Pastel Styling ---
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #fceae8 0%, #e0f7fa 100%) !important;
            background-attachment: fixed !important;
            color: #3a3a3a;
        }

        .stTextInput > div > div > input,
        .stSelectbox > div > div > div > div,
        .stTextArea textarea {
            background-color: #ffffffcc !important;
            color: #333333 !important;
            border-radius: 10px;
        }

        .stButton button {
            background-color: #ffd3b6 !important;
            color: #3a3a3a !important;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 12px;
        }

        .stRadio > div {
            background-color: #ffffffcc !important;
            color: #3a3a3a !important;
            padding: 10px;
            border-radius: 10px;
        }

        .book-box {
            background-color: #ffffffcc;
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.05);
        }

        footer {
            text-align: center;
            padding: 1rem;
            font-size: 0.9rem;
            color: #555;
        }
    </style>
""", unsafe_allow_html=True)

# --- App Title ---
st.title("📚 Book Finder App")

# --- Search Bar ---
search_option = st.radio("Search by:", ("Title", "Author", "Genre"))
search_query = st.text_input(f"Enter {search_option.lower()}:")

# --- Sample Book Data ---
books = [
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "genre": "Fantasy", "rating": "4.7"},
    {"title": "1984", "author": "George Orwell", "genre": "Science Fiction", "rating": "4.6"},
    {"title": "The Girl with the Dragon Tattoo", "author": "Stieg Larsson", "genre": "Mystery", "rating": "4.5"},
    {"title": "Twilight", "author": "Stephenie Meyer", "genre": "Fantasy", "rating": "3.9"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "genre": "Fiction", "rating": "4.8"},
]

# --- Filter Logic ---
filtered_books = [
    book for book in books
    if search_query.lower() in book[search_option.lower()].lower()
]

# --- Display Results ---
if search_query:
    if filtered_books:
        for book in filtered_books:
            st.markdown(f"""
                <div class="book-box">
                    <h4>📖 {book['title']}</h4>
                    <p>✍️ <strong>Author:</strong> {book['author']}</p>
                    <p>📚 <strong>Genre:</strong> {book['genre']}</p>
                    <p>⭐ <strong>Average Rating:</strong> {book['rating']}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No books found. Please try another search.")

# --- Footer ---
st.markdown("""
    <footer>
        © 2025 Next Read.
    </footer>
""", unsafe_allow_html=True)
