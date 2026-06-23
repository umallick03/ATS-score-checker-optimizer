import re

ROLE_PROFILES = {
    "software_engineering": [
        "python", "javascript", "docker", "kubernetes", "aws", "sql", "api", "git", "cicd", 
        "microservices", "react", "node", "java", "testing", "agile", "architecture", "database",
        "ci/cd", "rest api", "github", "linux", "cloud", "devops", "system design"
    ],
    "product_management": [
        "roadmap", "agile", "scrum", "user stories", "kpi", "product lifecycle", "sql", 
        "ab testing", "user research", "wireframing", "market analysis", "metrics", "stakeholders",
        "product strategy", "backlog", "jira", "launch", "analytics", "cross-functional"
    ],
    "data_science": [
        "python", "sql", "machine learning", "statistics", "pandas", "numpy", "tensorflow", 
        "pytorch", "tableau", "modeling", "predictive analysis", "scikit-learn", "data cleaning",
        "deep learning", "nlp", "data visualization", "spark", "hadoop", "r", "bi"
    ],
    "marketing": [
        "seo", "sem", "ppc", "google analytics", "crm", "campaign", "conversion", "social media", 
        "content strategy", "brand strategy", "copywriting", "email marketing", "roi",
        "growth hacking", "lead generation", "funnel", "b2b", "market research", "advertising"
    ],
    "project_management": [
        "project management", "scrum", "agile", "waterfall", "pmp", "project lifecycle", "risk mitigation",
        "resource allocation", "scheduling", "budgeting", "stakeholders", "sprint planning", "jira",
        "deliverables", "gantt chart", "milestones", "cross-functional", "kanban", "quality control"
    ],
    "sales": [
        "sales", "business development", "crm", "salesforce", "lead generation", "cold calling",
        "negotiation", "client relations", "revenue growth", "account management", "pipeline", "quota",
        "market expansion", "closing", "presentation", "strategy", "b2b", "b2c", "outreach"
    ],
    "design": [
        "ui/ux", "wireframing", "prototyping", "figma", "user research", "user testing", "design system",
        "user journeys", "accessibility", "web design", "visual design", "adobe creative cloud",
        "mockups", "interaction design", "usability", "sketches", "information architecture"
    ],
    "finance": [
        "finance", "accounting", "budget", "forecast", "reconciliation", "general ledger", "compliance",
        "audit", "cash flow", "equity", "portfolio", "valuation", "excel", "sap", "reporting",
        "analysis", "tax", "revenue", "cost", "balance sheet", "risk management", "regulatory"
    ],
    "hr": [
        "recruitment", "hiring", "onboarding", "talent acquisition", "performance management",
        "employee relations", "hris", "payroll", "benefits", "policy", "compliance", "sourcing",
        "interviews", "retention", "culture", "training", "conflict resolution", "labor laws"
    ],
    "operations": [
        "operations", "supply chain", "logistics", "procurement", "inventory", "process improvement",
        "vendor management", "lean", "six sigma", "optimization", "quality assurance", "facility",
        "scheduling", "warehouse", "efficiency", "distribution", "cost reduction", "kpi"
    ],
    "healthcare": [
        "clinical", "patient care", "hipaa", "medical records", "ehr", "emr", "healthcare administration",
        "healthcare compliance", "patient scheduling", "billing", "insurance", "medical terminology",
        "outpatient", "inpatient", "nursing", "therapy", "patient safety", "documentation"
    ],
    "general": [
        "management", "leadership", "communication", "project management", "collaboration",
        "strategy", "problem solving", "analysis", "organization", "operations", "planning"
    ]
}

ACTION_VERBS = [
    "led", "developed", "designed", "managed", "implemented", "architected", "created", 
    "optimized", "solved", "improved", "executed", "analyzed", "spearheaded", "directed", 
    "built", "coordinated", "negotiated", "accelerated", "accomplished", "achieved", 
    "delivered", "established", "expanded", "generated", "maximized", "reduced", "streamlined"
]

STANDARD_SECTIONS = {
    "summary": ["summary", "profile", "professional summary", "about me", "objective"],
    "experience": ["experience", "work history", "employment history", "professional experience", "work experience"],
    "education": ["education", "academic background", "degrees", "academic profile"],
    "skills": ["skills", "technical skills", "technologies", "core competencies", "skills & tools"]
}

