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

def get_ydl_opts(for_download=False):
    """Get yt-dlp options with multiple fallback strategies"""
    
    base_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'age_limit': None,
    }
    
    if for_download:
        base_opts['format'] = 'best'
    
    # Try with these options (multiple strategies)
    strategies = [
        # Strategy 1: Android + Web clients
        {
            **base_opts,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        },
        # Strategy 2: iOS client (often works when Android fails)
        {
            **base_opts,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'web'],
                }
            },
        },
        # Strategy 3: TV embedded client
        {
            **base_opts,
            'extractor_args': {
                'youtube': {
                    'player_client': ['tv_embedded'],
                }
            },
        },
    ]
    
    return strategies

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
        
        # Try multiple strategies
        strategies = get_ydl_opts()
        last_error = None
        
        for strategy_opts in strategies:
            try:
                with yt_dlp.YoutubeDL(strategy_opts) as ydl:
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
                last_error = str(e)
                continue
        
        # If all strategies failed
        return jsonify({
            'error': f'Unable to fetch video info. This video might be restricted. Last error: {last_error}'
        }), 500
            
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
        
        # Try multiple strategies
        strategies = get_ydl_opts(for_download=True)
        last_error = None
        
        for strategy_opts in strategies:
            try:
                # Update with download-specific options
                strategy_opts['format'] = format_id if format_id != 'bestaudio' else 'bestaudio/best'
                strategy_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
                
                # If audio only, convert to mp3
                if format_id == 'bestaudio':
                    strategy_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                
                # Download the video
                with yt_dlp.YoutubeDL(strategy_opts) as ydl:
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
                last_error = str(e)
                continue
        
        # If all strategies failed
        return jsonify({
            'error': f'Unable to download video. This video might be restricted. Last error: {last_error}'
        }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use environment variable for port (required by most free hosting services)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
