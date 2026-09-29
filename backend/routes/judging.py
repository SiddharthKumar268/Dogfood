from flask import Blueprint, request, jsonify, g
from models import get_db
from middleware import require_auth, require_role
from bson import ObjectId
import math

judging_bp = Blueprint('judging_bp', __name__, url_prefix='/api/judge')

@judging_bp.route('/scores', methods=['GET'])
def get_scores():
    if not getattr(g, 'user', None):
        return jsonify({'error': 'unauthorized'}), 401
        
    db = get_db()
    user = g.user
    role = user['role']
    judge_query = request.args.get('judge')
    
    if role == 'participant':
        event = db.events.find_one()
        if not event or not event.get('resultsPublished'):
            return jsonify({'error': 'forbidden: results not published'}), 403
        scores = list(db.scores.find({}))
    elif role == 'judge':
        # Highest risk requirement: Role isolation
        # If a judge provides ?judge=..., it must be their own ID, slug, or email
        if judge_query:
            is_own = (
                judge_query == str(user['_id']) or 
                judge_query == user.get('slug') or 
                judge_query == user.get('email')
            )
            if not is_own:
                return jsonify({'error': "cannot view another judge's scores"}), 403
        scores = list(db.scores.find({'judgeId': ObjectId(user['_id'])}))
    else:  # organizer / admin
        query = {}
        if judge_query:
            target_user = None
            if ObjectId.is_valid(judge_query):
                target_user = db.users.find_one({'_id': ObjectId(judge_query)})
            if not target_user:
                target_user = db.users.find_one({'$or': [{'slug': judge_query}, {'email': judge_query}]})
            if target_user:
                query['judgeId'] = target_user['_id']
            else:
                return jsonify([])
        scores = list(db.scores.find(query))
        
    for s in scores:
        s['_id'] = str(s['_id'])
        s['judgeId'] = str(s['judgeId'])
        s['submissionId'] = str(s['submissionId'])
    return jsonify(scores)

@judging_bp.route('/scores', methods=['POST'])
@require_role('judge')
def submit_score():
    data = request.get_json(silent=True) or request.form
    db = get_db()
    
    sub_id_str = data.get('submissionId') or data.get('submission_id')
    if not sub_id_str or not ObjectId.is_valid(sub_id_str):
        return jsonify({'error': 'invalid submission id'}), 400
        
    sub_id = ObjectId(sub_id_str)
    sub = db.submissions.find_one({'_id': sub_id})
    if not sub:
        return jsonify({'error': 'submission not found'}), 404
        
    rubric = db.rubrics.find_one({'eventId': sub.get('eventId')})
    if not rubric:
        rubric = db.rubrics.find_one()
    if not rubric:
        return jsonify({'error': 'rubric not found'}), 404
        
    criteria_map = {c['name']: c['weight'] for c in rubric['criteria']}
    is_draft = str(data.get('draft', 'false')).lower() in ('true', '1', 'yes')
    
    raw_criteria_scores = data.get('criteriaScores') or data.get('scores', {})
    criteria_scores = []
    if isinstance(raw_criteria_scores, dict):
        for name, score in raw_criteria_scores.items():
            criteria_scores.append({'criterionName': name, 'score': float(score)})
    elif isinstance(raw_criteria_scores, list):
        criteria_scores = raw_criteria_scores
        
    raw_total = sum(c['score'] * criteria_map.get(c['criterionName'], 0) for c in criteria_scores)
    score_status = 'draft' if is_draft else 'submitted'
    
    score_doc = {
        'judgeId': ObjectId(g.user['_id']),
        'submissionId': sub_id,
        'criteriaScores': criteria_scores,
        'comment': data.get('comment') or data.get('comments', ''),
        'rawTotal': raw_total,
        'status': score_status
    }
    
    if is_draft:
        # Upsert draft: overwrite any existing draft for this judge+submission
        db.scores.update_one(
            {'judgeId': ObjectId(g.user['_id']), 'submissionId': sub_id, 'status': 'draft'},
            {'$set': score_doc},
            upsert=True
        )
        updated = db.scores.find_one({'judgeId': ObjectId(g.user['_id']), 'submissionId': sub_id, 'status': 'draft'})
        score_doc['_id'] = str(updated['_id'])
        db.judgeAssignments.update_one(
            {'judgeId': ObjectId(g.user['_id']), 'submissionId': sub_id},
            {'$set': {'status': 'draft'}},
            upsert=True
        )
    else:
        # Final submission: remove any draft, insert final
        db.scores.delete_many({'judgeId': ObjectId(g.user['_id']), 'submissionId': sub_id, 'status': 'draft'})
        res = db.scores.insert_one(score_doc)
        score_doc['_id'] = str(res.inserted_id)
        db.judgeAssignments.update_one(
            {'judgeId': ObjectId(g.user['_id']), 'submissionId': sub_id},
            {'$set': {'status': 'scored'}},
            upsert=True
        )
    
    score_doc['judgeId'] = str(score_doc['judgeId'])
    score_doc['submissionId'] = str(score_doc['submissionId'])
    return jsonify(score_doc), 201

