import json
import os
import pandas as pd
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'careers.json')
MAX_RECORDS_PER_CAREER = 1000

def get_all_careers():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        careers = json.load(f)
    # Ensure maximum 1000 records/items per career for any nested skills, tools or activities
    for c in careers:
        if 'software_tools' in c and len(c['software_tools']) > MAX_RECORDS_PER_CAREER:
            c['software_tools'] = c['software_tools'][:MAX_RECORDS_PER_CAREER]
        if 'onet_essential_skills' in c and len(c['onet_essential_skills']) > MAX_RECORDS_PER_CAREER:
            c['onet_essential_skills'] = c['onet_essential_skills'][:MAX_RECORDS_PER_CAREER]
        if 'technical_skills' in c and len(c['technical_skills']) > MAX_RECORDS_PER_CAREER:
            c['technical_skills'] = c['technical_skills'][:MAX_RECORDS_PER_CAREER]
        if 'typical_work_activities' in c and len(c['typical_work_activities']) > MAX_RECORDS_PER_CAREER:
            c['typical_work_activities'] = c['typical_work_activities'][:MAX_RECORDS_PER_CAREER]
    return careers

def get_career_by_id(career_id):
    careers = get_all_careers()
    for c in careers:
        if c.get('id') == career_id or c.get('soc_code') == career_id:
            return c
    return None

def get_careers_by_category(category_name):
    careers = get_all_careers()
    return [c for c in careers if c.get('category') == category_name]

def search_careers(query):
    query_l = query.lower().strip()
    careers = get_all_careers()
    results = []
    for c in careers:
        name = c.get('display_name', '').lower()
        desc = c.get('description', '').lower()
        skills = ' '.join(c.get('technical_skills', [])).lower()
        tools = ' '.join(c.get('software_tools', [])).lower()
        cat = c.get('category', '').lower()
        if query_l in name or query_l in desc or query_l in skills or query_l in tools or query_l in cat:
            results.append(c)
    return results

def get_unique_categories():
    careers = get_all_careers()
    categories = list(dict.fromkeys([c.get('category') for c in careers if c.get('category')]))
    return categories

def validate_and_import_dataset(file_path):
    """
    Validates uploaded Excel or CSV file against required career schema.
    Detects duplicates, checks missing columns, normalizes names, reports errors.
    """
    report = {
        "status": "success",
        "total_rows_read": 0,
        "valid_careers_imported": 0,
        "duplicate_rows": 0,
        "rejected_rows": [],
        "missing_columns": [],
        "warnings": []
    }
    
    try:
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
    except Exception as e:
        report["status"] = "error"
        report["warnings"].append(f"Failed to read file: {str(e)}")
        return report

    report["total_rows_read"] = len(df)
    if len(df) > MAX_RECORDS_PER_CAREER:
        report["warnings"].append(f"Dataset exceeds {MAX_RECORDS_PER_CAREER} rows. Processing capped at maximum {MAX_RECORDS_PER_CAREER} records.")
        df = df.iloc[:MAX_RECORDS_PER_CAREER]
    
    # Check essential columns
    col_map = {c.lower().strip(): c for c in df.columns}
    
    # Required conceptual fields
    has_title = any(k in col_map for k in ['title', 'carrer name', 'career name', 'career', 'name'])
    has_soc = any(k in col_map for k in ['soc', 'o*net-soc code', 'code', 'soc code'])
    
    if not has_title:
        report["status"] = "error"
        report["missing_columns"].append("Career Title / Name column missing")
        return report
        
    title_col = next(col_map[k] for k in ['title', 'carrer name', 'career name', 'career', 'name'] if k in col_map)
    soc_col = next((col_map[k] for k in ['soc', 'o*net-soc code', 'code', 'soc code'] if k in col_map), None)
    
    seen_titles = set()
    valid_records = []
    
    for idx, row in df.iterrows():
        raw_title = str(row[title_col]).strip()
        if not raw_title or raw_title.lower() == 'nan':
            report["rejected_rows"].append({"row": idx + 1, "reason": "Empty career title"})
            continue
            
        clean_title = raw_title.title()
        if clean_title.lower() in seen_titles:
            report["duplicate_rows"] += 1
            report["rejected_rows"].append({"row": idx + 1, "reason": f"Duplicate career: '{clean_title}'"})
            continue
            
        seen_titles.add(clean_title.lower())
        valid_records.append({
            "name": clean_title,
            "soc": str(row[soc_col]).strip() if soc_col and pd.notnull(row[soc_col]) else "Data not available",
            "row_number": idx + 1
        })
        
    report["valid_careers_imported"] = len(valid_records)
    return report

def export_careers_to_csv():
    careers = get_all_careers()
    rows = []
    for c in careers:
        rows.append({
            "Career ID": c.get('id'),
            "SOC Code": c.get('soc_code'),
            "Career Name": c.get('display_name'),
            "Category": c.get('category'),
            "Coding Intensity": c.get('coding_intensity'),
            "Education Requirements": c.get('education_requirements'),
            "Median Salary USD": c.get('median_salary_usd'),
            "India Salary Benchmark": c.get('median_salary_inr_benchmark'),
            "Job Outlook %": c.get('job_outlook_pct'),
            "Source Name": c.get('source_name'),
            "Source URL": c.get('source_url'),
            "Last Verified": c.get('last_verified_date')
        })
    df = pd.DataFrame(rows)
    export_path = os.path.join(os.path.dirname(__file__), 'data', 'exported_careers.csv')
    df.to_csv(export_path, index=False)
    return export_path
