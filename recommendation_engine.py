import json
import os
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'careers.json')

def load_careers_master():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# Normalize weights so they always sum to 1.0
def normalize_weights(weights_dict=None):
    defaults = {
        'interests': 0.30,
        'skills': 0.30,
        'tools': 0.15,
        'education': 0.15,
        'work_preferences': 0.10,
        'salary': 0.0,
        'job_outlook': 0.0
    }
    if not weights_dict:
        return defaults
    
    merged = {}
    for k in defaults:
        val = weights_dict.get(k, defaults[k])
        try:
            merged[k] = max(0.0, float(val))
        except (ValueError, TypeError):
            merged[k] = defaults[k]
            
    total = sum(merged.values())
    if total <= 0:
        return defaults
        
    normalized = {k: round(v / total, 4) for k, v in merged.items()}
    return normalized

def calculate_career_match(student_input, career, weights):
    """
    Calculates transparent match score between student profile and a single career.
    student_input contains:
    - education: { qualification, semester, completed_courses }
    - interests: list of selected interest strings
    - skills: dict of { skill_name: rating_0_to_5 }
    - tools: list of selected tools
    - work_preferences: { coding_intensity, work_type, analytical_creative, independence }
    - goals: list of priorities
    """
    reasons = []
    matched_interests = []
    matched_skills = []
    missing_skills = []
    matched_tools = []
    missing_tools = []
    
    # 1. Interests Score (0 - 1.0)
    career_interest_tags = [t.lower() for t in career.get('interest_tags', [])]
    student_interests = [i.lower() for i in student_input.get('interests', [])]
    
    if student_interests and career_interest_tags:
        common_interests = []
        for s_int in student_interests:
            for c_int in career_interest_tags:
                if s_int in c_int or c_int in s_int or any(w in c_int for w in s_int.split()):
                    common_interests.append(s_int)
                    break
        common_interests = list(dict.fromkeys(common_interests))
        interest_score = min(1.0, len(common_interests) / max(1, min(3, len(career_interest_tags))))
        matched_interests = [s.title() for s in common_interests]
        if interest_score > 0.5:
            reasons.append(f"Strong interest alignment in {', '.join(matched_interests[:2])}.")
    else:
        interest_score = 0.2 # baseline neutral if student provided no interests

    # 2. Skills Score (0 - 1.0)
    # Compare student ratings with career's required technical & O*NET skills
    student_skills = student_input.get('skills', {})
    career_tech_skills = career.get('technical_skills', [])
    
    skill_match_sum = 0
    skills_evaluated = 0
    
    for req_skill in career_tech_skills:
        req_lower = req_skill.lower()
        best_rating = 0
        found = False
        
        for s_name, s_rating in student_skills.items():
            s_lower = s_name.lower()
            # Match tokens (e.g. 'python' matches 'python', 'sql' matches 'sql query')
            if s_lower in req_lower or req_lower in s_lower or any(word in req_lower for word in s_lower.split() if len(word) > 2):
                try:
                    r = float(s_rating)
                    if r > best_rating:
                        best_rating = r
                        found = True
                except:
                    pass
                    
        skills_evaluated += 1
        normalized_rating = min(1.0, best_rating / 5.0)
        skill_match_sum += normalized_rating
        
        if found and best_rating >= 3:
            matched_skills.append({"name": req_skill, "rating": int(best_rating)})
        elif found and best_rating > 0:
            missing_skills.append({"name": req_skill, "current_level": int(best_rating), "status": "Needs Practice"})
        else:
            missing_skills.append({"name": req_skill, "current_level": 0, "status": "Not Learned Yet"})

    skill_score = skill_match_sum / max(1, skills_evaluated)
    if matched_skills:
        top_matched_names = [s['name'] for s in matched_skills[:3]]
        reasons.append(f"Demonstrated foundation in {', '.join(top_matched_names)}.")

    # 3. Tools Score (0 - 1.0)
    student_tools = [t.lower().strip() for t in student_input.get('tools', [])]
    career_tools = [t.lower().strip() for t in career.get('software_tools', [])]
    
    if student_tools and career_tools:
        for ct in career.get('software_tools', []):
            ct_lower = ct.lower()
            if any(st in ct_lower or ct_lower in st for st in student_tools):
                matched_tools.append(ct)
            else:
                missing_tools.append(ct)
        tool_score = min(1.0, len(matched_tools) / max(1, min(4, len(career_tools))))
    else:
        tool_score = 0.2
        missing_tools = career.get('software_tools', [])[:6]

    # 4. Education Score (0 - 1.0)
    student_qual = student_input.get('education', {}).get('qualification', 'BCA').lower()
    career_edu = career.get('education_requirements', '').lower()
    
    if 'bachelor' in career_edu or 'bca' in career_edu or 'some college' in career_edu or 'associate' in career_edu:
        edu_score = 0.95
        reasons.append("Your BCA/Undergraduate curriculum provides direct eligibility for entry-level roles.")
    elif 'master' in career_edu or 'doctoral' in career_edu:
        edu_score = 0.65
        reasons.append("Often seeks postgraduate specialization, but accessible via relevant projects and certifications.")
    else:
        edu_score = 0.85

    # 5. Work Preferences Score (0 - 1.0)
    prefs = student_input.get('work_preferences', {})
    pref_score_items = []
    
    # Coding intensity match
    pref_coding = prefs.get('coding_intensity', 'Moderate').lower()
    career_coding = career.get('coding_intensity', 'Moderate').lower()
    if pref_coding == career_coding:
        pref_score_items.append(1.0)
    elif 'moderate' in [pref_coding, career_coding]:
        pref_score_items.append(0.75)
    else:
        pref_score_items.append(0.4)
        
    # Analytical vs creative
    pref_style = prefs.get('analytical_creative', 'Both').lower()
    career_category = career.get('category', '').lower()
    if 'creative' in pref_style and any(k in career_category for k in ['web', 'design', 'support']):
        pref_score_items.append(1.0)
    elif 'analytical' in pref_style and any(k in career_category for k in ['data', 'security', 'mathematical', 'cloud']):
        pref_score_items.append(1.0)
    else:
        pref_score_items.append(0.8)
        
    pref_score = sum(pref_score_items) / max(1, len(pref_score_items))

    # 6. Optional Salary & Outlook factors (if student sliders increase weight)
    # Normalize salary: 60k to 140k -> 0.0 to 1.0
    wage = career.get('median_salary_usd', 100000)
    salary_score = min(1.0, max(0.0, (wage - 60000) / 80000))
    
    # Normalize outlook: -5% to +35% -> 0.0 to 1.0
    growth = career.get('job_outlook_pct', 7.0)
    outlook_score = min(1.0, max(0.0, (growth + 5) / 40.0))

    # Aggregate weighted score
    final_score = (
        interest_score * weights['interests'] +
        skill_score * weights['skills'] +
        tool_score * weights['tools'] +
        edu_score * weights['education'] +
        pref_score * weights['work_preferences'] +
        salary_score * weights.get('salary', 0.0) +
        outlook_score * weights.get('job_outlook', 0.0)
    )
    
    # Percentage 0 to 100
    match_percentage = round(final_score * 100, 1)
    
    # Determine Readiness Meter level
    if match_percentage >= 72:
        readiness_level = "Better prepared for exploration"
        readiness_badge = "success"
    elif match_percentage >= 48:
        readiness_level = "Developing"
        readiness_badge = "primary"
    else:
        readiness_level = "Foundation to build"
        readiness_badge = "warning"
        
    # Build "Why Not" diagnostic summary if match is moderate or lower
    why_not_reasons = []
    if interest_score < 0.4:
        why_not_reasons.append("Your chosen interests did not prioritize the primary domains of this role.")
    if skill_score < 0.45:
        why_not_reasons.append(f"Several foundational technical skills ({', '.join([s['name'] for s in missing_skills[:2]])}) have not yet been learned or reported.")
    if tool_score < 0.35:
        why_not_reasons.append(f"Familiarity with standard industry tools like {', '.join(missing_tools[:2])} has not been recorded.")
    if pref_score < 0.6:
        why_not_reasons.append(f"Your stated preference for {pref_coding.capitalize()} coding differs from this career's typical {career.get('coding_intensity')} coding intensity.")
    if not why_not_reasons and match_percentage < 65:
        why_not_reasons.append("A balanced general match, but other paths aligned more specifically with your selected skills and tool background.")

    return {
        "career_id": career['id'],
        "soc_code": career['soc_code'],
        "display_name": career['display_name'],
        "category": career['category'],
        "description": career['description'],
        "match_score": match_percentage,
        "readiness_level": readiness_level,
        "readiness_badge": readiness_badge,
        "reasons": reasons if reasons else ["General compatibility based on your technical coursework."],
        "matched_interests": matched_interests,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills[:5],
        "matched_tools": matched_tools[:6],
        "missing_tools": missing_tools[:6],
        "coding_intensity": career.get('coding_intensity', 'Moderate'),
        "median_salary_usd": career.get('median_salary_usd'),
        "median_salary_inr_benchmark": career.get('median_salary_inr_benchmark'),
        "job_outlook_pct": career.get('job_outlook_pct'),
        "education_requirements": career.get('education_requirements'),
        "source_url": career.get('source_url'),
        "score_breakdown": {
            "interests": round(interest_score * 100, 1),
            "skills": round(skill_score * 100, 1),
            "tools": round(tool_score * 100, 1),
            "education": round(edu_score * 100, 1),
            "preferences": round(pref_score * 100, 1),
            "salary": round(salary_score * 100, 1),
            "outlook": round(outlook_score * 100, 1)
        },
        "why_not_analysis": why_not_reasons,
        "next_steps": [
            f"Review the step-by-step roadmap for {career['display_name']}.",
            f"Practice with the relevant hands-on task in the Career Trial Lab.",
            f"Focus your semester project on learning {missing_skills[0]['name'] if missing_skills else 'core domain tools'}."
        ]
    }

def get_recommendations(student_input, custom_weights=None, top_n=5):
    careers = load_careers_master()
    if not careers:
        return []
    
    weights = normalize_weights(custom_weights)
    scored = []
    
    for c in careers:
        match_result = calculate_career_match(student_input, c, weights)
        scored.append(match_result)
        
    scored.sort(key=lambda x: x['match_score'], reverse=True)
    return scored
