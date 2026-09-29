from flask import Blueprint, Response
from models import get_db
from middleware import require_role
from bson import ObjectId

export_bp = Blueprint('export_bp', __name__, url_prefix='/api')

@export_bp.route('/export.csv', methods=['GET'])
@require_role('organizer', 'admin')
def export_csv():
    db = get_db()
    
    # Calculate averages first
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
        if not sub: continue
        results.append({
            'submissionId': sid,
            'title': sub.get('title', ''),
            'track': sub.get('track', ''),
            'rawAvg': sum(stats['raw']) / len(stats['raw']) if stats['raw'] else 0,
            'normalizedAvg': sum(stats['norm']) / len(stats['norm']) if stats['norm'] else 0,
            'judgeCount': len(stats['raw'])
        })
        
    results.sort(key=lambda x: x['normalizedAvg'], reverse=True)
    
    csv_lines = ['Rank,Title,Track,RawAvg,NormalizedAvg,JudgeCount']
    for i, r in enumerate(results):
        line = f"{i+1},{r['title']},{r['track']},{r['rawAvg']:.4f},{r['normalizedAvg']:.4f},{r['judgeCount']}"
        csv_lines.append(line)
        
    csv_data = "\n".join(csv_lines)
    return Response(csv_data, mimetype='text/csv')
