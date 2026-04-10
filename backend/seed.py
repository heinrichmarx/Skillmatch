"""
SkillMatch — Database Seeder
Generates 100 realistic test candidates with randomised skill profiles.

Usage:
    cd skillmatch/backend
    python seed.py
    python seed.py --api http://localhost:5000   (default)
    python seed.py --api https://skillmatch-api.azurewebsites.net
"""

import random
import requests
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--api', default='http://localhost:5000', help='API base URL')
args = parser.parse_args()
API = args.api.rstrip('/')

# ── SKILL POOLS ───────────────────────────────────────────────────────────────

AWS_SKILLS = {
    "AWS — Compute":    ["EC2","Lambda","ECS","EKS","Elastic Beanstalk","AWS Batch","App Runner","Lightsail"],
    "AWS — Storage":    ["S3","EBS","EFS","FSx","S3 Glacier","Storage Gateway","AWS Backup"],
    "AWS — Database":   ["RDS","DynamoDB","Aurora","ElastiCache","Redshift","Neptune","DocumentDB","Keyspaces"],
    "AWS — Networking": ["VPC","Route 53","CloudFront","API Gateway","Direct Connect","Transit Gateway","Global Accelerator"],
    "AWS — DevOps":     ["CodePipeline","CodeBuild","CodeDeploy","CloudFormation","AWS CDK","SAM","Systems Manager"],
    "AWS — Security":   ["IAM","Cognito","KMS","Secrets Manager","GuardDuty","Shield","WAF","CloudTrail"],
    "AWS — AI & Data":  ["SageMaker","Glue","Athena","EMR","Kinesis","QuickSight","Rekognition","Lake Formation"],
    "AWS — Messaging":  ["SQS","SNS","EventBridge","Step Functions","Amazon MQ","AppSync"],
}

AZURE_SKILLS = {
    "Azure — Compute":   ["Virtual Machines","Azure Kubernetes Service","Azure Functions","App Service","Container Instances","VM Scale Sets"],
    "Azure — Storage":   ["Blob Storage","Azure Files","Data Lake Storage","Managed Disks","Azure Backup"],
    "Azure — Database":  ["Azure SQL","Cosmos DB","Azure Database for PostgreSQL","Azure Database for MySQL","Synapse Analytics","Azure Cache for Redis"],
    "Azure — Networking":["Virtual Network","Azure DNS","Traffic Manager","Application Gateway","Azure CDN","ExpressRoute","VPN Gateway","Azure Firewall","Front Door"],
    "Azure — DevOps":    ["Azure DevOps","Azure Pipelines","Azure Repos","Azure Artifacts","ARM Templates","Bicep","Azure CLI"],
    "Azure — Security":  ["Azure Active Directory","Key Vault","Defender for Cloud","Microsoft Sentinel","Azure Policy","Microsoft Purview","Identity Protection"],
    "Azure — AI & Data": ["Azure Machine Learning","Azure Cognitive Services","Azure OpenAI Service","Data Factory","Azure Databricks","Stream Analytics","Event Hubs","Power BI"],
    "Azure — Messaging": ["Service Bus","Event Grid","Logic Apps","API Management","SignalR Service","Notification Hubs"],
}

GCP_SKILLS = {
    "GCP — Compute":    ["Compute Engine","Google Kubernetes Engine","Cloud Run","Cloud Functions","App Engine","Dataflow","Dataproc"],
    "GCP — Storage":    ["Cloud Storage","Persistent Disk","Filestore"],
    "GCP — Database":   ["Cloud SQL","Firestore","Bigtable","Spanner","AlloyDB","Memorystore"],
    "GCP — Networking": ["VPC Network","Cloud DNS","Cloud CDN","Cloud Load Balancing","Cloud Armor","Cloud NAT"],
    "GCP — DevOps":     ["Cloud Build","Cloud Deploy","Artifact Registry","Deployment Manager","Terraform on GCP"],
    "GCP — Security":   ["Cloud IAM","Secret Manager","Cloud KMS","Security Command Center","BeyondCorp","VPC Service Controls"],
    "GCP — AI & Data":  ["Vertex AI","BigQuery","Looker","Pub/Sub","Cloud Composer","Dataplex","Document AI","AutoML"],
    "GCP — Messaging":  ["Cloud Pub/Sub","Cloud Tasks","Cloud Scheduler","Eventarc","Workflows"],
}

GENERAL_SKILLS = {
    "Languages":     ["Python","JavaScript","TypeScript","Java","C#",".NET","Go","Rust","Ruby","PHP","Scala","Kotlin","Bash/Shell"],
    "DevOps & CI/CD":["Docker","Kubernetes","Terraform","Ansible","Helm","Jenkins","GitHub Actions","GitLab CI","ArgoCD","Flux"],
    "Databases":     ["PostgreSQL","MySQL","SQL Server","MongoDB","Redis","Elasticsearch","Cassandra","Neo4j"],
    "Security":      ["Zero Trust","SIEM","Penetration Testing","ISO 27001","SOC 2","GDPR Compliance","OWASP"],
    "Observability": ["Prometheus","Grafana","Datadog","Splunk","New Relic","Dynatrace","OpenTelemetry","ELK Stack"],
}

