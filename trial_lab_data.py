TRIAL_LAB_TRACKS = {
    "data_analyst": {
        "track_id": "data_analyst",
        "title": "Data Analyst Practical Lab",
        "career_id": "data-scientists", # or business-intelligence-analysts
        "career_name": "Data Analyst / Business Intelligence Analyst",
        "badge_key": "data_detective",
        "badge_title": "Data Detective",
        "icon": "bi-graph-up-arrow",
        "overview": "In this lab, you will analyze a practical college campus cafeteria sales dataset, interpret trends, calculate metrics, and identify anomalies just like a junior data analyst.",
        "dataset_sample": [
            {"Day": "Monday", "Total_Orders": 320, "Revenue_INR": 28800, "Avg_Order_Value": 90, "Payment_Method": "UPI (78%)"},
            {"Day": "Tuesday", "Total_Orders": 345, "Revenue_INR": 31050, "Avg_Order_Value": 90, "Payment_Method": "UPI (80%)"},
            {"Day": "Wednesday", "Total_Orders": 410, "Revenue_INR": 34850, "Avg_Order_Value": 85, "Payment_Method": "UPI (82%)"},
            {"Day": "Thursday", "Total_Orders": 390, "Revenue_INR": 35100, "Avg_Order_Value": 90, "Payment_Method": "UPI (81%)"},
            {"Day": "Friday", "Total_Orders": 520, "Revenue_INR": 52000, "Avg_Order_Value": 100, "Payment_Method": "UPI (85%)"},
            {"Day": "Saturday", "Total_Orders": 110, "Revenue_INR": 9900, "Avg_Order_Value": 90, "Payment_Method": "Cash (60%)"}
        ],
        "questions": [
            {
                "id": "da_q1",
                "question": "Looking at the cafeteria sales table above, which day generated the highest total revenue, and what was the apparent driver?",
                "options": [
                    {"val": "A", "text": "Wednesday, because it had higher average order value than Friday"},
                    {"val": "B", "text": "Friday, driven by both peak order volume (520 orders) and the highest average order value (₹100)"},
                    {"val": "C", "text": "Saturday, due to high percentage of cash transactions"},
                    {"val": "D", "text": "Thursday, because it maintained exactly ₹90 per order"}
                ],
                "correct": "B",
                "explanation": "Friday generated ₹52,000, which is the highest revenue. The driver was a surge in order volume (520 orders) along with an elevated average order value (₹100 vs typical ₹90)."
            },
            {
                "id": "da_q2",
                "question": "Suppose the cafeteria manager wants to run a SQL query to find days where Total_Orders exceeded 350. Which query is syntactically and logically correct?",
                "options": [
                    {"val": "A", "text": "SELECT Day, Total_Orders FROM cafeteria_sales WHERE Total_Orders > 350;"},
                    {"val": "B", "text": "FILTER cafeteria_sales WITH Total_Orders > 350 ORDER BY Day;"},
                    {"val": "C", "text": "SELECT ALL FROM cafeteria_sales HAVING Total_Orders > 350;"},
                    {"val": "D", "text": "GET Day WHERE Total_Orders > 350 FROM cafeteria_sales;"}
                ],
                "correct": "A",
                "explanation": "Standard SQL uses 'SELECT column_names FROM table_name WHERE condition;'. The HAVING clause is used after GROUP BY for aggregated columns, not individual rows."
            },
            {
                "id": "da_q3",
                "question": "What business anomaly on Saturday warrants further data investigation by the analyst?",
                "options": [
                    {"val": "A", "text": "Average order value is too high compared to Monday"},
                    {"val": "B", "text": "Significant volume drop (110 orders) and a sharp reversal in payment method preference toward Cash (60%) compared to weekdays (~80% UPI)"},
                    {"val": "C", "text": "Revenue calculation does not match orders multiplied by ₹90"},
                    {"val": "D", "text": "UPI transactions were completely disabled on Saturday"}
                ],
                "correct": "B",
                "explanation": "A sharp 78% drop in order volume combined with payment behavior flipping from 80%+ digital to majority cash is a classic operational anomaly worth investigating (e.g. UPI network downtime or weekend campus attendance)."
            }
        ]
    },
    
    "software_developer": {
        "track_id": "software_developer",
        "title": "Software Developer Practical Lab",
        "career_id": "software-developers",
        "career_name": "Software Developer / Application Engineer",
        "badge_key": "code_architect",
        "badge_title": "Code Architect",
        "icon": "bi-code-slash",
        "overview": "Experience day-to-day software development tasks: inspecting Python logic, identifying edge cases, and selecting clean data structures.",
        "code_snippet": '''def calculate_student_discount(cart_total, is_student, coupon_code):
    discount = 0.0
    if is_student:
        discount = 0.15  # 15% student discount
    
    if coupon_code == "TECH10":
        discount = 0.10  # 10% coupon
    
    final_amount = cart_total * (1 - discount)
    return round(final_amount, 2)
''',
        "questions": [
            {
                "id": "sd_q1",
                "question": "Review the Python function above. What logical bug occurs when a verified student (`is_student=True`) enters coupon code 'TECH10'?",
                "options": [
                    {"val": "A", "text": "The function throws an indentation error at runtime"},
                    {"val": "B", "text": "The 10% coupon overwrites the student discount, reducing the student's savings from 15% to 10%"},
                    {"val": "C", "text": "The function returns a negative final amount"},
                    {"val": "D", "text": "The round() function fails on float variables"}
                ],
                "correct": "B",
                "explanation": "The second `if` statement replaces `discount` with 0.10 instead of either stacking them or keeping the higher discount (e.g., using `discount = max(discount, 0.10)` or `discount += 0.10`)."
            },
            {
                "id": "sd_q2",
                "question": "You need to store a million student roll numbers and quickly check whether a specific roll number has submitted an assignment. Which data structure provides O(1) average lookup time?",
                "options": [
                    {"val": "A", "text": "A standard Python List"},
                    {"val": "B", "text": "A Python Set (or Hash Table / Dict keys)"},
                    {"val": "C", "text": "A singly Linked List"},
                    {"val": "D", "text": "A sorted Array"}
                ],
                "correct": "B",
                "explanation": "In Python, sets and dictionaries are implemented using hash tables, giving average O(1) membership lookup `x in my_set`, compared to O(N) for linear list scans."
            },
            {
                "id": "sd_q3",
                "question": "When collaborating with a team using Git, which command creates and switches into a new branch named 'feature-auth'?",
                "options": [
                    {"val": "A", "text": "git commit -m 'feature-auth'"},
                    {"val": "B", "text": "git checkout -b feature-auth (or git switch -c feature-auth)"},
                    {"val": "C", "text": "git push origin feature-auth"},
                    {"val": "D", "text": "git merge feature-auth"}
                ],
                "correct": "B",
                "explanation": "`git checkout -b <branch_name>` or `git switch -c <branch_name>` simultaneously creates the branch from current HEAD and switches your working tree to it."
            }
        ]
    },

    "cybersecurity": {
        "track_id": "cybersecurity",
        "title": "Cybersecurity & Defense Lab",
        "career_id": "information-security-analysts",
        "career_name": "Cybersecurity Analyst / Information Security Analyst",
        "badge_key": "cyber_sentinel",
        "badge_title": "Cyber Sentinel",
        "icon": "bi-shield-check",
        "overview": "Triage a safe, realistic security scenario. Practice phishing email inspection, authentication policy evaluation, and incident awareness without running dangerous tools.",
        "scenario_text": '''From: IT-Support-Desk <service-alert@update-college-portal.net>
To: student@university.edu.in
Subject: URGENT: Your student portal account will expire in 2 hours!
Header Analysis:
SPF: Neutral | DKIM: None | Return-Path: <spoofed@mailer-unverified.com>

Body:
Dear Student,
We detected suspicious activity on your BCA LMS portal. Please click the secure link below immediately to re-verify your password and prevent account suspension:
http://portal-verify.university-edu.tk/login.php
Thank you,
IT Department''',
        "questions": [
            {
                "id": "cs_q1",
                "question": "Analyze the suspicious email scenario above. Which two indicators are red flags of a credential harvesting phishing attack?",
                "options": [
                    {"val": "A", "text": "The email is addressed to student@university.edu.in and mentions the BCA LMS"},
                    {"val": "B", "text": "Artificial urgency ('expire in 2 hours') and mismatched sender domain ('update-college-portal.net' / '.tk' link) with missing DKIM/SPF verification"},
                    {"val": "C", "text": "The signature says 'Thank you, IT Department'"},
                    {"val": "D", "text": "The email was delivered on a weekday"}
                ],
                "correct": "B",
                "explanation": "Phishers rely on psychological urgency ('2 hours left') and deceptive lookalike domains (`.tk`, `update-college-portal.net`). SPF neutral/DKIM none further prove the sender identity was forged."
            },
            {
                "id": "cs_q2",
                "question": "What is the most effective security mitigation to protect student accounts from compromised passwords?",
                "options": [
                    {"val": "A", "text": "Requiring passwords to be changed every single week"},
                    {"val": "B", "text": "Implementing Multi-Factor Authentication (MFA / 2FA) using an authenticator app or hardware token"},
                    {"val": "C", "text": "Hiding the login page URL from the search engines"},
                    {"val": "D", "text": "Blocking all student Wi-Fi connections after 6 PM"}
                ],
                "correct": "B",
                "explanation": "Multi-Factor Authentication (MFA) prevents over 99% of automated credential stuffing and password-theft attacks because an attacker cannot access the second factor."
            },
            {
                "id": "cs_q3",
                "question": "In the CIA Triad of Information Security, what principle is violated if an unauthorized attacker modifies database grades without detection?",
                "options": [
                    {"val": "A", "text": "Confidentiality"},
                    {"val": "B", "text": "Integrity"},
                    {"val": "C", "text": "Availability"},
                    {"val": "D", "text": "Non-Repudiation only"}
                ],
                "correct": "B",
                "explanation": "Integrity ensures that data is accurate, authentic, and protected from unauthorized modification or tampering."
            }
        ]
    },

    "ui_ux": {
        "track_id": "ui_ux",
        "title": "UI/UX & Digital Product Design Lab",
        "career_id": "web-and-digital-interface-designers",
        "career_name": "UI/UX Designer / Interface Specialist",
        "badge_key": "experience_craftsman",
        "badge_title": "UX Craftsman",
        "icon": "bi-palette",
        "overview": "Examine usability challenges, contrast requirements, and ergonomic design principles on mobile application screens.",
        "ui_critique_scenario": '''You are redesigning the BCA Exam Registration Mobile Flow:
Current screen issues reported by students:
1. 'Confirm Registration' button is bright red and identical in size to 'Cancel and Delete Application'.
2. Required fields have light grey text (#D0D0D0) on white background (#FFFFFF).
3. The form has 24 consecutive input fields on a single infinite-scrolling screen with no progress indicator.
4. Error messages only appear after clicking submit, saying: 'Form has errors' with no field highlighting.''',
        "questions": [
            {
                "id": "ux_q1",
                "question": "Regarding the light grey text (#D0D0D0) on white (#FFFFFF), why does this violate WCAG 2.1 accessibility guidelines?",
                "options": [
                    {"val": "A", "text": "Grey is not a modern color palette choice for college apps"},
                    {"val": "B", "text": "The contrast ratio is approximately 1.4:1, far below the required minimum 4.5:1 for normal text, making it unreadable for low-vision users"},
                    {"val": "C", "text": "Light grey text consumes more battery on OLED mobile screens"},
                    {"val": "D", "text": "Screen readers cannot parse text that is lighter than #999999"}
                ],
                "correct": "B",
                "explanation": "WCAG 2.1 Level AA mandates a minimum contrast ratio of 4.5:1 for standard body text. A 1.4:1 ratio causes severe readability barriers in bright sunlight and for users with visual impairments."
            },
            {
                "id": "ux_q2",
                "question": "How should a UX designer improve the 24-field infinite form to reduce cognitive load and drop-off rate?",
                "options": [
                    {"val": "A", "text": "Make all form fields mandatory with asterisk icons"},
                    {"val": "B", "text": "Break the form into 3-4 logical stepped stages (Personal Info -> Academic Details -> Subjects -> Review) with a clear progress tracker"},
                    {"val": "C", "text": "Reduce the font size of all 24 fields to fit on a single screen without scrolling"},
                    {"val": "D", "text": "Replace all input fields with free-form multi-line textareas"}
                ],
                "correct": "B",
                "explanation": "Chunking long complex forms into logical stepped milestones (Stepped Wizard / Stepper) significantly lowers cognitive overwhelm and provides clear sense of completion."
            },
            {
                "id": "ux_q3",
                "question": "What is the primary usability problem with having the primary 'Confirm Registration' button styled in bright red right next to 'Cancel'?",
                "options": [
                    {"val": "A", "text": "Red is universally recognized as a warning or destructive action; users may hesitate or accidentally cancel, creating high anxiety"},
                    {"val": "B", "text": "Red buttons cannot be rendered by Bootstrap 5 on mobile browsers"},
                    {"val": "C", "text": "Red color slows down page loading speeds"},
                    {"val": "D", "text": "Primary actions must always be styled as plain text links"}
                ],
                "correct": "A",
                "explanation": "In design psychology, red signals danger, deletion, or irreversible action. Primary positive actions should use dominant brand colors (e.g. blue or teal), with secondary/destructive actions styled distinctly to prevent catastrophic slips."
            }
        ]
    }
}

