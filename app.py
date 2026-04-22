import streamlit as st
import sqlite3
from PIL import Image
import imagehash

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

# ---------------- FINGERPRINT ----------------
def generate_image_hash(file):
    img = Image.open(file)
    return str(imagehash.phash(img))

def save_hash(file_name, hash_value):
    c.execute("INSERT INTO fingerprints (file_name, hash) VALUES (?, ?)", (file_name, hash_value))
    conn.commit()

# ---------------- MATCHING ----------------
from imagehash import hex_to_hash

def compare_hash(h1, h2):
    return hex_to_hash(h1) - hex_to_hash(h2)

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
def demo_crawler(uploaded_hash):
    return [
        {"url": "piratedsite.com/video1", "hash": uploaded_hash},  # forced match
        {"url": "unknownsite.com/image2", "hash": "aaab23cd98ef5678"},
    ]

# ---------------- UI ----------------
st.title("🏆 SportShield Dashboard")

st.sidebar.header("Upload Official Media")
uploaded_file = st.sidebar.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Media", use_column_width=True)

    # Generate hash
    file_hash = generate_image_hash(uploaded_file)
    save_hash(uploaded_file.name, file_hash)

    st.success("✅ Fingerprint Generated & Stored")
    st.write(f"Hash: {file_hash}")

    # Scan
    st.header("🔍 Scanning Web for Violations...")
    crawled_data = demo_crawler(file_hash)

    found = False

    for item in crawled_data:
        similarity = compare_hash(file_hash, item["hash"])

        if similarity < 10:
            found = True
            score = risk_score(similarity, frequency=3)
            action = recommend_action(score)

            st.subheader(f"⚠ Match Found: {item['url']}")

            # Similarity %
            similarity_percent = max(0, 100 - similarity * 10)
            st.write(f"Similarity: {similarity_percent}%")

            st.write(f"Similarity Score: {similarity}")
            st.write(f"Risk Score: {score}")
            st.write(f"Recommended Action: {action}")

            # Risk level UI
            if score >= 80:
                st.error("🚨 High Risk Detected")
                
                # 🔥 NEW: TAKEDOWN BUTTON
                if st.button("🚨 Execute Takedown"):
                    st.success("Takedown request sent successfully!")

            elif score >= 50:
                st.warning("⚠ Medium Risk")
            else:
                st.info("👁 Low Risk")

    if not found:
        st.success("✅ No Violations Detected")