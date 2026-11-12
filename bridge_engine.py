from data_manager import get_career_by_id

def compute_career_bridge(from_id, to_id):
    c1 = get_career_by_id(from_id)
    c2 = get_career_by_id(to_id)
    
    if not c1 or not c2:
        return None
        
    s1 = set(s.lower() for s in c1.get('technical_skills', []))
    s2 = set(s.lower() for s in c2.get('technical_skills', []))
    
    t1 = set(t.lower() for t in c1.get('software_tools', []))
    t2 = set(t.lower() for t in c2.get('software_tools', []))
    
    # Overlapping skills
    common_skills = []
    for skill in c2.get('technical_skills', []):
        if skill.lower() in s1 or any(word in s1 for word in skill.lower().split() if len(word) > 3):
            common_skills.append(skill)
            
    # Gap skills (in target, not in source)
    gap_skills = [s for s in c2.get('technical_skills', []) if s not in common_skills]
    
    # Overlapping tools
    common_tools = []
    for tool in c2.get('software_tools', []):
        if tool.lower() in t1 or any(word in t1 for word in tool.lower().split() if len(word) > 3):
            common_tools.append(tool)
            
    # Gap tools
    gap_tools = [t for t in c2.get('software_tools', []) if t not in common_tools][:8]
    
    # Overlap metric
    total_target_reqs = max(1, len(c2.get('technical_skills', [])) + len(c2.get('software_tools', [])[:10]))
    matched_reqs = len(common_skills) + len(common_tools)
    overlap_pct = min(92, max(18, round((matched_reqs / total_target_reqs) * 100)))
    
    # Transition feasibility rating
    if overlap_pct >= 60:
        difficulty = "Moderate & Highly Feasible"
        est_timeline = "3 to 5 Months of Targeted Study"
        difficulty_badge = "success"
    elif overlap_pct >= 35:
        difficulty = "Intermediate Transition"
        est_timeline = "6 to 9 Months of Structured Practice"
        difficulty_badge = "primary"
    else:
        difficulty = "Comprehensive Cross-Domain Pivot"
        est_timeline = "9 to 12 Months of Intensive Foundations"
        difficulty_badge = "warning"
        
    bridge_phases = [
        {
            "phase": "Phase 1: Capitalize on Transferable Strengths",
            "focus": f"Leverage existing proficiency in {', '.join(common_skills[:3]) if common_skills else 'analytical problem-solving'} and {common_tools[0] if common_tools else 'basic computing tools'}.",
            "action": "Map how your current daily workflows or academic coursework apply to the target role's problem space."
        },
        {
            "phase": "Phase 2: Close High-Priority Skill Gaps",
            "focus": f"Acquire core competencies in {', '.join(gap_skills[:3]) if gap_skills else 'advanced domain methodologies'}.",
            "action": f"Begin hands-on exercises using {gap_tools[0] if gap_tools else 'industry-standard tools'} and document your learning weekly."
        },
        {
            "phase": "Phase 3: Build a Hybrid Bridge Project",
            "focus": f"Create an end-to-end capstone project combining your background in {c1['display_name']} with {c2['display_name']} principles.",
            "action": "Publish the project with clean code, README documentation, and a live demonstration or presentation deck."
        },
        {
            "phase": "Phase 4: Resume Realignment & Technical Interviews",
            "focus": "Tailor your CV and LinkedIn to emphasize transferable outcomes and newly built project deliverables.",
            "action": "Practice explaining why your unique interdisciplinary background makes you a versatile candidate for the target role."
        }
    ]
    
    return {
        "from_career": c1,
        "to_career": c2,
        "overlap_percentage": overlap_pct,
        "difficulty": difficulty,
        "difficulty_badge": difficulty_badge,
        "estimated_timeline": est_timeline,
        "common_skills": common_skills,
        "gap_skills": gap_skills,
        "common_tools": common_tools[:8],
        "gap_tools": gap_tools,
        "bridge_phases": bridge_phases
    }
