# Summarify Chrome Extension

This is a Chrome/Edge extension for the Summarify project, allowing you to easily summarize YouTube videos directly from your browser.

## Features

- Summarize YouTube videos with one click
- Context menu integration for YouTube pages
- User authentication with your Summarify account
- Simple and intuitive interface

## Installation

### Development Mode

1. Clone the repository or download the extension folder
2. Open Chrome/Edge and navigate to `chrome://extensions/` or `edge://extensions/`
3. Enable "Developer mode" in the top right corner
4. Click "Load unpacked" and select the `extension` folder
5. The extension should now be installed and visible in your browser toolbar

### Production Mode (Coming Soon)

The extension will be available on the Chrome Web Store in the future.

## Usage

1. Click on the Summarify extension icon in your browser toolbar
2. Log in with your Summarify account credentials
3. To summarize a YouTube video:
   - Navigate to a YouTube video page and click the "Summarize Current Video" button
   - OR enter a YouTube URL in the extension popup and click "Summarize"
   - OR right-click on a YouTube page and select "Summarize this YouTube video"
4. View the generated summary in the extension popup

## Requirements

- A running instance of the Summarify backend API
- By default, the extension connects to `http://localhost:8080`
- To use a different backend URL, modify the `API_URL` in `background.js`

## Development

### Project Structure

- `manifest.json`: Extension configuration
- `popup.html`: Extension popup UI
- `popup.js`: Popup functionality
- `popup.css`: Popup styles
- `background.js`: Background script for API calls
- `content.js`: Content script for YouTube integration
- `icons/`: Extension icons

### Customization

To customize the extension:

1. Update the `API_URL` in `background.js` to point to your deployed Summarify backend
2. Replace the placeholder icons in the `icons/` directory with your own
3. Modify the UI in `popup.html` and `popup.css` as needed

## Notes for Production

Before publishing to the Chrome Web Store:

1. Replace placeholder icons with proper branded icons
2. Update the `API_URL` to point to a production backend
3. Consider implementing offline functionality
4. Add proper error handling and user feedback

## License

This project is licensed under the same terms as the main Summarify project.
