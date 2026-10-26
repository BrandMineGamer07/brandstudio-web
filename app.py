from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import string
import json
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')

def get_db_path():
    if os.environ.get('VERCEL'):
        tmp_db = '/tmp/database.db'
        original_db = os.path.join(BASE_DIR, 'database.db')
        if not os.path.exists(tmp_db) and os.path.exists(original_db):
            try:
                shutil.copy2(original_db, tmp_db)
            except Exception:
                pass
        return tmp_db
    return os.path.join(BASE_DIR, 'database.db')

def get_db():
    return sqlite3.connect(get_db_path())

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            items TEXT,
            total_price TEXT,
            requirements TEXT,
            status TEXT,
            created_at TEXT,
            messages TEXT DEFAULT '[]'
        )
    ''')
    
    # Safely add messages column if it doesn't exist
    try:
        c.execute("ALTER TABLE tickets ADD COLUMN messages TEXT DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    # Ensure any NULL messages are initialized to '[]'
    c.execute("UPDATE tickets SET messages = '[]' WHERE messages IS NULL OR messages = ''")

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            recovery_code TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def generate_recovery_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# Prevent browser from aggressively caching HTML files
@app.after_request
def add_header(response):
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/')
@app.route('/api/index')
@app.route('/index')
@app.route('/index.html')
def home():
    if os.path.exists(os.path.join(BASE_DIR, 'index.html')):
        return app.send_static_file('index.html')
    return app.send_static_file('index (4).html')

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('icon.png')

@app.route('/<path:path>')
def serve_file(path):
    if path in ['api/index', 'index', 'index.html', '']:
        return home()
    return app.send_static_file(path)

# --- AUTH API ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"}), 400
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
    if c.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Email already registered"}), 400
    hashed_pw = generate_password_hash(password)
    recovery_code = generate_recovery_code()
    c.execute("INSERT INTO users (email, password, recovery_code) VALUES (?, ?, ?)", (email, hashed_pw, recovery_code))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "recovery_code": recovery_code, "message": "Registered successfully!"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT password, email FROM users WHERE LOWER(email) = ?", (email,))
    row = c.fetchone()
    conn.close()
    if row and check_password_hash(row[0], password):
        return jsonify({"success": True, "email": row[1], "message": "Login successful!"})
    return jsonify({"success": False, "message": "Invalid email or password"}), 401

@app.route('/api/recover', methods=['POST'])
def recover():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    code = data.get('recovery_code', '').strip().upper()
    new_password = data.get('new_password', '').strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT recovery_code FROM users WHERE LOWER(email) = ?", (email,))
    row = c.fetchone()
    if row and row[0].upper() == code:
        new_hashed = generate_password_hash(new_password)
        c.execute("UPDATE users SET password = ? WHERE LOWER(email) = ?", (new_hashed, email))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Password reset successfully!"})
    conn.close()
    return jsonify({"success": False, "message": "Invalid email or recovery code"}), 401

# --- TICKETS API ---
@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    data = request.json or {}
    user = data.get('user', 'Guest')
    items = data.get('items', 'General Order')
    total_price = data.get('total_price', '₹0')
    reqs = data.get('requirements', '')
    date_str = datetime.now().strftime("%b %d, %Y - %I:%M %p")
    
    initial_messages = json.dumps([
        {"sender": "System", "text": f"Ticket created for: {items}.", "time": date_str},
        {"sender": "Staff", "text": "Hello! Thank you for reaching out to Brand Studio. Our team is reviewing your requirements.", "time": date_str}
    ])
    
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO tickets (user, items, total_price, requirements, status, created_at, messages) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (user, items, total_price, reqs, 'PENDING', date_str, initial_messages))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return jsonify({"success": True, "ticket_id": new_id, "message": "Ticket created successfully!"})

@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    user = request.args.get('email')
    conn = get_db()
    c = conn.cursor()
    if user:
        c.execute('SELECT * FROM tickets WHERE LOWER(user) = LOWER(?) ORDER BY id DESC', (user.strip(),))
    else:
        c.execute('SELECT * FROM tickets ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    
    tickets = []
    for r in rows:
        try:
            msgs = json.loads(r[7]) if r[7] else []
        except Exception:
            msgs = []
        tickets.append({
            "id": r[0], "user": r[1], "items": r[2], "total_price": r[3], 
            "requirements": r[4], "status": r[5], "created_at": r[6], "messages": msgs
        })
    return jsonify(tickets)

@app.route('/api/tickets/<int:ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    data = request.json or {}
    new_status = data.get('status')
    if new_status:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE tickets SET status = ? WHERE id = ?', (new_status, ticket_id))
        conn.commit()
        conn.close()
    return jsonify({"success": True})

@app.route('/api/tickets/<int:ticket_id>/message', methods=['POST'])
def add_message(ticket_id):
    data = request.json or {}
    sender = data.get('sender', 'User')
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"success": False, "message": "Message text cannot be empty"}), 400
        
    date_str = datetime.now().strftime("%b %d, %I:%M %p")
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT messages FROM tickets WHERE id = ?', (ticket_id,))
    row = c.fetchone()
    if row:
        try:
            msgs = json.loads(row[0]) if row[0] else []
        except Exception:
            msgs = []
        msgs.append({"sender": sender, "text": text, "time": date_str})
        c.execute('UPDATE tickets SET messages = ? WHERE id = ?', (json.dumps(msgs), ticket_id))
        conn.commit()
    conn.close()
    return jsonify({"success": True})

# --- PRICING API ---
DEFAULT_PRICING = {
    "mc_server": "₹450 / $5+",
    "mc_config": "₹99 / $1+",
    "discord_server": "₹199 / $2+",
    "roblox_game": "₹699 / $8+",
    "website": "₹199 / $2+",
    "mc_resource": "₹150 / $2+",
    "nitro_1": "₹50 / $0.5",
    "nitro_2": "₹90 / $0.9",
    "mcfa_1": "₹700 / $7",
    "mcfa_2": "₹1300 / $13",
    "yt_1m": "₹140 / $1.4",
    "amazon_1m": "₹150 / $1.5",
    "amazon_6m": "₹220 / $2.2",
    "spotify_1m": "₹130 / $1.3",
    "netflix_1m": "₹250 / $2.5",
    "crunchyroll_1m": "₹100 / $1"
}

@app.route('/api/pricing', methods=['GET'])
def get_pricing():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS site_pricing (key TEXT PRIMARY KEY, price TEXT)''')
    c.execute('SELECT key, price FROM site_pricing')
    saved = {r[0]: r[1] for r in c.fetchall()}
    conn.close()
    merged = {**DEFAULT_PRICING, **saved}
    return jsonify(merged)

@app.route('/api/pricing', methods=['POST'])
def update_pricing():
    data = request.json or {}
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS site_pricing (key TEXT PRIMARY KEY, price TEXT)''')
    for k, v in data.items():
        if k in DEFAULT_PRICING and str(v).strip():
            c.execute('INSERT OR REPLACE INTO site_pricing (key, price) VALUES (?, ?)', (k, str(v).strip()))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Pricing saved successfully!"})

if __name__ == '__main__':
    print("Brand Studio Server running on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
