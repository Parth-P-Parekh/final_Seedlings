# GitHub Issue Analyzer with AI

A full-stack application that leverages AI-powered analysis to automatically categorize, summarize, and provide actionable insights on GitHub issues. Built with FastAPI backend and Streamlit frontend.

## 🎯 Features

- **AI-Powered Analysis**: Uses Google Gemini API to analyze GitHub issues intelligently
- **GitHub Integration**: Connect to your repositories and analyze issues in real-time
- **Issue Categorization**: Automatically categorize issues by type (bug, feature, documentation, etc.)
- **Smart Summarization**: Generate concise summaries of complex issues
- **Caching Layer**: Redis integration for improved performance
- **RESTful API**: Clean, well-documented API endpoints
- **Web Interface**: User-friendly Streamlit dashboard
- **Analytics**: Track and visualize issue patterns
- **Comprehensive Testing**: Full test suite with pytest

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (modern Python web framework)
- **Server**: Uvicorn (ASGI server)
- **APIs**: Google Generative AI, PyGithub
- **Validation**: Pydantic
- **Caching**: Redis
- **Testing**: Pytest, Pytest-asyncio

### Frontend
- **Framework**: Streamlit (data visualization & web UI)
- **HTTP Client**: httpx
- **Styling**: Custom CSS

### Development Tools
- **Code Quality**: Black, Ruff, Mypy
- **Environment**: Python-dotenv

## 📁 Project Structure

```
final_Seedlings/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── core/             # Configuration and prompts
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # Business logic (GitHub, LLM)
│   │   └── utils/            # Utilities (cache, logger)
│   ├── main.py               # Backend entry point
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Streamlit app
│   ├── app.py                # Main Streamlit app
│   ├── pages/                # Streamlit pages (home, analytics)
│   └── utils/                # Frontend utilities
├── scripts/                    # Deployment scripts
├── tests/                      # Test suite
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git
- GitHub account (for API token)
- Google Gemini API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd final_Seedlings
```

### 2. Create Environment Variables

Create a `.env` file in the root directory:

```env
# API Keys
GEMINI_API_KEY=your_google_gemini_api_key_here
GITHUB_TOKEN=your_github_personal_access_token

# Backend Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true
DEBUG=false

# Frontend URL
FRONTEND_URL=http://localhost:8501

# Redis Configuration (optional)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CACHE_TTL=86400
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 4. Run Backend Server

```bash
cd backend
python main.py
```

The backend API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

### 5. Run Frontend (in a new terminal)

```bash
pip install streamlit
cd frontend
streamlit run app.py
```

The frontend will be available at `http://localhost:8501`

## 🔑 Environment Variables Explained

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Generative AI API key (required) | - |
| `GITHUB_TOKEN` | GitHub personal access token | - |
| `HOST` | Backend server host | 0.0.0.0 |
| `PORT` | Backend server port | 8000 |
| `RELOAD` | Auto-reload on code changes | true |
| `DEBUG` | Debug mode | false |
| `FRONTEND_URL` | Frontend URL for CORS | http://localhost:8501 |
| `REDIS_ENABLED` | Enable Redis caching | false |
| `REDIS_HOST` | Redis server host | localhost |
| `REDIS_PORT` | Redis server port | 6379 |

## 📚 API Endpoints

### Main Endpoints
- `GET /api/health` - Health check
- `POST /api/analyze` - Analyze GitHub issues
- `GET /api/issues` - Fetch issues from a repository
- `POST /api/cache/clear` - Clear cache

Detailed API documentation available at `http://localhost:8000/docs` when the server is running.

## 🧪 Running Tests

```bash
cd backend
pytest                    # Run all tests
pytest -v               # Verbose output
pytest --cov            # With coverage report
pytest test_api.py      # Run specific test file
```

## 🐛 Troubleshooting

### Backend won't start
- Ensure all dependencies are installed: `pip install -r backend/requirements.txt`
- Check that port 8000 is available
- Verify `.env` file has required API keys

### Frontend can't connect to backend
- Ensure backend is running on `http://localhost:8000`
- Check CORS settings in `backend/app/core/config.py`
- Verify firewall/network settings

### API Key errors
- Verify `GEMINI_API_KEY` is set correctly in `.env`
- Check that the API key has not expired
- Ensure the key has required permissions

## 📝 License

This project is provided as-is for educational and commercial use.

## 👤 Author

GitHub Issue Analyzer Team

## 🤝 Contributing

Contributions are welcome! Please follow PEP 8 style guidelines and ensure all tests pass before submitting pull requests.
