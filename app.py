from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_session import Session
from pymongo import MongoClient, DESCENDING
from datetime import datetime
import uuid
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')
CORS(app)
bcrypt = Bcrypt(app)

# Session config
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# MongoDB config
client = MongoClient(os.environ.get('MONGO_URI', 'mongodb://mongo:27017/'))
db = client.vektorized
users_collection = db.users
printers_collection = db.printers
machine_status_collection = db.machine_status  # NEW collection for ruuvi status data

# --- Helper Functions ---
def current_user():
    user_id = session.get('user_id')
    return users_collection.find_one({"_id": user_id})

# --- Routes ---
@app.route('/')
def home():
    if not current_user():
        return redirect(url_for('signin_page'))
    return redirect(url_for('dashboard'))

@app.route('/signup_page', methods=['GET'])
def signup_page():
    return '''
    <h2>Signup</h2>
    <form method="post" action="/signup">
      Email: <input name="email" type="email" required><br>
      Password: <input name="password" type="password" required><br>
      <button type="submit">Sign Up</button>
    </form>
    '''

@app.route('/signin_page', methods=['GET'])
def signin_page():
    return '''
    <h2>Sign In</h2>
    <form method="post" action="/login">
      Email: <input name="email" type="email" required><br>
      Password: <input name="password" type="password" required><br>
      <button type="submit">Sign In</button>
    </form>
    '''

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form.get('email') or request.json.get('email')
    password = request.form.get('password') or request.json.get('password')

    if users_collection.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 400

    user_id = str(uuid.uuid4())
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    users_collection.insert_one({
        '_id': user_id,
        'email': email,
        'password': hashed_pw,
        'printers': []
    })
    session['user_id'] = user_id
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email') or request.json.get('email')
    password = request.form.get('password') or request.json.get('password')

    user = users_collection.find_one({"email": email})
    if user and bcrypt.check_password_hash(user['password'], password):
        session['user_id'] = user['_id']
        return redirect(url_for('dashboard'))

    return jsonify({"error": "Invalid email or password"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route('/dashboard', methods=['GET'])
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for('signin_page'))
    
    statuses = list(machine_status_collection.find({}).sort("timestamp", DESCENDING))
    record_count = len(statuses)
    
    return render_template("dashboard.html",
                           statuses=statuses,
                           record_count=record_count)

@app.route('/add_printer', methods=['POST'])
def add_printer():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    ruuvi_tag_id = data.get('ruuvi_tag_id')

    printer_id = str(uuid.uuid4())
    printer = {
        '_id': printer_id,
        'ruuvi_tag_id': ruuvi_tag_id,
        'name': data.get('name', f'Printer-{printer_id[:4]}')
    }
    printers_collection.insert_one(printer)
    users_collection.update_one(
        {'_id': user['_id']},
        {'$push': {'printers': printer}}
    )

    return jsonify({"message": "Printer added", "printer": printer})

@app.route('/update_status', methods=['PUT', 'POST'])
def update_status():
    data = request.json
    ruuvi_id = data.get('ruuvi_id')
    if not ruuvi_id:
        return jsonify({"error": "ruuvi_id is required"}), 400

    state = data.get('state')
    if state not in ['running', 'idle']:
        return jsonify({"error": "state must be 'running' or 'idle'"}), 400

    payload_field = data.get('payload', {})  # Capture the payload field

    record = {
        '_id': ruuvi_id,  # Use ruuvi_id as the primary key
        'ruuvi_id': ruuvi_id,
        'state': state,
        'payload': payload_field,
        'timestamp': datetime.utcnow()
    }
    
    # Upsert: update an existing document or insert a new one if it doesn't exist.
    result = machine_status_collection.replace_one({'_id': ruuvi_id}, record, upsert=True)
    
    # Log write details to the terminal with immediate flush.
    print(f"Upserted record into MongoDB: {record}", flush=True)
    
    return jsonify({"message": "Status updated", "record": record})

@app.route('/delete_all_data', methods=['GET', 'POST'])
def delete_all_data():
    result = machine_status_collection.delete_many({})
    print(f"Deleted {result.deleted_count} records from machine_status_collection.", flush=True)
    return jsonify({"message": "All data deleted", "deleted_count": result.deleted_count})

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)
