from flask import Blueprint, request, jsonify, g
from models import get_db
from middleware import require_auth, require_role
from bson import ObjectId
from datetime import datetime
from dateutil import parser

events_bp = Blueprint('events_bp', __name__, url_prefix='/api/events')

@events_bp.route('/', methods=['GET'])
def list_events():
    db = get_db()
    events = list(db.events.find({}))
    for e in events:
        e['_id'] = str(e['_id'])
    return jsonify(events)

@events_bp.route('/<event_id>', methods=['GET'])
def get_event(event_id):
    db = get_db()
    try:
        e = db.events.find_one({'_id': ObjectId(event_id)})
    except:
        return jsonify({'error': 'invalid id'}), 400
    if not e:
        return jsonify({'error': 'not found'}), 404
    e['_id'] = str(e['_id'])
    return jsonify(e)

@events_bp.route('/', methods=['POST'])
@require_role('organizer', 'admin')
def create_event():
    data = request.json
    db = get_db()
    
    try:
        doc = {
            'name': data.get('name'),
            'description': data.get('description'),
            'tracks': data.get('tracks', []),
            'prizes': data.get('prizes', []),
            'startDate': parser.parse(data['startDate']) if data.get('startDate') else None,
            'endDate': parser.parse(data['endDate']) if data.get('endDate') else None,
            'submissionsClose': parser.parse(data['submissionsClose']) if data.get('submissionsClose') else None
        }
        res = db.events.insert_one(doc)
        doc['_id'] = str(res.inserted_id)
        return jsonify(doc), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