@judging_bp.route('/assignments', methods=['POST'])
@require_role('organizer', 'admin')
def create_assignments():
    data = request.get_json(silent=True) or request.form
    db = get_db()
    
    raw_judges = data.get('judgeIds') if data else None
    raw_subs = data.get('submissionIds') if data else None
    
    # If no explicit list, assign all active judges to all submitted projects
    if not raw_judges:
        judges = list(db.users.find({'role': 'judge'}))
    else:
        judges = [db.users.find_one({'_id': ObjectId(jid)}) for jid in raw_judges]
        judges = [j for j in judges if j]  # filter None
    judge_ids = [j['_id'] for j in judges]
    
    # Build judge identity lookup for COI checking
    judge_identities = {}
    for j in judges:
        identifiers = set()
        identifiers.add(j.get('name', '').lower())
        identifiers.add(j.get('email', '').lower())
        for aff in j.get('affiliations', []):
            identifiers.add(aff.lower())
        identifiers.discard('')
        judge_identities[j['_id']] = identifiers
        
    if not raw_subs:
        subs = list(db.submissions.find({'status': 'submitted'}))
    else:
        subs = [db.submissions.find_one({'_id': ObjectId(sid)}) for sid in raw_subs]
        subs = [s for s in subs if s]
    submission_ids = [s['_id'] for s in subs]
    
    # Build team member lookup for COI checking
    sub_team_members = {}
    for s in subs:
        members = set()
        for m in s.get('team_members', []):
            members.add(m.lower())
        sub_team_members[s['_id']] = members
        
    per_sub = int(data.get('perSubmission', 2)) if data else 2
    if not judge_ids or not submission_ids:
        return jsonify({'assigned': 0, 'message': 'No judges or submissions found'})
        
    assignments = []
    conflicts = []
    j_idx = 0
    for sid in submission_ids:
        assigned_count = 0
        attempts = 0
        while assigned_count < per_sub and attempts < len(judge_ids) * 2:
            jid = judge_ids[j_idx % len(judge_ids)]
            j_idx += 1
            attempts += 1
            
            # COI Check: overlap between judge identities and submission team members
            judge_ids_set = judge_identities.get(jid, set())
            team_members_set = sub_team_members.get(sid, set())
            overlap = judge_ids_set & team_members_set
            
            if overlap:
                # Log the conflict and skip
                conflict_doc = {
                    'judgeId': jid,
                    'submissionId': sid,
                    'reason': f'Name/affiliation overlap: {list(overlap)}',
                    'skipped': True
                }
                db.conflicts.insert_one(conflict_doc)
                conflicts.append({'judgeId': str(jid), 'submissionId': str(sid), 'reason': conflict_doc['reason']})
                continue
            
            db.judgeAssignments.update_one(
                {'judgeId': jid, 'submissionId': sid},
                {'$set': {'status': 'pending'}},
                upsert=True
            )
            assignments.append({'judgeId': str(jid), 'submissionId': str(sid)})
            assigned_count += 1
            
    return jsonify({
        'assigned': len(assignments),
        'conflicts': len(conflicts),
        'conflictDetails': conflicts,
        'message': f'{len(assignments)} assignments created, {len(conflicts)} conflict(s) detected and skipped'
    })

@judging_bp.route('/assignments', methods=['GET'])
@require_role('judge')
def get_assignments():
    db = get_db()
    assignments = list(db.judgeAssignments.find({'judgeId': ObjectId(g.user['_id'])}))
    for a in assignments:
        a['_id'] = str(a['_id'])
        a['judgeId'] = str(a['judgeId'])
        a['submissionId'] = str(a['submissionId'])
    return jsonify(assignments)

