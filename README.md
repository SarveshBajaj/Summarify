# Summarify

## Overview
Summarify is an extensible API and UI for summarizing YouTube videos (and later, other sources) using transcripts and a local LLM. The application provides a rate-limited API with user authentication and a simple frontend interface.

## Features
- User authentication (sign up/login) with secure password hashing
- Embedded SQLite database for user credentials and query history
- Rate-limited API (5 requests/sec per user)
- Summarizes YouTube videos via URL
- Chrome/Edge browser extension for easy access
- Multiple summarization models:
  - Local HuggingFace models (default)
  - OpenAI API integration (GPT-3.5/4)
  - Anthropic Claude API integration
- Extensible architecture for different content sources
- Validation of generated summaries
- Query history tracking and statistics
- Comprehensive logging
- Extensive test coverage (unit and integration tests)
- Simple frontend UI with query history display

## Requirements
- Python 3.8+
- Node.js 14+ (for frontend development)
- Internet connection (for YouTube API access)
- OpenAI API key (optional, for using OpenAI models)
- Anthropic API key (optional, for using Claude models)

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

3. Run the database migration script:
   ```sh
   python migrate_db.py
   ```
   This step is important when upgrading from a previous version to add support for multiple AI models.

4. Run the backend:
   ```sh
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

5. Access the API documentation:
   - Swagger UI: http://localhost:8080/docs
   - ReDoc: http://localhost:8080/redoc

### Frontend

The frontend is a simple HTML/CSS/JavaScript application located in the `frontend/` directory.

1. Open the `frontend/index.html` file in a web browser, or serve it using a simple HTTP server:
   ```sh
   # Using Python's built-in HTTP server
   cd frontend
   python -m http.server 8080
   ```

2. Access the frontend at http://localhost:8080

### Configuring External AI Models

By default, Summarify uses a local HuggingFace model for summarization. You can also configure it to use OpenAI or Anthropic Claude models:

1. Set API keys using the API endpoint:
   ```sh
   # For OpenAI
   curl -X POST http://localhost:8080/api-keys \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"provider": "openai", "api_key": "YOUR_OPENAI_API_KEY"}'

   # For Anthropic Claude
   curl -X POST http://localhost:8080/api-keys \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"provider": "anthropic", "api_key": "YOUR_ANTHROPIC_API_KEY"}'
   ```

2. Alternatively, you can set environment variables:
   ```sh
   # For OpenAI
   export OPENAI_API_KEY=your_openai_api_key

   # For Anthropic Claude
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

3. Or create a `config.json` file in the project root:
   ```json
   {
     "api_keys": {
       "openai": "your_openai_api_key",
       "anthropic": "your_anthropic_api_key"
     }
   }
   ```

### Chrome Extension

The Chrome/Edge extension allows you to summarize YouTube videos directly from your browser.

1. Load the extension in developer mode:
   ```sh
   # Open Chrome/Edge and navigate to:
   # Chrome: chrome://extensions/
   # Edge: edge://extensions/
   # Then enable "Developer mode" and click "Load unpacked"
   # Select the "extension" directory in the project
   ```

2. Use the extension:
   - Click the Summarify icon in your browser toolbar
   - Log in with your Summarify account
   - Navigate to a YouTube video and click "Summarize Current Video"
   - Or enter a YouTube URL manually
   - Or right-click on a YouTube page and select "Summarize this YouTube video"

3. View the generated summary directly in the extension popup

For more details, see the [extension README](extension/README.md).

## API Endpoints

### Authentication
- `POST /signup` - Register a new user
- `POST /login` - Authenticate and get access token
- `GET /users/me` - Get current user information

### Summarization
- `POST /summarize` - Summarize content from a URL
  - Parameters:
    - `url`: URL of the content to summarize
    - `max_length`: Maximum length of the summary in words (default: 1000)
    - `provider_type`: Type of content provider (default: "youtube")
    - `model_type`: Type of summarization model ("huggingface", "openai", or "claude")
    - `model_name`: Specific model name (optional)

### Query History
- `GET /queries/me` - Get the current user's query history
- `GET /queries/stats` - Get overall query statistics

### Model Management
- `GET /models` - Get available models and their configuration status
- `POST /api-keys` - Set API key for a provider
  - Parameters:
    - `provider`: Provider name ("openai" or "anthropic")
    - `api_key`: API key for the provider

## Testing

The project includes comprehensive test coverage with both unit and integration tests.

### Running Tests

Run the entire test suite with pytest:

```sh
python -m pytest
```

Run specific test categories:

```sh
# Run only unit tests
python -m pytest tests/unit

# Run only integration tests
python -m pytest tests/integration

# Run with verbose output
python -m pytest -v

# Run a specific test file
python -m pytest tests/unit/test_database.py
```

### Test Structure

Tests are organized into the following structure:

```
tests/
├── conftest.py         # Shared test fixtures
├── __init__.py
├── integration/        # API and end-to-end tests
│   ├── __init__.py
│   ├── test_api.py     # Tests for API endpoints with database
│   └── test_main.py    # Tests for main application functionality
└── unit/               # Unit tests for individual components
    ├── __init__.py
    └── test_database.py # Tests for database functionality
```

## Project Structure

```
├── app/                  # Backend application
│   ├── __init__.py
│   ├── main.py           # FastAPI application and routes
│   ├── auth.py           # Authentication logic
│   ├── database.py       # Database operations and models
│   ├── providers.py      # Content providers (YouTube, etc.)
│   └── schemas.py        # Pydantic models
├── data/                 # Database files
│   └── summarify.db      # SQLite database
├── extension/            # Chrome/Edge extension
│   ├── manifest.json     # Extension configuration
│   ├── popup.html        # Extension popup UI
│   ├── popup.js          # Popup functionality
│   ├── popup.css         # Popup styles
│   ├── background.js     # Background script for API calls
│   ├── content.js        # Content script for YouTube integration
│   └── icons/            # Extension icons
├── frontend/            # Frontend application
│   ├── index.html        # Main HTML page
│   ├── styles.css        # CSS styles
│   └── app.js            # JavaScript for the frontend
├── logs/                # Application logs
├── tests/               # Test suite
│   ├── conftest.py       # Shared test fixtures
│   ├── extension/        # Extension tests
│   ├── integration/      # Integration tests
│   └── unit/             # Unit tests
├── venv/                # Virtual environment
├── pytest.ini           # Pytest configuration
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
