# ==============================================================================
# Synthesis Studio: AI Presenter & Reel Editor
# Author: [Your Name]
# Version: 2.1 (Switched to HeyGen API)
#
# This version uses the HeyGen API for avatar generation due to persistent
# issues with the D-ID API.
# ==============================================================================

import streamlit as st
import requests
import time
import os

# --- Page Config & API Keys ---
st.set_page_config(page_title="Synthesis Studio", layout="wide")

# We will now use the HeyGen API key.
HEYGEN_API_KEY = st.secrets.get("HEYGEN_API_KEY")
REPLICATE_API_TOKEN = st.secrets.get("REPLICATE_API_TOKEN") # Reserved for captioning

if REPLICATE_API_TOKEN:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# --- HeyGen API Functions (NEW) ---
HEYGEN_API_URL = "https://api.heygen.com/v2/video/generate"
HEYGEN_STATUS_URL = "https://api.heygen.com/v1/video_status.get"

# We will use a standard HeyGen avatar and voice for simplicity
AVATAR_ID = "Daisy-inskirt-20220716"
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
                "voice": {"type": "text", "text": script_text, "voice_id": VOICE_ID}
            }
        ],
        "test": True, # Use test mode to not consume credits while developing
        "aspect_ratio": "9:16"
    }
    try:
        response = requests.post(HEYGEN_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("data", {})
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating HeyGen video: {e}")
        st.error(f"Response Body: {response.text if 'response' in locals() else 'No response'}")
        return None

def get_heygen_video(video_id):
    """Checks the status of the HeyGen job and returns the video URL when ready."""
    if not HEYGEN_API_KEY:
        return None
    
    headers = {"X-Api-Key": HEYGEN_API_KEY}
    status = ""
    while status != "DONE":
        try:
            params = {"video_id": video_id}
            response = requests.get(HEYGEN_STATUS_URL, headers=headers, params=params)
            response.raise_for_status()
            result = response.json().get("data", {})
            status = result.get("status")
            if status == "FAILED":
                st.error(f"HeyGen job failed: {result.get('error')}")
                return None
            st.toast(f"Video generation status: {status}...")
            time.sleep(10)
        except requests.exceptions.RequestException as e:
            st.error(f"Error getting video status: {e}")
            return None
    
    return result.get("video_url")

# --- Streamlit UI (Mostly the same) ---
st.title("Synthesis Studio 🤖🎬")
st.write("Generate a complete Reel from just a script, powered by AI.")

st.subheader("1. Write Your Script")
script = st.text_area("Enter the text you want the AI presenter to speak:", height=150,
                      placeholder="e.g., Hello! This video was generated using the HeyGen API.")

if st.button("Generate My AI Presenter Video", type="primary"):
    if not script:
        st.warning("Please enter a script first.")
    elif not HEYGEN_API_KEY:
        st.error("HeyGen API Key is missing. Cannot generate video.")
    else:
        with st.spinner("Sending script to our AI presenter (HeyGen)..."):
            video_data = create_heygen_video(script)
        
        if video_data and video_data.get("video_id"):
            video_id = video_data["video_id"]
            st.info(f"Video generation started! Job ID: {video_id}. Please wait, this can take a few minutes.")
            with st.spinner("AI is rendering your video..."):
                video_url = get_heygen_video(video_id)
            
            if video_url:
                st.success("Your AI Presenter video is ready!")
                st.video(video_url)
            else:
                st.error("Failed to retrieve the generated video.")
        else:
            st.error("Failed to start the video generation job.")
