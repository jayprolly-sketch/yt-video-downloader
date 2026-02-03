from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import tempfile
import re
import random
from pathlib import Path

app = Flask(__name__, static_folder='.')

# User agents pool - randomly selected for each request
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 11; EC1002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-A528B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; 2109119DG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; VOG-L29 Build/HUAWEIVOG-L29; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/103.0.5060.71 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/375.1.0.28.111;]",
    "Mozilla/5.0 (Linux; Android 10; moto g(7) Build/QPUS30.52-16-2-13; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/96.0.4664.104 Mobile Safari/537.36 GoogleApp/12.48.23.23.arm64",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7187.129 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7300.66 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7065.116 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6945.191 Safari/537.36",
]

def get_random_user_agent():
    """Get a random user agent from the pool"""
    return random.choice(USER_AGENTS)

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_extraction_strategies(user_agent, for_download=False):
    """Get multiple extraction strategies with random user agent"""
    
    base_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'age_limit': None,
        'user_agent': user_agent,
    }
    
    if for_download:
        base_opts['format'] = 'best'
    
    # Multiple aggressive strategies
    strategies = [
        # Strategy 1: Android client with aggressive bypassing
        {
            **base_opts,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                    'player_skip': ['webpage', 'configs'],
                    'skip': ['hls', 'dash'],
                }
            },
        },
        # Strategy 2: iOS client
        {
            **base_opts,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios'],
                    'player_skip': ['webpage'],
                }
            },
        },
        # Strategy 3: Web client with embed
        {
            **base_opts,
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                }
            },
        },
        # Strategy 4: TV embedded (often bypasses restrictions)
        {
            **base_opts,
            'extractor_args': {
                'youtube': {
                    'player_client': ['tv_embedded'],
                }
            },
        },
        # Strategy 5: Android + Web combo
        {
            **base_opts,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
        },
    ]
    
    return strategies

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
        
        # Extract video ID for embed fallback
        video_id = extract_video_id(url)
        
        # Get random user agent for this request
        user_agent = get_random_user_agent()
        
        # Try multiple strategies
        strategies = get_extraction_strategies(user_agent)
        urls_to_try = [url]
        
        # Add embed URLs as fallback
        if video_id:
            urls_to_try.append(f'https://www.youtube-nocookie.com/embed/{video_id}')
            urls_to_try.append(f'https://www.youtube.com/embed/{video_id}')
        
        last_error = None
        
        for test_url in urls_to_try:
            for strategy_opts in strategies:
                try:
                    with yt_dlp.YoutubeDL(strategy_opts) as ydl:
                        info = ydl.extract_info(test_url, download=False)
                        
                        # Get available formats
                        formats = []
                        seen_qualities = set()
                        
                        # Process video+audio combined formats
                        for f in info.get('formats', []):
                            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
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
                        
                        # If no combined formats, add best option
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
        
        # If all strategies failed, return detailed error
        return jsonify({
            'error': 'Unable to fetch video info after trying all methods. Possible reasons: 1) Video is age-restricted or private, 2) Video requires login, 3) Temporary YouTube block. Try a different video or wait 30 minutes.',
            'technical_error': last_error
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
        
        # Extract video ID for embed fallback
        video_id = extract_video_id(url)
        
        # Get random user agent for this request
        user_agent = get_random_user_agent()
        
        # Create temporary directory for downloads
        temp_dir = tempfile.mkdtemp()
        
        # Try multiple strategies
        strategies = get_extraction_strategies(user_agent, for_download=True)
        urls_to_try = [url]
        
        # Add embed URLs as fallback
        if video_id:
            urls_to_try.append(f'https://www.youtube-nocookie.com/embed/{video_id}')
            urls_to_try.append(f'https://www.youtube.com/embed/{video_id}')
        
        last_error = None
        
        for test_url in urls_to_try:
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
                        info = ydl.extract_info(test_url, download=True)
                        
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
            'error': 'Unable to download video after trying all methods. This video might be restricted.',
            'technical_error': last_error
        }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use environment variable for port (required by most free hosting services)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
