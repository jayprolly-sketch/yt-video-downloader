# YouTube Downloader Web App

A simple web application to download YouTube videos in any available quality using yt-dlp.

## Features

- 🎥 Download YouTube videos in multiple qualities
- 🎵 Download audio-only (MP3)
- 📱 Responsive design
- ⚡ Fast and reliable using yt-dlp
- 🎨 Modern, beautiful UI

## Files Included

- `index.html` - Frontend interface
- `app.py` - Flask backend server
- `requirements.txt` - Python dependencies
- `Procfile` - Deployment configuration
- `README.md` - This file

## Local Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and visit:
```
http://localhost:5000
```

## Deployment to Free Hosting Services

### Option 1: Render.com (Recommended)

1. Create a free account at [Render.com](https://render.com)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository or upload files
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3
5. Click "Create Web Service"
6. Wait for deployment (5-10 minutes)

### Option 2: Railway.app

1. Create account at [Railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Railway will auto-detect the Python app
4. Deploy automatically starts
5. Get your app URL from the deployment

### Option 3: Fly.io

1. Install Fly CLI: [https://fly.io/docs/hands-on/install-flyctl/](https://fly.io/docs/hands-on/install-flyctl/)
2. Create account: `flyctl auth signup`
3. In project directory: `flyctl launch`
4. Follow prompts to deploy

### Option 4: PythonAnywhere

1. Create free account at [PythonAnywhere.com](https://www.pythonanywhere.com)
2. Upload files via Files tab
3. Open Bash console and run:
```bash
pip install --user -r requirements.txt
```
4. Go to Web tab → Add new web app
5. Choose Flask
6. Set source code path to your app.py location
7. Reload web app

## Important Notes

### For Hosting Services

1. **FFmpeg Requirement**: For audio extraction (MP3), the hosting service needs FFmpeg installed. Most services like Render and Railway have it by default.

2. **Storage**: Downloaded files are stored temporarily and deleted after sending. Make sure your hosting has enough temporary storage.

3. **Rate Limits**: Free tiers have limitations. Be mindful of:
   - Request limits
   - Bandwidth limits
   - CPU time limits

4. **Timeout**: Some free services have request timeout limits (usually 30-60 seconds). Very large video downloads might timeout.

### Legal Considerations

- This tool is for personal use only
- Respect YouTube's Terms of Service
- Don't download copyrighted content without permission
- Don't redistribute downloaded content

## Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt --upgrade
```

### FFmpeg not found (for audio extraction)
Most hosting services include FFmpeg. For local use:
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Download fails
- Check if the YouTube URL is valid
- Some videos may be restricted or private
- Age-restricted videos might not work
- Try updating yt-dlp: `pip install yt-dlp --upgrade`

## Usage

1. Paste a YouTube video URL
2. Click "Get Video Info"
3. Select desired quality from dropdown
4. Click "Download Video"
5. Video will download to your device

## Technologies Used

- **Backend**: Flask (Python)
- **Downloader**: yt-dlp
- **Frontend**: HTML, CSS, JavaScript
- **Server**: Gunicorn (for production)

## Privacy

- No data is stored on the server
- No tracking or analytics
- Videos are downloaded directly to your device
- Temporary files are automatically cleaned up

## Updates

To update yt-dlp to the latest version:
```bash
pip install yt-dlp --upgrade
```

## License

This project is for educational purposes. Use responsibly and respect content creators' rights.

## Support

For issues or questions, check:
- [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp)
- [Flask documentation](https://flask.palletsprojects.com/)

---

**Note**: This application respects YouTube's robots.txt and uses official download methods. Always ensure you have the right to download content.
