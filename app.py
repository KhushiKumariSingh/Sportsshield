import streamlit as st
import sqlite3
from PIL import Image
import imagehash
import cv2
import tempfile
import numpy as np

# ---------------- DATABASE SETUP ----------------
conn = sqlite3.connect('sportshield.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS fingerprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT,
    hash TEXT
)
''')
conn.commit()

# ---------------- IMAGE HASH ----------------
def generate_image_hash(file):
    img = Image.open(file)
    return str(imagehash.phash(img))

# ---------------- VIDEO PROCESSING ----------------
def extract_frames(video_file, interval=1):
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(video_file.read())

    cap = cv2.VideoCapture(temp_file.name)

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval) if fps > 0 else 30

    frames = []
    count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if count % frame_interval == 0:
            frames.append(frame)

        count += 1

    cap.release()
    return frames

def generate_video_hashes(video_file):
    frames = extract_frames(video_file)
    hashes = []

    for frame in frames:
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        hashes.append(str(imagehash.phash(img)))

    return hashes

# ---------------- DATABASE SAVE ----------------
def save_hash(file_name, hash_value):
    c.execute(
        "INSERT INTO fingerprints (file_name, hash) VALUES (?, ?)",
        (file_name, hash_value)
    )
    conn.commit()

def save_video_hashes(file_name, hash_list):
    for h in hash_list:
        save_hash(file_name, h)

# ---------------- MATCHING ----------------
from imagehash import hex_to_hash

def compare_hash(h1, h2):
    return hex_to_hash(h1) - hex_to_hash(h2)

def get_all_hashes():
    c.execute("SELECT file_name, hash FROM fingerprints")
    return c.fetchall()

# ---------------- RISK ----------------
def risk_score(similarity, frequency):
    score = 0

    if similarity < 5:
        score += 50
    elif similarity < 10:
        score += 30

    if frequency > 2:
        score += 30

    return score

def recommend_action(score):
    if score >= 80:
        return "🚨 Takedown"
    elif score >= 50:
        return "⚠ Warning"
    else:
        return "👁 Monitor"

# ---------------- DEMO CRAWLER ----------------
def demo_crawler(uploaded_hashes):
    return [
        {"url": "piratedsite.com/video1", "hash": uploaded_hashes[0]},
        {"url": "unknownsite.com/media2", "hash": "aaab23cd98ef5678"},
    ]

# ---------------- UI ----------------
st.title("🏆 SportShield Dashboard (Image + Video)")

st.sidebar.header("Upload Media")
uploaded_file = st.sidebar.file_uploader(
    "Upload Image or Video",
    type=["jpg", "png", "jpeg", "mp4", "avi", "mov"]
)

if uploaded_file:
    file_type = uploaded_file.type

    # ---------------- IMAGE ----------------
    if "image" in file_type:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

        file_hash = generate_image_hash(uploaded_file)
        save_hash(uploaded_file.name, file_hash)

        st.success("✅ Image Fingerprint Stored")
        uploaded_hashes = [file_hash]

    # ---------------- VIDEO ----------------
    elif "video" in file_type:
        st.video(uploaded_file)

        st.write("⏳ Processing video...")

        video_hashes = generate_video_hashes(uploaded_file)
        save_video_hashes(uploaded_file.name, video_hashes)

        st.success(f"✅ Video processed ({len(video_hashes)} frames)")
        uploaded_hashes = video_hashes

    # ---------------- SCAN ----------------
    st.header("🔍 Scanning for Violations...")
    crawled_data = demo_crawler(uploaded_hashes)

    db_hashes = get_all_hashes()

    found = False

    for item in crawled_data:
        for up_hash in uploaded_hashes:
            similarity = compare_hash(up_hash, item["hash"])

            if similarity < 10:
                found = True

                score = risk_score(similarity, frequency=3)
                action = recommend_action(score)

                st.subheader(f"⚠ Match Found: {item['url']}")

                similarity_percent = max(0, 100 - similarity * 10)

                st.write(f"Similarity: {similarity_percent}%")
                st.write(f"Similarity Score: {similarity}")
                st.write(f"Risk Score: {score}")
                st.write(f"Recommended Action: {action}")

                # Risk UI
                if score >= 80:
                    st.error("🚨 High Risk Detected")

                    if st.button("🚨 Execute Takedown"):
                        st.success("Takedown request sent!")

                elif score >= 50:
                    st.warning("⚠ Medium Risk")
                else:
                    st.info("👁 Low Risk")

                break

    if not found:
        st.success("✅ No Violations Detected")

        # redeploy trigger