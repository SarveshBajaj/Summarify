# Summarify

## Overview
Summarify is an extensible API and UI for summarizing YouTube videos (and later, other sources) using transcripts and a local LLM. The application provides a rate-limited API with user authentication and a simple frontend interface.

## Features
- User authentication (sign up/login)
- Rate-limited API (5 requests/sec per user)
- Summarizes YouTube videos via URL
- Extensible architecture for different content sources
- Validation of generated summaries
- Comprehensive logging
- Test coverage
- Simple frontend UI

## Requirements
- Python 3.8+
- Node.js 14+ (for frontend development)
- Internet connection (for YouTube API access)

## Setup

### Backend

1. Create and activate a Python virtual environment:
   ```sh
   python -m venv venv

   # Windows:
   venv\Scripts\activate

   # Linux/macOS:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Run the backend:
   ```sh
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Frontend

The frontend is a simple HTML/CSS/JavaScript application located in the `frontend/` directory.

1. Open the `frontend/index.html` file in a web browser, or serve it using a simple HTTP server:
   ```sh
   # Using Python's built-in HTTP server
   cd frontend
   python -m http.server 8080
   ```

2. Access the frontend at http://localhost:8080

## API Endpoints

- `POST /signup` - Register a new user
- `POST /login` - Authenticate and get access token
- `GET /users/me` - Get current user information
- `POST /summarize` - Summarize content from a URL

## Testing

Run the test suite with pytest:

```sh
pytest
```

For more detailed test output:

```sh
pytest -v
```

## Project Structure

```
├── app/                  # Backend application
│   ├── __init__.py
│   ├── main.py           # FastAPI application and routes
│   ├── auth.py           # Authentication logic
│   ├── providers.py      # Content providers (YouTube, etc.)
│   ├── schemas.py        # Pydantic models
│   └── test_main.py      # Tests
├── frontend/            # Frontend application
│   ├── index.html        # Main HTML page
│   ├── styles.css        # CSS styles
│   └── app.js            # JavaScript for the frontend
├── logs/                # Application logs
├── venv/                # Virtual environment
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Extending

### Adding New Content Providers

To add support for a new content source:

1. Add a new provider type in `app/providers.py`:
   ```python
   class ProviderType(str, Enum):
       youtube = "youtube"
       web = "web"  # New provider type
   ```

2. Create a new provider class that inherits from `ContentProvider`:
   ```python
   class WebProvider(ContentProvider):
       def get_transcript(self, url: str) -> str:
           # Implementation for extracting text from web pages
           ...

       def summarize_and_validate(self, transcript: str, url: str) -> Tuple[str, bool]:
           # Implementation for summarizing web content
           ...
   ```

3. Update the `get_provider` function to return your new provider:
   ```python
   def get_provider(provider_type: ProviderType) -> ContentProvider:
       if provider_type == ProviderType.youtube:
           return YouTubeProvider()
       if provider_type == ProviderType.web:
           return WebProvider()
       raise NotImplementedError(f"Provider type {provider_type} not implemented")
   ```

## Security Considerations

- The current implementation uses an in-memory user database. For production, use a proper database.
- The secret key is hardcoded. For production, use environment variables.
- CORS is configured to allow all origins. For production, specify allowed origins.

## License

MIT