ALL_SKILL_POOLS = {**AWS_SKILLS, **AZURE_SKILLS, **GCP_SKILLS, **GENERAL_SKILLS}

# ── CANDIDATE DATA ────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "James","Sarah","Mohammed","Priya","Chen","Oluwaseun","Ana","Dmitri","Aisha","Lucas",
    "Emma","Kwame","Sofia","Arjun","Mei","Carlos","Fatima","Liam","Yuki","Amara",
    "Noah","Zara","Ravi","Elena","Kofi","Isabella","Tariq","Nadia","Ethan","Soo-Jin",
    "Oliver","Amelia","Vikram","Chloe","Babajide","Ingrid","Hassan","Maya","Ryan","Leila",
    "Alex","Chiara","Sipho","Hannah","Adrian","Yara","Patrick","Keiko","David","Aaliya",
    "Michael","Beatriz","Ankit","Freya","Chidi","Mia","Tobias","Nour","Samuel","Ling",
    "Benjamin","Astrid","Osei","Valentina","Finn","Hana","Jerome","Rania","Marcus","Nia",
    "Sebastian","Zoe","Javier","Sana","Daniel","Petra","Emeka","Lily","Nathan","Soraya",
    "Elijah","Camille","Adewale","Mara","Henry","Yasmin","Felix","Irene","Jack","Dayo",
    "George","Nina","Rahul","Stella","Tom","Layla","Oscar","Vera","Hugo","Amina",
]

LAST_NAMES = [
    "Smith","Johnson","Okafor","Patel","Wang","Müller","Garcia","Ivanov","Hassan","Silva",
    "Brown","Mensah","Rossi","Kumar","Nakamura","Rodriguez","Ahmed","Taylor","Kim","Diallo",
    "Wilson","Fernandez","Nwosu","Sharma","Chen","Andersen","Martinez","Sousa","Williams","Park",
    "Jones","Bianchi","Adeyemi","Gupta","Tanaka","López","Al-Rashid","Davis","Sato","Traoré",
    "Miller","Kovač","Eze","Desai","Yamamoto","Herrera","Khalil","Anderson","Ito","Coulibaly",
    "Thomas","Novak","Osei","Mehta","Watanabe","Cruz","Farouk","Jackson","Suzuki","Bah",
    "White","Almeida","Chukwu","Joshi","Fujita","Reyes","Mansour","Harris","Hayashi","Diop",
    "Martin","Oliveira","Okeke","Verma","Maeda","Morales","Ismail","Thompson","Kato","Sawadogo",
    "Clarke","Santos","Abara","Rao","Ogawa","Vargas","Youssef","Lewis","Mori","Cissé",
    "Walker","Pereira","Adebayo","Shah","Kobayashi","Ramirez","Nasser","Hall","Shimizu","Keïta",
]

COUNTRIES = ["South Africa","United Kingdom","United States","Germany","Australia","Netherlands","Canada","India","Singapore","UAE","Kenya","Nigeria","Brazil","Poland","Ireland"]
WORK_COUNTRIES = ["Remote Anywhere","United States","United Kingdom","Europe","Australia","South Africa","Singapore","Canada"]
INDUSTRIES = ["Banking & Finance","Retail","Healthcare","Telecommunications","Insurance","Manufacturing","Government","Media","Energy","Logistics","E-commerce","Education"]
NATIONALITIES = ["South African","British","American","German","Australian","Dutch","Canadian","Indian","Singaporean","Emirati","Kenyan","Nigerian","Brazilian","Polish","Irish"]
NOTICE_PERIODS = ["Immediately available","1 week","2 weeks","1 month","2 months","3 months"]
SALARIES = ["$60k-$80k","$80k-$100k","$100k-$130k","$130k-$160k","$160k-$200k","£50k-£70k","£70k-£90k","£90k-£120k","R600k-R800k","R800k-R1.2M","€60k-€80k","€80k-€110k"]
CERTS = [
    "AWS Solutions Architect Associate","AWS Solutions Architect Professional","AWS DevOps Engineer",
    "AZ-900","AZ-104","AZ-204","AZ-400","AZ-500","DP-203",
    "GCP Associate Cloud Engineer","GCP Professional Cloud Architect","GCP Professional Data Engineer",
    "CKA","CKAD","CKS","Terraform Associate","PMP","ITIL 4","CISSP","CompTIA Security+",
]
EMPLOYMENTS = ["active","active","active","open","open","employed"]
CONTRACTS = ["permanent","permanent","contract","contract","temp","any"]
ENVIRONMENTS = ["remote","remote","hybrid","hybrid","onsite","flexible"]
MGMT = ["management","leading","project","agile"]

