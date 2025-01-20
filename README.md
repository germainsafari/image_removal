# Portrait Background Replacer

A web application that automatically removes the background from portrait images and replaces it with a predefined background using AI-powered background removal.

## Features

- Upload portrait images through drag-and-drop or file selection
- AI-powered background removal using rembg
- Automatic background replacement with predefined image
- Progress indicator during processing
- Error handling for unsupported formats and failed operations
- Downloadable processed images
- Clean and responsive user interface

## Technical Stack

- Python 3.8+
- Flask (web framework)
- rembg (background removal)
- Pillow (image processing)
- HTML5/CSS3/JavaScript (frontend)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/portrait-background-replacer.git
cd portrait-background-replacer
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install requirements.txt
```

4. Add your default background:
- Place your desired background image in the `static` folder
- Name it `default_background.png`

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Upload a portrait image by either:
   - Dragging and dropping the image onto the upload area
   - Clicking the "Select File" button and choosing an image

4. Wait for the processing to complete

5. Download the processed image using the "Download" button

## Project Structure

```
portrait-background-replacer/
├── app.py                 # Main application file
├── static/               # Static files
│   └── default_background.jpg
├── templates/            # HTML templates
│   └── index.html
├── uploads/             # Temporary upload directory
├── outputs/             # Processed images directory
└── README.md            # Project documentation
```

## Error Handling

The application includes error handling for:
- Unsupported file formats
- File size limits
- Processing failures
- Server errors

## Limitations

- Maximum file size: 16MB
- Supported formats: PNG, JPG, JPEG
- Processing time depends on image size and server capacity

## License

This project is licensed under the MIT License - see the LICENSE file for details.