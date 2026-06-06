from typing import List, Dict, Any

# Dictionary of curated interview questions for common skills
SKILL_QUESTIONS = {
    "python": {
        "Beginner": [
            "What is the difference between list and tuple in Python?",
            "How does memory management work in Python?",
            "What are decorators and how do you use them?"
        ],
        "Intermediate": [
            "Explain the difference between deep copy and shallow copy.",
            "How does the Global Interpreter Lock (GIL) affect multi-threading?",
            "How do you implement custom context managers using contextlib?"
        ],
        "Advanced": [
            "Design a thread-safe singleton class in Python using metaclasses.",
            "How would you optimize a Python application suffering from memory leaks?",
            "Compare asyncio against multi-processing for CPU-bound vs I/O-bound tasks."
        ]
    },
    "sql": {
        "Beginner": [
            "What are the differences between INNER JOIN, LEFT JOIN, and RIGHT JOIN?",
            "What is the purpose of the GROUP BY clause?",
            "How do you filter records using wildcards in SQL?"
        ],
        "Intermediate": [
            "What are window functions (e.g. ROW_NUMBER, RANK) and how do they work?",
            "Explain the difference between a subquery and a CTE (Common Table Expression).",
            "What is database normalization and index structure (B-Trees)?"
        ],
        "Advanced": [
            "How would you optimize a query that is scanning millions of rows and causing locks?",
            "Compare column-oriented databases against row-oriented databases for OLAP workloads.",
            "Describe how database isolation levels affect transaction concurrency."
        ]
    },
    "docker": {
        "Beginner": [
            "What is the difference between a Docker image and a Docker container?",
            "How do you expose ports in a Dockerfile?",
            "What is docker-compose used for?"
        ],
        "Intermediate": [
            "How do Docker volumes differ from bind mounts, and when should you use each?",
            "What is multi-stage builds in Docker and why are they important?",
            "Explain the difference between host and bridge networking in Docker."
        ],
        "Advanced": [
            "How would you design a secure container architecture to prevent privilege escalation?",
            "Describe the containerization startup sequence and how cgroups/namespaces isolate processes.",
            "How do you optimize Docker image layer caching to reduce build times in CI/CD pipelines?"
        ]
    },
    "aws": {
        "Beginner": [
            "What is the difference between S3, EC2, and RDS?",
            "What is an IAM Role and how does it differ from a Policy?",
            "What is the AWS Free Tier?"
        ],
        "Intermediate": [
            "How do you set up a secure VPC with private and public subnets?",
            "Explain the difference between AWS Lambda and ECS container deployments.",
            "What is Route 53 and how does load balancing work with ALB vs NLB?"
        ],
        "Advanced": [
            "Design a highly available, multi-region disaster recovery architecture for an e-commerce platform.",
            "How would you implement a cost-optimized data warehousing pipeline using Redshift, Athena, and Glacier?",
            "Detail how AWS KMS encrypts data at rest and in transit using envelope encryption."
        ]
    },
    "git": {
        "Beginner": [
            "What is the difference between git clone and git pull?",
            "How do you resolve a basic merge conflict?",
            "What is git stash used for?"
        ],
        "Intermediate": [
            "Explain the difference between git merge and git rebase.",
            "What is git cherry-pick and when should you use it?",
            "How do you undo the last commit that has already been pushed to remote?"
        ],
        "Advanced": [
            "Describe the Git reflog and how you would recover a deleted branch that was not pushed.",
            "How do you set up Git hooks to enforce code style linting before committing?",
            "Explain how Git internally represents objects (commits, trees, blobs)."
        ]
    }
}

def generate_interview_questions(skills: List[str]) -> Dict[str, Dict[str, List[str]]]:
    """Generate Beginner, Intermediate, and Advanced questions for candidate's skills."""
    result = {}
    for skill in skills:
        skill_lower = skill.lower().strip()
        if skill_lower in SKILL_QUESTIONS:
            result[skill.title()] = SKILL_QUESTIONS[skill_lower]
        else:
            # Generate template-based dynamic questions for other skills
            result[skill.title()] = {
                "Beginner": [
                    f"What are the core fundamentals and architecture of {skill}?",
                    f"Can you describe a basic project where you implemented {skill}?",
                    f"What are the common syntax structures or tools associated with {skill}?"
                ],
                "Intermediate": [
                    f"What are the best practices for structuring code/designs in {skill}?",
                    f"How do you troubleshoot or debug common runtime exceptions in {skill}?",
                    f"Explain the differences between {skill} and its closest competitor/alternative."
                ],
                "Advanced": [
                    f"How would you optimize performance or scale a system built with {skill}?",
                    f"Describe how you would design a secure, high-concurrency module in {skill}.",
                    f"What is an architectural limitation of {skill} and how did you design around it?"
                ]
            }
    return result

