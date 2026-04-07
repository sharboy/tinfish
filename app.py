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

TWILIO_SID = os.environ.get('TWILIO_SID', '')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN', '')
TWILIO_FROM = os.environ.get('TWILIO_FROM', '')
TWILIO_RECIPIENTS = [
    '+18282347896',
    '+16094136151',
    '+15859054719',
    '+16036301144',
    '+12153014768',
]

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

import random as _random

TIN_LOGGED_MESSAGES = [
    "{name} just cracked open {n} tin{s} of {type}. The seas rejoice. 🐟",
    "BREAKING: {name} has consumed {n} tin{s} of {type}. Sources confirm it was delicious.",
    "{name} said 'not today, scurvy' and logged {n} tin{s} of {type}. Respect.",
    "The {type} didn't stand a chance. {name} — {n} tin{s} down.",
    "{name} is out here eating {type} like it's a personality. {n} tin{s} logged.",
    "Tin Pact update: {name} ate {n} tin{s} of {type} and felt absolutely no regret.",
    "{name} and {n} tin{s} of {type} walked so the rest of us could run.",
    "History will remember {name} for many things. Today, it's {n} tin{s} of {type}.",
    "{name} looked at a tin of {type}, looked at the goal, and said 'yes.' {n} tin{s} logged.",
    "The ocean called. {name} answered with {n} tin{s} of {type}.",
    "{name} is officially {n} tin{s} of {type} closer to legend status.",
    "Alert: {name} has logged {n} tin{s} of {type}. The leaderboard has been notified.",
    "{name} didn't wake up to play games. {n} tin{s} of {type}, logged and dusted.",
    "Somewhere, a fisherman is smiling because {name} just ate {n} tin{s} of {type}.",
    "{name}: 1. Hunger: 0. Tin{s} of {type}: consumed ({n}).",
    "Just in: {name} put away {n} tin{s} of {type} like it was nothing. Iconic.",
    "{name} has entered the chat with {n} tin{s} of {type}. The group is shaking.",
    "The {type} are gone. {name} took {n} tin{s}. No survivors.",
    "{name} is eating {type} like the fate of the group depends on it. {n} tin{s} logged.",
    "Scientists baffled as {name} logs {n} tin{s} of {type} with zero hesitation.",
    "{n} tin{s} of {type}. {name}. That's the whole message.",
    "{name} said grace, opened {n} tin{s} of {type}, and became a hero.",
    "Tin Pact dispatch: {name} has done the thing. {n} {type} tin{s}. We are proud.",
    "{name} smelled the {type}, felt the call, answered with {n} tin{s}.",
    "Not all heroes wear capes. Some eat {n} tin{s} of {type}. Hi {name}.",
    "{name} just quietly logged {n} tin{s} of {type} like an absolute professional.",
    "The numbers are in. {name}: {n} tin{s} of {type}. Competitors: shaking.",
    "{name} woke up and chose {type}. {n} tin{s}. No notes.",
    "Tin Pact: {name} has answered the call of the sea. {n} {type} tin{s} eaten.",
    "{name} did not come to the table to play. {n} tin{s} of {type}, filed and logged.",
    "A moment of appreciation for {name}, who just ate {n} tin{s} of {type}.",
    "{name} looked at the goal and said 'I got this.' {n} tin{s} of {type} prove it.",
    "The {type} population has decreased by {n} tin{s}, courtesy of {name}.",
    "{name}: fueled by {type}, logging tin{s} ({n}), unstoppable.",
    "Certified tin eater {name} has logged {n} more {type} tin{s}. The throne is theirs.",
    "{name} ate {n} tin{s} of {type} and didn't even blink. Cold blooded.",
    "Every great journey begins with a single tin. {name} is on tin{s} {n} (of {type}).",
    "{name} is giving {type} a moment in the spotlight. {n} tin{s} consumed.",
    "The leaderboard trembles. {name} has logged {n} tin{s} of {type}.",
    "Tin Pact news flash: {name} is eating {type} and not stopping. {n} tin{s} in.",
    "{name} just made the ocean proud. {n} {type} tin{s}, logged with authority.",
    "Nobody does it quite like {name}. {n} tin{s} of {type}. Just like that.",
    "{name} has filed {n} tin{s} of {type} with the Tin Pact authorities. Accepted.",
    "We interrupt your day to report: {name} ate {n} tin{s} of {type}. You're welcome.",
    "{name} opened the tin, ate the fish, logged the entry. A hero's journey in three acts.",
    "Tin Pact: {name} showing the group how it's done. {n} {type} tin{s} and counting.",
    "{name} took one look at the goal and said 'not on my watch.' {n} {type} tin{s}.",
    "The {type} never had a chance. {name} logged {n} tin{s} before breakfast.",
    "{name} is out here providing for the whole group. {n} tin{s} of {type}. Legend.",
    "Tin Pact bulletin: {name} ate {n} tin{s} of {type}. The group's morale is high.",
    "{name} and {type}: a love story. Chapter {n}.",
    "Fresh log from {name}: {n} tin{s} of {type}. The ancestors are pleased.",
    "{name} channeled their inner sailor and devoured {n} tin{s} of {type}.",
    "It's giving dedication. It's giving {type}. It's {name} with {n} tin{s}.",
    "{name} just ate {n} tin{s} of {type} and the whole group felt it.",
    "Tin Pact HQ reporting: {name} has submitted {n} tin{s} of {type} for review. Approved.",
    "{name} didn't ask for permission. Just ate {n} tin{s} of {type} and logged it.",
    "The sea provides. {name} receives. {n} tin{s} of {type}, logged.",
    "{name} is what peak performance looks like. {n} {type} tin{s}. Period.",
    "Nobody told {name} to eat {n} tin{s} of {type}. They just knew.",
    "Tin Pact: {name} has entered {n} tin{s} of {type} into the record books.",
    "{name} is built different. {n} tin{s} of {type} before you even knew they started.",
    "The {type} understood the assignment. So did {name}. {n} tin{s}.",
    "{name} said 'I will eat this fish and I will enjoy it.' {n} {type} tin{s} later, done.",
    "Certified moment: {name} logging {n} tin{s} of {type} like it's muscle memory.",
    "{name} just put {n} tin{s} of {type} on the board. Your move, group.",
    "Tin Pact update: {name} ate {n} tin{s} of {type}. The fish did not die in vain.",
    "{name} is locked in. {n} tin{s} of {type} don't lie.",
    "We asked for effort. {name} delivered {n} tin{s} of {type}. Exceeds expectations.",
    "{name}: quietly eating {type}, loudly winning. {n} tin{s} logged.",
    "Tin Pact: {name} has gone full maritime. {n} tin{s} of {type} consumed.",
    "In a world of excuses, {name} ate {n} tin{s} of {type}. Be like {name}.",
    "{name} smashed {n} tin{s} of {type} and didn't even gloat. Class act.",
    "The {type} is gone. {name} has {n} tin{s} to show for it.",
    "{name} treating the Tin Pact goal like a personal mission. {n} {type} tin{s}.",
    "Tin Pact: {name} has spoken. {n} tin{s} of {type}. The log is updated.",
    "{name} is the reason we can't have nice things. Just kidding. {n} {type} tin{s}. Amazing.",
    "{name} logged {n} tin{s} of {type} and the algorithm blessed the group.",
    "Tin Pact correspondent here: {name} ate {n} tin{s} of {type}. More at 11.",
    "{name} is not messing around. {n} tin{s} of {type}, logged and sealed.",
    "Today's MVP: {name}. Today's protein source: {type}. Tins eaten: {n}.",
    "{name} is fueling up on {type} and dragging this group to 200. {n} tin{s} in.",
    "Tin Pact: {name} did the thing again. {n} more {type} tin{s}. Respect.",
    "{name} ate {n} tin{s} of {type} and the whole Tin Pact felt a disturbance in the force.",
    "Plot twist: {name} was eating {type} this whole time. {n} tin{s} logged.",
    "{name} brought the energy, brought the fork, and brought {n} tin{s} of {type}.",
    "The ocean has a new champion. Their name is {name}. Their fuel: {type}. Tins: {n}.",
    "{name} is making the rest of us look bad and we are here for it. {n} {type} tin{s}.",
    "Log submitted. {name}. {n} tin{s}. {type}. No further questions.",
    "{name} just ate {n} tin{s} of {type} and the group's collective total just jumped.",
    "Tin Pact verified: {name} consumed {n} tin{s} of {type}. Outstanding work.",
    "The {type} arrived. {name} conquered. {n} tin{s} logged.",
    "{name} is giving the goal no choice. {n} more {type} tin{s} in the books.",
    "Tin Pact: {name} is not here to make friends. They're here to eat {type}. {n} tin{s}.",
    "{name} logged {n} tin{s} of {type} and didn't even need a round of applause. But here it is. 👏",
    "The tin is open. The fish is eaten. The log is filed. {name}. {n} {type} tin{s}.",
    "{name} ate {n} tin{s} of {type} and all we can say is: carry on.",
    "Tin Pact: {name} has done their part. {n} tin{s} of {type}. The group thanks you.",
]

