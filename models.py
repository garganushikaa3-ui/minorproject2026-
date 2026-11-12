import sqlite3
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pathwise.db')
# Migrate existing database if pathwise.db does not exist yet
_old_db = os.path.join(os.path.dirname(__file__), 'data', 'techfuture.db')
if not os.path.exists(DB_PATH) and os.path.exists(_old_db):
    import shutil
    shutil.copyfile(_old_db, DB_PATH)

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            college TEXT DEFAULT 'College of Computer Applications',
            qualification TEXT DEFAULT 'BCA',
            current_semester TEXT DEFAULT 'Semester 3',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Assessments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT,
            answers_json TEXT NOT NULL,
            results_json TEXT NOT NULL,
            weights_json TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Saved careers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_careers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            career_id TEXT NOT NULL,
            notes TEXT DEFAULT '',
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, career_id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Trial Lab results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trial_lab_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT,
            career_track TEXT NOT NULL,
            score INTEGER NOT NULL,
            max_score INTEGER NOT NULL,
            answers_json TEXT,
            feedback TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Career Quest Badges table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quest_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_key TEXT NOT NULL,
            badge_title TEXT NOT NULL,
            badge_icon TEXT NOT NULL,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, badge_key),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# User management functions
def create_user(username, email, password, full_name, college='College of Computer Applications', qualification='BCA', current_semester='Semester 3'):
    conn = get_db_connection()
    cursor = conn.cursor()
    pwd_hash = generate_password_hash(password)
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, college, qualification, current_semester)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, pwd_hash, full_name, college, qualification, current_semester))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id, None
    except sqlite3.IntegrityError as e:
        conn.close()
        return None, "Username or Email already registered."

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def verify_user_password(user, password):
    if not user:
        return False
    return check_password_hash(user['password_hash'], password)

# Assessment management
def save_assessment(user_id, session_id, answers, results, weights):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO assessments (user_id, session_id, answers_json, results_json, weights_json)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, session_id, json.dumps(answers), json.dumps(results), json.dumps(weights)))
    conn.commit()
    assessment_id = cursor.lastrowid
    conn.close()
    return assessment_id

def get_latest_assessment(user_id=None, session_id=None):
    conn = get_db_connection()
    if user_id:
        row = conn.execute('''
            SELECT * FROM assessments WHERE user_id = ? ORDER BY completed_at DESC LIMIT 1
        ''', (user_id,)).fetchone()
    elif session_id:
        row = conn.execute('''
            SELECT * FROM assessments WHERE session_id = ? ORDER BY completed_at DESC LIMIT 1
        ''', (session_id,)).fetchone()
    else:
        conn.close()
        return None
    conn.close()
    if row:
        return {
            'id': row['id'],
            'user_id': row['user_id'],
            'session_id': row['session_id'],
            'answers': json.loads(row['answers_json']),
            'results': json.loads(row['results_json']),
            'weights': json.loads(row['weights_json']) if row['weights_json'] else {},
            'completed_at': row['completed_at']
        }
    return None

def get_user_assessments(user_id):
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT id, completed_at, results_json FROM assessments WHERE user_id = ? ORDER BY completed_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    results = []
    for r in rows:
        res = json.loads(r['results_json'])
        top_career = res[0]['display_name'] if res and len(res) > 0 else 'General Tech'
        results.append({
            'id': r['id'],
            'completed_at': r['completed_at'],
            'top_career': top_career,
            'match_score': res[0]['match_score'] if res else 0
        })
    return results

# Saved careers
def save_career(user_id, career_id, notes=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO saved_careers (user_id, career_id, notes) VALUES (?, ?, ?)
        ''', (user_id, career_id, notes))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def unsave_career(user_id, career_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM saved_careers WHERE user_id = ? AND career_id = ?
    ''', (user_id, career_id))
    conn.commit()
    conn.close()
    return True

def get_saved_career_ids(user_id):
    conn = get_db_connection()
    rows = conn.execute('SELECT career_id FROM saved_careers WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return [r['career_id'] for r in rows]

# Trial Lab
def save_trial_result(user_id, session_id, career_track, score, max_score, answers, feedback):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trial_lab_results (user_id, session_id, career_track, score, max_score, answers_json, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, session_id, career_track, score, max_score, json.dumps(answers), feedback))
    conn.commit()
    result_id = cursor.lastrowid
    conn.close()
    return result_id

def get_trial_results(user_id=None, session_id=None):
    conn = get_db_connection()
    if user_id:
        rows = conn.execute('''
            SELECT * FROM trial_lab_results WHERE user_id = ? ORDER BY completed_at DESC
        ''', (user_id,)).fetchall()
    elif session_id:
        rows = conn.execute('''
            SELECT * FROM trial_lab_results WHERE session_id = ? ORDER BY completed_at DESC
        ''', (session_id,)).fetchall()
    else:
        conn.close()
        return []
    conn.close()
    return [dict(r) for r in rows]

# Quest Badges
def award_badge(user_id, badge_key, badge_title, badge_icon):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO quest_badges (user_id, badge_key, badge_title, badge_icon)
            VALUES (?, ?, ?, ?)
        ''', (user_id, badge_key, badge_title, badge_icon))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_user_badges(user_id):
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT * FROM quest_badges WHERE user_id = ? ORDER BY earned_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Anonymous aggregate exploration trends
def get_anonymous_trends():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT results_json FROM assessments')
    rows = cursor.fetchall()
    conn.close()
    
    category_counts = {}
    top_careers_count = {}
    total_assessments = len(rows)
    
    for r in rows:
        try:
            results = json.loads(r['results_json'])
            if results and len(results) > 0:
                top_1 = results[0]
                career_name = top_1.get('display_name', 'Unknown')
                category = top_1.get('category', 'Technical')
                top_careers_count[career_name] = top_careers_count.get(career_name, 0) + 1
                category_counts[category] = category_counts.get(category, 0) + 1
        except:
            continue
            
    return {
        'total_assessments': total_assessments,
        'category_counts': category_counts,
        'top_careers_count': top_careers_count
    }

def get_career_records(career_id=None, limit=50, offset=0, search=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM career_records WHERE 1=1"
    params = []
    if career_id and career_id != 'all':
        query += " AND (career_id = ? OR soc_code = ?)"
        params.extend([career_id, career_id])
    if search:
        query += " AND (career_name LIKE ? OR top_skills LIKE ? OR tools_proficient LIKE ? OR company_tier LIKE ? OR location LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term])
    query += " ORDER BY id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_career_records_count(career_id=None, search=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM career_records WHERE 1=1"
    params = []
    if career_id and career_id != 'all':
        query += " AND (career_id = ? OR soc_code = ?)"
        params.extend([career_id, career_id])
    if search:
        query += " AND (career_name LIKE ? OR top_skills LIKE ? OR tools_proficient LIKE ? OR company_tier LIKE ? OR location LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term])
    cursor.execute(query, params)
    cnt = cursor.fetchone()[0]
    conn.close()
    return cnt
