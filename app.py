import streamlit as st
import pandas as pd

st.set_page_config(page_title="NextRead", layout="wide")

df = pd.read_csv("required.csv", on_bad_lines='skip', encoding='utf-8')

if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

st.markdown(
    """
    <style>
    /* Full screen starry background container without gradient */
    #starry-night {
      pointer-events: none;
      position: fixed;
      top: 0; left: 0;
      width: 100vw;
      height: 100vh;
      background: #0a0a23;  /* dark night blue solid background */
      z-index: 0;
      overflow: hidden;
    }

    /* Create many white dots (stars) */
    #starry-night .star {
      position: absolute;
      background: white;
      border-radius: 50%;
      opacity: 0.8;
      animation-name: twinkle;
      animation-iteration-count: infinite;
      animation-direction: alternate;
      animation-timing-function: ease-in-out;
    }

    /* Different star sizes and twinkle durations */
    #starry-night .star:nth-child(odd) {
      width: 2px;
      height: 2px;
      animation-duration: 3s;
    }
    #starry-night .star:nth-child(even) {
      width: 1.5px;
      height: 1.5px;
      animation-duration: 2s;
    }
    #starry-night .star:nth-child(3n) {
      width: 3px;
      height: 3px;
      animation-duration: 4s;
    }

    @keyframes twinkle {
      0% { opacity: 0.3; transform: scale(1); }
      50% { opacity: 1; transform: scale(1.3); }
      100% { opacity: 0.3; transform: scale(1); }
    }

    /* Make sure your app content is above the starry background */
    .app-container {
      position: relative;
      z-index: 10;
    }

    /* Title styling */
    .main-title {
        color: #d1c4e9;
        font-size: 3.2em;
        font-weight: bold;
        text-align: center;
        margin-top: 30px;
        margin-bottom: 40px;
        text-shadow: 2px 2px 5px #311b92;
    }

    /* Card styling */
    .card {
        background-color: #ffffffcc;
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 25px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .card:hover {
        transform: scale(1.03);
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }

    /* Bookmark button */
    .bookmark-btn {
        background-color: #311b92;
        color: white;
        padding: 7px 12px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        margin-top: 10px;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }
    .bookmark-btn:hover {
        background-color: #512da8;
    }
    </style>

    <!-- Starry background container -->
    <div id="starry-night"></div>

    <script>
    // Create 100 stars randomly positioned
    const starry = document.getElementById("starry-night");
    for(let i=0; i<100; i++) {
      const star = document.createElement("div");
      star.classList.add("star");
      star.style.top = Math.random() * 100 + "vh";
      star.style.left = Math.random() * 100 + "vw";
      star.style.animationDelay = (Math.random() * 3) + "s";
      starry.appendChild(star);
    }
    </script>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="app-container">', unsafe_allow_html=True)

# Your Streamlit app content below

st.markdown("<h1 class='main-title'>📚 NextRead</h1>", unsafe_allow_html=True)

# ... rest of your app logic and UI here ...

st.markdown('</div>', unsafe_allow_html=True)