# ── GENERATORS ────────────────────────────────────────────────────────────────

def pick_skills(num_skills=None):
    """Return a list of skill dicts from random categories."""
    if num_skills is None:
        num_skills = random.randint(4, 16)

    # Pick a primary cloud specialisation (biased)
    primary = random.choices(
        [AWS_SKILLS, AZURE_SKILLS, GCP_SKILLS, None],
        weights=[30, 35, 20, 15]
    )[0]

    chosen = []
    seen = set()

    # Add skills from primary cloud
    if primary:
        for cat, skills in primary.items():
            n = random.randint(1, min(4, len(skills)))
            sample = random.sample(skills, n)
            for s in sample:
                if s not in seen:
                    chosen.append((s, cat, "cloud"))
                    seen.add(s)
            if len(chosen) >= num_skills // 2:
                break

    # Add general / multi-cloud skills
    for cat, skills in GENERAL_SKILLS.items():
        if random.random() < 0.6:
            n = random.randint(1, min(3, len(skills)))
            for s in random.sample(skills, n):
                if s not in seen:
                    chosen.append((s, cat, "general"))
                    seen.add(s)

    # Trim or shuffle
    random.shuffle(chosen)
    chosen = chosen[:num_skills]

    levels = ["novice", "capable", "capable", "capable", "expert"]
    result = []
    for skill_name, category, _ in chosen:
        level = random.choice(levels)
        years = round(random.uniform(0.5, 12 if level == "expert" else 6), 1)
        result.append({
            "skill_name": skill_name,
            "category": category,
            "experience_level": level,
            "years_experience": years,
        })
    return result

def make_candidate(i):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"
    email = f"{first.lower()}.{last.lower()}{random.randint(1,999)}@example.com"

    years_it = random.randint(1, 20)
    years_cloud = random.randint(0, min(years_it, 10))

    certs = random.sample(CERTS, random.randint(0, 3))

    return {
        "name": name,
        "email": email,
        "phone": f"+{random.randint(1,99)} {random.randint(100,999)} {random.randint(1000,9999)}",
        "nationality": random.choice(NATIONALITIES),
        "country_residence": random.choice(COUNTRIES),
        "country_work": random.sample(WORK_COUNTRIES, random.randint(1, 3)),
        "work_eligibility": random.choice(["Citizen","Permanent Resident","Work Permit","Open to sponsorship","EU citizen"]),
        "employment_status": random.choice(EMPLOYMENTS),
        "years_in_it": years_it,
        "years_in_cloud": years_cloud,
        "salary_expectation": random.choice(SALARIES),
        "contract_type": random.choice(CONTRACTS),
        "work_environment": random.choice(ENVIRONMENTS),
        "notice_period": random.choice(NOTICE_PERIODS),
        "linkedin_url": f"https://linkedin.com/in/{first.lower()}-{last.lower()}-{random.randint(100,999)}",
        "industry": random.choice(INDUSTRIES),
        "management_skills": random.sample(MGMT, random.randint(0, 3)),
        "freeform_notes": random.choice([
            "Open to relocation for the right opportunity.",
            "Strong background in regulated industries.",
            "Active open-source contributor.",
            "Available for immediate start.",
            "Prefer async-first remote teams.",
            "",
        ]),
        "qualifications": ", ".join(certs) if certs else "",
        "skills": pick_skills(),
    }

# ── SEEDER ────────────────────────────────────────────────────────────────────

def seed(n=100):
    print(f"🌱 Seeding {n} candidates to {API}\n")
    success = 0
    skipped = 0
    errors = 0

    for i in range(1, n + 1):
        candidate = make_candidate(i)
        try:
            res = requests.post(
                f"{API}/api/candidates",
                json=candidate,
                timeout=10
            )
            if res.status_code == 201:
                data = res.json()
                skill_count = len(candidate['skills'])
                print(f"  ✓ [{i:3d}] {candidate['name']:<30} ID:{data['id']:<6} {skill_count} skills  ({candidate['employment_status']})")
                success += 1
            elif res.status_code == 409:
                print(f"  ⚠ [{i:3d}] {candidate['name']:<30} skipped (email exists)")
                skipped += 1
            else:
                print(f"  ✗ [{i:3d}] {candidate['name']:<30} error {res.status_code}: {res.text[:80]}")
                errors += 1
        except requests.exceptions.ConnectionError:
            print(f"\n  ✗ Cannot connect to {API}")
            print("    Make sure the backend is running:  python app.py")
            sys.exit(1)
        except Exception as e:
            print(f"  ✗ [{i:3d}] Error: {e}")
            errors += 1

    print(f"\n{'─'*60}")
    print(f"  ✅ Created:  {success}")
    print(f"  ⚠ Skipped:  {skipped}")
    print(f"  ✗ Errors:   {errors}")
    print(f"{'─'*60}")
    print(f"\nDone! Open the Recruiter Portal and search for candidates.")

if __name__ == '__main__':
    seed(100)
