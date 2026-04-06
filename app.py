from flask import Flask, request, jsonify, render_template, send_from_directory
import json
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max
DATA_FILE = 'data.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"target": 100, "entries": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

@app.route('/api/entry', methods=['POST'])
def add_entry():
    data = load_data()
    name = request.form.get('name', '').strip()
    tins = request.form.get('tins', '0')
    date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    note = request.form.get('note', '').strip()

    if not name:
        return jsonify({"error": "Name is required"}), 400
    try:
        tins = int(tins)
        if tins < 1:
            raise ValueError()
    except:
        return jsonify({"error": "Tins must be a positive number"}), 400

    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            image_filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    entry = {
        "id": uuid.uuid4().hex,
        "name": name,
        "tins": tins,
        "date": date,
        "note": note,
        "image": image_filename,
        "timestamp": datetime.now().isoformat()
    }
    data["entries"].append(entry)
    save_data(data)
    return jsonify({"success": True, "entry": entry})

@app.route('/api/target', methods=['POST'])
def set_target():
    data = load_data()
    try:
        target = int(request.json.get('target', 0))
        if target < 1:
            raise ValueError()
    except:
        return jsonify({"error": "Invalid target"}), 400
    data["target"] = target
    save_data(data)
    return jsonify({"success": True, "target": target})

@app.route('/api/entry/<entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    data = load_data()
    data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]
    save_data(data)
    return jsonify({"success": True})

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
