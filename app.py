from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import json
import instaloader
from instaloader import Post
import os

app = Flask(__name__)
CORS(app)

# Initialize Instaloader once
L = instaloader.Instaloader(
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    quiet=True
)

def extract_shortcode(url):
    """Extract shortcode from Instagram URL"""
    patterns = [
        r'instagram\.com/p/([A-Za-z0-9_-]+)',
        r'instagram\.com/reel/([A-Za-z0-9_-]+)',
        r'instagram\.com/tv/([A-Za-z0-9_-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

def fetch_with_instaloader(shortcode):
    """Fetch media URLs using Instaloader"""
    try:
        print(f"Fetching post with Instaloader: {shortcode}")

        # Get post
        post = Post.from_shortcode(L.context, shortcode)

        media = []

        # Check if it's a video (reel or regular video)
        if post.is_video:
            print(f"  Found video/reel")
            media.append({
                'url': post.video_url,
                'type': 'video',
                'thumbnail': post.url  # thumbnail image
            })
        else:
            # Check if it's a sidecar (carousel/gallery)
            if post.typename == 'GraphSidecar':
                print(f"  Found carousel with {post.mediacount} items")
                # Get all images from carousel
                for node in post.get_sidecar_nodes():
                    if node.is_video:
                        media.append({
                            'url': node.video_url,
                            'type': 'video',
                            'thumbnail': node.display_url
                        })
                    else:
                        media.append({
                            'url': node.display_url,
                            'type': 'image'
                        })
            else:
                # Single image post
                print(f"  Found single image")
                media.append({
                    'url': post.url,
                    'type': 'image'
                })

        print(f"  Successfully extracted {len(media)} media item(s)")
        return media

    except Exception as e:
        print(f"  Instaloader error: {str(e)}")
        return None

@app.route('/api/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url', '')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        # Validate Instagram URL
        shortcode = extract_shortcode(url)

        if not shortcode:
            return jsonify({'error': 'Invalid Instagram URL'}), 400

        print(f"\nProcessing Instagram post: {shortcode}")

        # Use Instaloader to fetch media
        media = fetch_with_instaloader(shortcode)

        if not media:
            return jsonify({'error': 'Failed to fetch media. Post may be private or unavailable.'}), 404

        print(f"✅ Successfully fetched {len(media)} media item(s)\n")

        return jsonify({
            'success': True,
            'media': media
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
