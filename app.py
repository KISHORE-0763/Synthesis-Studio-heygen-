# ==============================================================================
# Synthesis Studio: AI Presenter & Reel Editor
# Author: [Your Name]
# Version: 3.2 (Final - Powered by HeyGen)
#
# This is the definitive, corrected version.
# - Uses the correct payload structure ('input_text').
# - Uses a valid and stable public avatar ID.
# - Includes robust error handling.
# ==============================================================================

# --- Core Libraries ---
import streamlit as st
import requests
import time
import os

# ==============================================================================
# 1. PAGE CONFIGURATION & API KEY MANAGEMENT
# ==============================================================================

st.set_page_config(
    page_title="Synthesis Studio",
    page_icon="🤖",
    layout="wide"
)

# Securely load API keys from Streamlit's secrets manager
HEYGEN_API_KEY = st.secrets.get("HEYGEN_API_KEY")
REPLICATE_API_TOKEN = st.secrets.get("REPLICATE_API_TOKEN") # Reserved for future captioning feature

# ==============================================================================
# 2. HELPER FUNCTIONS (The "Backend" Logic for HeyGen)
# ==============================================================================

HEYGEN_API_URL = "https://api.heygen.com/v2/video/generate"
HEYGEN_STATUS_URL = "https://api.heygen.com/v1/video_status.get"

# Using a verified, public, and stable HeyGen avatar and voice for reliability.
# Avatar: "Amelia"
AVATAR_ID = "863b35317f22457c83526a099482f51f" 
# Voice: A standard, high-quality female voice
VOICE_ID = "1bd001e7e50f421d891986aad515841e"

def create_heygen_video(script_text):
    """Sends the script to HeyGen to start the video generation job."""
    if not HEYGEN_API_KEY:
        st.error("HeyGen API Key not found. Please add it to your Streamlit secrets.")
        return None

    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "video_inputs": [
            {
                "character": {"type": "avatar", "avatar_id": AVATAR_ID},
                "voice": {"type": "text", "input_text": script_text, "voice_id": VOICE_ID}
            }
        ],
        "test": True,  # Use test mode to not consume credits while developing!
        "aspect_ratio": "9:16"
    }
    try:
        response = requests.post(HEYGEN_API_URL, headers=headers, json=payload)
        response.raise_for_status() # This will raise an error for 4xx or 5xx responses
        return response.json().get("data", {})
    except requests.exceptions.RequestException as e:
        # Provide detailed error feedback to the user
        st.error(f"Error communicating with HeyGen API: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            st.error(f"API Response Body: {response.text}")
        return None

def get_heygen_video_status(video_id):
    """Checks the status of the HeyGen job and returns the video URL when ready."""
    if not HEYGEN_API_KEY:
        return None
    
    headers = {"X-Api-Key": HEYGEN_API_KEY}
    status = ""
    # HeyGen's statuses are: PENDING, PROCESSING, DONE, FAILED
    while status not in ["DONE", "FAILED"]:
        try:
            params = {"video_id": video_id}
            response = requests.get(HEYGEN_STATUS_URL, headers=headers, params=params)
            response.raise_for_status()
            result = response.json().get("data", {})
            status = result.get("status")
            if status == "FAILED":
                st.error(f"HeyGen video generation failed. Reason: {result.get('error', 'Unknown error')}")
                return None
            st.toast(f"Video generation status: {status}...")
            time.sleep(10) # Wait 10 seconds before checking again
        except requests.exceptions.RequestException as e:
            st.error(f"Error checking video status: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                st.error(f"API Response Body: {response.text}")
            return None
    
    return result.get("video_url")

# ==============================================================================
# 3. STREAMLIT UI (The Frontend)
# ==============================================================================

st.title("Synthesis Studio 🤖🎬")
st.write("Generate a complete Reel from just a script, powered by AI.")

st.info("Powered by HeyGen API. You can generate unlimited watermarked test videos for free.")

st.subheader("1. Write Your Script")
script = st.text_area("Enter the text you want the AI presenter to speak:", height=150,
                      placeholder="e.g., Hello! This is the final test of the HeyGen API. Let's create a video!")

if st.button("Generate My AI Presenter Video", type="primary"):
    if not script:
        st.warning("Please enter a script first.")
    elif not HEYGEN_API_KEY:
        st.error("HeyGen API Key is missing. Cannot generate video.")
    else:
        with st.spinner("Contacting HeyGen... Sending your script..."):
            video_data = create_heygen_video(script)
        
        if video_data and video_data.get("video_id"):
            video_id = video_data["video_id"]
            st.info(f"Success! HeyGen has started your video job. Job ID: {video_id}. Please wait while it renders.")
            with st.spinner("AI is rendering your video... This can take a few minutes."):
                video_url = get_heygen_video_status(video_id)
            
            if video_url:
                st.success("Your AI Presenter video is ready!")
                st.video(video_url)
            else:
                st.error("Could not retrieve the final video. Please check the logs.")
        else:
            st.error("Failed to start the video generation job. Please check the error messages above.")
