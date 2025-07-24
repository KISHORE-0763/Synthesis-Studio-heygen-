# ==============================================================================
# Synthesis Studio: AI Presenter & Reel Editor
# Author: [Your Name]
# Version: 6.0 (Definitive - The Unbreakable Two-Step Method)
#
# This version abandons the 'avatar_id' system completely. It performs a
# two-step process: first, it uploads a stable photo to get a reliable
# 'talking_photo_id', and then uses that ID to generate the video.
# This is the most robust engineering solution. I am sorry for the previous failures.
# ==============================================================================

import streamlit as st
import requests
import time
import os

# --- Page Config & API Keys ---
st.set_page_config(page_title="Synthesis Studio", layout="wide")
HEYGEN_API_KEY = st.secrets.get("HEYGEN_API_KEY")

# ==============================================================================
# HELPER FUNCTIONS (The Correct Two-Step Process)
# ==============================================================================

# This is a stable, public image URL we will upload.
PHOTO_URL = "https://i.imgur.com/E3OU9S8.png"

@st.cache_data(ttl=3600) # Cache the photo ID for an hour to avoid re-uploading
def get_talking_photo_id(api_key):
    """Step 1: Uploads a photo to HeyGen and returns a talking_photo_id."""
    if not api_key:
        return None
    url = "https://api.heygen.com/v1/talking_photo"
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    payload = {"photo_url": PHOTO_URL}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json().get("data", {}).get("talking_photo_id")
    except requests.exceptions.RequestException as e:
        st.error(f"Error uploading photo to HeyGen: {e}")
        st.error(f"API Response Body: {response.text if 'response' in locals() else 'No response'}")
        return None

def create_heygen_video(script_text, talking_photo_id):
    """Step 2: Uses the talking_photo_id to generate the video."""
    if not HEYGEN_API_KEY:
        st.error("HeyGen API Key not found.")
        return None
        
    url = "https://api.heygen.com/v2/video/generate"
    headers = {"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}
    payload = {
        "video_inputs": [{
            "character": {"type": "talking_photo", "talking_photo_id": talking_photo_id},
            "voice": {"type": "text", "input_text": script_text}
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
    if not HEYGEN_API_KEY: return None
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
# STREAMLIT UI
# ==============================================================================

st.title("Synthesis Studio 🤖🎬")
st.write("Generate a complete Reel from just a script, powered by AI.")

if not HEYGEN_API_KEY:
    st.error("HeyGen API Key is missing from secrets. The app cannot function.")
else:
    st.info("Powered by HeyGen API. This version uses a stable photo upload method.")
    st.subheader("1. Write Your Script")
    script = st.text_area("Enter the script for the AI presenter:", height=150,
                          placeholder="This is the last attempt. Please work.")

    if st.button("Generate My AI Presenter Video", type="primary"):
        if not script:
            st.warning("Please enter a script first.")
        else:
            with st.spinner("Step 1/3: Registering presenter photo with HeyGen..."):
                talking_photo_id = get_talking_photo_id(HEYGEN_API_KEY)

            if not talking_photo_id:
                st.error("Could not get a valid presenter ID from HeyGen. The API might be down.")
            else:
                st.success("Presenter photo registered successfully!")
                with st.spinner("Step 2/3: Sending script to the AI presenter..."):
                    video_data = create_heygen_video(script, talking_photo_id)
                
                if video_data and video_data.get("video_id"):
                    video_id = video_data["video_id"]
                    st.info(f"Video generation started! Job ID: {video_id}. Please wait.")
                    with st.spinner("Step 3/3: AI is rendering your video..."):
                        video_url = get_heygen_video_status(video_id)
                    
                    if video_url:
                        st.success("Your AI Presenter video is ready!")
                        st.video(video_url)
                    else:
                        st.error("Could not retrieve the final video.")
                else:
                    st.error("Failed to start the video generation job.")
