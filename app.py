from flask import Flask, request, jsonify, render_template
import os
import uuid
from datetime import datetime
import zoneinfo
import urllib.request
import urllib.error
import urllib.parse
import json as jsonlib
import hashlib
import hmac
import base64
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
CLOUDINARY_CLOUD = os.environ.get('CLOUDINARY_CLOUD', '')
CLOUDINARY_KEY = os.environ.get('CLOUDINARY_KEY', '')
CLOUDINARY_SECRET = os.environ.get('CLOUDINARY_SECRET', '')

def supabase_request(method, path, data=None):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    prefer = 'return=minimal' if method == 'PATCH' else 'return=representation'
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': prefer
    }
    body = jsonlib.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return jsonlib.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print(f"Supabase error {method} {path}: {e.read()}")
        return None

def upload_to_cloudinary(file_bytes, public_id):
    timestamp = str(int(time.time()))
    params = f"public_id={public_id}&timestamp={timestamp}"
    sig = hashlib.sha1(f"{params}{CLOUDINARY_SECRET}".encode()).hexdigest()

    boundary = uuid.uuid4().hex
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="upload"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'
    ).encode() + file_bytes + (
        f'\r\n--{boundary}\r\n'
        f'Content-Disposition: form-data; name="public_id"\r\n\r\n{public_id}\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="timestamp"\r\n\r\n{timestamp}\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="api_key"\r\n\r\n{CLOUDINARY_KEY}\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="signature"\r\n\r\n{sig}\r\n'
        f'--{boundary}--\r\n'
    ).encode()

    url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD}/image/upload"
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    try:
        with urllib.request.urlopen(req) as resp:
            result = jsonlib.loads(resp.read())
            return result.get('secure_url')
    except urllib.error.HTTPError as e:
        print(f"Cloudinary error: {e.read()}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    config = supabase_request('GET', "config?key=eq.target&select=value")
    target = int(config[0]['value']) if config else 100
    entries = supabase_request('GET', "entries?select=*&order=timestamp.desc")
    if entries is None:
        entries = []
    return jsonify({"target": target, "entries": entries})

@app.route('/api/entry', methods=['POST'])
def add_entry():
    name = request.form.get('name', '').strip()
    tins = request.form.get('tins', '0')
    date = request.form.get('date', datetime.now(zoneinfo.ZoneInfo('America/New_York')).strftime('%Y-%m-%d'))
    note = request.form.get('note', '').strip()
    tin_type = request.form.get('tin_type', '').strip()

    if not name:
        return jsonify({"error": "Name is required"}), 400
    try:
        tins = int(tins)
        if tins < 1:
            raise ValueError()
    except:
        return jsonify({"error": "Tins must be a positive number"}), 400

    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            file_bytes = file.read()
            public_id = f"tinpact/{uuid.uuid4().hex}"
            image_url = upload_to_cloudinary(file_bytes, public_id)

    entry = {
        "id": uuid.uuid4().hex,
        "name": name,
        "tins": tins,
        "date": date,
        "note": note,
        "tin_type": tin_type,
        "image": image_url,
        "timestamp": datetime.now().isoformat()
    }

    result = supabase_request('POST', 'entries', entry)
    if result is None:
        return jsonify({"error": "Failed to save entry"}), 500

    return jsonify({"success": True, "entry": entry})

@app.route('/api/target', methods=['POST'])
def set_target():
    if request.json.get('key') != 'fishtins':
        return jsonify({"error": "Unauthorized"}), 403
    try:
        target = int(request.json.get('target', 0))
        if target < 1:
            raise ValueError()
    except:
        return jsonify({"error": "Invalid target"}), 400

    result = supabase_request('PATCH', "config?key=eq.target", {"value": str(target)})
    if result is None:
        return jsonify({"error": "Failed to update target"}), 500
    return jsonify({"success": True, "target": target})

@app.route('/api/entry/<entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    supabase_request('DELETE', f"entries?id=eq.{entry_id}")
    return jsonify({"success": True})


@app.route('/api/entry/<entry_id>', methods=['PATCH'])
def edit_entry(entry_id):
    if request.json.get('key') != 'fishtins':
        return jsonify({"error": "Unauthorized"}), 403
    updates = {
        "name": request.json.get('name'),
        "tins": request.json.get('tins'),
        "date": request.json.get('date'),
        "note": request.json.get('note'),
        "tin_type": request.json.get('tin_type'),
    }
    updates = {k: v for k, v in updates.items() if v is not None}
    result = supabase_request('PATCH', f"entries?id=eq.{entry_id}", updates)
    if result is None:
        return jsonify({"error": "Failed to update entry"}), 500
    return jsonify({"success": True})



@app.route('/api/comment-counts', methods=['GET'])
def comment_counts():
    comments = supabase_request('GET', "comments?select=entry_id")
    if not comments:
        return jsonify({})
    counts = {}
    for c in comments:
        eid = c['entry_id']
        counts[eid] = counts.get(eid, 0) + 1
    return jsonify(counts)

@app.route('/api/entry/<entry_id>/comments', methods=['GET'])
def get_comments(entry_id):
    comments = supabase_request('GET', f"comments?entry_id=eq.{entry_id}&select=*&order=timestamp.asc")
    if comments is None:
        comments = []
    votes = supabase_request('GET', f"votes?comment_id=in.({','.join([c['id'] for c in comments]) if comments else 'null'})&select=*")
    if votes is None:
        votes = []
    return jsonify({"comments": comments, "votes": votes})

@app.route('/api/entry/<entry_id>/comments', methods=['POST'])
def add_comment(entry_id):
    data = request.json
    author = data.get('author', '').strip()
    body = data.get('body', '').strip()
    if not author or not body:
        return jsonify({"error": "Author and body required"}), 400
    comment = {
        "id": uuid.uuid4().hex,
        "entry_id": entry_id,
        "author": author,
        "body": body,
        "timestamp": datetime.now(zoneinfo.ZoneInfo('America/New_York')).isoformat()
    }
    result = supabase_request('POST', 'comments', comment)
    if result is None:
        return jsonify({"error": "Failed to save comment"}), 500
    return jsonify({"success": True, "comment": comment})

@app.route('/api/comments/<comment_id>', methods=['PATCH'])
def edit_comment(comment_id):
    body = request.json.get('body', '').strip()
    author = request.json.get('author', '').strip()
    if not body:
        return jsonify({"error": "Body required"}), 400
    result = supabase_request('PATCH', f"comments?id=eq.{comment_id}&author=eq.{urllib.parse.quote(author)}", {"body": body})
    return jsonify({"success": True})

@app.route('/api/comments/<comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    key = request.json.get('key', '') if request.json else ''
    author = request.json.get('author', '') if request.json else ''
    if key == 'fishtins':
        supabase_request('DELETE', f"comments?id=eq.{comment_id}")
    elif author:
        supabase_request('DELETE', f"comments?id=eq.{comment_id}&author=eq.{urllib.parse.quote(author)}")
    else:
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({"success": True})

@app.route('/api/votes', methods=['POST'])
def cast_vote():
    data = request.json
    comment_id = data.get('comment_id')
    voter = data.get('voter', '').strip()
    value = data.get('value')
    if not comment_id or not voter or value not in [1, -1]:
        return jsonify({"error": "Invalid vote"}), 400
    # Check existing vote
    existing = supabase_request('GET', f"votes?comment_id=eq.{comment_id}&voter=eq.{urllib.parse.quote(voter)}&select=*")
    if existing:
        if existing[0]['value'] == value:
            # Same vote - remove it
            supabase_request('DELETE', f"votes?comment_id=eq.{comment_id}&voter=eq.{urllib.parse.quote(voter)}")
            return jsonify({"success": True, "action": "removed"})
        else:
            # Different vote - update it
            supabase_request('PATCH', f"votes?comment_id=eq.{comment_id}&voter=eq.{urllib.parse.quote(voter)}", {"value": value})
            return jsonify({"success": True, "action": "updated"})
    else:
        vote = {
            "id": uuid.uuid4().hex,
            "comment_id": comment_id,
            "voter": voter,
            "value": value
        }
        supabase_request('POST', 'votes', vote)
        return jsonify({"success": True, "action": "added"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
