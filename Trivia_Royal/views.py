"""
Routes and views for the Trivia Royale Flask application.
"""

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from datetime import datetime, timedelta
import random
from Trivia_Royal import app

# In-memory storage
users = {}  # {ip: {'name': str, 'score': int, 'last_seen': datetime, 'banned': bool, 'is_king': bool}}
chat_messages = []  # [{'user': str, 'message': str, 'time': str}]
direct_messages = []  # [{'from': str, 'to': str, 'message': str, 'time': str}]
kick_votes = {}  # {target_user: [voter1, voter2]}

# Constants
ADMIN_CREDENTIALS = {'username': 'admin', 'password': 'secret123'}
ONLINE_THRESHOLD = timedelta(minutes=5)

class QuestionGenerator:
    @staticmethod
    def generate():
        qas = [
            ("What is the capital of France?", "Paris"),
            ("Which planet has the most moons?", "Saturn"),
            ("Who developed the theory of relativity?", "Einstein")
        ]
        return dict(zip(['question', 'answer'], random.choice(qas)))

def get_user_ip():
    return request.remote_addr or 'unknown'

def get_online_users():
    now = datetime.utcnow()
    return {
        ip: info for ip, info in users.items()
        if 'last_seen' in info and now - info['last_seen'] < ONLINE_THRESHOLD
    }

def normalize_answer(text):
    return ''.join(c.lower() for c in text if c.isalnum() or c.isspace()).strip()

def check_answer(submitted, correct):
    a = normalize_answer(submitted)
    b = normalize_answer(correct)
    return a == b or b in a or a in b or any(word in a.split() for word in b.split())

def get_leader():
    sorted_users = sorted(users.items(), key=lambda x: x[1].get('score', 0), reverse=True)
    return sorted_users[0][1]['name'] if sorted_users else None

@app.route('/')
@app.route('/trivia')
def trivia():
    ip = session.get('user_ip')
    if ip not in users:
        return redirect(url_for('register'))

    result = session.pop('last_result', None)
    q = QuestionGenerator.generate()
    session['current_question'] = q

    users[ip]['last_seen'] = datetime.utcnow()

    leader = get_leader()
    leaderboard = sorted(((v['name'], v['score']) for v in users.values()), key=lambda x: x[1], reverse=True)

    return render_template(
        'trivia.html',
        question=q['question'],
        name=users[ip]['name'],
        score=users[ip]['score'],
        result=result,
        leaderboard=leaderboard,
        is_king=users[ip].get('is_king', False),
        leader=leader
    )

@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    ip = session.get('user_ip')
    if ip not in users:
        return 'Unauthorized', 401

    submitted = request.form.get('answer', '').strip()
    current = session.get('current_question')
    if not current:
        session['last_result'] = "No active question."
        return redirect(url_for('trivia'))

    correct = current.get('answer', '').strip()
    if check_answer(submitted, correct):
        users[ip]['score'] += 1
        session['last_result'] = "✅ Correct!"
    else:
        session['last_result'] = f"❌ Incorrect! Answer was: {correct}"

    # Determine king/queen
    leader_ip = max(users, key=lambda k: users[k].get('score', 0))
    for u in users.values():
        u['is_king'] = False
    users[leader_ip]['is_king'] = True

    return redirect(url_for('trivia'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    ip = get_user_ip()
    if ip in users and users[ip].get('banned'):
        return "You are banned", 403

    if request.method == 'POST':
        name = request.form.get('name')
        session['is_admin'] = request.form.get('admin_user') == ADMIN_CREDENTIALS['username'] and request.form.get('admin_pass') == ADMIN_CREDENTIALS['password']

        if name:
            users[ip] = {
                'name': name,
                'score': 0,
                'last_seen': datetime.utcnow(),
                'is_king': False
            }
            session['user_ip'] = ip
            return redirect(url_for('trivia'))

    return render_template('register.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    ip = session.get('user_ip')
    name = users.get(ip, {}).get('name', 'Unknown')

    if request.method == 'POST':
        recipient = request.form.get('to')
        message = request.form.get('message')

        if message:
            msg = {'from': name, 'message': message, 'time': datetime.now().strftime('%H:%M:%S')}
            if recipient and recipient != 'All':
                msg['to'] = recipient
                direct_messages.append(msg)
            else:
                msg['user'] = name
                chat_messages.append(msg)

        return '', 204

    recent = chat_messages[-20:] + [m for m in direct_messages if m['from'] == name or m.get('to') == name][-20:]
    return jsonify(recent)

@app.route('/users')
def users_list():
    return jsonify([v['name'] for v in users.values()])

@app.route('/admin/online-users')
def online_users():
    if not session.get('is_admin') and not users.get(session.get('user_ip'), {}).get('is_king'):
        return jsonify([]), 403
    return jsonify(get_online_users())

@app.route('/admin/rename', methods=['POST'])
def rename():
    if not session.get('is_admin') and not users.get(session.get('user_ip'), {}).get('is_king'):
        return jsonify(success=False), 403
    ip = request.form['ip']
    new_name = request.form['new_name']
    if ip in users:
        users[ip]['name'] = new_name
        return jsonify(success=True)
    return jsonify(success=False), 404

@app.route('/admin/kick', methods=['POST'])
def kick():
    if not session.get('is_admin') and not users.get(session.get('user_ip'), {}).get('is_king'):
        return jsonify(success=False), 403
    ip = request.form['ip']
    if ip in users:
        del users[ip]
        return jsonify(success=True)
    return jsonify(success=False), 404

@app.route('/admin/ban', methods=['POST'])
def ban():
    if not session.get('is_admin') and not users.get(session.get('user_ip'), {}).get('is_king'):
        return jsonify(success=False), 403
    ip = request.form['ip']
    if ip in users:
        users[ip]['banned'] = True
        return jsonify(success=True)
    return jsonify(success=False), 404
