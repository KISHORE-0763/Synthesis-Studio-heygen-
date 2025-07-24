# ==============================================================================
# Synthesis Studio: AI Presenter & Reel Editor
# Author: [Your Name]
# Version: 3.3 (Failsafe - Fetches Avatar ID Dynamically)
#
# This version no longer uses a hardcoded avatar ID. Instead, it asks the
# HeyGen API for a list of available avatars and uses the first one.
# This makes the app resilient to changes in their public avatar list.
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

# --- NEW: Function to get a list of available avatars ---
@st.cache_data(ttl=3600) # Cache the result for 1 hour to avoid repeated API calls
def get_available_avatars(api_key):
    """Fetches the list of public avatars from HeyGen."""
    if not api_key:
        return None
    url = "https://api.heygen.com/v1/avatar.list"
    headers = {"X-Api-Key": api_key}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        avatars = response.json().get("data", {}).get("list", [])
        if avatars:
            # Return the ID of the very first avatar in the list
            return avatars[0]['avatar_id']
        else:
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Could not fetch avatar list: {e}")
        return None

def create_heygen_video(script_text, avatar_id):
    """Sends the script and a VALID avatar_id to HeyGen."""
    if not HEYGEN_API_KEY:
        st.error("HeyGen API Key not found.")
        return None
        
    url = "https://api.heygen.com/v2/video/generate"
    headers = {"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}
    payload = {
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": avatar_id},
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
                          placeholder="e.g., Hello! Let's hope this final version works!")

    if st.button("Generate My AI Presenter Video", type="primary"):
        if not script:
            st.warning("Please enter a script first.")
        else:
            with st.spinner("Finding an available AI presenter..."):
                # --- THIS IS THE NEW, DYNAMIC STEP ---
                valid_avatar_id = get_available_avatars(HEYGEN_API_KEY)

            if not valid_avatar_id:
                st.error("Could not find a valid avatar from the HeyGen API. Please try again later.")
            else:
                st.success(f"Found a valid presenter! Using avatar ID: ...{valid_avatar_id[-6:]}")
                with st.spinner("Sending script to the AI presenter..."):
                    video_data = create_heygen_video(script, valid_avatar_id)
                
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
