"""
Flask Server for PDF Extraction Application
Runs on port 8080
"""

import os
import tempfile
from flask import Flask, render_template, request, jsonify
from extractor import get_extractor

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size


@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_pdf():
    """Handle PDF upload and extraction"""
    
    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "error": "No file provided"
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            "success": False,
            "error": "No file selected"
        }), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({
            "success": False,
            "error": "File must be a PDF"
        }), 400
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        # Get the extractor and process
        extractor = get_extractor()
        result = extractor.extract_from_pdf(tmp_path)
        
        # Update filename with original name
        if result["success"] and result["data"]:
            result["data"]["docname"] = file.filename
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
        
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    print("Starting PDF Extraction Server on http://localhost:8080")
    print("Loading model on first request...")
    app.run(host='0.0.0.0', port=8080, debug=False)
