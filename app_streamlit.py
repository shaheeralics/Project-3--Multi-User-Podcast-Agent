"""
Professional Podcast Generator App - Production Version
Converts articles to conversational podcasts using OpenAI and ElevenLabs
Uses Streamlit secrets for API keys (no manual input required)

"""

import streamlit as st
import requests
import json
import time
import io
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import base64

# Import utility modules
from utils.scrape import scrape_and_clean
from utils.script_prompt import build_messages, validate_script_response

# Try to import audio modules with graceful fallback
_AUDIO_AVAILABLE = True
_AUDIO_ERROR = ""
try:
    from utils.audio_streamlit import synthesize_episode, get_available_voices, preview_voice
except Exception as e:
    _AUDIO_AVAILABLE = False
    _AUDIO_ERROR = str(e)
    # Define dummy functions to prevent import errors
    def synthesize_episode(*args, **kwargs):
        raise Exception(f"Audio synthesis not available: {_AUDIO_ERROR}")
    def get_available_voices(*args, **kwargs):
        return []
    def preview_voice(*args, **kwargs):
        return None

# Page configuration
st.set_page_config(
    page_title="AI Podcast Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for futuristic design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    /* Dark futuristic theme */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
    }
    
    body, .main-header, .section-header {
        font-family: 'Orbitron', 'Inter', monospace;
        color: #ffffff;
    }
    
    .main-header {
        background: linear-gradient(135deg, #00d4ff 0%, #7b2cbf 50%, #ff006e 100%);
        padding: 2rem 0 1.5rem 0;
        text-align: center;
        color: #ffffff;
        margin-bottom: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
        letter-spacing: 1px;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        animation: shine 3s infinite;
    }
    
    @keyframes shine {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        letter-spacing: 3px;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.8);
        font-family: 'Orbitron', monospace;
    }
    
    .main-header p {
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 0.2rem;
        color: rgba(255,255,255,0.9);
        text-shadow: 0 0 10px rgba(255,255,255,0.5);
    }
    
    .section-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #00d4ff;
        font-size: 1.2rem;
        font-weight: 700;
        margin: 1.5rem 0 1rem 0;
        padding: 0.8rem 1.2rem;
        border: 1px solid #00d4ff;
        border-radius: 10px;
        letter-spacing: 1px;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
    }
    
    /* Futuristic inputs */
    .stTextInput > div > div > input {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #00d4ff;
        border-radius: 8px;
        color: #ffffff;
        padding: 0.7rem;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #ff006e;
        box-shadow: 0 0 20px rgba(255, 0, 110, 0.4);
    }
    
    .stSelectbox > div > div {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #00d4ff;
        border-radius: 8px;
        color: #ffffff;
    }
    
    /* Futuristic buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7b2cbf 0%, #ff006e 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 700;
        font-size: 1rem;
        font-family: 'Orbitron', monospace;
        transition: all 0.3s ease;
        box-shadow: 0 0 15px rgba(123, 44, 191, 0.4);
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #ff006e 0%, #00d4ff 100%);
        transform: translateY(-2px) scale(1.05);
        box-shadow: 0 0 25px rgba(255, 0, 110, 0.6);
    }
    
    /* Futuristic success/error boxes */
    .success-box, .error-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 8px;
        color: #ffffff;
        padding: 1rem;
        margin: 1rem 0;
        font-weight: 500;
        border: 1px solid;
        box-shadow: 0 0 15px;
    }
    
    .success-box {
        border-color: #00d4ff;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
    }
    
    .error-box {
        border-color: #ff006e;
        box-shadow: 0 0 15px rgba(255, 0, 110, 0.3);
    }
    
    /* Futuristic core config */
    .core-config {
        display: flex;
        flex-wrap: nowrap;
        gap: 1rem;
        justify-content: flex-start;
        align-items: flex-start;
        margin-bottom: 1.5rem;
        padding: 1rem;
        border: 1px solid #00d4ff;
        border-radius: 15px;
        background: linear-gradient(135deg, rgba(26,26,46,0.8) 0%, rgba(22,33,62,0.8) 100%);
        backdrop-filter: blur(10px);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
    }
    
    /* Fix text visibility in dark mode */
    .stApp, .stApp > div, .stApp p, .stApp span, .stApp label {
        color: #ffffff !important;
    }
    
    /* Input labels and text */
    .stTextInput label, .stSelectbox label, .stSlider label, .stCheckbox label {
        color: #00d4ff !important;
        font-weight: 600 !important;
        text-shadow: 0 0 5px rgba(0, 212, 255, 0.3) !important;
    }
    
    /* Selectbox options */
    .stSelectbox > div > div > div {
        background: #1a1a2e !important;
        color: #ffffff !important;
    }
    
    /* Slider text */
    .stSlider > div > div > div > div {
        color: #ffffff !important;
    }
    
    /* Checkbox text */
    .stCheckbox > label > div > p {
        color: #ffffff !important;
    }
    
    /* Metric text */
    .metric-container, .metric-container * {
        color: #ffffff !important;
    }
    
    /* Expander text */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
        color: #00d4ff !important;
        border: 1px solid #00d4ff !important;
    }
    
    /* General text elements */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #ffffff !important;
    }
    }
    .core-config > div {
        min-width: 140px;
        max-width: 180px;
        flex: 1 1 140px;
    }
    .section-header {
        background: none;
        color: #222;
        font-size: 1rem;
        font-weight: 700;
        margin: 1.2rem 0 0.2rem 0;
        padding: 0;
        border: none;
        letter-spacing: 0.5px;
        border-bottom: 1px solid #eee;
    }
    .stButton > button {
        background: #222;
        color: #fff;
        border: none;
        border-radius: 2px;
        padding: 0.3rem 1.2rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        box-shadow: none;
    }
    .stButton > button:hover {
        background: #555;
        color: #fff;
        transform: translateY(-1px) scale(1.03);
    }
    .success-box, .error-box {
        background: #f8f9fa;
        border-radius: 2px;
        color: #222;
        padding: 0.7rem;
        margin: 0.7rem 0;
        font-weight: 500;
        box-shadow: none;
        border: 1px solid #eee;
        font-size: 0.95rem;
    }
    .success-box {
        border-left: 2px solid #00c9a7;
    }
    .error-box {
        border-left: 2px solid #ff6a88;
    }
