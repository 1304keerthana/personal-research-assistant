import streamlit as st
import requests
from bs4 import BeautifulSoup
from elevenlabs.client import ElevenLabs
from gtts import gTTS
import time
import google.generativeai as genai


# 🔑 CONFIG
st.set_page_config(page_title="AI Research Assistant", page_icon="🧠", layout="wide")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# force new API behavior
genai.use_vertexai = False

model = genai.GenerativeModel("gemini-1.5-flash")

tts = ElevenLabs(api_key=st.secrets["ELEVENLABS_API_KEY"])

st.markdown("""
<style>

/* 🌌 Force entire app background */
html, body, .stApp {
    background-color: #0f172a !important;
}

/* 🧱 Fix bottom white container */
[data-testid="stBottomBlockContainer"] {
    background-color: #0f172a !important;
    border-top: 1px solid #1e293b;
}

/* 💬 Chat input wrapper */
[data-testid="stChatInput"] {
    background-color: #0f172a !important;
}

/* ✍️ Actual input box */
textarea {
    background-color: #1e293b !important;
    color: white !important;
    border-radius: 10px;
}

/* Optional: remove white padding */
.block-container {
    padding-bottom: 2rem;
}

</style>
""", unsafe_allow_html=True)


# 🧠 SESSION MEMORY
if "history" not in st.session_state:
    st.session_state.history = []

# 🔍 SEARCH
def search(query):
    url = f"https://html.duckduckgo.com/html/?q={query}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    links = []
    for a in soup.find_all("a", class_="result__a", limit=3):
        link = a.get("href")
        if link:
            links.append(link)
    return links
def get_images(query):
    headers = {
        "Authorization": st.secrets["PEXELS_API_KEY"]
    }

    url = f"https://api.pexels.com/v1/search?query={query}&per_page=3"

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        images = []

        for photo in data.get("photos", []):
            images.append(photo["src"]["large"])

        return images

    except Exception as e:
        st.error(f"Image Error: {e}")
        return []

# 📄 SCRAPE
def scrape(links):
    text = ""
    for link in links:
        try:
            res = requests.get(link, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            for s in soup(["script", "style"]):
                s.decompose()
            text += soup.get_text()[:1500]
        except:
            pass
    return text

def analyze(topic, content):
    content = content[:3000]

    prompt = f"""
    Topic: {topic}

    Based on:
    {content}

    Give:
    🧠 Summary
    📌 Key Points
    🔍 Conclusion
    """

    try:
        st.write("Calling Gemini...")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini Error: {e}")
        return f"Error: {e}"
# 🎙️ SPEAK (SAFE)
def speak(text, enable_voice):
    if not enable_voice:
        return None

    text = text[:800]

    try:
        audio_stream = tts.text_to_speech.convert(
            text=text,
            voice_id="EXAVITQu4vr4xnSDxMaL"
        )
        audio_bytes = b"".join(audio_stream)

        with open("output.mp3", "wb") as f:
            f.write(audio_bytes)

        return "output.mp3"

    except:
        # fallback
        tts_fallback = gTTS(text=text, lang='en')
        tts_fallback.save("output.mp3")
        return "output.mp3"

# ✨ HEADER
st.title("🧠 AI Research Assistant")
st.caption("Search • Analyze • Chat • Listen 🎧")

# 🎛️ SIDEBAR SETTINGS
st.sidebar.header("⚙️ Settings")

voice_toggle = st.sidebar.toggle("Enable Voice", True)

voice_choice = st.sidebar.selectbox(
    "Voice",
    ["Default", "Alternative"]
)

clear = st.sidebar.button("🗑️ Clear Chat")

if clear:
    st.session_state.history = []

# 📥 INPUT
user_input = st.chat_input("Ask something...")

if user_input:
    st.session_state.history.append(("user", user_input))

    with st.spinner("Thinking..."):
        links = search(user_input)
        content = scrape(links)
        result = analyze(user_input, content)
        audio = speak(result, voice_toggle)
        images = get_images(user_input)

    st.session_state.history.append(("bot", result))
    st.session_state.history.append(("audio", audio))
    st.session_state.history.append(("links", links))
    st.session_state.history.append(("images", images))

# 💬 DISPLAY CHAT
for item in st.session_state.history:
    role, content = item

    if role == "user":
        st.markdown(f"<div class='chat-box user'>👤 {content}</div>", unsafe_allow_html=True)

    elif role == "bot":
        # typing effect
        placeholder = st.empty()
        text = ""
        for char in content:
            text += char
            placeholder.markdown(f"<div class='chat-box bot'>🤖 {text}</div>", unsafe_allow_html=True)
            time.sleep(0.002)

    elif role == "audio" and content:
        st.audio(content)

    elif role == "links":
        with st.expander("📚 Sources"):
            for l in content:
                st.write(l)
    elif role == "images":
        if content:
            st.subheader("🖼️ Related Images")
            cols = st.columns(len(content))
            for col, img_url in zip(cols, content):
                with col:
                    st.image(img_url, use_container_width=True)

# 📥 DOWNLOAD
if st.session_state.history:
    last_response = [i for i in st.session_state.history if i[0]=="bot"][-1][1]

    st.download_button(
        "📥 Download Report",
        last_response,
        file_name="research.txt"
    )
