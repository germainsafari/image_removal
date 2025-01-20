import os
from dotenv import load_dotenv
from flask import Flask, request, render_template, send_file, jsonify
from PIL import Image
import io
import requests
import logging
from datetime import datetime
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
DEFAULT_BACKGROUND = 'static/default_background.png'
OUTPUT_FOLDER = 'outputs'
REMOVE_BG_API_KEY = os.getenv('REMOVE_BG_API_KEY')
REMOVE_BG_API_URL = 'https://api.remove.bg/v1.0/removebg'

# Verify API key is available
if not REMOVE_BG_API_KEY:
    raise ValueError("Missing REMOVE_BG_API_KEY in environment variables")

# Ensure required directories exist
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, 'static']:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# This is the function that interacts with the remove.bg API to remove the background of an image.

def remove_background_api(image_path):
    """
    Remove background using remove.bg API
    
    Args:image_path (str): Path to input image
        
    Returns:bytes: Processed image data with transparent background
    """
    headers = {
        'X-Api-Key': REMOVE_BG_API_KEY,
    }

    with open(image_path, 'rb') as image_file:
        files = {
            'image_file': image_file,
            'size': 'auto',
            'format': 'png',
        }
        
        response = requests.post(
            REMOVE_BG_API_URL,
            headers=headers,
            files=files
        )
        
        if response.status_code == requests.codes.ok:
            return response.content
        else:
            raise Exception(f"Remove.bg API error: {response.status_code} - {response.text}")
        
#  This function processes an image by removing the background using the remove.bg API and then compositing it with a background image.

def process_image(input_path, background_path):
    """
    Process the input image using remove.bg API and compose with background.
    
    Args:
        input_path (str): Path to input portrait image
        background_path (str): Path to background image
    
    Returns:
        str: Path to processed output image
    """
    try:
        # Remove background using remove.bg API
        removed_bg_data = remove_background_api(input_path)
        foreground = Image.open(io.BytesIO(removed_bg_data)).convert('RGBA')

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

        try:
            # Process image
            output_filename = process_image(input_path, DEFAULT_BACKGROUND)
            
            return jsonify({
                'success': True, 
                'output_path': f'static/{output_filename}',
                'download_path': f'download/{output_filename}'
            })

        finally:
            # Clean up input file
            if os.path.exists(input_path):
                os.remove(input_path)

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
    
"""
 This conditional block checks whether the current Python 
 file is being run directly as the main program or if it is being 
 imported as a module into another script.
"""
if __name__ == '__main__':
    app.run(debug=True)