SLACKER_MESSAGES = [
    "{name} hasn't logged a tin in {days} days. The fish are confused. Are you okay?",
    "{days} days. No tins from {name}. The leaderboard has a {name}-shaped hole in it.",
    "{name}, it's been {days} days. The sardines are starting to think you don't like them.",
    "Reminder: {name} hasn't eaten a tin in {days} days. This is not a drill.",
    "{days} days of silence from {name}. The group is concerned. The fish are concerned. We're all concerned.",
    "{name}. {days} days. No tins. What are we doing here?",
    "The Tin Pact would like to remind {name} that it has been {days} days since their last contribution. Ahem.",
    "{name} has gone {days} days without a tin. The goal is not going to hit itself.",
    "Missing: {name}'s tin logs. Last seen {days} days ago. If found, please return to the leaderboard.",
    "{days} days tin-free. {name}, the group needs you. The fish need you.",
    "{name}, {days} days without a tin is a choice. A bad one, but a choice.",
    "The Tin Pact officially reports {name} AWOL for {days} days. Come back.",
    "{name} hasn't logged in {days} days. Meanwhile, the goal isn't getting any closer.",
    "Day {days} of waiting for {name} to eat a tin. We remain hopeful. Barely.",
    "{name}: {days} days without a tin. The mackerel are personally offended.",
    "Fun fact: {name} has not eaten a tin in {days} days. Unfun fact: that's too long.",
    "{days} days, {name}. The tins are just sitting there. They're not going to eat themselves.",
    "We have not heard from {name}'s fork in {days} days. Send help. Send tins.",
    "{name} has been tin-absent for {days} days. The leaderboard misses you. Sort of.",
    "Tin Pact audit: {name} — {days} days of zero contributions. The board is not pleased.",
    "{name}, {days} days is a long time to go without a tin. Just saying.",
    "The ocean is vast. The tins are plentiful. {name} has eaten zero in {days} days. Tragic.",
    "{days} days. No tins. No excuses, {name}. Get back in the game.",
    "{name} went {days} days without logging a tin. A fish somewhere is breathing a sigh of relief. Don't let it.",
    "Tin Pact: {name} has been missing from the tin logs for {days} days. We see you. We're watching.",
    "{name}, the group carried you for {days} days. Time to carry yourself. Eat a tin.",
    "{days} days of silence from {name}. The anchovies are throwing a party. Shut it down.",
    "Just a reminder that {name} has logged zero tins in {days} days. Just a reminder.",
    "{name}: {days} days without a tin. The leaderboard is side-eyeing you.",
    "Tin Pact to {name}: it's been {days} days. The tins aren't going to eat themselves. Neither are you, apparently.",
    "{days} days. {name}. No tins. This is your intervention.",
    "{name} has gone dark for {days} days. The tin tracker has noticed. We've all noticed.",
    "Breaking: {name} still hasn't logged a tin. This has been going on for {days} days now.",
    "{name}, {days} days is a long vacation from tins. Time to come home.",
    "The Tin Pact misses {name}'s contributions. Specifically their tins. It's been {days} days.",
    "{days} days since {name} last logged. The herring are getting comfortable. Don't let them.",
    "{name} is currently on a {days}-day tin strike. Management is not impressed.",
    "Tin Pact correspondent: {name} has eaten exactly zero tins in {days} days. Developing story.",
    "{name}: we get it, life is busy. But it's been {days} days. Open a tin. Please.",
    "The group has been covering for {name} for {days} days. It's time to pull your weight. In tins.",
    "{days} days without a tin from {name}. The goal is sad. We're all sad.",
    "{name} has been MIA from the tin front for {days} days. Return to base immediately.",
    "Tin Pact: {name} logged their last tin {days} days ago. The memory fades.",
    "{name}, even a single sardine would make the group feel better. {days} days is too long.",
    "Somewhere a tin of {name}'s name on it has been waiting {days} days. Collect it.",
    "{days} days of nothing from {name}. The tins are patient. The group is less so.",
    "Official notice: {name} has been tin-delinquent for {days} days. Shape up.",
    "{name}: {days} days. The ocean does not sleep. Neither does the Tin Pact.",
    "Tin Pact reminder: {name} hasn't logged in {days} days. This affects all of us.",
    "Day {days}. Still no tins from {name}. The saga continues. Disappointingly.",
    "{name} took a {days}-day break from tins. The break is over. Time to eat.",
    "{days} days, {name}. That's how long you've been letting the group down. Fix it.",
    "Tin Pact: {name} — {days} days without a log. The fish are laughing. Stop letting fish laugh.",
    "{name}, the goal won't hit 200 on its own. {days} days of no tins is not helping.",
    "Gentle reminder: {name} hasn't opened a tin in {days} days. Less gentle: eat a tin now.",
    "Tin Pact audit complete. {name}: {days} days of absence. Grade: incomplete.",
    "{days} days. {name}. The tins are right there. We've checked. They're there.",
    "{name} has been dormant for {days} days. Wake up. Eat a tin. Log it.",
    "The group is at {days} days without a {name} sighting in the tin logs. Reward offered.",
    "{name}: {days} days since your last tin. The leaderboard has moved on. Come back.",
    "Tin Pact official: {name} — {days} days AWOL. The anchovies are not pleased.",
    "{days} days of no tins from {name}. The goal needs heroes. Be a hero.",
    "{name} has been avoiding tins for {days} days. It's getting obvious.",
    "Tin Pact: {name} hasn't contributed in {days} days. The group chat has been too polite to say something. We are not.",
    "{days} days, {name}. Open the app. Open a tin. Log it. It takes 30 seconds.",
    "{name}: last seen eating a tin {days} days ago. Current status: unknown. Tin status: uneaten.",
    "Tin Pact dispatch: {name} is {days} days deep into a tin drought. End it.",
    "{days} days of silence from {name}. The tins are piling up. Unopened. Waiting.",
    "{name} went {days} days without logging. The sardines filed a missing persons report.",
    "Tin Pact: {days} days since {name} last ate a tin. We're not angry. We're disappointed.",
    "{name}, the {days}-day tin gap ends today. Eat something from the sea.",
    "Nobody panic but {name} hasn't logged a tin in {days} days. Okay, panic a little.",
    "{days} days of nothing, {name}. The leaderboard has a you-sized hole in it.",
    "Tin Pact: {name} has been quiet for {days} days. Too quiet. Eat a tin.",
    "{name}: {days} days without a tin is {days} days too many. You know what to do.",
    "The Tin Pact formally requests {name}'s return from their {days}-day tin sabbatical.",
    "{days} days, {name}. The group marches on. Will you march with them? Into the tins?",
    "Tin Pact: {name} has logged zero tins in {days} days. Zero. The number zero.",
    "{name} has been off the grid for {days} days. The grid is made of tins. Come back.",
    "It's been {days} days since {name} logged a tin. The fish are organizing.",
    "{name}: {days} days. We're not keeping score. Actually we are. That's the whole app.",
    "Tin Pact update: {name} — {days} days absent. The leaderboard weeps.",
    "{days} days since {name} last showed up in the tin logs. The group has noticed.",
    "{name} has taken a {days}-day hiatus from tins. The hiatus is now over. Eat.",
    "Tin Pact: {name} — missing from the logs for {days} days. Last seen near a tin aisle.",
    "{days} days without a log from {name}. The group carries on. Barely.",
    "Tin Pact HQ to {name}: it's been {days} days. We're going to need you to eat a tin.",
    "{name}: {days} days of no tins. The goal isn't going anywhere. Neither are we.",
    "{days} days, {name}. Somewhere a tin is unopened because of you. Think about that.",
    "Tin Pact: {name} has gone {days} days without logging. The intervention begins now.",
    "{name}, the group has been patient for {days} days. Patience is running low. Tins should not.",
    "{days} days since {name} ate a tin. The mackerel are writing a memoir about it.",
    "Tin Pact: official {days}-day notice to {name}. Eat. A. Tin.",
    "{name} hasn't logged in {days} days. The goal has {days} fewer tins because of this.",
    "Day {days} of the {name} tin drought. The group refuses to give up hope.",
    "{name}: {days} days of inactivity detected. Suggested action: eat a tin immediately.",
    "Tin Pact: {name} — {days} days without a tin. The fish are waiting. So are we.",
    "{days} days, {name}. That's a lot of missed tins. Start with one. Just one.",
    "Tin Pact reminder {days}: {name}, the tins miss you. Come home.",
]

