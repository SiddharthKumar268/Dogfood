from functools import wraps
from flask import request, jsonify, g
from models import get_db
from bson import ObjectId

def load_user():
    """Before-request handler: load user from session cookie."""
    session_token = request.cookies.get('session')
    if not session_token:
        g.user = None
        return
    db = get_db()
    session = db.sessions.find_one({'token': session_token})
    if session:
        user = db.users.find_one({'_id': session['userId']})
        if user:
            user['_id'] = str(user['_id'])
            g.user = user
            return
    g.user = None

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.user:
            return jsonify({'error': 'unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not g.user:
                return jsonify({'error': 'unauthorized'}), 401
            if g.user['role'] not in roles:
                return jsonify({'error': 'forbidden'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