@judging_bp.route('/progress', methods=['GET'])
@require_role('judge')
def get_progress():
    db = get_db()
    judge_id = ObjectId(g.user['_id'])
    total_assignments = db.judgeAssignments.count_documents({'judgeId': judge_id})
    scored_assignments = db.judgeAssignments.count_documents({'judgeId': judge_id, 'status': 'scored'})
    draft_assignments = db.judgeAssignments.count_documents({'judgeId': judge_id, 'status': 'draft'})
    return jsonify({
        'scored': scored_assignments,
        'drafts': draft_assignments,
        'total': total_assignments,
        'complete': scored_assignments == total_assignments and total_assignments > 0
    })

@judging_bp.route('/conflicts', methods=['GET'])
@require_role('organizer', 'admin')
def get_conflicts():
    db = get_db()
    conflicts = list(db.conflicts.find({}))
    for c in conflicts:
        c['_id'] = str(c['_id'])
        c['judgeId'] = str(c['judgeId'])
        c['submissionId'] = str(c['submissionId'])
        # Resolve names for display
        judge = db.users.find_one({'_id': ObjectId(c['judgeId'])})
        sub = db.submissions.find_one({'_id': ObjectId(c['submissionId'])})
        c['judgeName'] = judge.get('name', 'Unknown') if judge else 'Unknown'
        c['submissionTitle'] = sub.get('title', 'Unknown') if sub else 'Unknown'
    return jsonify(conflicts)

@judging_bp.route('/normalize', methods=['POST'])
@require_role('organizer', 'admin')
def normalize_scores():
    db = get_db()
    scores = list(db.scores.find({'status': {'$ne': 'draft'}}))
    judge_scores = {}
    for s in scores:
        jid = str(s['judgeId'])
        if jid not in judge_scores:
            judge_scores[jid] = []
        judge_scores[jid].append(s)
        
    for jid, j_scores in judge_scores.items():
        n = len(j_scores)
        if n == 0:
            continue
        mean = sum(s['rawTotal'] for s in j_scores) / n
        variance = sum((s['rawTotal'] - mean) ** 2 for s in j_scores) / n
        stddev = math.sqrt(variance)
        if stddev == 0:
            stddev = 1.0  # Safe fallback for uniform scoring
            
        for s in j_scores:
            norm_total = (s['rawTotal'] - mean) / stddev
            db.scores.update_one({'_id': s['_id']}, {'$set': {'normalizedTotal': norm_total}})
            
    return jsonify({'message': 'Scores successfully normalized using per-judge z-score formula'})

@judging_bp.route('/publish', methods=['POST'])
@require_role('organizer', 'admin')
def publish_results():
    db = get_db()
    db.events.update_many({}, {'$set': {'resultsPublished': True}})
    return jsonify({'message': 'Results published successfully'})

@judging_bp.route('/leaderboard-toggle', methods=['POST'])
@require_role('organizer', 'admin')
def toggle_leaderboard():
    db = get_db()
    settings = db.settings.find_one({'key': 'leaderboard'}) or {}
    current = settings.get('visible', False)
    db.settings.update_one(
        {'key': 'leaderboard'},
        {'$set': {'key': 'leaderboard', 'visible': not current}},
        upsert=True
    )
    return jsonify({'leaderboard_visible': not current, 'message': f'Leaderboard preview {"enabled" if not current else "disabled"}'})

@judging_bp.route('/leaderboard-status', methods=['GET'])
def get_leaderboard_status():
    db = get_db()
    settings = db.settings.find_one({'key': 'leaderboard'}) or {}
    return jsonify({'leaderboard_visible': settings.get('visible', False)})

@judging_bp.route('/results', methods=['GET'])
def get_results():
    db = get_db()
    event = db.events.find_one()
    if not event or not event.get('resultsPublished'):
        return jsonify({'error': 'results not published yet'}), 403
        
    scores = list(db.scores.find({}))
    sub_stats = {}
    for s in scores:
        sid = str(s['submissionId'])
        if sid not in sub_stats:
            sub_stats[sid] = {'raw': [], 'norm': []}
        sub_stats[sid]['raw'].append(s.get('rawTotal', 0))
        sub_stats[sid]['norm'].append(s.get('normalizedTotal', 0))
        
    results = []
    for sid, stats in sub_stats.items():
        sub = db.submissions.find_one({'_id': ObjectId(sid)})
        if not sub:
            continue
        results.append({
            'submissionId': sid,
            'title': sub.get('title'),
            'track': sub.get('track'),
            'rawAvg': sum(stats['raw']) / len(stats['raw']) if stats['raw'] else 0,
            'normalizedAvg': sum(stats['norm']) / len(stats['norm']) if stats['norm'] else 0,
            'judgeCount': len(stats['raw'])
        })
        
    results.sort(key=lambda x: x['normalizedAvg'], reverse=True)
    return jsonify(results)