def evaluate_lab_submission(track_id, submitted_answers):
    track = TRIAL_LAB_TRACKS.get(track_id)
    if not track:
        return None
        
    score = 0
    total = len(track['questions'])
    question_feedback = []
    
    for q in track['questions']:
        qid = q['id']
        student_ans = submitted_answers.get(qid, '')
        is_correct = (student_ans == q['correct'])
        if is_correct:
            score += 1
            
        question_feedback.append({
            "id": qid,
            "question": q['question'],
            "student_answer": student_ans,
            "correct_answer": q['correct'],
            "is_correct": is_correct,
            "explanation": q['explanation']
        })
        
    percentage = round((score / total) * 100, 1)
    
    if percentage >= 100:
        summary = "Exceptional performance! You demonstrated outstanding clarity on core concepts."
    elif percentage >= 66:
        summary = "Solid foundational intuition! You correctly reasoned through the majority of scenarios."
    else:
        summary = "Good initial exploration. Practical scenarios involve domain nuances that become clearer with focused practice."
        
    return {
        "track_id": track_id,
        "track_title": track['title'],
        "career_id": track['career_id'],
        "career_name": track['career_name'],
        "score": score,
        "max_score": total,
        "percentage": percentage,
        "summary": summary,
        "feedback_items": question_feedback,
        "badge_key": track.get('badge_key'),
        "badge_title": track.get('badge_title')
    }
