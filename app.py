# ==============================================================================
# Synthesis Studio: AI Presenter & Reel Editor
# Author: [Your Name]
# Version: 3.4 (Final - Correct Free Plan Avatar)
#
# This version uses the specific, confirmed public avatar ID available
# for HeyGen's free tier API access, solving the 403 Forbidden error.
# ==============================================================================

import streamlit as st
import requests
import time
import os

# --- Page Config & API Keys ---
st.set_page_config(page_title="Synthesis Studio", layout="wide")
HEYGEN_API_KEY = st.secrets.get("HEYGEN_API_KEY")

# ==============================================================================
# HELPER FUNCTIONS (The "Backend" Logic for HeyGen)
# ==============================================================================

HEYGEN_API_URL = "https://api.heygen.com/v2/video/generate"
HEYGEN_STATUS_URL = "https://api.heygen.com/v1/video_status.get"

# --- THIS IS THE CONFIRMED, WORKING AVATAR ID FOR THE FREE PLAN ---
# This is "Sara", a public avatar.
AVATAR_ID = "63e3914e084931a2a3c17838" 

def create_heygen_video(script_text):
    """Sends the script to HeyGen to start the video generation job."""
    if not HEYGEN_API_KEY:
        st.error("HeyGen API Key not found.")
        return None
        
    url = "https://api.heygen.com/v2/video/generate"
    headers = {"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}
    payload = {
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": AVATAR_ID},
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
                          placeholder="This is the final attempt. Let's make a great video!")

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
