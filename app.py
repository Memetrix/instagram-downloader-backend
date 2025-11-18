from flask import Flask, request, jsonify
from flask_cors import CORS
import instaloader

app = Flask(__name__)
CORS(app)

@app.route('/api/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url', '')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        # Extract shortcode from URL
        if '/p/' in url:
            shortcode = url.split('/p/')[1].split('/')[0].split('?')[0]
        elif '/reel/' in url:
            shortcode = url.split('/reel/')[1].split('/')[0].split('?')[0]
        else:
            return jsonify({'error': 'Invalid Instagram URL'}), 400

        # Create Instaloader instance
        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern='',
            quiet=True
        )

        # Get post
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        media = []

        # Handle carousel/sidecar posts (multiple images/videos)
        if post.typename == 'GraphSidecar':
            for node in post.get_sidecar_nodes():
                if node.is_video:
                    media.append({
                        'url': node.video_url,
                        'type': 'video'
                    })
                else:
                    media.append({
                        'url': node.display_url,
                        'type': 'image'
                    })
        else:
            # Single image or video
            if post.is_video:
                media.append({
                    'url': post.video_url,
                    'type': 'video'
                })
            else:
                media.append({
                    'url': post.url,
                    'type': 'image'
                })

        return jsonify({
            'success': True,
            'media': media
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