def send_tin_sms(name, tins, tin_type, date):
    if not TWILIO_SID or not TWILIO_TOKEN or not TWILIO_FROM:
        return
    tin_s = 's' if tins != 1 else ''
    type_str = tin_type if tin_type else 'tinned fish'
    # Pick a message seeded on name+tins for variety
    seed = sum(ord(c) for c in name) + tins + len(type_str)
    msg_template = TIN_LOGGED_MESSAGES[seed % len(TIN_LOGGED_MESSAGES)]
    msg = msg_template.format(name=name, n=tins, s=tin_s, type=type_str)
    msg += " Reply STOP to opt out."
    _send_sms_to_all(msg)

def send_slacker_sms(name, days):
    if not TWILIO_SID or not TWILIO_TOKEN or not TWILIO_FROM:
        return
    seed = sum(ord(c) for c in name) + days
    msg_template = SLACKER_MESSAGES[seed % len(SLACKER_MESSAGES)]
    msg = msg_template.format(name=name, days=days)
    msg += " Reply STOP to opt out."
    _send_sms_to_all(msg)

def _send_sms_to_all(msg):
    auth = base64.b64encode(f"{TWILIO_SID}:{TWILIO_TOKEN}".encode()).decode()
    print(f"SMS: attempting to send to {len(TWILIO_RECIPIENTS)} recipients")
    print(f"SMS: from={TWILIO_FROM}, sid={TWILIO_SID[:8]}...")
    for number in TWILIO_RECIPIENTS:
        try:
            data = urllib.parse.urlencode({
                'From': TWILIO_FROM,
                'To': number,
                'Body': msg
            }).encode()
            req = urllib.request.Request(
                f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
                data=data,
                headers={
                    'Authorization': f'Basic {auth}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                method='POST'
            )
            with urllib.request.urlopen(req) as resp:
                result = jsonlib.loads(resp.read())
                print(f"SMS sent to {number}: sid={result.get('sid')}, status={result.get('status')}")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"SMS HTTP error to {number}: {e.code} {error_body}")
        except Exception as e:
            print(f"SMS error to {number}: {e}")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/terms')
