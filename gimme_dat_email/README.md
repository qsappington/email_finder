# Gimme Dat Email

A Chrome extension and web app for finding professional email addresses quickly and easily.

## Features
- Find company email patterns
- Generate professional email addresses
- Copy to clipboard with one click
- Multiple domain support
- Clean, modern interface

## Setup

### Web App
1. Create virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate virtual environment:
   ```bash
   source venv/bin/activate  # Unix/macOS
   .\venv\Scripts\activate   # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Hunter.io API key
   ```
5. Run the app:
   ```bash
   python web/app.py
   ```

### Chrome Extension
1. Open Chrome Extensions (chrome://extensions/)
2. Enable "Developer mode" in the top right
3. Click "Load unpacked"
4. Select the `extension` directory
5. Add your Hunter.io API key in extension settings

## Development

### Project Structure 