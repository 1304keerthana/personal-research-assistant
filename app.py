import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from gtts import gTTS
import time

# 🔑 CONFIG
st.set_page_config(page_title="AI Research Assistant", page_icon="🧠", layout="wide")

# 🔐 APIs
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-flash-latest")
tts = ElevenLabs(api_key=st.secrets["ELEVENLABS_API_KEY"])

st.markdown("""
<style>

/* Full page background */
.stApp {
    background: linear-gradient(to right, #0f172a, #1e293b);
    color: white;
}

/* Force all text visible */
html, body, [class*="css"]  {
    color: white !important;
}

/* Chat bubbles */
.chat-box {
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    font-size: 16px;
}

/* User message */
.user {
    background: #38bdf8;
    color: black !important;
}

/* Bot message */
.bot {
    background: #1e293b;
    color: white !important;
}

/* Input box */
input {
    color: white !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #020617;
    color: white;
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

# 🤖 ANALYZE
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

    return model.generate_content(prompt).text

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

    st.session_state.history.append(("bot", result))
    st.session_state.history.append(("audio", audio))
    st.session_state.history.append(("links", links))

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

# 📥 DOWNLOAD
if st.session_state.history:
    last_response = [i for i in st.session_state.history if i[0]=="bot"][-1][1]

    st.download_button(
        "📥 Download Report",
        last_response,
        file_name="research.txt"
    )