def terms():
    return render_template('terms.html')

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

    # Send SMS notifications (non-blocking)
    try:
        send_tin_sms(name, tins, tin_type, date)
    except Exception as e:
        print(f"SMS notification error: {e}")

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


@app.route('/api/entry/<entry_id>/reactions', methods=['GET'])
def get_reactions(entry_id):
    reactions = supabase_request('GET', f"reactions?entry_id=eq.{entry_id}&select=*")
    if reactions is None:
        reactions = []
    return jsonify({"reactions": reactions})

@app.route('/api/entry/<entry_id>/reactions', methods=['POST'])
def toggle_reaction(entry_id):
    data = request.json
    reactor = data.get('reactor', '').strip()
    emoji = data.get('emoji', '').strip()
    if not reactor or not emoji:
        return jsonify({"error": "Reactor and emoji required"}), 400
    
    # Check if reaction already exists
    existing = supabase_request('GET', f"reactions?entry_id=eq.{entry_id}&reactor=eq.{urllib.parse.quote(reactor)}&emoji=eq.{urllib.parse.quote(emoji)}&select=*")
    if existing:
        # Remove it (toggle off)
        supabase_request('DELETE', f"reactions?entry_id=eq.{entry_id}&reactor=eq.{urllib.parse.quote(reactor)}&emoji=eq.{urllib.parse.quote(emoji)}")
        return jsonify({"success": True, "action": "removed"})
    else:
        # Add it
        reaction = {
            "id": uuid.uuid4().hex,
            "entry_id": entry_id,
            "reactor": reactor,
            "emoji": emoji
        }
        supabase_request('POST', 'reactions', reaction)
        return jsonify({"success": True, "action": "added"})

