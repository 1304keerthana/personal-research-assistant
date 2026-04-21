import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from elevenlabs.client import ElevenLabs

# 🔑 API setup
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-flash-latest")

tts = ElevenLabs(api_key=st.secrets["ELEVENLABS_API_KEY"])


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


def scrape(links):
    text_data = ""

    for link in links:
        try:
            res = requests.get(link, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            for s in soup(["script", "style"]):
                s.decompose()

            text_data += soup.get_text()[:1500]
        except:
            pass

    return text_data


def analyze(topic, content):
    content = content[:3000]

    prompt = f"""
    Topic: {topic}

    Based on:
    {content}

    Give:
    - Summary
    - Key Points
    - Conclusion
    """

    response = model.generate_content(prompt)
    return response.text


def speak(text):
    text = text[:1000]

    audio_stream = tts.text_to_speech.convert(
        text=text,
        voice_id="8EEE0OzQy5ya1FinKf4y"
    )

    audio_bytes = b"".join(audio_stream)

    with open("output.mp3", "wb") as f:
        f.write(audio_bytes)

    return "output.mp3"


# UI
st.title("🔬 Personal Research Assistant 🎙️")

topic = st.text_input("Enter your topic")

if st.button("Research"):

    if topic:
        with st.spinner("Researching..."):

            links = search(topic)
            content = scrape(links)
            result = analyze(topic, content)
            audio = speak(result)

            st.subheader("📊 Analysis")
            st.write(result)

            st.subheader("📚 Sources")
            for link in links:
                st.write(link)

            st.subheader("🎧 Audio")
            st.audio(audio)
