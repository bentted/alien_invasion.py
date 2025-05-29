from flask import Flask, request, jsonify, Response 
from flask_sqlalchemy import SQLAlchemy
import os
import time 
import json 

script_dir = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(script_dir, 'leaderboard.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DATABASE_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

sse_message_queue = [] 

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True) 
    score = db.Column(db.Integer, nullable=False)
    banned = db.Column(db.Boolean, default=False, nullable=False) 

    def __repr__(self):
        return f'<Score {self.username}: {self.score} (Banned: {self.banned})>'

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