@app.route('/api/reaction-counts', methods=['GET'])
def reaction_counts():
    reactions = supabase_request('GET', "reactions?select=entry_id,emoji,reactor")
    if not reactions:
        return jsonify({})
    # Build map: entry_id -> {emoji -> [reactors]}
    counts = {}
    for r in reactions:
        eid = r['entry_id']
        emoji = r['emoji']
        reactor = r['reactor']
        if eid not in counts:
            counts[eid] = {}
        if emoji not in counts[eid]:
            counts[eid][emoji] = []
        counts[eid][emoji].append(reactor)
    return jsonify(counts)

@app.route('/api/slacker-check', methods=['POST'])
def slacker_check():
    # Protected endpoint - only callable with admin key
    if request.json.get('key') != 'fishtins':
        return jsonify({"error": "Unauthorized"}), 403
    
    entries = supabase_request('GET', "entries?select=name,date&order=date.desc")
    if not entries:
        return jsonify({"checked": 0})
    
    # Find last log date per person
    from datetime import date as _date, timedelta
    today = _date.today()
    last_logged = {}
    for e in entries:
        n = e['name']
        if n not in last_logged:
            last_logged[n] = e['date']
    
    called_out = []
    for name, last_date in last_logged.items():
        try:
            d = _date.fromisoformat(last_date)
            days_ago = (today - d).days
            if days_ago >= 2:
                send_slacker_sms(name, days_ago)
                called_out.append({"name": name, "days": days_ago})
        except Exception as ex:
            print(f"Slacker check error for {name}: {ex}")
    
    return jsonify({"checked": len(last_logged), "called_out": called_out})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
