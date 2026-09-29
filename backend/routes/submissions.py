from flask import Blueprint, request, jsonify, g, render_template, redirect
from models import get_db
from middleware import require_auth, require_role
from bson import ObjectId
from datetime import datetime, timezone

submissions_bp = Blueprint('submissions_bp', __name__, url_prefix='/api/submissions')
pages_bp = Blueprint('pages_bp', __name__)

@submissions_bp.route('/', methods=['GET'])
def list_submissions():
    db = get_db()
    subs = list(db.submissions.find({'status': 'submitted'}))
    for s in subs:
        s['_id'] = str(s['_id'])
        if s.get('teamId'): s['teamId'] = str(s['teamId'])
        if s.get('eventId'): s['eventId'] = str(s['eventId'])
    return jsonify(subs)

@submissions_bp.route('/<sub_id>', methods=['GET'])
def get_submission(sub_id):
    db = get_db()
    try:
        s = db.submissions.find_one({'_id': ObjectId(sub_id)})
    except Exception:
        return jsonify({'error': 'invalid id'}), 400
    if not s:
        return jsonify({'error': 'not found'}), 404
    s['_id'] = str(s['_id'])
    if s.get('teamId'): s['teamId'] = str(s['teamId'])
    if s.get('eventId'): s['eventId'] = str(s['eventId'])
    return jsonify(s)

@submissions_bp.route('/', methods=['POST'])
@require_role('participant')
def create_submission():
    data = request.get_json(silent=True) or request.form
    db = get_db()
    event_id_str = data.get('eventId')
    event = None
    if event_id_str and ObjectId.is_valid(event_id_str):
        event = db.events.find_one({'_id': ObjectId(event_id_str)})
    if not event:
        event = db.events.find_one()
    if not event:
        return jsonify({'error': 'event not found'}), 404
        
    if event.get('submissionsClose'):
        close_time = event['submissionsClose']
        if close_time.tzinfo is None:
            close_time = close_time.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > close_time:
            return jsonify({'error': 'submissions are closed'}), 403
        
    team_id = None
    if data.get('teamId') and ObjectId.is_valid(data.get('teamId')):
        team_id = ObjectId(data.get('teamId'))
    
    raw_members = data.get('team_members', [])
    if isinstance(raw_members, str):
        team_members = [m.strip() for m in raw_members.split(',') if m.strip()]
    elif isinstance(raw_members, list):
        team_members = raw_members
    else:
        team_members = []

    doc = {
        'title': data.get('title'),
        'summary': data.get('summary'),
        'description': data.get('description'),
        'repoUrl': data.get('repoUrl'),
        'demoUrl': data.get('demoUrl'),
        'track': data.get('track'),
        'team_members': team_members,
        'teamId': team_id,
        'status': data.get('status', 'submitted'),
        'eventId': event['_id'],
        'submittedAt': datetime.now(timezone.utc),
        'updatedAt': datetime.now(timezone.utc)
    }
    res = db.submissions.insert_one(doc)
    doc['_id'] = str(res.inserted_id)
    if doc['teamId']: doc['teamId'] = str(doc['teamId'])
    doc['eventId'] = str(doc['eventId'])
    return jsonify(doc), 201

@submissions_bp.route('/<sub_id>', methods=['PUT'])
@require_auth
def update_submission(sub_id):
    data = request.get_json(silent=True) or request.form
    db = get_db()
    try:
        sub = db.submissions.find_one({'_id': ObjectId(sub_id)})
    except Exception:
        return jsonify({'error': 'invalid id'}), 400
        
    if not sub:
        return jsonify({'error': 'not found'}), 404
        
    update_data = {
        k: v for k, v in data.items() 
        if k in ['title', 'summary', 'description', 'repoUrl', 'demoUrl', 'track', 'status']
    }
    update_data['updatedAt'] = datetime.now(timezone.utc)
    db.submissions.update_one({'_id': ObjectId(sub_id)}, {'$set': update_data})
    return jsonify({'message': 'updated'})


# --- HTML PAGES ---

@pages_bp.route('/projects', methods=['GET'])
def gallery_page():
    db = get_db()
    track_filter = request.args.get('track')
    query = {'status': 'submitted'}
    if track_filter:
        query['track'] = track_filter
    subs = list(db.submissions.find(query))
    for s in subs:
        s['_id'] = str(s['_id'])
    tracks = db.submissions.distinct('track', {'status': 'submitted'})
    return render_template('gallery.html', submissions=subs, tracks=tracks, active_track=track_filter or '')

@pages_bp.route('/projects/new', methods=['GET'])
def new_project_page():
    if not getattr(g, 'user', None) or g.user.get('role') != 'participant':
        return redirect('/login')
    db = get_db()
    events = list(db.events.find({}))
    for e in events:
        e['_id'] = str(e['_id'])
    return render_template('submit.html', events=events)

@pages_bp.route('/projects/new', methods=['POST'])
def new_project_submit():
    if not getattr(g, 'user', None) or g.user.get('role') != 'participant':
        return jsonify({'error': 'unauthorized'}), 401
    
    db = get_db()
    event = db.events.find_one()
    if event and event.get('submissionsClose'):
        close_time = event['submissionsClose']
        if close_time.tzinfo is None:
            close_time = close_time.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > close_time:
            return jsonify({'error': 'submissions are closed'}), 403
        
    data = request.get_json(silent=True) or request.form
    raw_members = data.get('team_members', [])
    if isinstance(raw_members, str):
        team_members = [m.strip() for m in raw_members.split(',') if m.strip()]
    elif isinstance(raw_members, list):
        team_members = raw_members
    else:
        team_members = []

    doc = {
        'title': data.get('title'),
        'summary': data.get('summary'),
        'description': data.get('description'),
        'repoUrl': data.get('repoUrl'),
        'demoUrl': data.get('demoUrl'),
        'track': data.get('track'),
        'team_members': team_members,
        'status': 'submitted',
        'eventId': event['_id'] if event else None,
        'submittedAt': datetime.now(timezone.utc),
        'updatedAt': datetime.now(timezone.utc)
    }
    db.submissions.insert_one(doc)
    if request.is_json:
        return jsonify({'message': 'submitted'}), 201
    return redirect('/projects')
