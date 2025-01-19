import os
from flask import Flask, request, render_template, send_file, jsonify
from rembg import remove, new_session
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
DEFAULT_BACKGROUND = 'static/default_background.png'
OUTPUT_FOLDER = 'outputs'

# Initialize rembg session with enhanced settings
session = new_session(model_name="u2net_human_seg")

# Ensure required directories exist
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, 'static']:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(input_path, background_path):
    """
    Process the input image with enhanced background removal and compositing.
    
    Args:
        input_path (str): Path to input portrait image
        background_path (str): Path to background image
    
    Returns:
        str: Path to processed output image
    """
    try:
        # Read input image and remove background with enhanced settings
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
            
            # Enhanced removal with alpha matting
            output_data = remove(
                input_data,
                session=session,
                alpha_matting=True,
                alpha_matting_foreground_threshold=240,
                alpha_matting_background_threshold=10,
                alpha_matting_erode_size=10
            )
            foreground = Image.open(io.BytesIO(output_data)).convert('RGBA')

        # Load and resize background to match foreground dimensions
        background = Image.open(background_path).convert('RGBA')
        background = background.resize(foreground.size, Image.Resampling.LANCZOS)

        # Create a new blank image with white background
        composite = Image.new('RGBA', foreground.size, (255, 255, 255, 255))
        
        # Paste background first
        composite.paste(background, (0, 0))
        
        # Paste foreground with alpha channel
        composite.paste(foreground, (0, 0), foreground)

        # Save output
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'processed_{timestamp}.png'
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        composite.save(output_path, 'PNG')
        
        # Save a copy to static folder for immediate display
        display_path = os.path.join('static', output_filename)
        composite.save(display_path, 'PNG')

        return output_filename

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
        output_filename = process_image(input_path, DEFAULT_BACKGROUND)

        # Clean up input file
        os.remove(input_path)

        return jsonify({
            'success': True, 
            'output_path': f'static/{output_filename}',
            'download_path': f'download/{output_filename}'
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Handle download of processed image."""
    try:
        return send_file(
            os.path.join(OUTPUT_FOLDER, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)