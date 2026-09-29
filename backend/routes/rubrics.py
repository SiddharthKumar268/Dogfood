from flask import Blueprint, request, jsonify
from models import get_db
from middleware import require_role
from bson import ObjectId

rubrics_bp = Blueprint('rubrics_bp', __name__, url_prefix='/api/rubrics')

@rubrics_bp.route('/<event_id>', methods=['GET'])
def get_rubric(event_id):
    db = get_db()
    try:
        r = db.rubrics.find_one({'eventId': ObjectId(event_id)})
    except:
        return jsonify({'error': 'invalid id'}), 400
    if not r:
        return jsonify({'error': 'not found'}), 404
    r['_id'] = str(r['_id'])
    r['eventId'] = str(r['eventId'])
    return jsonify(r)

@rubrics_bp.route('/', methods=['POST'])
@require_role('organizer', 'admin')
def update_rubric():
    data = request.json
    db = get_db()
    
    criteria = data.get('criteria', [])
    total_weight = sum(c.get('weight', 0) for c in criteria)
    
    if abs(total_weight - 1.0) > 0.0001:
        return jsonify({'error': 'weights must sum to 1.0'}), 400
        
    doc = {
        'eventId': ObjectId(data['eventId']),
        'criteria': criteria
    }
    
    res = db.rubrics.update_one(
        {'eventId': doc['eventId']},
        {'$set': doc},
        upsert=True
    )
    
    return jsonify({'message': 'rubric updated'})
