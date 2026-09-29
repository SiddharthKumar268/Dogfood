from flask import Blueprint, request, jsonify, g
from models import get_db
from middleware import require_auth, require_role
from bson import ObjectId
import os
import binascii

teams_bp = Blueprint('teams_bp', __name__, url_prefix='/api/teams')

@teams_bp.route('/', methods=['POST'])
@require_role('participant')
def create_team():
    data = request.json
    db = get_db()
    
    invite_code = binascii.hexlify(os.urandom(8)).decode('utf-8').upper()
    team_doc = {
        'name': data.get('name'),
        'memberIds': [ObjectId(g.user['_id'])],
        'inviteCode': invite_code,
        'eventId': ObjectId(data.get('eventId')) if data.get('eventId') else None
    }
    
    res = db.teams.insert_one(team_doc)
    team_doc['_id'] = str(res.inserted_id)
    team_doc['memberIds'] = [str(mid) for mid in team_doc['memberIds']]
    if team_doc['eventId']:
        team_doc['eventId'] = str(team_doc['eventId'])
    return jsonify(team_doc), 201

@teams_bp.route('/join', methods=['POST'])
@require_auth
def join_team():
    data = request.json
    db = get_db()
    code = data.get('inviteCode')
    
    team = db.teams.find_one({'inviteCode': code})
    if not team:
        return jsonify({'error': 'invalid code'}), 404
        
    user_id = ObjectId(g.user['_id'])
    if user_id not in team['memberIds']:
        db.teams.update_one({'_id': team['_id']}, {'$push': {'memberIds': user_id}})
        
    return jsonify({'message': 'joined team successfully'})

@teams_bp.route('/<team_id>', methods=['GET'])
@require_auth
def get_team(team_id):
    db = get_db()
    try:
        team = db.teams.find_one({'_id': ObjectId(team_id)})
    except:
        return jsonify({'error': 'invalid id'}), 400
    if not team:
        return jsonify({'error': 'not found'}), 404
    
    team['_id'] = str(team['_id'])
    team['memberIds'] = [str(mid) for mid in team['memberIds']]
    if team.get('eventId'):
        team['eventId'] = str(team['eventId'])
    return jsonify(team)
