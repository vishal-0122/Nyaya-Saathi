# Nyaya Saathi Streamlit Frontend

A beautiful, interactive web interface for the Nyaya Saathi legal AI assistant built with Streamlit.

## Features

✨ **Key Features:**
- 💬 **Chat Interface** - Ask legal questions in a conversational format
- 📚 **Chat History** - View and reload previous conversations from a dropdown
- 📋 **Structured Responses** - Get well-formatted answers with relevant laws, cases, and actions
- 🔄 **Session Management** - Each conversation has a unique session ID for tracking
- ⚖️ **Legal Information** - Displays relevant laws, case citations, and suggested actions
- 🎨 **Beautiful UI** - Clean, professional interface with custom styling

## Prerequisites

Before running the Streamlit app, ensure:

1. **Backend is running** - FastAPI server at `http://127.0.0.1:8000`
   ```bash
   cd g:\My Drive\Projects CV\Nyaya Saathi
   python -m uvicorn app.main:app --reload
   ```

2. **Database is configured** - PostgreSQL/Supabase connection is set up properly

3. **All dependencies are installed**
   ```bash
   pip install -r requirements.txt
   ```

## Installation

### 1. Install Streamlit and dependencies

```bash
pip install streamlit requests
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Verify backend configuration

Make sure your `.env` file has:
```env
# Database configuration
DATABASE_URL=your_database_url

# OpenAI configuration
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0

# LangSmith configuration (optional but recommended)
LANGSMITH_TRACING=true
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=nyaya-saathi
```

## Running the Frontend

### Start the Streamlit app:

```bash
streamlit run frontend/app.py
```

This will:
- Launch the Streamlit server on `http://localhost:8501`
- Open the app in your default browser automatically

### Running both backend and frontend:

**Terminal 1 - Backend:**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
streamlit run frontend/app.py
```

## Usage Guide

### 📝 Asking Questions

1. **New Chat:** Click the "➕ New Chat" button to start a fresh conversation
2. **Type Your Question:** Enter your legal question in the text area
3. **Send:** Click "Send" or press Enter
4. **View Response:** The assistant will provide:
   - Relevant laws and sections
   - Explanation of the legal scenario
   - Possible scenarios
   - Recent related cases
   - Suggested actions
   - Important disclaimers

### 📚 Accessing Previous Chats

1. **View Sessions:** Click "🔄 Refresh" to load all previous chat sessions
2. **Select a Chat:** Choose from the dropdown menu showing:
   - Session ID (first 8 characters)
   - Date and time of last message
3. **View History:** The full chat history for that session will be displayed
4. **Load Session:** Click to load that session and continue the conversation

### 🔍 Session ID

- **Current Session:** Displayed at the top of the sidebar
- **Purpose:** Tracks all related queries in a single conversation
- **Automatic:** New session ID generated when you click "➕ New Chat"

## API Endpoints Used

The Streamlit app communicates with these backend endpoints:

### POST `/query`
Send a legal query
```json
{
  "query": "What are my rights if I'm hit by a car?",
  "session_id": "unique-session-id"
}
```

### GET `/sessions`
Fetch all available sessions
```
GET /sessions?limit=50
```
Returns list of sessions with timestamps

### GET `/history/{session_id}`
Fetch chat history for a session
```
GET /history/unique-session-id?limit=50
```
Returns all chats in that session

## Troubleshooting

### Backend Connection Error
**Error:** `Failed to fetch sessions: Connection refused`
- **Solution:** Ensure the FastAPI backend is running on `http://127.0.0.1:8000`
- Run: `python -m uvicorn app.main:app --reload`

### No Previous Chats Showing
**Solution:** 
- Click "🔄 Refresh" button to reload sessions
- Check that database is properly configured
- Verify PostgreSQL/Supabase connection

### Long Response Times
- Check backend LangSmith tracing (may add latency)
- Verify OpenAI API key is valid
- Ensure backend logs for any errors

### Streamlit Port Already in Use
**Error:** `Port 8501 already in use`
- **Solution:** Run on different port:
  ```bash
  streamlit run frontend/app.py --server.port 8502
  ```

## File Structure

```
frontend/
├── app.py              # Main Streamlit application
└── components/         # Optional: Reusable Streamlit components
    ├── chat_ui.py      # Chat message components
    └── result_display.py # Response formatting components
```

## Performance Tips

1. **Use Sessions:** Load previous sessions to avoid re-querying
2. **Narrow Down:** Ask specific questions for faster, better responses
3. **Monitor Backend:** Keep an eye on backend logs for errors
4. **Cache Responses:** Streamlit automatically caches calls within the session

## Customization

### Change Backend URL
Edit the configuration at the top of `frontend/app.py`:
```python
BACKEND_URL = "http://127.0.0.1:8000"  # Change this
```

### Modify UI Theme
Edit the CSS in the `st.markdown()` call with `<style>` tags:
```python
st.markdown("""
    <style>
    /* Customize colors, fonts, spacing here */
    </style>
""", unsafe_allow_html=True)
```

### Add New Features
- Display lawyer recommendations
- Export chat history as PDF
- Add search within chat history
- Implement user accounts

## Deployment

### Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Select `frontend/app.py` as the main file
5. Add secrets for API keys

### Deploy Locally (Production)

```bash
streamlit run frontend/app.py --logger.level=error --client.showErrorDetails=false
```

## Disclaimer

⚠️ **Important:** This is an AI-powered legal assistant and should NOT be considered as:
- Professional legal advice
- A substitute for consultation with qualified lawyers
- Definitive legal guidance

Always consult with licensed legal professionals for important matters.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review backend logs for errors
3. Verify all environment variables are set
4. Ensure database connectivity

## License

Part of Nyaya Saathi project. See main LICENSE file.
