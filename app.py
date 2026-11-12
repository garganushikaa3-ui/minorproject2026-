import os
import json
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename

import models
from models import (
    init_db, create_user, get_user_by_email, get_user_by_id,
    verify_user_password, save_assessment, get_latest_assessment,
    get_user_assessments, save_career, unsave_career, get_saved_career_ids,
    save_trial_result, get_trial_results, award_badge, get_user_badges,
    get_anonymous_trends, get_career_records, get_career_records_count
)
from recommendation_engine import get_recommendations, calculate_career_match, normalize_weights, load_careers_master
from data_manager import (
    get_all_careers, get_career_by_id, get_careers_by_category,
    search_careers, get_unique_categories, validate_and_import_dataset,
    export_careers_to_csv
)
from trial_lab_data import TRIAL_LAB_TRACKS, evaluate_lab_submission
from bridge_engine import compute_career_bridge
from future_paths_data import FUTURE_PATHS
from quest_data import QUEST_MISSIONS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pathwise-career-decision-support-key-2026'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
init_db()

@app.before_request
def ensure_session_identity():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    if 'user_id' in session:
        session['is_logged_in'] = True
    else:
        session['is_logged_in'] = False

@app.context_processor
def inject_global_data():
    user = None
    if session.get('user_id'):
        user = get_user_by_id(session['user_id'])
    saved_ids = []
    if session.get('user_id'):
        saved_ids = get_saved_career_ids(session['user_id'])
    return {
        'current_user': user,
        'saved_career_ids': saved_ids,
        'categories': get_unique_categories(),
        'all_careers_summary': get_all_careers()
    }

# ----------------- HOME & STATIC PAGES ----------------- #

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.svg', mimetype='image/svg+xml')

@app.route('/')
def index():
    all_careers = get_all_careers()
    total_careers = len(all_careers)
    categories = get_unique_categories()
    latest_assess = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    return render_template('index.html', total_careers=total_careers, categories=categories, latest_assess=latest_assess)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/methodology')
def methodology():
    return render_template('methodology.html')

