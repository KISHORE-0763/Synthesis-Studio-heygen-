# ==============================================================================
# Synthesis Studio: AI Presenter & Reel Editor
# Author: [Your Name]
# Version: 4.0 (Definitive Fix - Stable Photo URL)
#
# This version ABANDONS the unreliable 'avatar_id' system and instead uses a
# direct, stable 'photo_url' to create the avatar. This is the most robust
# method and removes the dependency on HeyGen's changing avatar library.
# ==============================================================================

import streamlit as st
import requests
import time
import os

# --- Page Config & API Keys ---
st.set_page_config(page_title="Synthesis Studio", layout="wide")
HEYGEN_API_KEY = st.secrets.get("HEYGEN_API_KEY")

# ==============================================================================
# HELPER FUNCTIONS (Corrected for HeyGen with Photo URL)
# ==============================================================================

HEYGEN_API_URL = "https://api.heygen.com/v2/video/generate"
HEYGEN_STATUS_URL = "https://api.heygen.com/v1/video_status.get"

# --- USING A STABLE, PUBLIC IMAGE URL INSTEAD OF AN AVATAR_ID ---
# This is a high-quality, AI-generated, front-facing portrait.
PHOTO_URL = "https://i.imgur.com/E3OU9S8.png"

# We still need to specify a voice.
VOICE_ID = "1bd001e7e50f421d891986aad515841e"

def create_heygen_video(script_text):
    """Sends the script and a photo_url to HeyGen to start the job."""
    if not HEYGEN_API_KEY:
        st.error("HeyGen API Key not found.")
        return None
        
    url = "https://api.heygen.com/v2/video/generate"
    headers = {"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}
    
    # --- THIS PAYLOAD USES THE STABLE 'photo' CHARACTER TYPE ---
    payload = {
        "video_inputs": [{
            "character": {"type": "photo", "photo_url": PHOTO_URL},
            "voice": {"type": "text", "input_text": script_text, "voice_id": VOICE_ID}
        }],
        "test": True,
        "aspect_ratio": "9:16"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("data", {})
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating HeyGen video: {e}")
        st.error(f"API Response Body: {response.text if 'response' in locals() else 'No response'}")
        return None

def get_heygen_video_status(video_id):
    """Checks the status of the HeyGen job."""
    if not HEYGEN_API_KEY:
        return None
    url = "https://api.heygen.com/v1/video_status.get"
    headers = {"X-Api-Key": HEYGEN_API_KEY}
    status = ""
    while status not in ["DONE", "FAILED"]:
        try:
            params = {"video_id": video_id}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json().get("data", {})
            status = result.get("status")
            if status == "FAILED":
                st.error(f"HeyGen job failed: {result.get('error', 'Unknown error')}")
                return None
            st.toast(f"Video generation status: {status}...")
            time.sleep(10)
        except requests.exceptions.RequestException as e:
            st.error(f"Error checking video status: {e}")
            return None
    return result.get("video_url")

# ==============================================================================
# STREAMLIT UI (The Frontend)
# ==============================================================================

st.title("Synthesis Studio 🤖🎬")
st.write("Generate a complete Reel from just a script, powered by AI.")

if not HEYGEN_API_KEY:
    st.error("HeyGen API Key is missing from secrets. The app cannot function.")
else:
    st.info("Powered by HeyGen API. You can generate unlimited watermarked test videos for free.")
    
    st.subheader("1. Write Your Script")
    script = st.text_area("Enter the text you want the AI presenter to speak:", height=150,
                          placeholder="This version uses a stable photo URL. This must be the one that works.")

    if st.button("Generate My AI Presenter Video", type="primary"):
        if not script:
            st.warning("Please enter a script first.")
        else:
            with st.spinner("Sending script to the AI presenter..."):
                video_data = create_heygen_video(script)
            
            if video_data and video_data.get("video_id"):
                video_id = video_data["video_id"]
                st.info(f"Video generation started! Job ID: {video_id}. Please wait.")
                with st.spinner("AI is rendering your video..."):
                    video_url = get_heygen_video_status(video_id)
                
                if video_url:
                    st.success("Your AI Presenter video is ready!")
                    st.video(video_url)
                else:
                    st.error("Could not retrieve the final video.")
            else:
                st.error("Failed to start the video generation job.")
