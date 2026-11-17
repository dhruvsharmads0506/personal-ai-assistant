 <div align="center">

# 🤖 Personal AI Assistant

**Your AI-powered assistant for conversations, documents, voice and workflow automation.**

<p>
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" />
  <img src="https://img.shields.io/badge/Streamlit-Frontend-red?logo=streamlit" />
  <img src="https://img.shields.io/badge/n8n-Automation-orange?logo=n8n" />
  <img src="https://img.shields.io/badge/Google-Gemini-4285F4?logo=google" />
  <img src="https://img.shields.io/badge/Database-SQLite-blue?logo=sqlite" />
</p>

</div>

---

## 📌 About The Project

Personal AI Assistant is an AI-powered application built using Python, Streamlit, n8n and Google Gemini.

It provides a ChatGPT-inspired interface where users can interact with AI, upload PDF documents, use voice input and perform automated tasks through n8n workflows.

## 🖥️ Application Preview

![Personal AI Assistant](screenshots/home.png)


## ✨ Features

- 💬 **AI Chat Interface** – Interactive conversational interface.
- 🎤 **Voice Input** – Convert speech into text using Google Gemini.
- 📄 **PDF Upload** – Extract and analyze PDF document content.
- 💾 **Chat History** – Store conversations using SQLite.
- 🗑️ **Chat Management** – Create, rename and delete conversations.
- ⚙️ **Workflow Automation** – Execute tasks using n8n webhooks.
- 📧 **Gmail Integration** – Email operations through configured workflows.
- 📅 **Calendar Integration** – Calendar operations through configured workflows.
- 🌐 **Web Search** – Retrieve online information through configured workflows.
- 📝 **Notes & Tasks** – Manage notes, expenses and tasks through configured workflows.
- 🌙 **Dark UI** – Clean and user-friendly interface.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| Streamlit | Frontend development |
| n8n | Workflow automation |
| Google Gemini API | Voice transcription |
| SQLite | Database |
| Docker | Running n8n |
| Git & GitHub | Version control |

## 📂 Project Structure

```text
personal-ai-assistant/
│
├── .devcontainer/
├── .streamlit/
│   └── secrets.toml
├── uploads/
│
├── app.py
├── requirements.txt
├── .gitignore
├── assistant.db
└── chat_history.db
```

## ⚙️ Installation & Setup

### 1. Clone Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd personal-ai-assistant
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

Activate on Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
N8N_WEBHOOK_URL = "your-n8n-webhook-url"
```

### 5. Start n8n Using Docker

```bash
docker run -it --rm --name n8n -p 5678:5678 -e GENERIC_TIMEZONE="Asia/Kolkata" -e TZ="Asia/Kolkata" -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n
```

### 6. Run Application

```bash
streamlit run app.py
```

Open in browser: `http://localhost:8501`

## 🔄 Application Workflow

1. User sends a message through the Streamlit interface.
2. Python processes the user input.
3. Voice input is transcribed using Gemini.
4. PDF documents are processed using PyPDF.
5. Requests are forwarded to n8n through webhooks.
6. n8n executes the configured automation workflows.
7. Responses are displayed in the chat interface.
8. Chat history is stored in SQLite.

## 🌐 Deployment

The application frontend can be deployed using Streamlit Community Cloud.

- **Frontend:** Streamlit Community Cloud
- **Automation:** n8n
- **AI Service:** Google Gemini API
- **Webhook:** Publicly accessible n8n endpoint

---

## 🔒 Live Demo & Privacy Notice

A public live demo is intentionally not available for this project because it is designed as a personal AI assistant connected to private services such as Gmail, Google Calendar and other personal integrations.

To protect personal information, account permissions and sensitive data, public access has been restricted.

The source code is available for learning and demonstration purposes. You can explore the implementation and set up your own instance using the provided installation instructions.

---

## 🔐 Security

- Store API keys in Streamlit Secrets.
- Never upload `.streamlit/secrets.toml` to GitHub.
- Protect n8n webhooks with authentication.
- Keep personal credentials private.

## 🎯 Project Objective

To develop a centralized personal AI assistant that combines conversational AI, voice interaction, document processing and workflow automation in a single application.

---

## 👨‍💻 Developer

**Dhruv Sharma**

GitHub: [dhruvsharmads0506](https://github.com/dhruvsharmads0506)

---

<div align="center">

**⭐ If you like this project, consider giving it a star!**

Built with Python, AI and Automation ❤️

</div>
