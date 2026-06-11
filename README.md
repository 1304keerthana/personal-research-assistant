# AI Personal Research Assistant

A Streamlit app that:
- Searches the web for research topic results
- Scrapes source text and generates a concise summary with Gemini AI
- Produces a voice note using ElevenLabs or gTTS fallback
- Shows 2-3 related images from Pexels

## Setup

1. Create a Python environment and install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Add secrets via `Streamlit` secrets or environment configuration.

Example `./.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your_gemini_key"
ELEVENLABS_API_KEY = "your_elevenlabs_key"
PEXELS_API_KEY = "your_pexels_key"
```

`PEXELS_API_KEY` is optional; if missing, the app will still generate summaries and voice notes.

## Run

```bash
streamlit run app.py
```

## Notes

- The app uses DuckDuckGo HTML search for source discovery.
- It scrapes text from the top result pages, then summarizes using Gemini.
- Voice notes are saved as `output.mp3` and played in the app.
- Use the sidebar to enable/disable voice and adjust search result count.
