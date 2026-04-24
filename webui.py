import os
import json
import functools
from datetime import datetime

import bcrypt
from flask import Flask, Blueprint, request, jsonify, session, send_from_directory
from flask_cors import CORS

from cognitive_task_planner import (
    CognitiveTaskPlanner, Task, MentalEffort, UserState
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

CORS(app, supports_credentials=True)

DATA_ROOT = os.environ.get('DATA_DIR', '.')
USERS_FILE = os.path.join(DATA_ROOT, 'users.json')
DATA_DIR = os.path.join(DATA_ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')

api = Blueprint('api', __name__, url_prefix='/api')

# In-memory caches — eliminates repeated Volume I/O on every request.
# Safe with 1 Gunicorn worker + threads (single process, shared memory).
_users_cache: dict | None = None
_planner_cache: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_users() -> dict:
    global _users_cache
    if _users_cache is None:
        try:
            with open(USERS_FILE, 'r') as f:
                _users_cache = json.load(f)
        except FileNotFoundError:
            _users_cache = {}
    return _users_cache


def save_users(users: dict):
    global _users_cache
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)
    _users_cache = users


def get_planner(user_id: str) -> CognitiveTaskPlanner:
    if user_id not in _planner_cache:
        planner = CognitiveTaskPlanner()
        state_path = os.path.join(DATA_DIR, f'{user_id}.json')
        if os.path.exists(state_path):
            planner.load_state(state_path)
        _planner_cache[user_id] = planner
    return _planner_cache[user_id]


def save_planner(planner: CognitiveTaskPlanner, user_id: str):
    planner.save_state(os.path.join(DATA_DIR, f'{user_id}.json'))
    _planner_cache[user_id] = planner


def parse_tasks(task_list: list) -> list[Task]:
    tasks = []
    for t in task_list:
        effort_str = t.get('effort', '')
        try:
            effort = MentalEffort[effort_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid effort value '{effort_str}'. Must be LOW, MEDIUM, or HIGH.")
        tasks.append(Task(
            name=t.get('name', ''),
            mental_effort=effort,
            duration_minutes=int(t.get('duration', 0)),
        ))
    return tasks


def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        return fn(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@api.route('/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    confirm = data.get('confirm_password') or ''

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    if password != confirm:
        return jsonify({'error': 'Passwords do not match'}), 400

    users = load_users()
    if username in users:
        return jsonify({'error': 'Username already taken'}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[username] = hashed
    save_users(users)

    session['user'] = username
    return jsonify({'message': 'Account created', 'username': username}), 201


@api.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    users = load_users()
    stored_hash = users.get(username)
    if not stored_hash or not bcrypt.checkpw(password.encode(), stored_hash.encode()):
        return jsonify({'error': 'Invalid username or password'}), 401

    session['user'] = username
    return jsonify({'message': 'Logged in', 'username': username})


@api.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

HOURS_BASE   = {'1-2': 7.0, '3-4': 8.5, '5+': 12.0}
TENDENCY_ADJ = {'over': -1.5, 'right': 0.0, 'under': 0.5}
SCHEDULE_ADJ = {'light': 1.0, 'moderate': 0.0, 'heavy': -1.5}
DEFAULT_LIMIT = 8.5

@api.route('/onboarding', methods=['POST'])
@login_required
def onboarding():
    data = request.get_json(force=True)

    if data.get('skip'):
        starting_limit = DEFAULT_LIMIT
    else:
        hours    = data.get('hours', '3-4')
        tendency = data.get('tendency', 'right')
        schedule = data.get('schedule', 'moderate')
        starting_limit = (
            HOURS_BASE.get(hours, 7.0)
            + TENDENCY_ADJ.get(tendency, 0.0)
            + SCHEDULE_ADJ.get(schedule, 0.0)
        )

    planner = get_planner(session['user'])
    planner.capacity_learner.current_limit = starting_limit
    planner.capacity_learner.limit_set_date = datetime.now()
    save_planner(planner, session['user'])

    return jsonify({'starting_limit': starting_limit})


# ---------------------------------------------------------------------------
# Planner endpoints
# ---------------------------------------------------------------------------

@api.route('/plan', methods=['POST'])
@login_required
def plan():
    data = request.get_json(force=True)
    try:
        tasks = parse_tasks(data.get('tasks') or [])
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    planner = get_planner(session['user'])
    try:
        result = planner.plan_day(tasks)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    return jsonify(result)


@api.route('/plan/commit', methods=['POST'])
@login_required
def commit_plan():
    data = request.get_json(force=True)
    planner = get_planner(session['user'])
    now = datetime.now()
    planner.today_plan = {
        'date': now.strftime('%Y-%m-%d'),
        'tasks': data.get('tasks', []),
        'planned_load': (data.get('analysis') or {}).get('daily_load'),
        'analysis': data.get('analysis'),
        'committed_at': now.isoformat(),
    }
    planner.log_committed_plan(now)
    save_planner(planner, session['user'])
    return jsonify({'ok': True})


@api.route('/plan/today', methods=['GET'])
@login_required
def today_plan():
    planner = get_planner(session['user'])
    p = planner.today_plan
    if p and p.get('date') == datetime.now().strftime('%Y-%m-%d'):
        return jsonify(p)
    return jsonify(None)


@api.route('/record', methods=['POST'])
@login_required
def record():
    data = request.get_json(force=True)
    planner = get_planner(session['user'])
    today = datetime.now().strftime('%Y-%m-%d')
    p = planner.today_plan

    try:
        if p and p.get('date') == today:
            tasks = parse_tasks(p['tasks'])
        else:
            tasks = parse_tasks(data.get('tasks') or [])
        completion_rate = float(data.get('completion_rate', -1))
    except (ValueError, TypeError) as e:
        return jsonify({'error': str(e)}), 400

    try:
        planner.record_outcome(datetime.now(), tasks, completion_rate)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    planner.today_plan = None
    save_planner(planner, session['user'])
    return jsonify({'message': 'Outcome recorded', 'days_recorded': len(planner.capacity_learner.history)})


@api.route('/history', methods=['GET'])
@login_required
def history():
    planner = get_planner(session['user'])
    return jsonify({'history': planner.get_history()})


@api.route('/usage-metrics', methods=['GET'])
@login_required
def usage_metrics():
    planner = get_planner(session['user'])
    return jsonify(planner.get_usage_metrics())


@api.route('/calibration-metrics', methods=['GET'])
@login_required
def calibration_metrics():
    planner = get_planner(session['user'])
    return jsonify(planner.get_calibration_metrics())


@api.route('/status', methods=['GET'])
@login_required
def status():
    planner = get_planner(session['user'])
    user_state = planner.capacity_learner.get_user_state()
    return jsonify({
        'username': session['user'],
        'user_state': user_state.value,
        'current_limit': planner.capacity_learner.current_limit,
        'days_recorded': len(planner.capacity_learner.history),
    })


# ---------------------------------------------------------------------------
# Register blueprint and serve frontend
# ---------------------------------------------------------------------------

app.register_blueprint(api)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if os.path.exists(FRONTEND_DIST):
        full = os.path.join(FRONTEND_DIST, path)
        if path and os.path.exists(full):
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, 'index.html')
    return jsonify({'error': 'Frontend not built. Run: cd frontend && npm run build'}), 404


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
