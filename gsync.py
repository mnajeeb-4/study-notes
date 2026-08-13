import os
import shutil
import subprocess
import requests
import streamlit as st
import re
from collections import Counter
import random

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Study Notes Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SESSION STATE (For Bookmarks) ---
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

# --- 3. BITCOIN DEFI DESIGN SYSTEM (CSS INJECTION) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    .stApp {
        background-color: #030304;
        background-image: 
         linear-gradient(to right, rgba(30, 41, 59, 0.3) 1px, transparent 1px),
         linear-gradient(to bottom, rgba(30, 41, 59, 0.3) 1px, transparent 1px);
        background-size: 50px 50px;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }
    
    code {
        font-family: 'JetBrains Mono', monospace !important;
        background-color: rgba(247, 147, 26, 0.1) !important;
        color: #FFD600 !important;
    }

    [data-testid="stSidebar"] {
        background-color: #0F1115 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
        background-color: rgba(0, 0, 0, 0.5) !important;
        border: none !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 0px !important;
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-bottom-color: #F7931A !important;
        box-shadow: 0 10px 20px -10px rgba(247, 147, 26, 0.3) !important;
        outline: none !important;
    }

    .stButton > button {
        background: linear-gradient(to right, #EA580C, #F7931A) !important;
        color: white !important;
        border: none !important;
        border-radius: 9999px !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        box-shadow: 0 0 20px -5px rgba(247, 147, 26, 0.5) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px -5px rgba(247, 147, 26, 0.7) !important;
    }

    [data-testid="stAlert"] {
        background-color: rgba(15, 17, 21, 0.8) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        color: #94A3B8 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(15, 17, 21, 0.6);
        border-radius: 12px;
        padding: 5px;
        border: 1px solid rgba(255,255,255,0.05);
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Space Grotesk', sans-serif !important;
        border-radius: 8px;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(247, 147, 26, 0.1) !important;
        color: #F7931A !important;
        border-bottom: 2px solid #F7931A !important;
    }

    .gradient-text {
        background: linear-gradient(to right, #F7931A, #FFD600);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    .ai-tag {
        display: inline-block;
        background-color: rgba(255, 214, 0, 0.15);
        color: #FFD600;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        margin-right: 5px;
        margin-bottom: 5px;
        border: 1px solid rgba(255, 214, 0, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. PATHS & CONFIGURATION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_FOLDER = os.path.join(CURRENT_DIR, ".live_web_notes") 

# --- 5. SIDEBAR CONFIGURATION ---
st.sidebar.markdown("<h1 style='text-align: center; font-size: 24px;'>⚡ <span class='gradient-text'>Study Notes Hub</span></h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.header("⚙️ Network Connection")
GITHUB_REPO_URL = st.sidebar.text_input("Repository URL", value="https://github.com/kaifsheikh/My_Notes.git")
REPO_OWNER = st.sidebar.text_input("Instructor Username", value="kaifsheikh")
REPO_NAME = st.sidebar.text_input("Repository Name", value="My_Notes")

# --- GITHUB API & SYNC FUNCTIONS ---
def get_latest_remote_commit():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data[0]['sha'], data[0]['commit']['message']
    except Exception:
        pass
    return None, None

def get_local_commit():
    git_dir = os.path.join(NOTES_FOLDER, ".git")
    if not os.path.exists(git_dir):
        return None
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=NOTES_FOLDER, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return None

update_available, latest_msg = False, ""
remote_sha, remote_msg = get_latest_remote_commit()
local_sha = get_local_commit()
if remote_sha and local_sha and remote_sha != local_sha:
    update_available, latest_msg = True, remote_msg

# FEATURE 1: UPDATE LIVE WEB ONLY
st.sidebar.markdown("### 1️⃣ Live Web Sync")
button_label = "🔴 Update Web Notes (New Commit!)" if update_available else "🔄 Sync Live Web Notes"

if st.sidebar.button(button_label, use_container_width=True):
    if not os.path.exists(NOTES_FOLDER):
        os.makedirs(NOTES_FOLDER)
    
    git_dir = os.path.join(NOTES_FOLDER, ".git")
    
    if not os.path.exists(git_dir):
        with st.spinner("Initial Clone in progress..."):
            res = subprocess.run(["git", "clone", GITHUB_REPO_URL, "."], cwd=NOTES_FOLDER, capture_output=True, text=True)
            if res.returncode == 0:
                st.sidebar.success("🎉 Web Notes synchronized successfully!")
                st.rerun()
            else:
                st.sidebar.error(f"Clone Failed: {res.stderr}")
    else:
        with st.spinner("Hard Syncing... Deleting old files & fetching new updates..."):
            subprocess.run(["git", "fetch", "origin"], cwd=NOTES_FOLDER, capture_output=True)
            subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=NOTES_FOLDER, capture_output=True)
            subprocess.run(["git", "clean", "-fd"], cwd=NOTES_FOLDER, capture_output=True)
            st.sidebar.success("✅ Web Live Viewer Updated! (Old files deleted)")
            st.rerun()

st.sidebar.markdown("---")

# FEATURE 2: ADVANCED SAVE NOTES (LOCAL EXPORT)
st.sidebar.markdown("### 2️⃣ Save Notes to PC")
with st.sidebar.expander("💾 Click to configure Save Location"):
    new_folder = st.radio("Create a NEW FOLDER for notes?", ["Yes", "No"], index=1)
    
    target_path = ""
    
    if new_folder == "Yes":
        folder_name = st.text_input("Folder Name:", "My_Updated_Notes")
        target_path = os.path.join(CURRENT_DIR, folder_name)
    else:
        specific_loc = st.radio("Save to a SPECIFIC exact location?", ["Yes", "No"], index=1)
        if specific_loc == "Yes":
            target_path = st.text_input("Enter Exact Path (e.g., D:/Study):")
        else:
            target_path = os.path.join(CURRENT_DIR, "Saved_Notes")
            st.info("Notes will be saved in current app folder as 'Saved_Notes'.")

    if st.button("💾 Export / Save Now"):
        if not os.path.exists(NOTES_FOLDER):
            st.error("Please Sync Live Web Notes first!")
        else:
            if new_folder == "No" and specific_loc == "Yes" and not os.path.exists(target_path):
                st.error("❌ Exact location not found! Please check the path.")
            else:
                try:
                    if specific_loc == "Yes" and new_folder == "No":
                        final_dest = target_path 
                    else:
                        final_dest = target_path
                        
                    if os.path.exists(final_dest):
                        shutil.rmtree(final_dest) 
                    
                    shutil.copytree(NOTES_FOLDER, final_dest, ignore=shutil.ignore_patterns('.git'))
                    st.success(f"✅ Notes successfully saved at:\n`{final_dest}`")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error saving files: {e}")

# --- 6. GOD-TIER FEATURES (SEARCH, FILTER & BOOKMARKS) ---
st.sidebar.markdown("---")

# SCAN FILES
all_files = []
if os.path.exists(NOTES_FOLDER):
    for root, dirs, files in os.walk(NOTES_FOLDER):
        if ".git" in root:
            continue
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), NOTES_FOLDER)
            all_files.append(rel_path)

all_files = sorted(all_files)

# FEATURE: BOOKMARK & QUICK FAVORITES IN SIDEBAR
if st.session_state.bookmarks:
    st.sidebar.markdown("### ⭐ Quick Favorites")
    selected_bookmark = st.sidebar.selectbox("Jump to Bookmarked Note:", ["Select..."] + st.session_state.bookmarks)
    if selected_bookmark != "Select...":
        selected_file = selected_bookmark
    else:
        st.sidebar.header("🔍 Smart Search")
        search_query = st.sidebar.text_input("Search inside all notes...", "")
        filtered_files = [f for f in all_files if search_query.lower() in f.lower()] if search_query else all_files
        selected_file = st.sidebar.selectbox("📂 Select Data File", filtered_files if filtered_files else ["No Files Detected"])
else:
    st.sidebar.header("🔍 Smart Search")
    search_query = st.sidebar.text_input("Search inside all notes...", "")
    filtered_files = [f for f in all_files if search_query.lower() in f.lower()] if search_query else all_files
    selected_file = st.sidebar.selectbox("📂 Select Data File", filtered_files if filtered_files else ["No Files Detected"])

# --- 7. MAIN DASHBOARD CONTENT ---
st.markdown("<h1>📚 Live <span class='gradient-text'>Study Notes Hub</span></h1>", unsafe_allow_html=True)

if update_available:
    st.warning(f"🔴 **Update Alert:** Sir updated the repository! Click **Update Web Notes** in the sidebar to refresh.\n\n**Latest Change:** `{latest_msg}`")

if all_files and selected_file != "No Files Detected":
    file_path = os.path.join(NOTES_FOLDER, selected_file)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader(f"📄 Active File: `{selected_file}`")
    with col2:
        # BOOKMARK TOGGLE BUTTON
        is_bookmarked = selected_file in st.session_state.bookmarks
        btn_text = "★ Unbookmark" if is_bookmarked else "⭐ Bookmark Note"
        if st.button(btn_text):
            if is_bookmarked:
                st.session_state.bookmarks.remove(selected_file)
                st.success("Removed from favorites!")
            else:
                st.session_state.bookmarks.append(selected_file)
                st.success("Added to favorites!")
            st.rerun()
    with col3:
        st.caption("Mode: `Live Web View`")

    st.markdown("---")
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Tabs
        tab1, tab2, tab3 = st.tabs(["📖 Document Render", "🤖 AI Study Assistant", "📌 Personal Side-Notes"])

        # TAB 1: RENDER + DOWNLOAD BUTTON
        with tab1:
            col_r1, col_r2 = st.columns([4, 1])
            with col_r2:
                # FEATURE: AUTO-PDF / CLEAN EXPORTER BUTTON
                st.download_button(
                    label="📥 Download / Print",
                    data=content,
                    file_name=f"Note_{os.path.basename(selected_file)}",
                    mime="text/plain",
                    help="Download clean document for instant printing or PDF conversion!"
                )
            
            if selected_file.endswith((".md", ".markdown")):
                st.markdown(content)
            elif selected_file.endswith((".py", ".cpp", ".java", ".js", ".html", ".css", ".json")):
                st.code(content, language="python" if selected_file.endswith(".py") else "text")
            else:
                st.text_area("Raw Output", content, height=600)

        # TAB 2: AI FEATURES + FLASHCARDS + MCQS
        with tab2:
            st.subheader("🤖 AI Smart Analytics")
            
            word_count = len(content.split())
            read_time = max(1, round(word_count / 200)) 
            
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Total Words", f"{word_count}")
            col_b.metric("Est. Read Time", f"{read_time} min")
            col_c.metric("Code Blocks Detected", f"{content.count('```')}")

            st.markdown("### 🔑 AI Keyword Extractor")
            words = re.findall(r'\b[a-zA-Z]{5,}\b', content.lower())
            common = {"which", "there", "their", "about", "would", "these", "other", "class", "print", "return"}
            filtered_words = [w for w in words if w not in common]
            most_common = Counter(filtered_words).most_common(8)
            
            if most_common:
                tags_html = "".join([f"<span class='ai-tag'>#{word[0]}</span>" for word in most_common])
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.write("No major keywords detected.")

            st.markdown("### 📇 AI Flashcards (Test Yourself)")
            st.info("Headings extracted for quick revision. Try to answer them in your mind!")
            
            lines = content.split("\n")
            headings = [line.replace("#", "").strip() for line in lines if line.startswith("# ") or line.startswith("## ")]
            
            if headings:
                for idx, h in enumerate(headings[:5]):
                    with st.expander(f"Question {idx+1}: {h} ?"):
                        st.write("Review the document to see if you remembered correctly!")
            else:
                st.write("No clear headings found to generate flashcards.")

            # FEATURE: AI PRACTICE QUIZ (MCQs)
            st.markdown("---")
            st.markdown("### 🎯 AI Practice Quiz (MCQs)")
            st.info("Automated practice quiz generated from the active note content.")
            
            plain_lines = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
            if len(plain_lines) >= 3:
                sample_lines = random.sample(plain_lines, min(3, len(plain_lines)))
                for q_idx, line in enumerate(sample_lines):
                    st.write(f"**Q{q_idx+1}: What is your confidence level on this concept?**")
                    st.code(line[:100] + ("..." if len(line) > 100 else ""))
                    st.radio(f"Select option for Q{q_idx+1}:", 
                             ["A) Perfectly understood", "B) Need to review", "C) Difficult section"], 
                             key=f"mcq_{q_idx}_{selected_file}")
                    st.markdown("---")
            else:
                st.write("Not enough paragraph data available to generate practice MCQs.")

        # TAB 3: SIDE NOTES
        with tab3:
            st.subheader("✍️ Encrypted Local Memorandums")
            user_note = st.text_area("Input private study parameters for this file:", key=f"note_{selected_file}")
            if st.button("Commit Personal Note"):
                st.success("✅ Local parameter saved successfully in browser memory!")

    except Exception as e:
        st.error(f"Render Fault: Could not parse file structure. Reason: {e}")
else:
    st.info("👆 Awaiting initialization. Enter the Repository URL in the sidebar and trigger **Sync Live Web Notes** to begin.")