</style>
""", unsafe_allow_html=True)

def get_api_keys():
    """Get API keys from Streamlit secrets"""
    try:
        openai_api_key = st.secrets["openaiapi"]
        elevenlabs_api_key = st.secrets["elevenlabsapi"]
        return openai_api_key, elevenlabs_api_key
    except KeyError as e:
        st.error(f"Missing API key in secrets: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Error accessing secrets: {e}")
        st.stop()

def generate_script_text_file(script_turns, article_title):
    """
    Generate a formatted text file from the podcast script
    
    Args:
        script_turns: List of script turns with speaker and text
        article_title: Title of the article
    
    Returns:
        Formatted text content for download
    """
    lines = []
    lines.append("=" * 60)
    lines.append("PODCAST SCRIPT")
    lines.append("=" * 60)
    lines.append(f"Title: {article_title}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")
    
    for i, turn in enumerate(script_turns, 1):
        speaker = turn.get('speaker', 'Unknown').upper()
        text = turn.get('text', '')
        
        lines.append(f"[{i:02d}] {speaker}:")
        lines.append(f"    {text}")
        lines.append("")
    
    lines.append("=" * 60)
    lines.append("END OF SCRIPT")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def initialize_session_state():
    """Initialize session state variables"""
    if 'voices_loaded' not in st.session_state:
        st.session_state.voices_loaded = False
    if 'available_voices' not in st.session_state:
        st.session_state.available_voices = []
    if 'script_generated' not in st.session_state:
        st.session_state.script_generated = False
    if 'generated_script' not in st.session_state:
        st.session_state.generated_script = []
    if 'audio_generated' not in st.session_state:
        st.session_state.audio_generated = False
    if 'api_keys_loaded' not in st.session_state:
        st.session_state.api_keys_loaded = False

def render_header():
    """Render the main application header"""
    st.markdown("""
    <div class="main-header">
        <h1>Podcast GPT</h1>
        <p>Transform articles into professional, conversational podcasts with AI.</p>
    </div>
    """, unsafe_allow_html=True)

def render_api_status(openai_api_key, elevenlabs_api_key):
    """Render configuration: full-width model row, full-width voice row."""
    st.markdown('<div class="section-header"><h3>⚙️ Core Configuration</h3></div>', unsafe_allow_html=True)

    # Row 1: Model selection
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    openai_model = st.selectbox(
        "Select OpenAI Model",
        ["gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        index=1 if "gpt-5" not in (st.session_state.get('selected_model') or '') else 0,
        help="Choose the model that will convert article content into a structured, conversational script."
    )
    st.session_state.selected_model = openai_model
    st.caption("Model loaded securely (keys never exposed). Higher-tier models may improve nuance.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Row 2: Voice loading
    st.markdown('<div class="info-box" style="margin-top:0.75rem;">', unsafe_allow_html=True)
    if not st.session_state.voices_loaded:
        st.write("Optionally load ElevenLabs voices for later audio synthesis (if supported).")
        if st.button("🎵 Load Voices", key="load_voices"):
            with st.spinner("Loading voices..."):
                try:
                    voices = get_available_voices(elevenlabs_api_key)
                    st.session_state.available_voices = voices
                    st.session_state.voices_loaded = True
                    st.success(f"Loaded {len(voices)} voices")
                    st.rerun()
                except Exception as e:
                    st.error(f"Voice load failed: {str(e)}")
    else:
        st.success(f"Voices loaded: {len(st.session_state.available_voices)}")
        cols = st.columns([1,1,2])
        with cols[0]:
            if st.button("🔄 Refresh", key="refresh_voices"):
                with st.spinner("Refreshing voices..."):
                    try:
                        voices = get_available_voices(elevenlabs_api_key)
                        st.session_state.available_voices = voices
                        st.success(f"Updated: {len(voices)} voices")
                    except Exception as e:
                        st.error(f"Refresh failed: {str(e)}")
        with cols[1]:
            st.write(f"Default host voices: {min(3, len(st.session_state.available_voices))} shown in selector later")
        with cols[2]:
            st.caption("You can adjust host/guest voices in the Speaker Configuration section once loaded.")
    st.caption("Skip this step if you only need the script.")
    st.markdown('</div>', unsafe_allow_html=True)

    return openai_model

def render_voice_selection():
    """Render voice selection interface"""
    # Check if audio is available
    if not _AUDIO_AVAILABLE:
        st.markdown(f'<div class="error-box">⚠️ {_AUDIO_ERROR}</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">Audio synthesis features are currently unavailable. Script generation will still work.</div>', unsafe_allow_html=True)
        return None, None, None, None
    
    if not st.session_state.voices_loaded:
        st.markdown('<div class="info-box">🎵 Please load voices first to configure podcast speakers</div>', unsafe_allow_html=True)
        return None, None, None, None
    
    st.markdown('<div class="section-header"><h3>🎭 Speaker Configuration</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    voice_options = [(v['name'], v['voice_id']) for v in st.session_state.available_voices]
    
    with col1:
        st.markdown('<div class="voice-card">', unsafe_allow_html=True)
        st.subheader("🎤 Host")
        host_name = st.text_input("Host Name", value="Alex", key="host_name")
        host_voice = st.selectbox(
            "Host Voice",
            voice_options,
            format_func=lambda x: x[0],
            key="host_voice"
        )
        
        if host_voice and st.button("🔊 Preview Host Voice", key="preview_host"):
            with st.spinner("Generating preview..."):
                try:
                    _, elevenlabs_api_key = get_api_keys()
                    audio_data = preview_voice(
                        elevenlabs_api_key,
                        host_voice[1],
                        f"G'day! I'm {host_name}, your podcast host."
                    )
                    st.audio(audio_data)
                except Exception as e:
                    st.error(f"❌ Preview failed: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="voice-card">', unsafe_allow_html=True)
        st.subheader("👥 Guest")
        guest_name = st.text_input("Guest Name", value="Sarah", key="guest_name")
        guest_voice = st.selectbox(
            "Guest Voice",
            voice_options,
            format_func=lambda x: x[0],
            key="guest_voice"
        )
        
        if guest_voice and st.button("🔊 Preview Guest Voice", key="preview_guest"):
            with st.spinner("Generating preview..."):
                try:
                    _, elevenlabs_api_key = get_api_keys()
                    audio_data = preview_voice(
                        elevenlabs_api_key,
                        guest_voice[1],
                        f"Hello! I'm {guest_name}, excited to be here!"
                    )
                    st.audio(audio_data)
                except Exception as e:
                    st.error(f"❌ Preview failed: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return host_name, host_voice, guest_name, guest_voice

def render_script_generation(openai_model, article_url, host_name, guest_name, aussie_style):
    """Render script generation section - simplified version"""
    if st.button("🚀 Generate Podcast Script", key="generate_script"):
        with st.spinner("🔄 Processing article and generating script..."):
            try:
                # Get API key
                openai_api_key, _ = get_api_keys()
                
                # Scrape article
                article = scrape_and_clean(article_url)
                
                # Generate script using OpenAI
                import openai
                openai.api_key = openai_api_key
                
                messages = build_messages(
                    article_title=article["title"],
                    article_text=article["text"],
                    host_name=host_name,
                    guest_name=guest_name,
                    aussie=aussie_style
                )
                
                response = openai.ChatCompletion.create(
                    model=openai_model,
                    messages=messages,
                    temperature=0.7
                )
                
                response_content = response.choices[0].message.content
                script_content = validate_script_response(response_content, host_name, guest_name)
                st.session_state.generated_script = script_content.get("script", [])
                st.session_state.script_generated = True
                st.session_state.article_title = article["title"]
                
                st.success("🎉 Script generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display generated script
    if st.session_state.script_generated and st.session_state.generated_script:
        with st.expander("� View Generated Script", expanded=True):
            for i, turn in enumerate(st.session_state.generated_script, 1):
                speaker = turn.get('speaker', 'Unknown')
                text = turn.get('text', '')
                
                if speaker.lower() == 'host':
                    st.markdown(f"**🎤 {host_name} (Host):** {text}")
                else:
                    st.markdown(f"**👥 {guest_name} (Guest):** {text}")
                
                if i < len(st.session_state.generated_script):
                    st.markdown("---")

def render_audio_generation(host_voice, guest_voice, pause_duration):
    """Render audio generation section"""
    if not st.session_state.script_generated:
        return
    
    st.markdown('<div class="section-header"><h3>🎵 Audio Generation</h3></div>', unsafe_allow_html=True)
    
    # Check if audio synthesis is available
    if not _AUDIO_AVAILABLE:
        st.warning(f"⚠️ {_AUDIO_ERROR}")
        st.info("💡 The app will generate a downloadable script text file instead of audio.")
        
        # Provide script download option
        if st.button("📄 Generate Script Text File", key="generate_script_file"):
            script_text = generate_script_text_file(st.session_state.generated_script, st.session_state.article_title)
            st.download_button(
                label="📥 Download Script as Text File",
                data=script_text,
                file_name=f"podcast_script_{st.session_state.article_title.replace(' ', '_')[:50]}.txt",
                mime="text/plain",
                key="download_script"
            )
            st.success("✅ Script text file generated! Click the download button above.")
        return
    
    if not all([host_voice, guest_voice]):
        st.warning("⚠️ Please configure voices and load them first")
        return
    
    if st.button("🎧 Generate Podcast Audio", key="generate_audio"):
        with st.spinner("🎵 Generating high-quality audio... This may take a few minutes."):
            try:
                _, elevenlabs_api_key = get_api_keys()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                audio_bytes = None
                filename = None
                format_label = "MP3"
                mime_type = "audio/mp3"
                playback_format = 'audio/mp3'

                try:
                    # Primary (advanced) path using pydub utilities
                    audio_bytes, filename = synthesize_episode(
                        script=st.session_state.generated_script,
                        pause_ms=pause_duration,
                        host_voice_id=host_voice[1],
                        guest_voice_id=guest_voice[1],
                        eleven_key=elevenlabs_api_key,
                        progress_callback=lambda p, s: (
                            progress_bar.progress(p),
                            status_text.text(s)
                        )
                    )
                except Exception as advanced_err:
                    # Fallback to basic WAV synthesis that doesn't rely on pydub/audioop
                    try:
                        from utils.audio_basic import synthesize_episode_basic, BasicAudioError
                        status_text.text("⚙️ Falling back to basic WAV synthesis...")
                        progress_bar.progress(10)
                        audio_bytes, filename = synthesize_episode_basic(
                            script=st.session_state.generated_script,
                            host_voice_id=host_voice[1],
                            guest_voice_id=guest_voice[1],
                            eleven_key=elevenlabs_api_key,
                            pause_ms=pause_duration,
                            progress_callback=lambda p, s: (
                                progress_bar.progress(min(90, p)),
                                status_text.text(s)
                            )
                        )
                        if filename.lower().endswith('.mp3'):
                            format_label = "MP3 (basic concat)"
                            mime_type = "audio/mp3"
                            playback_format = 'audio/mp3'
                        else:
                            format_label = "WAV (basic)"
                            mime_type = "audio/wav"
                            playback_format = 'audio/wav'
                    except Exception as basic_err:
                        raise Exception(f"Advanced synthesis failed ({advanced_err}); basic fallback failed ({basic_err})")
                
                st.session_state.audio_generated = True
                st.session_state.audio_bytes = audio_bytes
                st.session_state.audio_filename = filename
                st.session_state.audio_mime = mime_type
                st.session_state.audio_format_label = format_label
                st.session_state.audio_playback_format = playback_format
                
                progress_bar.progress(100)
                status_text.text("✅ Audio generation complete!")
                
                st.markdown('<div class="success-box">🎉 Podcast audio generated successfully!</div>', unsafe_allow_html=True)
                
                # Audio statistics
                audio_size_mb = len(audio_bytes) / (1024 * 1024)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📁 File Size", f"{audio_size_mb:.1f} MB")
                with col2:
                    st.metric("🎵 Format", format_label)
                
            except Exception as e:
                st.markdown(f'<div class="error-box">❌ Audio generation failed: {str(e)}</div>', unsafe_allow_html=True)
    
    # Display audio player and download
    if st.session_state.audio_generated:
        st.subheader("🎧 Your Podcast")
        
        # Audio player
        playback_fmt = st.session_state.get('audio_playback_format', 'audio/mp3')
        st.audio(st.session_state.audio_bytes, format=playback_fmt)
        
        # Download section
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label=f"📥 Download Podcast {st.session_state.get('audio_format_label','Audio')}",
                data=st.session_state.audio_bytes,
                file_name=st.session_state.audio_filename,
                mime=st.session_state.get('audio_mime','audio/mp3'),
                key="download_audio"
            )
        
        with col2:
            if st.button("🔄 Generate New Podcast", key="reset_app"):
                # Reset session state for new podcast
                st.session_state.script_generated = False
                st.session_state.audio_generated = False
                st.session_state.generated_script = []
                st.success("Ready for new podcast generation!")
                st.rerun()

def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    # Check OpenAI
    try:
        import openai
        # Test if it's the older version we need
        if not hasattr(openai, 'ChatCompletion'):
            missing_deps.append("openai (need version 0.28.1)")
    except ImportError:
        missing_deps.append("openai")
    
    # Check requests
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    if missing_deps:
        st.error(f"❌ Missing required packages: {', '.join(missing_deps)}")
        st.error("Please ensure these packages are listed in requirements.txt:")
        for dep in missing_deps:
            if "openai" in dep:
                st.code("openai==0.28.1")
            else:
                st.code(dep)
        st.stop()

def main():
    """Main application function"""
    # Check dependencies first
    check_dependencies()
    
    initialize_session_state()
    render_header()

    # Core Configurations Section (compact, top)
    st.markdown('<div class="section-header">Core Configuration</div>', unsafe_allow_html=True)
    
    # First Line: API keys, model, and load voices
    col1, col2, col3, col4 = st.columns([2, 1.5, 2, 1])
    with col1:
        openai_api_key = st.text_input("OpenAI API Key", type="password", help="Required for script generation")
    with col2:
        openai_model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], help="Choose the OpenAI model")
    with col3:
        elevenlabs_api_key = st.text_input("ElevenLabs API Key", type="password", help="Required for voice synthesis")
    with col4:
        if elevenlabs_api_key and not st.session_state.voices_loaded:
            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
            if st.button("Load Voices"):
                with st.spinner("Loading voices..."):
                    try:
                        voices = get_available_voices(elevenlabs_api_key)
                        st.session_state.available_voices = voices
                        st.session_state.voices_loaded = True
                        st.success(f"Loaded {len(voices)} voices successfully!")
                    except Exception as e:
                        st.error(f"Failed to load voices: {str(e)}")
    
    # Second Line: Names, Voice Selection, and Preview Buttons (only show if voices are loaded)
    if st.session_state.voices_loaded:
        voice_options = [(v['name'], v['voice_id']) for v in st.session_state.available_voices]
        
        col5, col6, col7, col8, col9, col10 = st.columns([1.2, 1.5, 0.8, 1.2, 1.5, 0.8])
        
        # Guest configuration
        with col5:
            guest_name = st.text_input("Guest Name", value="Sarah")
        with col6:
            guest_voice = st.selectbox("Guest Voice", voice_options, format_func=lambda x: x[0])
        with col7:
            preview_guest = st.button("Preview Guest", key="preview_guest")
        
        # Host configuration  
        with col8:
            host_name = st.text_input("Host Name", value="Alex")
        with col9:
            host_voice = st.selectbox("Host Voice", voice_options, format_func=lambda x: x[0])
        with col10:
            preview_host = st.button("Preview Host", key="preview_host")
        
        # Third Line: Preview audio players
        col11, col12 = st.columns(2)
        
        # Guest voice preview
        if preview_guest and guest_voice:
            with col11:
                with st.spinner("Generating guest voice preview..."):
                    try:
                        audio_data = preview_voice(
                            elevenlabs_api_key,
                            guest_voice[1],
                            f"Hello! I'm {guest_name}, excited to be here!"
                        )
                        st.audio(audio_data)
                        st.caption(f"Guest: {guest_name}")
                    except Exception as e:
                        st.error(f"Guest preview failed: {str(e)}")
        
        # Host voice preview
        if preview_host and host_voice:
            with col12:
                with st.spinner("Generating host voice preview..."):
                    try:
                        audio_data = preview_voice(
                            elevenlabs_api_key,
                            host_voice[1],
                            f"G'day! I'm {host_name}, your podcast host."
                        )
                        st.audio(audio_data)
                        st.caption(f"Host: {host_name}")
                    except Exception as e:
                        st.error(f"Host preview failed: {str(e)}")
        
    else:
        host_voice = guest_voice = None
        host_name = "Alex"
        guest_name = "Sarah"

    # Configuration inputs (moved here from removed Article Input section)
    col_url, col_btn = st.columns([3, 1])  # 75% for URL, 25% for button
    with col_url:
        article_url = st.text_input("Article URL", placeholder="https://example.com/article", help="Paste the URL of the article")
    with col_btn:
        st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
        scrape_button = st.button("🔍 Scrape Article", disabled=not article_url)
    
    # Set default values
    pause_duration = 800  # Default 800ms pause
    aussie_style = True   # Default Australian style
    
    # Script Generation
    if article_url:
        render_script_generation(openai_model, article_url, host_name, guest_name, aussie_style)

    # Audio Generation Section
    st.markdown('<div class="section-header">Audio Generation</div>', unsafe_allow_html=True)
    render_audio_generation(host_voice, guest_voice, pause_duration)

    # Footer
    st.markdown("""
    <div style="text-align: center; color: #888; margin-top:2rem; font-size:0.95rem;">
        Podcast GPT &mdash; Powered by Streamlit, OpenAI, and ElevenLabs
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