def rewrite_bullet_point(bullet: str) -> List[str]:
    """Rewrite a weak bullet point into 3 strong achievement-oriented versions."""
    cleaned = bullet.strip().rstrip(".").lower()
    
    # Extract key nouns/action concepts from the bullet point
    # Simple heuristics to find action concepts
    action_verb = "engineered"
    core_concept = "responsibilities"
    
    if "wrote" in cleaned or "code" in cleaned or "program" in cleaned:
        action_verb = "architected"
        core_concept = "software modules"
    elif "test" in cleaned or "debug" in cleaned:
        action_verb = "formulated"
        core_concept = "testing protocols"
    elif "manage" in cleaned or "lead" in cleaned or "head" in cleaned:
        action_verb = "spearheaded"
        core_concept = "cross-functional teams"
    elif "build" in cleaned or "develop" in cleaned:
        action_verb = "developed"
        core_concept = "scalable modules"
    elif "data" in cleaned or "sql" in cleaned:
        action_verb = "streamlined"
        core_concept = "database systems"
        
    # Standard template replacements
    metric_version = f"{action_verb.title()} high-performance {core_concept}, optimizing processing speed by 35% and saving 10+ hours weekly."
    scale_version = f"Deployed and scaled {core_concept} in production, supporting over 50,000 active transactions with zero downtime."
    leadership_version = f"Spearheaded a technical initiative to redesign {core_concept}, driving cross-team adoption and aligning technical deliverables."
    
    return [metric_version, scale_version, leadership_version]

def analyze_skill_gaps(missing_skills: List[str]) -> Dict[str, Dict[str, Any]]:
    """Generate roadmap and suggested courses for missing skills."""
    analysis = {}
    for skill in missing_skills:
        skill_title = skill.title().strip()
        analysis[skill_title] = {
            "roadmap": [
                "Days 1-3: Study core syntax, documentation, and fundamental APIs.",
                "Days 4-7: Build 2 minor playground applications to solidify syntax.",
                "Days 8-12: Implement a full case study project integrating other tech stacks.",
                "Days 13+: Review advanced concepts, system optimization, and deployment patterns."
            ],
            "courses": [
                f"Coursera: '{skill_title} Fundamentals for Professional Developers'",
                f"Udemy: 'Mastering {skill_title} - From Zero to Production Hero'",
                f"Official Tutorial: '{skill_title} Documentation & Quickstart Guides'"
            ]
        }
    return analysis

def generate_recruiter_report(
    name: str, 
    education: str, 
    experience_years: float, 
    skills: List[str], 
    missing_skills: List[str]
) -> Dict[str, Any]:
    """Compiles a detailed recruiter scorecard hiring report."""
    
    # Scorecard calculation
    suitability = "Recommended"
    if experience_years >= 5 and len(skills) >= 7:
        suitability = "Strong Buy"
    elif experience_years < 2 or len(missing_skills) > 4:
        suitability = "Pass / Low Priority"
        
    focus_areas = []
    if missing_skills:
        focus_areas.append(f"Technical depth in: {', '.join(missing_skills[:3]).title()}.")
    if experience_years < 3:
        focus_areas.append("Ability to work independently and manage project lifecycles.")
    else:
        focus_areas.append("System architecture decisions and senior-level troubleshooting.")
        
    summary = (
        f"Candidate {name} has {experience_years} years of experience and holds a '{education}' degree status. "
        f"They demonstrate core strengths in {', '.join(skills[:4]).title()}. "
        f"Hiring decision rating is categorized as '{suitability}'."
    )
    
    return {
        "summary": summary,
        "suitability_rating": suitability,
        "interview_focus_areas": focus_areas,
        "core_technologies": [s.title() for s in skills],
        "missing_technologies": [s.title() for s in missing_skills]
    }
