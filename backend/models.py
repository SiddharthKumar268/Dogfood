from pymongo import MongoClient, ASCENDING
import os

client = None
db = None

def init_db():
    global client, db
    uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/dogfood')
    client = MongoClient(uri)
    db_name = uri.rsplit('/', 1)[-1] if '/' in uri else 'dogfood'
    db = client[db_name]
    # Create indexes
    db.users.create_index('email', unique=True)
    db.teams.create_index('inviteCode', unique=True)
    db.judgeAssignments.create_index(
        [('judgeId', ASCENDING), ('submissionId', ASCENDING)],
        unique=True
    )
    db.sessions.create_index('token', unique=True)
    db.checkAudits.create_index([('timestamp', ASCENDING)])
    return db

def get_db():
    return db
