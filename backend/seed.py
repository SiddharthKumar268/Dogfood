import json
import os
import math
import bcrypt
from datetime import datetime, timezone
from dateutil import parser
from models import get_db

def seed_if_empty():
    db = get_db()
    if db.users.count_documents({}) > 0:
        return

    fixture_path = os.path.join(os.path.dirname(__file__), '..', 'fixtures.json')
    if not os.path.exists(fixture_path):
        fixture_path = os.path.join(os.getcwd(), 'fixtures.json')
    if not os.path.exists(fixture_path):
        return

    with open(fixture_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 1. Users
    user_id_map = {}
    print("=== AUTH HEADERS FOR .dogfood.toml ===")
    for u in data.get('users', []):
        pw_hash = bcrypt.hashpw(u['password'].encode('utf-8'), bcrypt.gensalt())
        slug = u['email'].split('@')[0]
        user_doc = {
            'name': u['name'],
            'email': u['email'],
            'password': pw_hash,
            'role': u['role'],
            'slug': slug,
            'affiliations': u.get('affiliations', []),
            'createdAt': datetime.now(timezone.utc)
        }
        res = db.users.insert_one(user_doc)
        user_id_map[u['email']] = res.inserted_id
        
        session_token = u.get('sessionToken')
        if session_token:
            db.sessions.insert_one({'token': session_token, 'userId': res.inserted_id})
            
            # Print auth headers
            header_name = slug
            if header_name == 'organizer':
                print(f'organizer   = "Cookie: session={session_token}"')
            elif header_name == 'judge_a':
                print(f'judge_a     = "Cookie: session={session_token}"')
            elif header_name == 'judge_b':
                print(f'judge_b     = "Cookie: session={session_token}"')
            elif header_name == 'participant':
                print(f'participant = "Cookie: session={session_token}"')

    # 2. Events
    event_id = None
    for e in data.get('events', []):
        e['startDate'] = parser.parse(e['startDate'])
        e['endDate'] = parser.parse(e['endDate'])
        e['submissionsClose'] = parser.parse(e['submissionsClose'])
        e['createdAt'] = datetime.now(timezone.utc)
        res = db.events.insert_one(e)
        if not event_id:
            event_id = res.inserted_id

    # 3. Teams
    team_name_map = {}
    for t in data.get('teams', []):
        member_ids = [user_id_map[email] for email in t['memberEmails'] if email in user_id_map]
        team_doc = {
            'name': t['name'],
            'memberIds': member_ids,
            'inviteCode': t['inviteCode'],
            'eventId': event_id,
            'createdAt': datetime.now(timezone.utc)
        }
        res = db.teams.insert_one(team_doc)
        team_name_map[t['name']] = res.inserted_id

    # 4. Submissions
    for s in data.get('submissions', []):
        sub_doc = {
            'title': s['title'],
            'summary': s['summary'],
            'description': s['description'],
            'repoUrl': s['repoUrl'],
            'demoUrl': s['demoUrl'],
            'track': s['track'],
            'team_members': s.get('team_members', []),
            'teamId': team_name_map.get(s['teamName']),
            'status': s['status'],
            'eventId': event_id,
            'submittedAt': datetime.now(timezone.utc),
            'updatedAt': datetime.now(timezone.utc)
        }
        db.submissions.insert_one(sub_doc)

    # 5. Rubric
    rubric_data = data.get('rubric')
    criteria_map = {}
    if rubric_data:
        db.rubrics.insert_one({'eventId': event_id, 'criteria': rubric_data['criteria']})
        criteria_map = {c['name']: c['weight'] for c in rubric_data['criteria']}

    # 6. Judge Assignments & Scores
    scores_data = data.get('scores', {})
    for judge_email_prefix, submissions in scores_data.items():
        judge_email = f"{judge_email_prefix}@dogfood.dev"
        judge_id = user_id_map.get(judge_email)
        if not judge_id:
            continue
        
        for sub_score in submissions:
            sub = db.submissions.find_one({'title': sub_score['submissionTitle'], 'status': 'submitted'})
            if not sub:
                continue
            sub_id = sub['_id']
            
            raw_total = sum(c['score'] * criteria_map.get(c['criterionName'], 0) for c in sub_score['criteriaScores'])
            
            db.judgeAssignments.update_one(
                {'judgeId': judge_id, 'submissionId': sub_id},
                {'$set': {'status': 'scored', 'eventId': event_id, 'assignedAt': datetime.now(timezone.utc)}},
                upsert=True
            )
            
            db.scores.insert_one({
                'judgeId': judge_id,
                'submissionId': sub_id,
                'criteriaScores': sub_score['criteriaScores'],
                'comment': sub_score.get('comment'),
                'rawTotal': raw_total,
                'scoredAt': datetime.now(timezone.utc)
            })

    # Run initial z-score normalization
    all_scores = list(db.scores.find({}))
    judge_grouped = {}
    for s in all_scores:
        jid = str(s['judgeId'])
        if jid not in judge_grouped:
            judge_grouped[jid] = []
        judge_grouped[jid].append(s)

    for jid, j_scores in judge_grouped.items():
        n = len(j_scores)
        if n == 0:
            continue
        mean = sum(s['rawTotal'] for s in j_scores) / n
        variance = sum((s['rawTotal'] - mean) ** 2 for s in j_scores) / n
        stddev = math.sqrt(variance)
        if stddev == 0:
            stddev = 1.0  # Guard against uniform scoring (e.g. Judge Beta all 5s)
        for s in j_scores:
            norm_total = (s['rawTotal'] - mean) / stddev
            db.scores.update_one({'_id': s['_id']}, {'$set': {'normalizedTotal': norm_total}})

    print("Seeded fixture data. Auth headers printed above.")

if __name__ == '__main__':
    from models import init_db
    init_db()
    seed_if_empty()
