# Prompt for Building the "NEURAL PODCAST" Streamlit Application

## 1. High-Level Objective

Create a sophisticated, visually stunning Streamlit web application named "NEURAL PODCAST". The application's core function is to take a URL of a web article and automatically convert it into a high-quality, two-person conversational podcast using AI services. The user experience should be seamless, automated, and highly polished, with a futuristic "2035" aesthetic.

## 2. Visual Design & Theme ("The Look and Feel")

The application must have a custom, injected CSS theme to create a futuristic, holographic user interface.

- **Font**: Use 'Space Grotesk' from Google Fonts.
- **Color Palette**:
    - **Background**: A dark, space-like linear gradient (e.g., from `#0a0a2e` to `#1a1a4e`).
    - **Accent Colors**: Bright cyan (`#00ffff`) and magenta (`#ff00ff`) for highlights, gradients, and interactive elements.
    - **Text Color**: A light, slightly blue-tinted white (e.g., `#e0e0ff`) for body text and a muted version for captions (e.g., `#a0a0ff`).
- **Header**:
    - The main title should be "NEURAL PODCAST".
    - It must be large, bold, and have an animated, glowing gradient text effect using the accent colors.
    - It should have a subtle, slow "pulse" animation on its text shadow to give it a dynamic feel.
- **UI Elements**:
    - **Inputs/Selects**: Should have a dark, semi-transparent background with a bright cyan border on focus (glassmorphism effect).
    - **Buttons**: Should have a semi-transparent gradient background and a bright border that glows on hover.
    - **Containers/Sections**: Use `st.markdown` to create custom containers with rounded corners, blurred backgrounds (`backdrop-filter: blur(10px)`), and subtle borders to enhance the glassmorphism look.

## 3. Core Architecture & Backend Logic

- **Framework**: Streamlit.
- **API Keys**: The application must not ask the user for API keys. It should be configured to pull the `openai_api` and `elevenlab_api` keys directly from Streamlit's secrets management (`st.secrets`). The app should fail gracefully with a clear error message if the secrets are not configured.
- **Dependencies**:
    - `streamlit`: For the web app interface.
    - `openai`: To interact with the GPT model for script generation.
    - `requests`: For making API calls to ElevenLabs.
    - `beautifulsoup4` (or similar): For web scraping.
- **Error Handling for Audio**: The application must be robust. Some environments (like Streamlit Cloud) may lack system dependencies for advanced audio processing (`pydub`, `pyaudioop`). The app must handle this by:
    1.  Trying to import a "basic" audio synthesis utility first. This utility should perform simple audio concatenation that doesn't rely on complex libraries.
    2.  If the basic utility fails, it should fall back to an "advanced" one.
    3.  If all audio imports fail, the app must still run. It should disable all audio-related features, inform the user about the issue, and allow them to generate and download the text script only.

## 4. Application Workflow & UI Components

The application flow is designed to be linear and intuitive, with heavy automation.

### Step 1: Automated Initialization (On App Load)

1.  The app starts.
2.  It immediately attempts to load the OpenAI and ElevenLabs API keys from `st.secrets`.
3.  It then automatically calls the ElevenLabs API to get a list of all available voices.
4.  A spinner should be displayed during this voice-loading process (e.g., "Initializing AI voices...").
5.  The list of voices is cached in `st.session_state` to prevent re-fetching on every interaction.

### Step 2: Voice Configuration

-   The UI should present two configuration sections side-by-side: "Guest" and "Host".
-   Each section contains:
    1.  A text input (`st.text_input`) for the speaker's name (e.g., default to "Sarah" and "Alex").
    2.  A dropdown (`st.selectbox`) to select a voice from the list fetched during initialization.
    3.  A "Preview" button.
-   **Preview Functionality**:
    -   When a "Preview" button is clicked, the app generates a short audio clip of the selected voice saying a sample sentence (e.g., "Hello! I'm [Name], excited to be here!").
    -   The generated audio is then displayed directly below the button using `st.audio`.
    -   **Crucially**, the generated preview audio data must be stored in `st.session_state`. This ensures that if the user previews one voice, the other preview doesn't disappear from the screen.

### Step 3: Main Action - The "Record Podcast" Button

-   This is the central part of the UI.
-   It consists of a single, centered text input field for the user to paste the article URL.
-   Next to it is the primary action button, labeled "🎙️ Record Podcast".
-   This button should be disabled until a URL is entered.
-   When the button is clicked, a single, overarching spinner should appear (e.g., "🎙️ Creating your podcast..."), and the following sequence is executed:

    1.  **Scrape Article**: A utility function scrapes the provided URL to extract the article's title and clean text content.
    2.  **Generate Script**:
        -   A prompt is constructed for the OpenAI API (`gpt-4o-mini` is a good choice). The prompt should instruct the model to convert the article text into a natural, conversational dialogue between the specified Host and Guest names.
        -   The prompt should request the output in a structured JSON format, like: `{"script": [{"speaker": "Host", "text": "..."}, {"speaker": "Guest", "text": "..."}]}`.
        -   The app calls the OpenAI API and parses the JSON response.
    3.  **Synthesize Audio**:
        -   The app iterates through the generated script.
        -   For each line of dialogue, it calls the ElevenLabs API with the corresponding text and selected voice ID (Host or Guest).
        -   It concatenates the resulting audio clips, adding a short, configurable pause (e.g., 800ms) between each clip to simulate natural conversation flow.
        -   A progress bar should update during this process.
    4.  **Display Output**:
        -   Once the final audio is compiled, it is displayed prominently using `st.audio`.
        -   A `st.download_button` is provided for the user to download the final MP3 file.
        -   **Fallback**: If audio synthesis fails at any point during this process, the app should catch the exception, display an error message, and instead provide a download button for the generated *text script*.

## 5. Suggested File Structure

```
.
├── app_streamlit.py       # Main Streamlit application file
├── requirements.txt       # Python dependencies
├── secrets.toml           # For local development (to be mirrored in st.secrets)
└── utils/
    ├── __init__.py
    ├── scrape.py          # Contains function to scrape and clean article text
    ├── script_prompt.py   # Contains function to build the OpenAI prompt
    └── audio.py           # Contains functions for voice preview and final audio synthesis
```

By following this detailed prompt, the resulting application will be a feature-rich, robust, and aesthetically pleasing tool that fully automates the process of turning an article into a podcast.