class ATSScorer:
    @staticmethod
    def calculate_score(text: str, structural_issues: list, target_profile: str = None) -> dict:
        text_lower = text.lower()
        
        # 1. Detect target profile if not specified
        if not target_profile or target_profile not in ROLE_PROFILES:
            # Auto-detect profile with highest keyword match
            best_profile = "software_engineering"
            max_matches = 0
            for profile, keywords in ROLE_PROFILES.items():
                if profile == "general":
                    continue
                matches = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower))
                if matches > max_matches:
                    max_matches = matches
                    best_profile = profile
            target_profile = best_profile

        # 2. Keyword Match Density (40%)
        profile_keywords = ROLE_PROFILES.get(target_profile, [])
        general_keywords = ROLE_PROFILES.get("general", [])
        all_keywords = list(set(profile_keywords + general_keywords))
        
        matched_keywords = []
        missing_keywords = []
        for kw in all_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                matched_keywords.append(kw)
            else:
                missing_keywords.append(kw)
        
        keyword_match_ratio = len(matched_keywords) / len(all_keywords) if all_keywords else 1.0
        keyword_score = round(keyword_match_ratio * 40.0, 1)

        # 3. Structural Parsing Compatibility (30%)
        structure_score = 30.0
        remarks = []
        
        # Check standard sections
        found_sections = []
        missing_sections = []
        for section, alternate_names in STANDARD_SECTIONS.items():
            found = False
            for alt in alternate_names:
                # Looking for standalone section headings or capitalized headings
                if re.search(r'\b' + re.escape(alt) + r'\b', text_lower):
                    found = True
                    break
            if found:
                found_sections.append(section)
            else:
                missing_sections.append(section)
                structure_score -= 4.0  # Deduct 4 pts per missing section (max 16)
                remarks.append({
                    "section": section,
                    "issue": f"Standard section heading for '{section.capitalize()}' not detected.",
                    "severity": "Warning",
                    "suggestion": f"Add a clear '{section.capitalize()}' section header to help the ATS categorize your resume content."
                })
        
        # Check date format compliance (looks for standard patterns like MM/YYYY, Month YYYY, or Year-Year)
        date_patterns = [
            r'\b(1[0-2]|0?[1-9])/(20\d{2}|19\d{2})\b',  # MM/YYYY
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)\s+(20\d{2}|19\d{2})\b', # Month YYYY
            r'\b(20\d{2}|19\d{2})\s*-\s*(20\d{2}|19\d{2}|present)\b' # YYYY-YYYY or YYYY-Present
        ]
        has_valid_dates = any(re.search(pat, text_lower) for pat in date_patterns)
        if not has_valid_dates:
            structure_score -= 4.0
            remarks.append({
                "section": "formatting",
                "issue": "Standard date formats not detected.",
                "severity": "Warning",
                "suggestion": "Format employment dates using standard formats like 'MM/YYYY' or 'Month YYYY' (e.g., '06/2022' or 'June 2022')."
            })
            
        # Add deductions for structural issues from parser
        for issue in structural_issues:
            if issue["severity"] == "Critical":
                structure_score -= 15.0
            else:
                structure_score -= 5.0
            
            remarks.append({
                "section": "formatting",
                "issue": issue["issue"],
                "severity": issue["severity"],
                "suggestion": issue["description"]
            })
            
        structure_score = max(0.0, round(structure_score, 1))

        # 4. Content Impact & Quantifiable Metrics (30%)
        # Let's divide it: Action Verbs (15%) + Numeric Metrics (15%)
        content_score = 0.0
        
        # Action Verbs matching
        verbs_found = []
        for verb in ACTION_VERBS:
            if re.search(r'\b' + re.escape(verb) + r'\b', text_lower):
                verbs_found.append(verb)
        
        action_verb_score = min(15.0, len(verbs_found) * 1.5)  # 1.5 pts per unique action verb (max 10 verbs)
        content_score += action_verb_score
        
        if len(verbs_found) < 5:
            remarks.append({
                "section": "content",
                "issue": f"Low usage of strong action verbs. Found only {len(verbs_found)} verbs.",
                "severity": "Warning",
                "suggestion": "Start experience bullet points with strong action verbs like 'Led', 'Spearheaded', 'Optimized', or 'Architected' instead of passive phrasing."
            })

        # Numeric Metrics matching (percentages, dollar values, numbers)
        # Avoid matching years like 2020 or 1999
        metric_matches = re.findall(
            r'(\b\d+%\b|\b\$\d+(?:\.\d+)?[kKmM]?\b|\b\d+\s*(?:percent|times|x|years|employees|users|clients|projects|million|thousand)\b)', 
            text_lower
        )
        # Also simple counts that look like metrics: e.g. "by 20%", "reduced costs by 15", "led 5 engineers"
        # We can scan paragraphs or bullets to see how many contain numbers
        metric_score = min(15.0, len(metric_matches) * 3.0)  # 3.0 pts per unique metric (max 5 metrics)
        content_score += metric_score
        
        if len(metric_matches) < 3:
            remarks.append({
                "section": "content",
                "issue": "Resume lacks quantifiable business impact metrics.",
                "severity": "Warning",
                "suggestion": "Include numeric metrics to show business results (e.g. 'Increased user engagement by 25%' or 'Managed a team of 6 software developers')."
            })
            
        content_score = round(content_score, 1)

        # 5. Consolidated Score out of 100
        consolidated_score = round(keyword_score + structure_score + content_score, 0)
        consolidated_score = min(100.0, max(0.0, consolidated_score))
        
        # Formulate status
        if consolidated_score >= 85:
            status = "Excellent"
        elif consolidated_score >= 70:
            status = "Good - Needs Minor Tweaks"
        else:
            status = "Action Required - Critical Gaps Found"
            
        return {
            "score": int(consolidated_score),
            "status": status,
            "profile": target_profile,
            "breakdown": {
                "keywords": {
                    "score": keyword_score,
                    "max": 40,
                    "matched": matched_keywords,
                    "missing": missing_keywords
                },
                "structure": {
                    "score": structure_score,
                    "max": 30,
                    "found_sections": found_sections,
                    "missing_sections": missing_sections
                },
                "content": {
                    "score": content_score,
                    "max": 30,
                    "verbs_found": verbs_found,
                    "metrics_found": list(set(metric_matches))
                }
            },
            "remarks": remarks
        }
