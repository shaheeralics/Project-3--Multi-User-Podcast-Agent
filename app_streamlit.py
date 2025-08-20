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
    # Try basic audio first (works without pydub/audioop)
    from utils.audio_basic import synthesize_episode_basic as synthesize_episode
    from utils.audio_streamlit import get_available_voices, preview_voice
except Exception as e:
    try:
        # Fallback to advanced audio
        from utils.audio_streamlit import synthesize_episode, get_available_voices, preview_voice
    except Exception as e2:
        _AUDIO_AVAILABLE = False
        _AUDIO_ERROR = str(e2)
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

# Custom CSS for 2035 futuristic design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    /* 2035 Futuristic Theme */
    .stApp {
        background: linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2a2a6e 100%);
        color: #e0e0ff;
    }
    
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, rgba(0,255,255,0.1) 0%, rgba(128,0,255,0.1) 100%);
        border: 1px solid rgba(0,255,255,0.3);
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        border-radius: 15px;
        backdrop-filter: blur(10px);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 600;
        background: linear-gradient(135deg, #00ffff 0%, #ff00ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Space Grotesk', sans-serif;
    }
    
    .main-header p {
        color: #a0a0ff;
        font-size: 1.1rem;
    }
    
    /* Section headers */
    .section-header {
        background: rgba(0,255,255,0.1);
        color: #00ffff;
        padding: 1rem 1.5rem;
        border: 1px solid rgba(0,255,255,0.3);
        border-radius: 10px;
        margin: 1.5rem 0;
        font-weight: 600;
        backdrop-filter: blur(5px);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(20,20,60,0.8) !important;
        border: 1px solid rgba(0,255,255,0.3) !important;
        border-radius: 8px !important;
        color: #e0e0ff !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00ffff !important;
        box-shadow: 0 0 10px rgba(0,255,255,0.3) !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0,255,255,0.2) 0%, rgba(128,0,255,0.2) 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(0,255,255,0.5) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stButton > button:hover {
        border-color: #00ffff !important;
        box-shadow: 0 0 15px rgba(0,255,255,0.4) !important;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div > div {
        background: rgba(20,20,60,0.8) !important;
        color: #e0e0ff !important;
        border: 1px solid rgba(0,255,255,0.3) !important;
    }
    
    /* Text color fixes */
    .stApp * {
        color: #e0e0ff;
    }
    
    /* Labels */
    label {
        color: #a0a0ff !important;
        font-weight: 500 !important;
    }
    
    /* Success/Error boxes */
    .success-box {
        background: rgba(0,255,128,0.1);
        border: 1px solid rgba(0,255,128,0.5);
        color: #00ff80;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .error-box {
        background: rgba(255,0,128,0.1);
        border: 1px solid rgba(255,0,128,0.5);
        color: #ff0080;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
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
    <div style="text-align: center; margin: 2rem 0 3rem 0;">
        <h1 style="
            font-size: 3.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00ffff 0%, #ff00ff 50%, #ffff00 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-family: 'Space Grotesk', sans-serif;
            letter-spacing: 2px;
            margin-bottom: 0.5rem;
            text-shadow: 0 0 40px rgba(0,255,255,0.3);
            animation: glow-pulse 2s ease-in-out infinite alternate;
        ">NEURAL PODCAST</h1>
        <p style="
            font-size: 1.2rem;
            color: #a0a0ff;
            font-weight: 400;
            letter-spacing: 1px;
            margin: 0;
            text-shadow: 0 0 10px rgba(160,160,255,0.5);
        ">AI-Powered Audio Generation System</p>
    </div>
    <style>
        @keyframes glow-pulse {
            from { text-shadow: 0 0 40px rgba(0,255,255,0.3); }
            to { text-shadow: 0 0 60px rgba(0,255,255,0.6), 0 0 80px rgba(255,0,255,0.3); }
        }
    </style>
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

    # Get API keys from Streamlit secrets and set default model
    try:
        openai_api_key = st.secrets["openai_api"]
        elevenlabs_api_key = st.secrets["elevenlab_api"]
    except (KeyError, AttributeError):
        st.error("API keys (openai_api, elevenlab_api) not found in Streamlit secrets.")
        st.info("Please add your API keys to the secrets.toml file and restart the app.")
        st.code("""
[secrets]
openai_api = "sk-..."
elevenlab_api = "..."
        """, language="toml")
        st.stop()
        
    openai_model = "gpt-4o-mini"

    # Auto-load voices on startup if not already loaded
    if not st.session_state.voices_loaded:
        with st.spinner("Initializing AI voices..."):
            try:
                voices = get_available_voices(elevenlabs_api_key)
                if not voices:
                    raise Exception("No voices returned from ElevenLabs. Check your API key and account status.")
                st.session_state.available_voices = voices
                st.session_state.voices_loaded = True
            except Exception as e:
                st.error(f"Fatal Error: Could not load voices from ElevenLabs. {e}")
                st.stop()

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
            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
            preview_guest = st.button("Preview Guest", key="preview_guest")
        
        # Host configuration  
        with col8:
            host_name = st.text_input("Host Name", value="Alex")
        with col9:
            host_voice = st.selectbox("Host Voice", voice_options, format_func=lambda x: x[0])
        with col10:
            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
            preview_host = st.button("Preview Host", key="preview_host")
        
        # Third Line: Preview audio players
        col11, col12 = st.columns(2)
        
        # Guest voice preview
        if preview_guest and guest_voice:
            with st.spinner("Generating guest voice preview..."):
                try:
                    audio_data = preview_voice(
                        elevenlabs_api_key,
                        guest_voice[1],
                        f"Hello! I'm {guest_name}, excited to be here!"
                    )
                    st.session_state.guest_preview_audio = audio_data
                    st.session_state.guest_preview_name = guest_name
                except Exception as e:
                    st.error(f"Guest preview failed: {str(e)}")
        
        # Host voice preview
        if preview_host and host_voice:
            with st.spinner("Generating host voice preview..."):
                try:
                    audio_data = preview_voice(
                        elevenlabs_api_key,
                        host_voice[1],
                        f"G'day! I'm {host_name}, your podcast host."
                    )
                    st.session_state.host_preview_audio = audio_data
                    st.session_state.host_preview_name = host_name
                except Exception as e:
                    st.error(f"Host preview failed: {str(e)}")
        
        # Display stored previews
        with col11:
            if hasattr(st.session_state, 'guest_preview_audio') and st.session_state.guest_preview_audio:
                st.audio(st.session_state.guest_preview_audio)
                st.caption(f"Guest: {st.session_state.guest_preview_name}")
        
        with col12:
            if hasattr(st.session_state, 'host_preview_audio') and st.session_state.host_preview_audio:
                st.audio(st.session_state.host_preview_audio)
                st.caption(f"Host: {st.session_state.host_preview_name}")
        
    else:
        host_voice = guest_voice = None
        host_name = "Alex"
        guest_name = "Sarah"

    # Centered configuration inputs with 15% padding on each side
    left_pad, center_col, right_pad = st.columns([0.15, 0.7, 0.15])
    with center_col:
        # Nested columns for the input field and button
        col_url, col_btn = st.columns([3, 1])
        with col_url:
            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
            article_url = st.text_input(
                "Article URL", 
                placeholder="Paste article URL here...", 
                help="Paste the URL of the article to generate a podcast",
                label_visibility="collapsed"
            )
        with col_btn:
            st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
            record_podcast = st.button("🎙️ Record Podcast", disabled=not (article_url and host_voice and guest_voice and elevenlabs_api_key and openai_api_key))
    
    # Set default values
    pause_duration = 800  # Default 800ms pause
    aussie_style = True   # Default Australian style
    
    # All-in-one podcast generation
    if record_podcast and article_url:
        with st.spinner("🎙️ Creating your podcast... This may take a few minutes"):
            try:
                # Step 1: Scrape Article
                st.info("📖 Scraping article content...")
                article = scrape_and_clean(article_url)
                
                # Step 2: Generate Script
                st.info("🤖 Generating conversational script...")
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
                
                # Step 3: Generate Audio (if available)
                if _AUDIO_AVAILABLE and all([host_voice, guest_voice]):
                    st.info("🎵 Generating podcast audio...")
                    
                    try:
                        # Use the basic audio synthesis function (works without pydub)
                        audio_bytes, filename = synthesize_episode(
                            script=st.session_state.generated_script,
                            host_voice_id=host_voice[1],
                            guest_voice_id=guest_voice[1],
                            eleven_key=elevenlabs_api_key,
                            pause_ms=pause_duration
                        )
                        
                        st.session_state.audio_generated = True
                        st.session_state.combined_audio = audio_bytes
                        
                        st.success("🎉 Podcast created successfully!")
                        
                        # Display results
                        st.markdown("### 🎧 Your Podcast is Ready!")
                        st.audio(audio_bytes)
                        
                        # Download button
                        st.download_button(
                            label="⬇️ Download Podcast",
                            data=audio_bytes,
                            file_name=f"podcast_{st.session_state.article_title.replace(' ', '_')[:50]}.mp3",
                            mime="audio/mp3"
                        )
                        
                    except Exception as audio_error:
                        st.warning(f"⚠️ Audio generation failed: {str(audio_error)}")
                        st.info("📄 Audio synthesis not available in this environment. Generating script text file instead...")
                        
                        # Fallback to script file
                        script_text = generate_script_text_file(st.session_state.generated_script, st.session_state.article_title)
                        st.download_button(
                            label="📥 Download Script as Text File",
                            data=script_text,
                            file_name=f"podcast_script_{st.session_state.article_title.replace(' ', '_')[:50]}.txt",
                            mime="text/plain"
                        )
                        st.info("💡 **Tip**: Download the script and use text-to-speech software like ElevenLabs, Google TTS, or Azure Speech Services to generate audio locally.")
                        
                else:
                    # Audio not available, provide script download
                    st.info("📄 Audio synthesis not available in Streamlit Cloud environment. Generating script text file...")
                    script_text = generate_script_text_file(st.session_state.generated_script, st.session_state.article_title)
                    st.download_button(
                        label="📥 Download Script as Text File",
                        data=script_text,
                        file_name=f"podcast_script_{st.session_state.article_title.replace(' ', '_')[:50]}.txt",
                        mime="text/plain"
                    )
                    st.success("✅ Podcast script generated successfully!")
                    st.info("💡 **Next Steps**: Use the downloaded script with ElevenLabs API directly, or other TTS services to create your podcast audio.")
                
            except Exception as e:
                st.error(f"❌ Error creating podcast: {str(e)}")
    
    # Display generated script if available
    if st.session_state.script_generated and st.session_state.generated_script:
        with st.expander("🔍 View Generated Script"):
            for i, turn in enumerate(st.session_state.generated_script, 1):
                speaker = turn.get('speaker', 'Unknown')
                text = turn.get('text', '')
                
                if speaker.lower() == 'host':
                    st.markdown(f"**🎤 {host_name} (Host):** {text}")
                else:
                    st.markdown(f"**👥 {guest_name} (Guest):** {text}")
                
                if i < len(st.session_state.generated_script):
                    st.markdown("---")

    # Footer
    st.markdown("""
    <div style="text-align: center; color: #888; margin-top:2rem; font-size:0.95rem;">
        Podcast GPT &mdash; Powered by Streamlit, OpenAI, and ElevenLabs
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
