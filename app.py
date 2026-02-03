from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import tempfile
import re
from pathlib import Path

app = Flask(__name__, static_folder='.')

# Serve the HTML page
@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/info', methods=['POST'])
def get_video_info():
    """Get video information and available formats"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate YouTube URL
        if not re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/', url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get available formats
            formats = []
            seen_qualities = set()
            
            # Process video+audio combined formats
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    # Combined video+audio format
                    height = f.get('height', 0)
                    if height and height not in seen_qualities:
                        quality_label = f"{height}p"
                        ext = f.get('ext', 'mp4')
                        filesize = f.get('filesize', 0)
                        size_str = f" ({filesize / 1024 / 1024:.1f} MB)" if filesize else ""
                        
                        formats.append({
                            'format_id': f['format_id'],
                            'label': f"{quality_label} - {ext}{size_str}",
                            'height': height
                        })
                        seen_qualities.add(height)
            
            # If no combined formats found, add best option
            if not formats:
                formats.append({
                    'format_id': 'best',
                    'label': 'Best Quality (auto)',
                    'height': 9999
                })
            
            # Sort by quality (highest first)
            formats.sort(key=lambda x: x['height'], reverse=True)
            
            # Add audio-only option
            formats.append({
                'format_id': 'bestaudio',
                'label': 'Audio Only (MP3)',
                'height': 0
            })
            
            return jsonify({
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'formats': formats
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    """Download video in selected quality"""
    try:
        data = request.json
        url = data.get('url')
        format_id = data.get('format_id', 'best')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Create temporary directory for downloads
        temp_dir = tempfile.mkdtemp()
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': format_id if format_id != 'bestaudio' else 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        # If audio only, convert to mp3
        if format_id == 'bestaudio':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Find the downloaded file
            filename = ydl.prepare_filename(info)
            
            # If audio extraction, change extension to mp3
            if format_id == 'bestaudio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            if not os.path.exists(filename):
                # Try to find any file in the temp directory
                files = list(Path(temp_dir).glob('*'))
                if files:
                    filename = str(files[0])
                else:
                    raise Exception('Downloaded file not found')
            
            # Send the file
            return send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename),
                mimetype='application/octet-stream'
            )
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use environment variable for port (required by most free hosting services)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
