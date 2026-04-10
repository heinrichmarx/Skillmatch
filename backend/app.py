"""
SkillMatch API - Azure-deployable Flask backend
Handles candidate profiles, recruiter requirements, and skill matching.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json
import math

app = Flask(__name__)
CORS(app)

# Azure SQL Database connection (uses environment variable in production)
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'sqlite:///skillmatch.db'  # Fallback to SQLite for local dev
)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

db = SQLAlchemy(app)

# ─────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────

class Candidate(db.Model):
    __tablename__ = 'candidates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    country_residence = db.Column(db.String(100))
    country_work = db.Column(db.String(200))   # JSON array
    work_eligibility = db.Column(db.String(200))
    employment_status = db.Column(db.String(50))  # active, open, employed
    years_in_it = db.Column(db.Integer)
    years_in_cloud = db.Column(db.Integer)
    salary_expectation = db.Column(db.String(100))
    contract_type = db.Column(db.String(100))  # perm/contract/temp
    work_environment = db.Column(db.String(100))  # remote/hybrid/onsite
    notice_period = db.Column(db.String(100))
    linkedin_url = db.Column(db.String(500))
    industry = db.Column(db.String(200))
    nationality = db.Column(db.String(100))
    management_skills = db.Column(db.Text)  # JSON array
    freeform_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    skills = db.relationship('CandidateSkill', backref='candidate', lazy=True, cascade='all, delete-orphan')

class CandidateSkill(db.Model):
    __tablename__ = 'candidate_skills'
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    skill_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))  # cloud, platform, language, tool, etc.
    experience_level = db.Column(db.String(50))  # novice, capable, expert
    years_experience = db.Column(db.Float)
    qualification = db.Column(db.String(200))

class JobRequirement(db.Model):
    __tablename__ = 'job_requirements'
    id = db.Column(db.Integer, primary_key=True)
    recruiter_email = db.Column(db.String(200))
    job_title = db.Column(db.String(200))
    company = db.Column(db.String(200))
    years_it_required = db.Column(db.Integer)
    years_cloud_required = db.Column(db.Integer)
    contract_type = db.Column(db.String(100))
    work_environment = db.Column(db.String(100))
    salary_range = db.Column(db.String(100))
    notice_period_max = db.Column(db.String(100))
    nationality_requirement = db.Column(db.String(200))
    work_eligibility_required = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    required_skills = db.relationship('RequiredSkill', backref='job', lazy=True, cascade='all, delete-orphan')

class RequiredSkill(db.Model):
    __tablename__ = 'required_skills'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_requirements.id'), nullable=False)
    skill_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    importance = db.Column(db.String(50))  # required, optional
    min_experience_level = db.Column(db.String(50))  # novice, capable, expert
    min_years = db.Column(db.Float)

# ─────────────────────────────────────────────
# SKILL TAXONOMY
# ─────────────────────────────────────────────

SKILL_CATALOG = {
    "Cloud Platforms": ["AWS", "Azure", "GCP", "Oracle Cloud", "IBM Cloud"],
    "Azure Services": ["Azure DevOps", "Azure Kubernetes Service", "Azure Functions",
                       "Azure SQL", "Azure Cosmos DB", "Azure Active Directory",
                       "Azure Blob Storage", "Azure Logic Apps", "Azure API Management"],
    "AWS Services": ["EC2", "S3", "Lambda", "RDS", "DynamoDB", "EKS", "ECS",
                     "CloudFormation", "IAM", "CloudWatch"],
    "GCP Services": ["GKE", "BigQuery", "Cloud Run", "Cloud Functions", "Pub/Sub",
                     "Firestore", "Cloud SQL"],
    "Programming Languages": ["Python", "JavaScript", "TypeScript", "Java", "C#", ".NET",
                               "Go", "Rust", "Ruby", "PHP", "Scala", "Kotlin"],
    "DevOps & CI/CD": ["Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins",
                        "GitHub Actions", "GitLab CI", "ArgoCD", "Helm"],
    "Data & AI": ["Machine Learning", "Data Engineering", "Apache Spark", "Kafka",
                   "Databricks", "Snowflake", "Power BI", "Tableau", "dbt"],
    "Databases": ["SQL Server", "PostgreSQL", "MySQL", "MongoDB", "Redis",
                   "Elasticsearch", "Cassandra"],
    "Security": ["IAM/Identity", "Zero Trust", "SIEM", "Penetration Testing",
                  "Compliance (ISO 27001)", "SOC 2"],
    "Networking": ["VPN", "SD-WAN", "Load Balancing", "DNS", "Firewall"],
    "Soft Skills": ["Agile/Scrum", "Team Leadership", "Project Management",
                    "Stakeholder Management", "Technical Writing"],
}

# ─────────────────────────────────────────────
# MATCHING ENGINE
# ─────────────────────────────────────────────

LEVEL_SCORE = {"novice": 1, "capable": 2, "expert": 3}

def compute_match(candidate, job):
    """
    Returns a dict with overall percentage and per-skill breakdown.
    """
    required_skills = [s for s in job.required_skills if s.importance == 'required']
    optional_skills = [s for s in job.required_skills if s.importance == 'optional']

    cand_skill_map = {s.skill_name.lower(): s for s in candidate.skills}

    skill_results = []
    total_weight = 0
    earned_weight = 0

    def score_skill(req_skill, weight):
        nonlocal total_weight, earned_weight
        total_weight += weight
        cand_s = cand_skill_map.get(req_skill.skill_name.lower())
        if not cand_s:
            skill_results.append({
                "skill": req_skill.skill_name,
                "importance": req_skill.importance,
                "required_level": req_skill.min_experience_level,
                "required_years": req_skill.min_years,
                "candidate_level": None,
                "candidate_years": None,
                "match_pct": 0,
                "match_status": "missing"
            })
            return

        # Level score
        cand_level = LEVEL_SCORE.get(cand_s.experience_level, 0)
        req_level = LEVEL_SCORE.get(req_skill.min_experience_level, 1)
        level_ratio = min(cand_level / max(req_level, 1), 1.0)

        # Years score
        if req_skill.min_years and req_skill.min_years > 0:
            years_ratio = min((cand_s.years_experience or 0) / req_skill.min_years, 1.0)
        else:
            years_ratio = 1.0

        match_ratio = (level_ratio * 0.6 + years_ratio * 0.4)
        skill_pct = round(match_ratio * 100)
        earned_weight += weight * match_ratio

        status = "full" if skill_pct >= 100 else ("partial" if skill_pct >= 50 else "weak")
        skill_results.append({
            "skill": req_skill.skill_name,
            "importance": req_skill.importance,
            "required_level": req_skill.min_experience_level,
            "required_years": req_skill.min_years,
            "candidate_level": cand_s.experience_level,
            "candidate_years": cand_s.years_experience,
            "match_pct": skill_pct,
            "match_status": status
        })

    for s in required_skills:
        score_skill(s, 2.0)
    for s in optional_skills:
        score_skill(s, 1.0)

    # General experience bonus
    it_bonus = 0
    if job.years_it_required and candidate.years_in_it:
        it_bonus = min(candidate.years_in_it / max(job.years_it_required, 1), 1.0) * 5

    overall = round((earned_weight / max(total_weight, 1)) * 95 + it_bonus)
    overall = min(overall, 100)

    return {
        "candidate_id": candidate.id,
        "candidate_name": candidate.name,
        "candidate_email": candidate.email,
        "overall_match": overall,
        "skill_breakdown": skill_results,
        "years_in_it": candidate.years_in_it,
        "years_in_cloud": candidate.years_in_cloud,
        "work_environment": candidate.work_environment,
        "contract_type": candidate.contract_type,
        "notice_period": candidate.notice_period,
        "salary_expectation": candidate.salary_expectation,
        "employment_status": candidate.employment_status,
    }

# ─────────────────────────────────────────────
# ROUTES — CANDIDATES
# ─────────────────────────────────────────────

@app.route('/api/skills/catalog', methods=['GET'])
def get_skill_catalog():
    return jsonify(SKILL_CATALOG)

@app.route('/api/candidates', methods=['POST'])
def create_candidate():
    data = request.json
    existing = Candidate.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    candidate = Candidate(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone'),
        country_residence=data.get('country_residence'),
        country_work=json.dumps(data.get('country_work', [])),
        work_eligibility=data.get('work_eligibility'),
        employment_status=data.get('employment_status', 'active'),
        years_in_it=data.get('years_in_it'),
        years_in_cloud=data.get('years_in_cloud'),
        salary_expectation=data.get('salary_expectation'),
        contract_type=data.get('contract_type'),
        work_environment=data.get('work_environment'),
        notice_period=data.get('notice_period'),
        linkedin_url=data.get('linkedin_url'),
        industry=data.get('industry'),
        nationality=data.get('nationality'),
        management_skills=json.dumps(data.get('management_skills', [])),
        freeform_notes=data.get('freeform_notes'),
    )
    db.session.add(candidate)
    db.session.flush()

    for skill in data.get('skills', []):
        cs = CandidateSkill(
            candidate_id=candidate.id,
            skill_name=skill['skill_name'],
            category=skill.get('category'),
            experience_level=skill.get('experience_level', 'novice'),
            years_experience=skill.get('years_experience', 0),
            qualification=skill.get('qualification'),
        )
        db.session.add(cs)

    db.session.commit()
    return jsonify({"id": candidate.id, "message": "Profile created successfully"}), 201

@app.route('/api/candidates/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    c = Candidate.query.get_or_404(candidate_id)
    return jsonify({
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "skills": [{"skill_name": s.skill_name, "experience_level": s.experience_level,
                     "years_experience": s.years_experience, "category": s.category} for s in c.skills]
    })

# ─────────────────────────────────────────────
# ROUTES — JOBS / RECRUITERS
# ─────────────────────────────────────────────

@app.route('/api/jobs', methods=['POST'])
def create_job():
    data = request.json
    job = JobRequirement(
        recruiter_email=data.get('recruiter_email'),
        job_title=data.get('job_title'),
        company=data.get('company'),
        years_it_required=data.get('years_it_required'),
        years_cloud_required=data.get('years_cloud_required'),
        contract_type=data.get('contract_type'),
        work_environment=data.get('work_environment'),
        salary_range=data.get('salary_range'),
        notice_period_max=data.get('notice_period_max'),
        nationality_requirement=data.get('nationality_requirement'),
        work_eligibility_required=data.get('work_eligibility_required'),
    )
    db.session.add(job)
    db.session.flush()

    for skill in data.get('required_skills', []):
        rs = RequiredSkill(
            job_id=job.id,
            skill_name=skill['skill_name'],
            category=skill.get('category'),
            importance=skill.get('importance', 'required'),
            min_experience_level=skill.get('min_experience_level', 'novice'),
            min_years=skill.get('min_years', 0),
        )
        db.session.add(rs)

    db.session.commit()
    return jsonify({"id": job.id, "message": "Job requirement saved"}), 201

# ─────────────────────────────────────────────
# ROUTES — MATCHING
# ─────────────────────────────────────────────

@app.route('/api/jobs/<int:job_id>/matches', methods=['GET'])
def get_matches(job_id):
    job = JobRequirement.query.get_or_404(job_id)
    # Only match active or open candidates
    candidates = Candidate.query.filter(
        Candidate.employment_status.in_(['active', 'open'])
    ).all()

    results = [compute_match(c, job) for c in candidates]
    results.sort(key=lambda x: x['overall_match'], reverse=True)

    return jsonify({
        "job_id": job_id,
        "job_title": job.job_title,
        "total_candidates": len(results),
        "matches": results
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