# ----------------- AUTHENTICATION ----------------- #

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('profile'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        college = request.form.get('college', 'Manav Rachna International Institute of Research and Studies').strip()
        qualification = request.form.get('qualification', 'BCA').strip()
        current_semester = request.form.get('current_semester', 'Semester 3').strip()
        
        if not username or not email or not password or not full_name:
            flash("All required fields must be completed.", "danger")
            return render_template('register.html')
            
        user_id, error = create_user(username, email, password, full_name, college, qualification, current_semester)
        if error:
            flash(error, "danger")
            return render_template('register.html')
            
        session['user_id'] = user_id
        session['username'] = username
        session['full_name'] = full_name
        flash("Registration successful! Welcome to PathWise.", "success")
        return redirect(url_for('assessment'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('profile'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = get_user_by_email(email)
        if user and verify_user_password(user, password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('full_name', None)
    session.pop('is_logged_in', None)
    flash("You have logged out safely.", "info")
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    user = None
    if session.get('user_id'):
        user = get_user_by_id(session['user_id'])
    assessments = get_user_assessments(session.get('user_id')) if session.get('user_id') else []
    saved_ids = get_saved_career_ids(session.get('user_id')) if session.get('user_id') else []
    saved_careers = [get_career_by_id(cid) for cid in saved_ids if get_career_by_id(cid)]
    badges = get_user_badges(session.get('user_id')) if session.get('user_id') else []
    trials = get_trial_results(user_id=session.get('user_id'), session_id=session.get('session_id'))
    return render_template('profile.html', user=user, assessments=assessments, saved_careers=saved_careers, badges=badges, trials=trials)

# ----------------- CAREER ASSESSMENT & RECOMMENDATIONS ----------------- #

@app.route('/assessment', methods=['GET', 'POST'])
def assessment():
    if request.method == 'POST':
        # Education
        education = {
            "qualification": request.form.get('qualification', 'BCA'),
            "semester": request.form.get('semester', 'Semester 3'),
            "completed_courses": request.form.getlist('completed_courses')
        }
        
        # Interests
        interests = request.form.getlist('interests')
        
        # Current Skills (0-5 scale)
        skill_keys = [
            "Python", "Java", "C/C++", "SQL", "HTML/CSS/JavaScript",
            "Excel & Spreadsheets", "Data Analysis", "Statistics & Probability",
            "Networking Fundamentals", "Problem-Solving", "System Design & Architecture"
        ]
        skills = {}
        for sk in skill_keys:
            val = request.form.get(f"skill_{sk}", "0")
            try:
                skills[sk] = int(val)
            except ValueError:
                skills[sk] = 0
                
        # Tools Known
        tools = request.form.getlist('tools')
        
        # Work Preferences
        work_preferences = {
            "coding_intensity": request.form.get('coding_intensity', 'Moderate'),
            "work_type": request.form.get('work_type', 'Application Building'),
            "analytical_creative": request.form.get('analytical_creative', 'Both'),
            "independence": request.form.get('independence', 'Balanced')
        }
        
        # Priorities & Goals
        priorities = request.form.getlist('priorities')
        
        student_input = {
            "education": education,
            "interests": interests,
            "skills": skills,
            "tools": tools,
            "work_preferences": work_preferences,
            "priorities": priorities
        }
        
        # Custom Weights starting configuration
        default_weights = {
            'interests': 0.30,
            'skills': 0.30,
            'tools': 0.15,
            'education': 0.15,
            'work_preferences': 0.10,
            'salary': 0.05 if 'Salary' in priorities else 0.0,
            'job_outlook': 0.05 if 'Job outlook' in priorities else 0.0
        }
        normalized = normalize_weights(default_weights)
        
        # Run recommendation algorithm
        recommendations = get_recommendations(student_input, custom_weights=normalized)
        
        # Save to database
        user_id = session.get('user_id')
        session_id = session.get('session_id')
        save_assessment(user_id, session_id, student_input, recommendations, normalized)
        
        # Award badge if user is logged in
        if user_id:
            award_badge(user_id, "profile_pioneer", "Profile Pioneer", "bi-person-check")
            
        session['has_assessment'] = True
        flash("Career assessment completed successfully! Here are your explainable recommendations.", "success")
        return redirect(url_for('recommendations_view'))
        
    # GET request - show assessment form
    latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    return render_template('assessment.html', existing_answers=latest.get('answers') if latest else None)

@app.route('/recommendations')
def recommendations_view():
    latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    if not latest:
        # Provide instant demo baseline so guests and new visitors immediately experience the explainable matching engine & comparison matrix
        demo_answers = {
            "education": {"qualification": "BCA", "semester": "Semester 3"},
            "interests": ["Programming and software development", "Data analysis and visualisation", "Web development"],
            "skills": {"Python": 4, "SQL": 3, "HTML/CSS/JavaScript": 3, "Excel & Spreadsheets": 4, "Data Analysis": 3, "Problem-Solving": 4, "Java": 3, "C/C++": 3},
            "tools": ["VS Code", "Git / GitHub", "Python / Jupyter Notebook", "MySQL / SQLite"],
            "work_preferences": {"coding_intensity": "High", "work_type": "Application Building", "analytical_creative": "Both", "independence": "Balanced"},
            "priorities": ["Interest in the work", "Skill compatibility", "Salary"]
        }
        demo_weights = normalize_weights()
        demo_results = get_recommendations(demo_answers, custom_weights=demo_weights)
        latest = {
            'answers': demo_answers,
            'weights': demo_weights,
            'results': demo_results
        }
        
    results = latest.get('results', [])
    answers = latest.get('answers', {})
    weights = latest.get('weights', {})
    
    top_3 = results[:3]
    remaining = results[3:10]
    lower_ranked = results[10:18] # for Why Not module
    
    return render_template('recommendations.html',
                           top_3=top_3,
                           remaining=remaining,
                           lower_ranked=lower_ranked,
                           answers=answers,
                           weights=weights)

@app.route('/api/recalculate', methods=['POST'])
def api_recalculate():
    """Recalculate recommendations dynamically when priority slider is adjusted."""
    latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    if not latest:
        return jsonify({"error": "No existing assessment found"}), 400
        
    data = request.get_json() or {}
    new_weights = {
        'interests': float(data.get('interests', 30)),
        'skills': float(data.get('skills', 30)),
        'tools': float(data.get('tools', 15)),
        'education': float(data.get('education', 15)),
        'work_preferences': float(data.get('work_preferences', 10)),
        'salary': float(data.get('salary', 0)),
        'job_outlook': float(data.get('job_outlook', 0))
    }
    
    normalized = normalize_weights(new_weights)
    recalculated = get_recommendations(latest['answers'], custom_weights=normalized)
    
    return jsonify({
        "status": "success",
        "normalized_weights": normalized,
        "recommendations": recalculated[:10]
    })

# ----------------- CAREERS EXPLORER & DETAILS ----------------- #

@app.route('/careers')
def careers_list():
    category_filter = request.args.get('category', '').strip()
    search_query = request.args.get('q', '').strip()
    
    if search_query:
        careers = search_careers(search_query)
    elif category_filter:
        careers = get_careers_by_category(category_filter)
    else:
        careers = get_all_careers()
        
    return render_template('careers_list.html', careers=careers, selected_category=category_filter, search_query=search_query)

@app.route('/career/<career_id>')
def career_detail(career_id):
    career = get_career_by_id(career_id)
    if not career:
        flash("Career record not found.", "warning")
        return redirect(url_for('careers_list'))
        
    # Check if student has taken assessment to show personalized readiness and why-not insights
    latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    personalized_match = None
    if latest:
        personalized_match = calculate_career_match(latest['answers'], career, normalize_weights(latest.get('weights')))
        
    related = [get_career_by_id(rid) for rid in career.get('related_careers', []) if get_career_by_id(rid)]
    is_saved = career_id in get_saved_career_ids(session.get('user_id')) if session.get('user_id') else False
    
    return render_template('career_detail.html', career=career, personalized_match=personalized_match, related=related, is_saved=is_saved)

# ----------------- CAREER COMPARISON ----------------- #

@app.route('/compare')
def compare():
    latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    suggested_careers = latest.get('results', []) if latest else []
    
    # Default to top suggested careers if available
    default_c1 = suggested_careers[0]['career_id'] if len(suggested_careers) > 0 else 'software-developers'
    default_c2 = suggested_careers[1]['career_id'] if len(suggested_careers) > 1 else 'data-scientists'
    
    c1_id = request.args.get('c1', default_c1)
    c2_id = request.args.get('c2', default_c2)
    c3_id = request.args.get('c3', '')
    
    all_careers = get_all_careers()
    c1 = get_career_by_id(c1_id) or all_careers[0]
    c2 = get_career_by_id(c2_id) or (all_careers[1] if len(all_careers) > 1 else c1)
    c3 = get_career_by_id(c3_id) if c3_id else None
    
    # Calculate personalized match scores for compared careers if user took assessment
    c1_match = None
    c2_match = None
    c3_match = None
    if latest:
        norm_w = normalize_weights(latest.get('weights'))
        c1_match = calculate_career_match(latest['answers'], c1, norm_w)
        c2_match = calculate_career_match(latest['answers'], c2, norm_w)
        if c3:
            c3_match = calculate_career_match(latest['answers'], c3, norm_w)
            
    return render_template(
        'compare.html',
        c1=c1, c2=c2, c3=c3,
        c1_match=c1_match, c2_match=c2_match, c3_match=c3_match,
        suggested_careers=suggested_careers,
        all_careers=all_careers
    )

# ----------------- SKILL GAP ANALYSIS ----------------- #

@app.route('/skill-gap')
@app.route('/skill-gap/<career_id>')
def skill_gap(career_id=None):
    all_careers = get_all_careers()
    latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    
    if not career_id:
        if latest and latest.get('results'):
            career_id = latest['results'][0]['career_id']
        else:
            career_id = all_careers[0]['id'] if all_careers else None
            
    career = get_career_by_id(career_id)
    if not career:
        flash("Career not found.", "warning")
        return redirect(url_for('careers_list'))
        
    analysis = None
    if latest:
        analysis = calculate_career_match(latest['answers'], career, normalize_weights(latest.get('weights')))
    
    # Task evidence
    trials = get_trial_results(user_id=session.get('user_id'), session_id=session.get('session_id'))
    
    return render_template('skill_gap.html', career=career, analysis=analysis, all_careers=all_careers, trials=trials)

# ----------------- CAREER ROADMAP ----------------- #

@app.route('/roadmap')
@app.route('/roadmap/<career_id>')
def roadmap(career_id=None):
    all_careers = get_all_careers()
    if not career_id:
        latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
        if latest and latest.get('results'):
            career_id = latest['results'][0]['career_id']
        else:
            career_id = 'software-developers'
            
    career = get_career_by_id(career_id) or get_all_careers()[0]
    return render_template('roadmap.html', career=career, all_careers=all_careers)

# ----------------- CAREER TRIAL LAB ----------------- #

@app.route('/trial-lab')
def trial_lab_index():
    user_id = session.get('user_id')
    session_id = session.get('session_id')
    user_trials = get_trial_results(user_id=user_id, session_id=session_id)
    completed_tracks = {t['career_track']: t for t in user_trials}
    return render_template('trial_lab_index.html', tracks=TRIAL_LAB_TRACKS, completed_tracks=completed_tracks)

@app.route('/trial-lab/<track_id>')
def trial_lab_task(track_id):
    track = TRIAL_LAB_TRACKS.get(track_id)
    if not track:
        flash("Trial Lab track not found.", "danger")
        return redirect(url_for('trial_lab_index'))
    return render_template('trial_lab_task.html', track=track)

@app.route('/api/submit-lab', methods=['POST'])
def api_submit_lab():
    data = request.get_json() or {}
    track_id = data.get('track_id')
    answers = data.get('answers', {})
    
    result = evaluate_lab_submission(track_id, answers)
    if not result:
        return jsonify({"error": "Invalid lab track"}), 400
        
    user_id = session.get('user_id')
    session_id = session.get('session_id')
    
    save_trial_result(user_id, session_id, track_id, result['score'], result['max_score'], answers, result['summary'])
    
    # Award badge if user is logged in
    badge_awarded = False
    if user_id and result.get('badge_key'):
        badge_awarded = award_badge(user_id, result['badge_key'], result['badge_title'], "bi-award")
        
    result['badge_awarded'] = badge_awarded
    return jsonify(result)

# ----------------- SELF-RATING VS EVIDENCE CHECK ----------------- #

@app.route('/evidence-check')
def evidence_check():
    latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    trials = get_trial_results(user_id=session.get('user_id'), session_id=session.get('session_id'))
    
    # Map trial performances
    trial_map = {}
    for t in trials:
        track = t['career_track']
        if track not in trial_map: # keep latest
            trial_map[track] = t
            
    # Pair self-ratings with lab scores
    student_skills = latest.get('answers', {}).get('skills', {}) if latest else {}
    
    comparison = [
        {
            "domain": "Software Development & Python",
            "self_skill_name": "Python",
            "self_rating": student_skills.get("Python", 0),
            "trial_key": "software_developer",
            "trial_data": trial_map.get("software_developer"),
            "feedback": "Practical tasks evaluate syntax edge-cases and algorithmic tradeoffs. Continuous hands-on debugging bridges self-perception and real-world execution."
        },
        {
            "domain": "Data Analysis & Interpretation",
            "self_skill_name": "Data Analysis",
            "self_rating": student_skills.get("Data Analysis", 0),
            "trial_key": "data_analyst",
            "trial_data": trial_map.get("data_analyst"),
            "feedback": "Data analysis requires both statistical arithmetic and contextual domain intuition to spot anomalies in operational datasets."
        },
        {
            "domain": "Cybersecurity & Incident Awareness",
            "self_skill_name": "Problem-Solving",
            "self_rating": student_skills.get("Problem-Solving", 0),
            "trial_key": "cybersecurity",
            "trial_data": trial_map.get("cybersecurity"),
            "feedback": "Security involves adversarial thinking and careful header/authentication inspection beyond general troubleshooting."
        },
        {
            "domain": "UI/UX & Accessibility",
            "self_skill_name": "HTML/CSS/JavaScript",
            "self_rating": student_skills.get("HTML/CSS/JavaScript", 0),
            "trial_key": "ui_ux",
            "trial_data": trial_map.get("ui_ux"),
            "feedback": "Visual interface design balances aesthetic styling with strict accessibility standards (contrast ratios, cognitive load, user feedback)."
        }
    ]
    
    return render_template('evidence_check.html', comparison=comparison, latest=latest, trials=trials)

# ----------------- WHAT-IF CAREER SIMULATOR ----------------- #

@app.route('/simulator')
def simulator():
    latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    if not latest:
        # Provide default baseline so student can experiment immediately
        baseline_answers = {
            "education": {"qualification": "BCA", "semester": "Semester 3"},
            "interests": ["Programming and software development", "Data analysis and visualisation"],
            "skills": {"Python": 2, "SQL": 2, "HTML/CSS/JavaScript": 2, "Data Analysis": 2, "Networking Fundamentals": 1},
            "tools": ["VS Code", "Python / Jupyter Notebook"],
            "work_preferences": {"coding_intensity": "Moderate", "work_type": "Application Building", "analytical_creative": "Both", "independence": "Balanced"}
        }
        baseline_results = get_recommendations(baseline_answers)[:5]
    else:
        baseline_answers = latest.get('answers', {})
        baseline_results = latest.get('results', [])[:5]
    
    return render_template('simulator.html', baseline_answers=baseline_answers, baseline_results=baseline_results)

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    if not latest:
        # Default baseline if student jumped straight into simulator
        baseline_answers = {
            "education": {"qualification": "BCA", "semester": "Semester 3"},
            "interests": ["Programming and software development", "Data analysis and visualisation"],
            "skills": {"Python": 2, "SQL": 2, "HTML/CSS/JavaScript": 2, "Data Analysis": 2, "Networking Fundamentals": 1},
            "tools": ["VS Code", "Python / Jupyter Notebook"],
            "work_preferences": {"coding_intensity": "Moderate", "work_type": "Application Building", "analytical_creative": "Both", "independence": "Balanced"}
        }
        baseline_weights = normalize_weights()
        baseline_results = get_recommendations(baseline_answers, custom_weights=baseline_weights)[:5]
        latest = {
            'answers': baseline_answers,
            'weights': baseline_weights,
            'results': baseline_results
        }
        
    data = request.get_json() or {}
    simulated_answers = json.loads(json.dumps(latest['answers'])) # deep copy
    
    # Apply simulated modifications
    if 'skills' in data:
        for sk, val in data['skills'].items():
            simulated_answers['skills'][sk] = int(val)
            
    if 'tools' in data:
        simulated_answers['tools'] = data['tools']
        
    if 'coding_intensity' in data:
        simulated_answers['work_preferences']['coding_intensity'] = data['coding_intensity']
        
    custom_weights = data.get('weights', latest.get('weights'))
    normalized = normalize_weights(custom_weights)
    
    # Calculate baseline and simulated
    baseline_results = latest['results'][:5]
    simulated_results = get_recommendations(simulated_answers, custom_weights=normalized)[:5]
    
    # Calculate diff
    baseline_map = {r['career_id']: r for r in latest['results']}
    diffs = []
    for rank_idx, sim_item in enumerate(simulated_results):
        cid = sim_item['career_id']
        base_item = baseline_map.get(cid)
        old_score = base_item['match_score'] if base_item else 0.0
        score_diff = round(sim_item['match_score'] - old_score, 1)
        diffs.append({
            "career_id": cid,
            "display_name": sim_item['display_name'],
            "new_rank": rank_idx + 1,
            "simulated_score": sim_item['match_score'],
            "baseline_score": old_score,
            "score_diff": score_diff,
            "status": "higher" if score_diff > 0 else ("lower" if score_diff < 0 else "neutral")
        })
        
    # Award simulator badge if user logged in
    if session.get('user_id'):
        award_badge(session['user_id'], "simulator_strategist", "Simulator Strategist", "bi-sliders2")
        
    return jsonify({
        "status": "success",
        "diffs": diffs,
        "simulated_top": simulated_results
    })

# ----------------- CAREER REALITY CHECK & WHY NOT ----------------- #

@app.route('/reality-check')
@app.route('/reality-check/<career_id>')
def reality_check(career_id=None):
    all_careers = get_all_careers()
    if not career_id:
        career_id = 'software-developers'
    career = get_career_by_id(career_id) or all_careers[0]
    
    c2_id = request.args.get('compare_with')
    c2 = get_career_by_id(c2_id) if c2_id else None
    
    return render_template('reality_check.html', career=career, compare_career=c2, all_careers=all_careers)

@app.route('/why-not/<career_id>')
def why_not(career_id):
    career = get_career_by_id(career_id)
    if not career:
        flash("Career not found.", "warning")
        return redirect(url_for('careers_list'))
        
    latest = get_latest_assessment(user_id=session.get('user_id'), session_id=session.get('session_id'))
    analysis = None
    if latest:
        analysis = calculate_career_match(latest['answers'], career, normalize_weights(latest.get('weights')))
        
    return render_template('why_not.html', career=career, analysis=analysis, latest=latest)

# ----------------- CAREER SWITCH BRIDGE ----------------- #

@app.route('/switch-bridge')
def switch_bridge():
    all_careers = get_all_careers()
    from_id = request.args.get('from', 'web-developers')
    to_id = request.args.get('to', 'data-scientists')
    
    bridge = compute_career_bridge(from_id, to_id)
    
    if session.get('user_id'):
        award_badge(session['user_id'], "bridge_explorer", "Bridge Explorer", "bi-signpost-split")
        
    return render_template('switch_bridge.html', bridge=bridge, all_careers=all_careers, from_id=from_id, to_id=to_id)

# ----------------- CAREER QUEST & GAMIFICATION ----------------- #

@app.route('/quest')
def quest():
    user_id = session.get('user_id')
    earned_badges = get_user_badges(user_id) if user_id else []
    earned_keys = {b['badge_key']: b for b in earned_badges}
    
    missions_with_status = []
    total_xp = 0
    for m in QUEST_MISSIONS:
        is_earned = m['key'] in earned_keys
        if is_earned:
            total_xp += m['xp']
        missions_with_status.append({
            **m,
            "completed": is_earned,
            "earned_at": earned_keys[m['key']]['earned_at'] if is_earned else None
        })
        
    trials = get_trial_results(user_id=user_id, session_id=session.get('session_id'))
    
    return render_template('quest.html', missions=missions_with_status, earned_count=len(earned_badges), total_xp=total_xp, trials=trials)

# ----------------- FUTURE PATH PREVIEW ----------------- #

@app.route('/future-paths')
def future_paths():
    p1_key = request.args.get('p1', 'data_path')
    p2_key = request.args.get('p2', 'web_path')
    
    path_a = FUTURE_PATHS.get(p1_key, FUTURE_PATHS['data_path'])
    path_b = FUTURE_PATHS.get(p2_key, FUTURE_PATHS['web_path'])
    
    return render_template('future_paths.html', path_a=path_a, path_b=path_b, all_paths=FUTURE_PATHS)

# ----------------- SAVED CAREERS & DASHBOARD ----------------- #

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    saved_ids = get_saved_career_ids(user_id) if user_id else []
    saved_careers = [get_career_by_id(cid) for cid in saved_ids if get_career_by_id(cid)]
    assessments = get_user_assessments(user_id) if user_id else []
    latest = get_latest_assessment(user_id=user_id, session_id=session.get('session_id'))
    badges = get_user_badges(user_id) if user_id else []
    trials = get_trial_results(user_id=user_id, session_id=session.get('session_id'))
    
    return render_template('dashboard.html', saved_careers=saved_careers, assessments=assessments, latest=latest, badges=badges, trials=trials)

@app.route('/api/save-career', methods=['POST'])
def api_save_career():
    if not session.get('user_id'):
        return jsonify({"status": "error", "message": "Please log in or register to save careers to your permanent dashboard."}), 401
        
    data = request.get_json() or {}
    career_id = data.get('career_id')
    action = data.get('action', 'toggle')
    user_id = session['user_id']
    
    saved_ids = get_saved_career_ids(user_id)
    if career_id in saved_ids:
        unsave_career(user_id, career_id)
        is_saved = False
    else:
        save_career(user_id, career_id)
        is_saved = True
        if len(saved_ids) + 1 >= 2:
            award_badge(user_id, "career_scholar", "Career Scholar", "bi-bookmark-star")
            
    return jsonify({"status": "success", "is_saved": is_saved})

# ----------------- DATASET & ADMIN MANAGEMENT ----------------- #

@app.route('/admin/dataset', methods=['GET', 'POST'])
def admin_dataset():
    report = None
    if request.method == 'POST' and 'dataset_file' in request.files:
        file = request.files['dataset_file']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            report = validate_and_import_dataset(save_path)
            flash(f"Validation completed. {report['valid_careers_imported']} valid career records detected.", "info")
            
    careers = get_all_careers()
    
    selected_career = request.args.get('career_id', 'all')
    search = request.args.get('search', '').strip()
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
        
    limit = 25
    offset = (page - 1) * limit
    
    records = get_career_records(career_id=selected_career, limit=limit, offset=offset, search=search)
    filtered_count = get_career_records_count(career_id=selected_career, search=search)
    total_records = get_career_records_count()
    
    total_pages = max(1, (filtered_count + limit - 1) // limit)
    
    return render_template(
        'admin_dataset.html',
        careers=careers,
        report=report,
        records=records,
        filtered_count=filtered_count,
        total_records=total_records,
        selected_career=selected_career,
        search=search,
        page=page,
        total_pages=total_pages
    )

@app.route('/admin/export-csv')
def admin_export_csv():
    csv_file = export_careers_to_csv()
    return send_file(csv_file, as_attachment=True, download_name="PathWise_Careers_Master.csv")

@app.route('/admin/export-all-records-csv')
def admin_export_all_records_csv():
    career_id = request.args.get('career_id')
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'career_records_38000.csv')
    if career_id and career_id != 'all':
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        records = get_career_records(career_id=career_id, limit=2000, offset=0)
        if records:
            writer.writerow(list(records[0].keys()))
            for r in records:
                writer.writerow(list(r.values()))
        output.seek(0)
        mem = io.BytesIO(output.getvalue().encode('utf-8'))
        return send_file(mem, as_attachment=True, download_name=f"PathWise_{career_id}_1000_records.csv", mimetype='text/csv')
    return send_file(csv_path, as_attachment=True, download_name="PathWise_38000_Career_Records_Master.csv", mimetype='text/csv')

if __name__ == '__main__':
    # Server accessible locally and across devices on the same Wi-Fi network
    app.run(debug=True, host='0.0.0.0', port=5000)
