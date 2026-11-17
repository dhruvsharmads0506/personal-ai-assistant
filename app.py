import os
import sqlite3
from datetime import datetime
from google import genai
from google.genai import types
import tempfile

import requests
import streamlit as st
from pypdf import PdfReader

st.set_page_config(
    page_title="Personal AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]
DB_PATH = "assistant.db"

# ChatGPT-inspired dark interface
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: #212121; color: #ececec; }
[data-testid="stSidebar"] { background: #171717; border-right: 1px solid #303030; }
[data-testid="stHeader"] { background: #212121; }
.block-container { max-width: 900px; padding-top: 2rem; padding-bottom: 7rem; }
[data-testid="stChatMessage"] { background: transparent; border: none; padding: 1rem 0; }
[data-testid="stChatInput"] { background: #2f2f2f; border: 1px solid #454545; border-radius: 24px; }
[data-testid="stChatInput"] textarea { color: #f5f5f5; }
.brand { font-size: 22px; font-weight: 700; padding: 4px 0 18px; }
.welcome { text-align: center; padding-top: 14vh; padding-bottom: 2rem; }
.welcome h1 { font-size: 2.2rem; font-weight: 650; color: #f5f5f5; }
.welcome p { color: #a6a6a6; font-size: 1rem; }
.sidebar-note { color: #929292; font-size: 12px; padding-top: 16px; }
div.stButton > button { border-radius: 12px; min-height: 40px; border-color: #404040; }
</style>
""", unsafe_allow_html=True)


# -------------------- SQLite chat history --------------------
def db_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(chat_id) REFERENCES chats(id)
            )
        """)


def create_chat():
    with db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO chats (title, created_at) VALUES (?, ?)",
            ("New chat", datetime.now().isoformat()),
        )
        return cursor.lastrowid


def get_chats():
    with db_connection() as conn:
        return conn.execute(
            "SELECT id, title FROM chats ORDER BY id DESC"
        ).fetchall()


def rename_chat(chat_id, title):
    with db_connection() as conn:
        conn.execute("UPDATE chats SET title=? WHERE id=?", (title, chat_id))


def delete_chat(chat_id):
    with db_connection() as conn:
        conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        conn.execute("DELETE FROM chats WHERE id=?", (chat_id,))


def save_message(chat_id, role, content):
    with db_connection() as conn:
        conn.execute(
            """INSERT INTO messages (chat_id, role, content, created_at)
               VALUES (?, ?, ?, ?)""",
            (chat_id, role, content, datetime.now().isoformat()),
        )


def get_messages(chat_id):
    with db_connection() as conn:
        return conn.execute(
            """SELECT role, content, created_at FROM messages
               WHERE chat_id=? ORDER BY id""",
            (chat_id,),
        ).fetchall()


initialize_database()

if "active_chat_id" not in st.session_state:
    chats_at_start = get_chats()
    st.session_state.active_chat_id = (
        chats_at_start[0][0] if chats_at_start else create_chat()
    )

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# -------------------- Attachments and n8n --------------------
def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    parts = []
    for page_no, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(f"[Page {page_no}]\n{page_text}")
    return "\n\n".join(parts)




def transcribe_audio(audio_file):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            api_key = None

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing.")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(api_version="v1beta")
    )

    suffix = os.path.splitext(
        getattr(audio_file, "name", "recording.wav")
    )[1] or ".wav"

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as temp:
            temp.write(audio_file.getvalue())
            temp_path = temp.name

        uploaded_file = client.files.upload(file=temp_path)

        response = client.interactions.create(
            model="gemini-3.5-transcribe",
            api_version="v1beta",
            input=[
                {
                    "type": "audio",
                    "uri": uploaded_file.uri,
                    "mime_type": uploaded_file.mime_type
                }
            ]
        )

        return response.output_text

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)




def call_n8n(user_text, pdf_context=None):
    message = user_text.strip()
    if pdf_context:
        message = (
            "The user attached a PDF. Use the extracted document text below "
            "as source material. Do not invent details that are not present.\n\n"
            f"PDF CONTENT:\n{pdf_context[:30000]}\n\n"
            f"USER QUESTION:\n{user_text}"
        )

    response = requests.post(
        WEBHOOK_URL,
        json={"message": message},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list):
        data = data[0] if data else {}

    if isinstance(data, dict):
        answer = data.get("output") or data.get("text") or data.get("response")
        if isinstance(answer, dict):
            answer = answer.get("output") or str(answer)
        return str(answer) if answer is not None else str(data)

    return str(data)


# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown('<div class="brand">🤖 Personal AI</div>', unsafe_allow_html=True)

    if st.button("＋  New chat", use_container_width=True, type="primary"):
        st.session_state.active_chat_id = create_chat()
        st.rerun()

    st.markdown("##### Your chats")
    chats = get_chats()
    chat_ids = [row[0] for row in chats]

    if st.session_state.active_chat_id not in chat_ids:
        st.session_state.active_chat_id = (
            chat_ids[0] if chat_ids else create_chat()
        )
        st.rerun()

    if chats:
        selected_id = st.selectbox(
            "Chat history",
            options=chat_ids,
            format_func=lambda cid: next(title for row_id, title in chats if row_id == cid),
            index=chat_ids.index(st.session_state.active_chat_id),
            label_visibility="collapsed",
        )

        if selected_id != st.session_state.active_chat_id:
            st.session_state.active_chat_id = selected_id
            st.rerun()

        with st.popover("⋯  Chat options", use_container_width=True):
            old_title = next(title for row_id, title in chats if row_id == selected_id)
            new_title = st.text_input("Rename chat", value=old_title)
            if st.button("Save name", use_container_width=True):
                if new_title.strip():
                    rename_chat(selected_id, new_title.strip())
                    st.rerun()

            st.divider()
            if st.button("Delete this chat", use_container_width=True):
                delete_chat(selected_id)
                remaining = get_chats()
                st.session_state.active_chat_id = (
                    remaining[0][0] if remaining else create_chat()
                )
                st.rerun()

    st.divider()
    st.markdown("##### What I can help with")
    st.markdown(
        """
        - 📧 **Gmail** — read and summarize emails; draft or send replies when enabled.
        - 📅 **Calendar** — check schedules and create events.
        - 🌐 **Web search** — find current information.
        - 📝 **Notes** — create and retrieve notes.
        - 💰 **Expenses** — record and review expenses.
        - ✅ **Tasks** — create and manage to-do items.
        - 📄 **PDFs** — answer questions using uploaded PDF text.
        - 🎤 **Voice** — transcribe a spoken message (API key required).
        """
    )
    st.markdown(
        '<div class="sidebar-note">These actions depend on the corresponding tools being connected and enabled in your n8n workflow. Conversations are saved locally.</div>',
        unsafe_allow_html=True,
    )


# -------------------- Main conversation --------------------
active_chat_id = st.session_state.active_chat_id
chat_messages = get_messages(active_chat_id)

if not chat_messages:
    st.markdown("""
    <div class="welcome">
        <h1>What can I help with?</h1>
        <p>Your personal assistant for email, calendar, search and everyday tasks.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Try asking me to")
    quick_actions = [
        ("📧 Summarize my latest emails", "Summarize my latest emails."),
        ("📅 Create a calendar event", "Help me create a calendar event."),
        ("🌐 Search the web", "Search the web for the latest technology news."),
        ("📝 Create a note", "Create a note."),
        ("💰 Record an expense", "Help me record an expense."),
        ("✅ Create a task", "Create a task for me."),
    ]
    action_cols = st.columns(2)
    for index, (label, prompt) in enumerate(quick_actions):
        with action_cols[index % 2]:
            if st.button(label, key=f"quick_action_{index}", use_container_width=True):
                st.session_state.pending_prompt = prompt
                st.rerun()
else:
    for role, content, created_at in chat_messages:
        with st.chat_message(role):
            st.markdown(content)


# -------------------- Chat composer --------------------
# Requires a recent Streamlit version supporting file/audio in chat_input.
chat_input = st.chat_input(
    "Message Personal AI...",
    accept_file="multiple",
    file_type=["pdf"],
    accept_audio=True,
)

# Quick-action buttons submit their prompt through the same n8n path.
if st.session_state.pending_prompt:
    pending_text = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
    user_text = pending_text
    attached_files = []
    audio_file = None
elif chat_input:
    user_text = (chat_input.text or "").strip()
    attached_files = chat_input.files or []
    audio_file = getattr(chat_input, "audio", None)
else:
    user_text = None

if user_text is not None:
    if audio_file is not None:
        try:
            with st.spinner("Transcribing your voice..."):
                voice_text = transcribe_audio(audio_file)
            user_text = f"{user_text}\n{voice_text}".strip()
        except Exception as error:
            st.error(f"Voice transcription failed: {error}")
            st.stop()

    pdf_parts = []
    file_names = []

    for uploaded_file in attached_files:
        if uploaded_file.name.lower().endswith(".pdf"):
            try:
                extracted = extract_pdf_text(uploaded_file)
                if extracted.strip():
                    pdf_parts.append(f"DOCUMENT: {uploaded_file.name}\n{extracted}")
                    file_names.append(uploaded_file.name)
                else:
                    st.warning(
                        f"No selectable text found in {uploaded_file.name}. "
                        "Scanned PDFs need OCR."
                    )
            except Exception as error:
                st.error(f"Could not read {uploaded_file.name}: {error}")

    pdf_context = "\n\n".join(pdf_parts) if pdf_parts else None

    if not user_text and not pdf_context:
        st.warning("Type a message, record audio, or attach a readable PDF.")
        st.stop()

    if not user_text:
        user_text = "Please summarize this PDF and identify its key points."

    display_text = user_text
    if file_names:
        display_text += "\n\n📎 Attached: " + ", ".join(file_names)

    if not get_messages(active_chat_id):
        rename_chat(active_chat_id, user_text[:40] or "PDF conversation")

    save_message(active_chat_id, "user", display_text)

    with st.chat_message("user"):
        st.markdown(display_text)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                answer = call_n8n(user_text, pdf_context)
            st.markdown(answer)
        except requests.exceptions.Timeout:
            answer = "The request timed out. Please try again."
            st.error(answer)
        except requests.exceptions.ConnectionError:
            answer = (
                "I couldn't connect to n8n. Check that n8n is running "
                "and the webhook URL is correct."
            )
            st.error(answer)
        except requests.exceptions.HTTPError as error:
            answer = f"n8n returned an HTTP error: {error}"
            st.error(answer)
        except Exception as error:
            answer = f"Something went wrong: {error}"
            st.error(answer)

    save_message(active_chat_id, "assistant", answer)
    st.rerun()
