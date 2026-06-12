import streamlit as st
import requests
from bs4 import BeautifulSoup
from elevenlabs.client import ElevenLabs
from gtts import gTTS
import time
import google.generativeai as genai


# 🔑 CONFIG
st.set_page_config(page_title="AI Research Assistant", page_icon="🧠", layout="wide")

genai_key = st.secrets.get("GEMINI_API_KEY", "")
genai.configure(api_key=genai_key)
genai.use_vertexai = False

# Try multiple model options
models_to_try = [
    "gemini-3.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp", 
    "gemini-1.5-flash",
    "gemini-pro"
]

model = None
model_name_used = None
for model_name in models_to_try:
    try:
        test_model = genai.GenerativeModel(model_name)
        model = test_model
        model_name_used = model_name
        break
    except Exception as e:
        continue

if not model:
    st.error("❌ No compatible Gemini model found. Please check your API key.")
    st.info("""
    **Setup Instructions:**
    1. Go to https://share.streamlit.io/settings
    2. Click 'Secrets' tab
    3. Add these secrets:
    ```
    GEMINI_API_KEY = "your_key"
    ELEVENLABS_API_KEY = "your_key"
    PEXELS_API_KEY = "your_key"
    ```
    """)
    st.stop()

elevenlabs_key = st.secrets.get("ELEVENLABS_API_KEY", "")
try:
    if elevenlabs_key and elevenlabs_key != "your_elevenlabs_api_key_here":
        tts = ElevenLabs(api_key=elevenlabs_key)
    else:
        tts = None
except Exception:
    tts = None

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
def search(query, max_results=3):
    encoded = requests.utils.requote_uri(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(res.text, "html.parser")

    links = []
    for a in soup.find_all("a", class_="result__a", limit=max_results):
        link = a.get("href")
        if link:
            links.append(link)
    return links
def get_images(query):
    pexels_key = st.secrets.get("PEXELS_API_KEY")
    if not pexels_key:
        return []

    headers = {
        "Authorization": pexels_key
    }

    url = f"https://api.pexels.com/v1/search?query={requests.utils.requote_uri(query)}&per_page=3"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        images = []
        for photo in data.get("photos", []):
            images.append(photo["src"]["large"])

        return images
    except Exception as e:
        st.warning(f"Image fetch failed: {e}")
        return []

# 📄 SCRAPE
def scrape(links, max_chars=4000):
    text = ""
    headers = {"User-Agent": "Mozilla/5.0"}

    for link in links:
        try:
            res = requests.get(link, timeout=10, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            for s in soup(["script", "style"]):
                s.decompose()

            paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
            page_text = "\n\n".join(paragraphs)
            text += page_text[:1500] + "\n\n"

            if len(text) >= max_chars:
                break
        except requests.RequestException:
            continue

    return text.strip()

def analyze(topic, content, sources):
    source_text = content[:3200]
    prompt = f"""
    Topic: {topic}

    Sources:
    {sources}

    Content excerpts:
    {source_text}

    Please provide a high-quality research summary for the topic above.
    Include:
    - A short summary of the topic
    - 3 key points
    - A concise conclusion
    - Suggested next steps or further questions for research
    """

    try:
        st.write("Calling Gemini...")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini Error: {e}")
        return f"Error: {e}"
# 🎙️ SPEAK (SAFE)
VOICE_IDS = {
    "Default": "EXAVITQu4vr4xnSDxMaL",
    "Alternative": "EXAVITQu4vr4xnSDxMaL"
}


def speak(text, enable_voice, voice_id):
    if not enable_voice or not text:
        return None

    text = text[:800]

    try:
        if tts:
            audio_stream = tts.text_to_speech.convert(
                text=text,
                voice_id=voice_id
            )
            audio_bytes = b"".join(audio_stream)
            with open("output.mp3", "wb") as f:
                f.write(audio_bytes)
            return "output.mp3"
        else:
            raise Exception("ElevenLabs not configured")
    except Exception:
        # Use gTTS fallback
        tts_fallback = gTTS(text=text, lang='en')
        tts_fallback.save("output.mp3")
        return "output.mp3"

# ✨ HEADER
st.title("🧠 AI Research Assistant")
st.caption("Search • Analyze • Chat • Listen 🎧")

# 🎛️ SIDEBAR SETTINGS
st.sidebar.header("⚙️ Settings")

voice_toggle = st.sidebar.checkbox("Enable Voice", True)

voice_choice = st.sidebar.selectbox(
    "Voice",
    ["Default", "Alternative"],
    index=0
)

max_results = st.sidebar.slider("Search results to scrape", min_value=1, max_value=5, value=3)

clear = st.sidebar.button("🗑️ Clear Chat")

if clear:
    st.session_state.history = []

# 📥 INPUT
user_input = st.chat_input("Ask something...")

if user_input:
    st.session_state.history.append(("user", user_input))

    with st.spinner("Researching and summarizing..."):
        links = search(user_input, max_results=max_results)
        content = scrape(links)
        result = analyze(user_input, content, "\n".join(links))
        audio = speak(result, voice_toggle, VOICE_IDS.get(voice_choice, VOICE_IDS["Default"]))
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
        if content:
            with st.expander("📚 Sources"):
                for l in content:
                    st.write(l)
    elif role == "images" and content:
        st.subheader("🖼️ Related Images")
        cols = st.columns(len(content))
        for col, img_url in zip(cols, content):
            with col:
                st.image(img_url, width='stretch')
bot_responses = [i for i in st.session_state.history if i[0] == "bot"]

if bot_responses:
    last_response = bot_responses[-1][1]

    st.download_button(
        "📥 Download Report",
        last_response,
        file_name="research.txt"
    )
