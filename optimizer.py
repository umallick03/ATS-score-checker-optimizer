import re
import os
import urllib.request
import json

WEAK_PHRASES = {
    r'\bresponsible for managing\b': 'Managed',
    r'\bresponsible for developing\b': 'Developed',
    r'\bresponsible for designing\b': 'Designed',
    r'\bresponsible for\b': 'Spearheaded',
    r'\bhelped with\b': 'Coordinated',
    r'\bhelped to\b': 'Facilitated',
    r'\bassisted in\b': 'Collaborated on',
    r'\bassisted with\b': 'Supported',
    r'\bworked on\b': 'Executed',
    r'\bmanaged to\b': 'Achieved',
    r'\bstarted to\b': 'Initiated',
    r'\bparticipated in\b': 'Contributed to',
    r'\bduty was to\b': 'Executed',
    r'\bwas in charge of\b': 'Directed'
}

SUGGESTED_METRICS = [
    "increasing processing speed by 25%",
    "reducing deployment downtime by 40%",
    "resulting in a 15% increase in team productivity",
    "saving approximately $12,000 in monthly cloud infrastructure costs",
    "delivering the project 2 weeks ahead of schedule",
    "improving system reliability to 99.99% uptime",
    "reducing response latency by 150ms"
]

class ATSOptimizer:
    @staticmethod
    def clean_typos(text: str) -> str:
        # Detect and remove double-word typos (e.g., "to ensure to ensure" -> "to ensure")
        # Match word boundaries and any duplicate word separated by whitespace
        text_cleaned = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
        # Also clean specific multi-word duplicates like "to ensure to ensure"
        text_cleaned = re.sub(r'\b(to ensure)\s+\1\b', r'\1', text_cleaned, flags=re.IGNORECASE)
        return text_cleaned

    @staticmethod
    def get_manual_suggestions(score_result: dict) -> dict:
        profile = score_result.get("profile", "general")
        missing_kw = score_result.get("breakdown", {}).get("keywords", {}).get("missing", [])
        
        # Select standard bullet frameworks (STAR Method)
        star_frameworks = [
            "Accomplished [Action/Result] as measured by [Metrics/Data], by implementing [Skills/Tools].",
            "Spearheaded [Project/Initiative] leading to [Business Impact Metric] through [Specific Technology/Methodology].",
            "Optimized [System/Process] which reduced [Inefficiency/Cost] by [Percentage/Value] using [Skill/Tool]."
        ]
        
        return {
            "profile_suggestions": f"To optimize for your '{profile.replace('_', ' ').capitalize()}' target profile, focus on inserting relevant technical terms.",
            "recommended_keywords": missing_kw[:10], # Top 10 missing keywords
            "formatting_tips": [
                "Remove any tables, text boxes, or custom graphic columns. Standard scanners parse single-column text top-to-bottom.",
                "Stick to standard section headers (Summary, Experience, Education, Skills).",
                "Ensure your employment dates are clearly written as MM/YYYY or Month YYYY (e.g., '08/2021 - Present')."
            ],
            "star_frameworks": star_frameworks
        }

    @classmethod
    def analyze_bullet_deficiencies(cls, original: str, optimized: str) -> dict:
        """
        Analyzes the original sentence/bullet against the optimized output to
        highlight points lowering the score and suggest the correct version.
        """
        import html
        highlighted_original = html.escape(original)
        badges = []
        
        # 1. Detect weak phrases and highlight them
        has_weak_phrase = False
        for pattern in WEAK_PHRASES.keys():
            if re.search(pattern, original, flags=re.IGNORECASE):
                has_weak_phrase = True
                highlighted_original = re.sub(
                    pattern,
                    lambda m: f'<span style="background-color: rgba(239, 68, 68, 0.15); color: #ef4444; border-bottom: 1px dashed #ef4444; font-weight: 600; padding: 0 4px;">{html.escape(m.group(0))}</span>',
                    highlighted_original,
                    flags=re.IGNORECASE
                )
                
        if has_weak_phrase:
            badges.append("Weak Phrasing")
            
        # 2. Check for missing metrics
        original_has_num = bool(re.search(r'\d', original))
        optimized_has_num = bool(re.search(r'\d', optimized))
        if not original_has_num and optimized_has_num:
            badges.append("Missing Metric")
            
        # 3. Check for missing action verbs
        from scorer import ACTION_VERBS
        original_lower = original.lower()
        original_has_verb = any(re.search(r'\b' + re.escape(v) + r'\b', original_lower) for v in ACTION_VERBS)
        if not original_has_verb:
            badges.append("Weak Action Verb")
            
        # If no specific badge but it was rewritten
        if not badges and original.strip().lower() != optimized.strip().lower():
            badges.append("Formatting / Typos")
            
        return {
            "original_html": highlighted_original,
            "badges": badges
        }

    @classmethod
    def rewrite_sentence_locally(cls, text: str, target_profile: str = "general") -> str:
        # 1. Clean typos
        optimized = cls.clean_typos(text)
        
        # 2. Replace weak passive phrases with strong action verbs
        for pattern, replacement in WEAK_PHRASES.items():
            optimized = re.sub(pattern, replacement, optimized, flags=re.IGNORECASE)
            
        # 3. Capitalize first letter of bullets if they are lowercase
        if optimized and optimized[0].islower():
            optimized = optimized[0].upper() + optimized[1:]
            
        # 4. If no numeric metric is detected, append a mock metric helper based on target profile
        has_metric = bool(re.search(r'\d', optimized))
        if not has_metric:
            # Add a realistic outcome suffix
            metric_suffix = SUGGESTED_METRICS[hash(text) % len(SUGGESTED_METRICS)]
            if optimized.rstrip().endswith('.'):
                optimized = optimized.rstrip('.') + f", {metric_suffix}."
            else:
                optimized = optimized + f", {metric_suffix}."
                
        return optimized

    @classmethod
    def rewrite_sentence_gemini(cls, text: str, target_profile: str = "general", api_key: str = None) -> str:
        if not api_key:
            return cls.rewrite_sentence_locally(text, target_profile)
            
        prompt = (
            f"You are an expert resume writer and ATS optimization specialist. "
            f"Rewrite the following resume bullet point to make it high-impact, professional, and optimized for an ATS scan targeting a '{target_profile}' role. "
            f"Ensure you start with a strong action verb, remove weak phrases (like 'responsible for'), integrate relevant keywords if natural, "
            f"and include/enhance quantifiable metrics (e.g., percentages, dollar amounts, project scopes) showing business impact. "
            f"Do not add any conversational text or explanation. Output ONLY the single rewritten bullet point.\n\n"
            f"Original bullet: {text}"
        )
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                rewritten = res_body['candidates'][0]['content']['parts'][0]['text'].strip()
                # Clean up any surrounding quotes or markdown bullet symbols the model might have returned
                rewritten = re.sub(r'^[\s•\-\*"\']+|[\s"\']+$', '', rewritten)
                return rewritten
        except Exception:
            # Fallback to local rule-based engine if network/API fails
            return cls.rewrite_sentence_locally(text, target_profile)

    @classmethod
    def optimize_resume_text(cls, text: str, target_profile: str = "general", api_key: str = None) -> dict:
        # Split text into lines/bullets
        lines = text.split('\n')
        rewritten_lines = []
        changes = []
        
        for line in lines:
            trimmed = line.strip()
            # If the line is a candidate for bullet point optimization:
            # It starts with a bullet symbol, hyphen, or is a typical experience item (length > 20, doesn't look like section header)
            is_bullet = trimmed.startswith(('•', '-', '*', '▪', '●'))
            cleaned_bullet = re.sub(r'^[\s•\-\*▪●]+', '', trimmed).strip()
            
            # Simple section header checker
            is_header = len(cleaned_bullet) < 30 and cleaned_bullet.isupper()
            
            if (is_bullet or len(cleaned_bullet) > 30) and not is_header and cleaned_bullet:
                # Rewrite this bullet
                rewritten = cls.rewrite_sentence_gemini(cleaned_bullet, target_profile, api_key)
                
                # Check if it was modified
                if rewritten.lower() != cleaned_bullet.lower():
                    # Prefix with a bullet symbol
                    bullet_prefix = "• "
                    rewritten_lines.append(bullet_prefix + rewritten)
                    changes.append({
                        "original": trimmed,
                        "optimized": bullet_prefix + rewritten
                    })
                else:
                    rewritten_lines.append(trimmed)
            else:
                # Keep section headings and formatting intact, but clean double-word typos
                rewritten_lines.append(cls.clean_typos(trimmed))
                
        return {
            "optimized_text": "\n".join(rewritten_lines),
            "changes": changes
        }
