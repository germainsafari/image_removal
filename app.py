import os
from flask import Flask, request, render_template, send_file, jsonify
from rembg import remove
from PIL import Image
import io
import numpy as np
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
DEFAULT_BACKGROUND = 'static/default_background.jpg'
OUTPUT_FOLDER = 'outputs'

# Ensure required directories exist
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(input_path, background_path):
    """
    Process the input image by removing background and compositing with new background.
    
    Args:
        input_path (str): Path to input portrait image
        background_path (str): Path to background image
    
    Returns:
        str: Path to processed output image
    """
    try:
        # Read input image and remove background
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
            output_data = remove(input_data)
            foreground = Image.open(io.BytesIO(output_data)).convert('RGBA')

        # Load and resize background to match foreground dimensions
        background = Image.open(background_path).convert('RGBA')
        background = background.resize(foreground.size, Image.Resampling.LANCZOS)

        # Composite images
        composite = Image.alpha_composite(background, foreground)

        # Save output
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(OUTPUT_FOLDER, f'processed_{timestamp}.png')
        composite.save(output_path, 'PNG')

        return output_path

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise

@app.route('/', methods=['GET'])
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle image upload and processing."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        # Process image
        output_path = process_image(input_path, DEFAULT_BACKGROUND)

        # Clean up input file
        os.remove(input_path)

        return jsonify({'success': True, 'output_path': output_path})

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    """Handle download of processed image."""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)