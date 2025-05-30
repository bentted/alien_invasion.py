from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import time
import json
from stem.control import Controller

script_dir = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(script_dir, 'leaderboard.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DATABASE_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

sse_message_queue = []
chat_message_queue = []

SOCIAL_SCORE_FILE = os.path.join(script_dir, 'social_scores.json')
NEG_REPORTS_FILE = os.path.join(script_dir, 'neg_reports.json')
POS_REPORTS_FILE = os.path.join(script_dir, 'pos_reports.json')

social_scores = {}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    score = db.Column(db.Integer, nullable=False)
    banned = db.Column(db.Boolean, default=False, nullable=False)
    bonus_lives = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<Score {self.username}: {self.score} (Banned: {self.banned})>'

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Invalid data. Username and password are required.'}), 400

    username = data['username']
    password = data['password']

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists.'}), 400

    password_hash = generate_password_hash(password)
    new_user = User(username=username, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()

    social_scores[username] = 100

    return jsonify({'success': True, 'message': 'User registered successfully.'}), 201

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Invalid data. Username and password are required.'}), 400

    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid username or password.'}), 401

    return jsonify({'success': True, 'message': 'Login successful.'}), 200

@app.route('/api/scores', methods=['POST'])
def add_score():
    data = request.get_json()
    if not data or 'username' not in data or 'score' not in data:
        return jsonify({'error': 'Invalid data. Username and score are required.'}), 400

    username = data['username']
    score_value = data['score']
    message_to_send = None

    existing_score = Score.query.filter_by(username=username).first()

    if existing_score:
        if existing_score.banned:
            return jsonify({'error': 'User is banned. Cannot update score.'}), 403
        if score_value > existing_score.score:
            existing_score.score = score_value
            db.session.commit()
            message_to_send = json.dumps({"type": "leaderboard_update", "message": f"Score updated for {username} to {score_value}"})
            response_message = {'message': 'Score updated successfully'}
            status_code = 200
        else:
            response_message = {'message': 'Existing score is higher or equal. No update.'}
            status_code = 200
    else:
        new_score = Score(username=username, score=score_value)
        db.session.add(new_score)
        db.session.commit()
        message_to_send = json.dumps({"type": "leaderboard_update", "message": f"New score added for {username}: {score_value}"})
        response_message = {'message': 'Score added successfully'}
        status_code = 201

    if message_to_send:
        sse_message_queue.append(message_to_send)
        if len(sse_message_queue) > 20:
            sse_message_queue.pop(0)

    return jsonify(response_message), status_code

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    top_scores = Score.query.filter_by(banned=False).order_by(Score.score.desc()).limit(10).all()
    leaderboard = [{'username': score.username, 'score': score.score} for score in top_scores]
    return jsonify(leaderboard), 200

@app.route('/api/admin/users/<string:username>', methods=['DELETE'])
def admin_remove_user(username):
    user_score = Score.query.filter_by(username=username).first()
    if user_score:
        db.session.delete(user_score)
        db.session.commit()
        message_to_send = json.dumps({"type": "leaderboard_update", "message": f"User {username} removed by admin"})
        sse_message_queue.append(message_to_send)
        return jsonify({'message': f'User {username} removed successfully'}), 200
    else:
        return jsonify({'error': f'User {username} not found'}), 404

@app.route('/api/admin/users/<string:username>/score', methods=['PUT'])
def admin_edit_user_score(username):
    data = request.get_json()
    if not data or 'score' not in data:
        return jsonify({'error': 'Invalid data. Score is required.'}), 400
    
    new_score_value = data['score']
    if not isinstance(new_score_value, int):
        return jsonify({'error': 'Invalid score format. Must be an integer.'}), 400

    user_score = Score.query.filter_by(username=username).first()
    if user_score:
        user_score.score = new_score_value
        db.session.commit()
        message_to_send = json.dumps({"type": "leaderboard_update", "message": f"Score for {username} updated by admin to {new_score_value}"})
        sse_message_queue.append(message_to_send)
        return jsonify({'message': f'Score for user {username} updated to {new_score_value}'}), 200
    else:
        new_score = Score(username=username, score=new_score_value)
        db.session.add(new_score)
        db.session.commit()
        message_to_send = json.dumps({"type": "leaderboard_update", "message": f"New user {username} with score {new_score_value} added by admin"})
        sse_message_queue.append(message_to_send)
        return jsonify({'message': f'New user {username} added with score {new_score_value}'}), 201

@app.route('/api/admin/users/<string:username>/ban', methods=['PUT'])
def admin_ban_user(username):
    user_score = Score.query.filter_by(username=username).first()
    if user_score:
        user_score.banned = True
        db.session.commit()
        message_to_send = json.dumps({"type": "leaderboard_update", "message": f"User {username} banned by admin"})
        sse_message_queue.append(message_to_send)
        return jsonify({'message': f'User {username} has been banned'}), 200
    else:
        return jsonify({'error': f'User {username} not found'}), 404

@app.route('/api/admin/users/<string:username>/unban', methods=['PUT'])
def admin_unban_user(username):
    user_score = Score.query.filter_by(username=username).first()
    if user_score:
        user_score.banned = False
        db.session.commit()
        message_to_send = json.dumps({"type": "leaderboard_update", "message": f"User {username} unbanned by admin"})
        sse_message_queue.append(message_to_send)
        return jsonify({'message': f'User {username} has been unbanned'}), 200
    else:
        return jsonify({'error': f'User {username} not found'}), 404

@app.route('/api/chat', methods=['POST'])
def send_chat_message():
    data = request.get_json()
    if not data or 'username' not in data or 'message' not in data:
        return jsonify({'error': 'Invalid data. Username and message are required.'}), 400

    username = data['username']
    message = data['message']
    chat_message = json.dumps({"type": "chat_message", "username": username, "message": message})
    
    chat_message_queue.append(chat_message)
    if len(chat_message_queue) > 50:
        chat_message_queue.pop(0)

    sse_message_queue.append(chat_message)
    return jsonify({'message': 'Chat message sent successfully'}), 200

@app.route('/api/chat', methods=['GET'])
def get_chat_messages():
    messages = [json.loads(msg) for msg in chat_message_queue]
    return jsonify(messages), 200

@app.route('/stream') 
def stream():
    def event_stream():
        yield 'data: {{"type": "connection_ack", "message": "SSE connection established"}}\n\n'
        client_last_sent_index = len(sse_message_queue) 
        
        try:
            while True:
                if len(sse_message_queue) > client_last_sent_index:
                    for i in range(client_last_sent_index, len(sse_message_queue)):
                        yield f'data: {sse_message_queue[i]}\n\n'
                    client_last_sent_index = len(sse_message_queue)
                
                time.sleep(1)
        except GeneratorExit:
            print(f"Client disconnected from SSE stream.")
    
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

def setup_tor_hidden_service():
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="your_tor_control_password")
            response = controller.create_hidden_service(
                ports={80: 5000},
                key_type="NEW",
                key_content="ED25519-V3"
            )
            onion_address = response.service_id + ".onion"
            print(f"Tor hidden service is running at: {onion_address}")
            return onion_address
    except Exception as e:
        print(f"Error setting up Tor hidden service: {e}")
        return None

@app.route('/api/chat/report', methods=['POST'])
def report_user():
    data = request.get_json()
    if not data or 'username' not in data or 'type' not in data:
        return jsonify({'error': 'Invalid data. Username and type are required.'}), 400

    username = data['username']
    report_type = data['type']
    reporter = data.get('reporter', 'Anonymous')
    reason = data.get('reason', '')

    if username not in social_scores:
        social_scores[username] = 100

    if report_type == 'positive':
        social_scores[username] += 50
        report_entry = {
            'username': username,
            'reporter': reporter,
            'reason': reason,
            'timestamp': time.time()
        }
        with open(POS_REPORTS_FILE, 'a') as f:
            json.dump(report_entry, f)
            f.write('\n')
        response_message = {'message': f'Positive feedback recorded for {username}'}

        if social_scores[username] >= 500:
            user_score = Score.query.filter_by(username=username).first()
            if user_score:
                user_score.bonus_lives = 1
                db.session.commit()

    elif report_type == 'negative':
        social_scores[username] -= 25
        report_entry = {
            'username': username,
            'reporter': reporter,
            'reason': reason,
            'timestamp': time.time()
        }
        with open(NEG_REPORTS_FILE, 'a') as f:
            json.dump(report_entry, f)
            f.write('\n')
        response_message = {'message': f'Negative feedback recorded for {username}'}

        user_score = Score.query.filter_by(username=username).first()
        if user_score:
            user_score.bonus_lives = 0
            db.session.commit()

    else:
        return jsonify({'error': 'Invalid report type. Must be "positive" or "negative".'}), 400

    with open(SOCIAL_SCORE_FILE, 'w') as f:
        json.dump(social_scores, f)

    return jsonify(response_message), 200

@app.route('/api/social_scores', methods=['GET'])
def get_social_scores():
    return jsonify(social_scores), 200

@app.route('/api/admin/social_scores', methods=['GET'])
def admin_get_social_scores():
    return jsonify(social_scores), 200

@app.route('/api/penalty', methods=['GET'])
def get_user_penalty():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username is required.'}), 400

    if username not in social_scores:
        return jsonify({'penalty': 0}), 200

    negative_reports = 0
    try:
        with open(NEG_REPORTS_FILE, 'r') as f:
            for line in f:
                report = json.loads(line)
                if report['username'] == username:
                    negative_reports += 1
    except FileNotFoundError:
        pass

    penalty = negative_reports * 10
    return jsonify({'penalty': penalty}), 200

@app.route('/api/bonus', methods=['GET'])
def get_user_bonus():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username is required.'}), 400

    if username not in social_scores:
        return jsonify({'bonus': 0}), 200

    positive_reports = 0
    try:
        with open(POS_REPORTS_FILE, 'r') as f:
            for line in f:
                report = json.loads(line)
                if report['username'] == username:
                    positive_reports += 1
    except FileNotFoundError:
        pass

    bonus = positive_reports * 10
    return jsonify({'bonus': bonus}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    for report_file in [NEG_REPORTS_FILE, POS_REPORTS_FILE]:
        if not os.path.exists(report_file):
            with open(report_file, 'w') as f:
                pass

    onion_address = setup_tor_hidden_service()
    if onion_address:
        print(f"Server is accessible via Tor at: {onion_address}")
    else:
        print("Failed to set up Tor hidden service. Running server without Tor.")

    app.run(debug=True)
