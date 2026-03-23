#!/usr/bin/env python3
"""Generate synthetic Harmonic-format CSV data for pipeline testing.

Produces ~500 people with realistic career trajectories across ~200 companies.
Output mimics the schema of fetch_harmonic_sample.sh.
"""

import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

# ---------------------------------------------------------------------------
# Company templates
# ---------------------------------------------------------------------------

COMPANIES = [
    # (name, urn, customer_type, company_type, funding_stage, headcount, city, state, country, tags)
    ("Stripe", "urn:li:company:stripe", "Business (B2B)", "COMPANY", "SERIES_I", 8000, "San Francisco", "CA", "US",
     [("Financial Technology", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Payments", "MARKET_VERTICAL"), ("Cloud", "TECHNOLOGY")]),
    ("Plaid", "urn:li:company:plaid", "Business (B2B)", "COMPANY", "SERIES_D", 1200, "San Francisco", "CA", "US",
     [("Financial Technology", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Data Analytics", "TECHNOLOGY")]),
    ("Robinhood", "urn:li:company:robinhood", "Consumer (B2C)", "COMPANY", "IPO", 3800, "Menlo Park", "CA", "US",
     [("Financial Technology", "INDUSTRY"), ("Marketplace", "PRODUCT_TYPE"), ("Mobile", "TECHNOLOGY")]),
    ("Oscar Health", "urn:li:company:oscar", "Consumer (B2C)", "COMPANY", "IPO", 3000, "New York", "NY", "US",
     [("Health / Wellness", "INDUSTRY"), ("Insurance", "MARKET_VERTICAL"), ("Software", "TECHNOLOGY")]),
    ("Tempus", "urn:li:company:tempus", "Business (B2B)", "COMPANY", "SERIES_G", 2500, "Chicago", "IL", "US",
     [("Life Sciences & Healthcare", "INDUSTRY"), ("Data Analytics", "TECHNOLOGY"), ("Artificial Intelligence", "TECHNOLOGY")]),
    ("Datadog", "urn:li:company:datadog", "Business (B2B)", "COMPANY", "IPO", 5000, "New York", "NY", "US",
     [("Data Analytics", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Cloud", "TECHNOLOGY"), ("Software", "TECHNOLOGY")]),
    ("Figma", "urn:li:company:figma", "Business (B2B)", "COMPANY", "ACQUIRED", 1500, "San Francisco", "CA", "US",
     [("Software", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Design", "MARKET_VERTICAL")]),
    ("Notion", "urn:li:company:notion", "Business (B2B)", "COMPANY", "SERIES_C", 800, "San Francisco", "CA", "US",
     [("Software", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Productivity", "MARKET_VERTICAL")]),
    ("Anduril", "urn:li:company:anduril", "Government (B2G)", "COMPANY", "SERIES_F", 2800, "Costa Mesa", "CA", "US",
     [("Defense", "INDUSTRY"), ("Hardware", "PRODUCT_TYPE"), ("Artificial Intelligence", "TECHNOLOGY")]),
    ("Palantir", "urn:li:company:palantir", "Government (B2G)", "COMPANY", "IPO", 3500, "Denver", "CO", "US",
     [("Data Analytics", "INDUSTRY"), ("Software", "PRODUCT_TYPE"), ("Artificial Intelligence", "TECHNOLOGY")]),
    ("Brex", "urn:li:company:brex", "Business (B2B)", "COMPANY", "SERIES_D", 1100, "San Francisco", "CA", "US",
     [("Financial Technology", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Payments", "MARKET_VERTICAL")]),
    ("Ramp", "urn:li:company:ramp", "Business (B2B)", "COMPANY", "SERIES_D", 900, "New York", "NY", "US",
     [("Financial Technology", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Payments", "MARKET_VERTICAL")]),
    ("Hims & Hers", "urn:li:company:hims", "Consumer (B2C)", "COMPANY", "IPO", 1800, "San Francisco", "CA", "US",
     [("Health / Wellness", "INDUSTRY"), ("E-Commerce", "PRODUCT_TYPE"), ("Telehealth", "MARKET_VERTICAL")]),
    ("Navan", "urn:li:company:navan", "Business (B2B)", "COMPANY", "SERIES_G", 3200, "Palo Alto", "CA", "US",
     [("Software", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Travel", "MARKET_VERTICAL")]),
    ("Rippling", "urn:li:company:rippling", "Business (B2B)", "COMPANY", "SERIES_E", 2800, "San Francisco", "CA", "US",
     [("Software", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Human Resources", "MARKET_VERTICAL")]),
    ("Scale AI", "urn:li:company:scaleai", "Business (B2B)", "COMPANY", "SERIES_F", 1500, "San Francisco", "CA", "US",
     [("Data Analytics", "INDUSTRY"), ("Artificial Intelligence", "TECHNOLOGY"), ("Software", "PRODUCT_TYPE")]),
    ("Abridge", "urn:li:company:abridge", "Business (B2B)", "COMPANY", "SERIES_C", 250, "Pittsburgh", "PA", "US",
     [("Life Sciences & Healthcare", "INDUSTRY"), ("Artificial Intelligence", "TECHNOLOGY"), ("SaaS", "PRODUCT_TYPE")]),
    ("Cerebras", "urn:li:company:cerebras", "Business (B2B)", "COMPANY", "SERIES_F", 500, "Sunnyvale", "CA", "US",
     [("Hardware", "PRODUCT_TYPE"), ("Artificial Intelligence", "TECHNOLOGY"), ("Semiconductor", "TECHNOLOGY")]),
    ("Whatnot", "urn:li:company:whatnot", "Consumer (B2C)", "COMPANY", "SERIES_D", 400, "Los Angeles", "CA", "US",
     [("E-Commerce", "PRODUCT_TYPE"), ("Marketplace", "PRODUCT_TYPE"), ("Media & Entertainment", "INDUSTRY")]),
    ("Mercury", "urn:li:company:mercury", "Business (B2B)", "COMPANY", "SERIES_C", 600, "San Francisco", "CA", "US",
     [("Financial Technology", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Banking", "MARKET_VERTICAL")]),
    # Startups
    ("Vercel", "urn:li:company:vercel", "Business (B2B)", "COMPANY", "SERIES_D", 450, "San Francisco", "CA", "US",
     [("Software", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Cloud", "TECHNOLOGY")]),
    ("Linear", "urn:li:company:linear", "Business (B2B)", "COMPANY", "SERIES_B", 80, "San Francisco", "CA", "US",
     [("Software", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Productivity", "MARKET_VERTICAL")]),
    ("Vanta", "urn:li:company:vanta", "Business (B2B)", "COMPANY", "SERIES_C", 500, "San Francisco", "CA", "US",
     [("Software", "INDUSTRY"), ("SaaS", "PRODUCT_TYPE"), ("Security", "MARKET_VERTICAL")]),
    ("Anthropic", "urn:li:company:anthropic", "Business (B2B)", "COMPANY", "SERIES_D", 1000, "San Francisco", "CA", "US",
     [("Artificial Intelligence", "TECHNOLOGY"), ("Software", "INDUSTRY"), ("Research", "MARKET_VERTICAL")]),
    ("OpenAI", "urn:li:company:openai", "Business (B2B)", "COMPANY", "SERIES_E", 2000, "San Francisco", "CA", "US",
     [("Artificial Intelligence", "TECHNOLOGY"), ("Software", "INDUSTRY"), ("Research", "MARKET_VERTICAL")]),
    # Big companies for career background
    ("Google", "urn:li:company:google", "Business (B2B)", "COMPANY", "IPO", 180000, "Mountain View", "CA", "US",
     [("Software", "INDUSTRY"), ("Advertising", "MARKET_VERTICAL"), ("Cloud", "TECHNOLOGY"), ("Artificial Intelligence", "TECHNOLOGY")]),
    ("Meta", "urn:li:company:meta", "Consumer (B2C)", "COMPANY", "IPO", 67000, "Menlo Park", "CA", "US",
     [("Software", "INDUSTRY"), ("Social Media", "MARKET_VERTICAL"), ("Advertising", "MARKET_VERTICAL")]),
    ("Amazon", "urn:li:company:amazon", "Consumer (B2C)", "COMPANY", "IPO", 1500000, "Seattle", "WA", "US",
     [("E-Commerce", "PRODUCT_TYPE"), ("Cloud", "TECHNOLOGY"), ("Software", "INDUSTRY")]),
    ("JPMorgan Chase", "urn:li:company:jpmorgan", "Business (B2B)", "COMPANY", "IPO", 300000, "New York", "NY", "US",
     [("Financial Services", "INDUSTRY"), ("Banking", "MARKET_VERTICAL")]),
    ("Goldman Sachs", "urn:li:company:goldman", "Business (B2B)", "COMPANY", "IPO", 45000, "New York", "NY", "US",
     [("Financial Services", "INDUSTRY"), ("Banking", "MARKET_VERTICAL"), ("Investment Banking", "MARKET_VERTICAL")]),
    ("McKinsey", "urn:li:company:mckinsey", "Business (B2B)", "COMPANY", "IPO", 35000, "New York", "NY", "US",
     [("Consulting", "INDUSTRY"), ("Professional Services", "PRODUCT_TYPE")]),
    ("Mayo Clinic", "urn:li:company:mayoclinic", "Consumer (B2C)", "COMPANY", "IPO", 75000, "Rochester", "MN", "US",
     [("Life Sciences & Healthcare", "INDUSTRY"), ("Healthcare Provider Services", "MARKET_VERTICAL")]),
    ("Pfizer", "urn:li:company:pfizer", "Business (B2B)", "COMPANY", "IPO", 83000, "New York", "NY", "US",
     [("Life Sciences & Healthcare", "INDUSTRY"), ("Pharmaceutical", "MARKET_VERTICAL")]),
    ("Northrop Grumman", "urn:li:company:northrop", "Government (B2G)", "COMPANY", "IPO", 95000, "Falls Church", "VA", "US",
     [("Defense", "INDUSTRY"), ("Aerospace", "MARKET_VERTICAL"), ("Hardware", "PRODUCT_TYPE")]),
    ("Lockheed Martin", "urn:li:company:lockheed", "Government (B2G)", "COMPANY", "IPO", 120000, "Bethesda", "MD", "US",
     [("Defense", "INDUSTRY"), ("Aerospace", "MARKET_VERTICAL"), ("Hardware", "PRODUCT_TYPE")]),
]

# Career path templates: (department, titles_by_seniority_progression)
CAREER_PATHS = {
    "Engineering": [
        ["Software Engineering Intern", "Software Engineer", "Software Engineer", "Senior Software Engineer", "Staff Software Engineer", "Principal Engineer", "Engineering Director", "VP Engineering"],
        ["Software Engineering Intern", "Backend Engineer", "Backend Engineer", "Senior Backend Engineer", "Staff Backend Engineer", "Engineering Manager", "Senior Engineering Manager", "Director of Engineering"],
        ["QA Intern", "QA Engineer", "QA Engineer", "Senior QA Engineer", "QA Lead", "QA Manager", "Director of Quality"],
        ["DevOps Engineer", "Senior DevOps Engineer", "Staff SRE", "Infrastructure Manager", "Director of Infrastructure"],
    ],
    "Data": [
        ["Data Analyst Intern", "Data Analyst", "Data Analyst", "Senior Data Analyst", "Lead Data Analyst", "Analytics Manager", "Director of Analytics", "VP Data"],
        ["Data Science Intern", "Data Scientist", "Data Scientist", "Senior Data Scientist", "Staff Data Scientist", "Lead Data Scientist", "Head of Data Science"],
        ["Data Engineering Intern", "Data Engineer", "Data Engineer", "Senior Data Engineer", "Staff Data Engineer", "Data Engineering Manager", "Director of Data Engineering"],
        ["ML Engineer", "Senior ML Engineer", "Staff ML Engineer", "ML Engineering Manager", "Head of Machine Learning"],
    ],
    "Sales": [
        ["Sales Development Rep", "Business Development Rep", "Account Executive", "Senior Account Executive", "Enterprise Account Executive", "Sales Manager", "Director of Sales", "VP Sales"],
        ["SDR", "SDR", "Account Executive", "Senior AE", "Enterprise AE", "Regional VP", "VP Sales", "CRO"],
    ],
    "Marketing": [
        ["Marketing Intern", "Marketing Coordinator", "Marketing Manager", "Senior Marketing Manager", "Director of Marketing", "VP Marketing", "CMO"],
        ["Content Intern", "Content Writer", "Content Strategist", "Senior Content Strategist", "Head of Content", "Director of Content Marketing"],
        ["Growth Analyst", "Growth Manager", "Senior Growth Manager", "Head of Growth", "VP Growth"],
    ],
    "Product": [
        ["Product Analyst", "Associate Product Manager", "Product Manager", "Senior Product Manager", "Group Product Manager", "Director of Product", "VP Product", "CPO"],
        ["Product Design Intern", "Product Designer", "Product Designer", "Senior Product Designer", "Staff Designer", "Design Manager", "Head of Design", "VP Design"],
    ],
    "Operations": [
        ["Operations Analyst", "Operations Associate", "Operations Manager", "Senior Operations Manager", "Director of Operations", "VP Operations", "COO"],
        ["Project Coordinator", "Project Manager", "Senior Project Manager", "Program Manager", "Senior Program Manager", "Director of Program Management"],
    ],
    "Finance": [
        ["Financial Analyst", "Financial Analyst", "Senior Financial Analyst", "Finance Manager", "Senior Finance Manager", "Director of Finance", "VP Finance", "CFO"],
        ["Staff Accountant", "Senior Accountant", "Accounting Manager", "Controller", "VP Finance", "CFO"],
    ],
    "People": [
        ["HR Coordinator", "HR Generalist", "HR Business Partner", "Senior HRBP", "HR Manager", "Director of People", "VP People", "Chief People Officer"],
        ["Recruiting Coordinator", "Recruiter", "Senior Recruiter", "Lead Recruiter", "Recruiting Manager", "Head of Talent Acquisition", "VP Talent"],
    ],
    "Customer Success": [
        ["Customer Support Rep", "Customer Success Associate", "Customer Success Manager", "Senior CSM", "Lead CSM", "CS Manager", "Director of Customer Success", "VP Customer Success"],
    ],
    "Legal": [
        ["Paralegal", "Associate Attorney", "Attorney", "Senior Counsel", "Associate General Counsel", "General Counsel", "Chief Legal Officer"],
    ],
    "Healthcare/Clinical": [
        ["Medical Intern", "Resident Physician", "Attending Physician", "Senior Physician", "Medical Director", "Chief Medical Officer"],
        ["Registered Nurse", "Registered Nurse", "Senior Nurse", "Charge Nurse", "Nurse Manager", "Director of Nursing", "Chief Nursing Officer"],
    ],
}

SCHOOLS = [
    ("Stanford University", "Computer Science", "BS"),
    ("Stanford University", "Computer Science", "MS"),
    ("MIT", "Electrical Engineering", "BS"),
    ("MIT", "Computer Science", "MS"),
    ("Harvard University", "Economics", "BA"),
    ("Harvard Business School", "Business Administration", "MBA"),
    ("Wharton School", "Finance", "MBA"),
    ("UC Berkeley", "Computer Science", "BS"),
    ("UC Berkeley", "Data Science", "MS"),
    ("Carnegie Mellon", "Machine Learning", "MS"),
    ("Carnegie Mellon", "Computer Science", "BS"),
    ("University of Michigan", "Industrial Engineering", "BS"),
    ("Georgia Tech", "Computer Science", "BS"),
    ("Columbia University", "Statistics", "MS"),
    ("NYU", "Finance", "BS"),
    ("Yale University", "Political Science", "BA"),
    ("Duke University", "Biology", "BS"),
    ("Johns Hopkins", "Public Health", "MPH"),
    ("Johns Hopkins", "Medicine", "MD"),
    ("Northwestern", "Journalism", "BA"),
    ("UT Austin", "Computer Science", "BS"),
    ("University of Washington", "Computer Science", "BS"),
    ("UCLA", "Mathematics", "BS"),
    ("UIUC", "Computer Science", "BS"),
    ("Purdue University", "Mechanical Engineering", "BS"),
    ("Ohio State University", "Business", "BS"),
    ("Penn State", "Information Science", "BS"),
    ("University of Florida", "Marketing", "BS"),
    ("Arizona State University", "Business", "BS"),
    ("University of Texas at Dallas", "Computer Science", "MS"),
]

FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
               "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
               "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
               "Matthew", "Margaret", "Anthony", "Betty", "Mark", "Sandra", "Andrew", "Ashley",
               "Steven", "Emily", "Paul", "Donna", "Joshua", "Michelle", "Kevin", "Carol",
               "Brian", "Amanda", "George", "Dorothy", "Edward", "Melissa", "Ronald", "Deborah",
               "Timothy", "Stephanie", "Jason", "Rebecca", "Ryan", "Sharon", "Jacob", "Laura",
               "Gary", "Cynthia", "Nicholas", "Kathleen", "Eric", "Amy", "Jonathan", "Angela",
               "Stephen", "Shirley", "Larry", "Anna", "Justin", "Brenda", "Scott", "Pamela",
               "Brandon", "Emma", "Benjamin", "Nicole", "Samuel", "Helen", "Raymond", "Samantha",
               "Gregory", "Katherine", "Frank", "Christine", "Alexander", "Debra", "Patrick", "Rachel",
               "Aisha", "Wei", "Priya", "Carlos", "Yuki", "Olga", "Raj", "Fatima", "Hans", "Sofia"]


def generate_person(pid: int, company_pool: list) -> dict:
    """Generate a single person with career trajectory."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
                          "Davis", "Rodriguez", "Martinez", "Chen", "Wang", "Kim", "Patel",
                          "Singh", "Lee", "Park", "Nguyen", "Kumar", "Ali", "Müller", "Cohen",
                          "Thompson", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris",
                          "Martin", "Clark", "Lewis", "Walker", "Hall", "Young", "King"])
    full_name = f"{first} {last}"

    # Pick a career path
    department = random.choice(list(CAREER_PATHS.keys()))
    path_template = random.choice(CAREER_PATHS[department])

    # Career length: 2-8 roles
    career_length = random.randint(2, min(8, len(path_template)))
    start_idx = random.randint(0, max(0, len(path_template) - career_length))
    titles = path_template[start_idx:start_idx + career_length]

    # Generate experience
    experiences = []
    current_date = datetime(2024, 12, 1)
    exp_id = pid * 100

    # Pick companies for each role (prefer moving between related companies)
    role_companies = random.sample(company_pool, min(career_length, len(company_pool)))
    if len(role_companies) < career_length:
        role_companies = [random.choice(company_pool) for _ in range(career_length)]

    for i, title in enumerate(reversed(titles)):
        is_current = (i == 0)
        tenure_months = random.randint(8, 60)
        end_date = current_date if not is_current else None
        start_date = current_date - timedelta(days=tenure_months * 30)

        comp = role_companies[i]
        experiences.append({
            "id": exp_id + i,
            "person_id": pid,
            "company_urn": comp[1],
            "company_name": comp[0],
            "title": title,
            "department": department,
            "description": f"Worked on {department.lower()} initiatives.",
            "role_type": "EMPLOYEE" if "Intern" not in title else "INTERN",
            "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S+00"),
            "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S+00") if end_date else "",
            "is_current_position": "t" if is_current else "f",
            "location": f"{comp[5]}, {comp[6]}" if len(comp) > 6 else "",
        })
        current_date = start_date - timedelta(days=random.randint(0, 90))

    # Current company info
    current_comp = role_companies[0]
    current_title = titles[-1]

    # Headline
    headline = f"{current_title} at {current_comp[0]}"

    # Location
    city = current_comp[5] if len(current_comp) > 5 else "San Francisco"
    state = current_comp[6] if len(current_comp) > 6 else "CA"

    # Education
    num_edu = random.choice([1, 1, 1, 2])
    edu_picks = random.sample(SCHOOLS, min(num_edu, len(SCHOOLS)))
    education = []
    for j, (school, field, degree) in enumerate(edu_picks):
        grad_year = random.randint(2005, 2022)
        education.append({
            "id": pid * 100 + 50 + j,
            "person_id": pid,
            "school_name": school,
            "school_linkedin_url": "",
            "school_urn": f"urn:li:school:{school.lower().replace(' ', '')}",
            "degree": degree,
            "field": field,
            "grade": "",
            "start_date": f"{grad_year - 4}-09-01 00:00:00+00",
            "end_date": f"{grad_year}-06-01 00:00:00+00",
        })

    return {
        "person": {
            "id": pid,
            "entity_urn": f"urn:li:person:{pid}",
            "full_name": full_name,
            "first_name": first,
            "last_name": last,
            "linkedin_headline": headline,
            "location_display": f"{city}, {state}",
            "city": city,
            "state": state,
            "country": "US",
            "linkedin_url": f"https://linkedin.com/in/{first.lower()}{last.lower()}{pid}",
            "twitter_url": "",
            "crunchbase_url": "",
            "languages": "",
            "current_company_urns": f"{{{current_comp[1]}}}",
            "last_checked_at": "2025-01-01 00:00:00+00",
            "last_refreshed_at": "2025-01-01 00:00:00+00",
            "updated_at": "2025-01-01 00:00:00+00",
            "synced_at": "2025-01-01 00:00:00+00",
        },
        "experiences": experiences,
        "education": education,
        "department": department,
        "current_company": current_comp,
    }


def main() -> int:
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data/harmonic_sample")
    out_dir.mkdir(parents=True, exist_ok=True)

    num_people = 500

    # Generate people
    all_persons = []
    all_experiences = []
    all_education = []

    for i in range(num_people):
        pid = 100000 + i
        data = generate_person(pid, COMPANIES)
        all_persons.append(data["person"])
        all_experiences.extend(data["experiences"])
        all_education.extend(data["education"])

    # Write persons.csv
    person_fields = list(all_persons[0].keys())
    with (out_dir / "persons.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=person_fields)
        w.writeheader()
        w.writerows(all_persons)

    # Write person_experience.csv
    exp_fields = list(all_experiences[0].keys())
    with (out_dir / "person_experience.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=exp_fields)
        w.writeheader()
        w.writerows(all_experiences)

    # Write person_education.csv
    edu_fields = list(all_education[0].keys())
    with (out_dir / "person_education.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=edu_fields)
        w.writeheader()
        w.writerows(all_education)

    # Write companies.csv
    comp_fields = ["id", "entity_urn", "name", "legal_name", "description", "short_description",
                   "customer_type", "ownership_status", "company_type", "founding_date",
                   "headcount", "website_url", "website_domain", "city", "state", "country",
                   "linkedin_url", "twitter_url", "crunchbase_url",
                   "funding_total", "funding_num_rounds", "funding_last_date", "funding_last_type",
                   "funding_stage", "updated_at", "synced_at"]
    with (out_dir / "companies.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=comp_fields)
        w.writeheader()
        for i, comp in enumerate(COMPANIES):
            name, urn, cust, ctype, funding, hc, city, state, country, tags = comp
            w.writerow({
                "id": i + 1,
                "entity_urn": urn,
                "name": name,
                "legal_name": name,
                "description": f"{name} is a leading company in its space.",
                "short_description": f"{name} — {cust} company.",
                "customer_type": cust,
                "ownership_status": "PUBLIC" if funding == "IPO" else "PRIVATE",
                "company_type": ctype,
                "founding_date": f"{random.randint(2005, 2020)}-01-01 00:00:00+00",
                "headcount": hc,
                "website_url": f"https://{name.lower().replace(' ', '')}.com",
                "website_domain": f"{name.lower().replace(' ', '')}.com",
                "city": city, "state": state, "country": country,
                "linkedin_url": f"https://linkedin.com/company/{name.lower().replace(' ', '')}",
                "twitter_url": "", "crunchbase_url": "",
                "funding_total": random.randint(50, 5000) * 1_000_000,
                "funding_num_rounds": random.randint(1, 8),
                "funding_last_date": f"{random.randint(2020, 2024)}-06-01",
                "funding_last_type": funding,
                "funding_stage": funding,
                "updated_at": "2025-01-01 00:00:00+00",
                "synced_at": "2025-01-01 00:00:00+00",
            })

    # Write company_tags.csv
    tag_fields = ["id", "company_id", "tag_urn", "display_value", "tag_type", "date_added", "is_primary_tag"]
    tag_id = 1
    with (out_dir / "company_tags.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=tag_fields)
        w.writeheader()
        for i, comp in enumerate(COMPANIES):
            for display, ttype in comp[9]:
                w.writerow({
                    "id": tag_id,
                    "company_id": i + 1,
                    "tag_urn": f"urn:tag:{display.lower().replace(' ', '_')}",
                    "display_value": display,
                    "tag_type": ttype,
                    "date_added": "2024-01-01",
                    "is_primary_tag": "t" if tag_id % 3 == 0 else "f",
                })
                tag_id += 1

    # Run finalize to generate person_documents.csv
    import subprocess
    subprocess.run(
        [sys.executable, "scripts/finalize_harmonic_sample.py", str(out_dir)],
        check=True,
    )

    print(f"Generated synthetic data: {num_people} people, {len(COMPANIES)} companies")
    print(f"  {len(all_experiences)} experience rows, {len(all_education)} education rows")
    print(f"  Output: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
