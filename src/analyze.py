"""
AI Job Analysis Module
Uses Claude API to analyze job relevance and score matches
"""

from typing import Dict, Optional
import json


class JobAnalyzer:
    """Analyzes job descriptions and scores relevance using AI"""

    def __init__(self, api_key: str, config: Dict, user_profile: Dict = None):
        """Initialize Claude API client"""
        self.api_key = api_key
        self.config = config
        self.criteria = config.get('criteria', {})
        self.matching_config = config.get('matching', {})
        self.use_ai = self.matching_config.get('use_ai', True)

        # User profile for matching
        self.user_profile = user_profile or self._default_profile()

        # Import Anthropic only if API key is provided
        if api_key and api_key != "YOUR_ANTHROPIC_API_KEY_HERE" and self.use_ai:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
                self.enabled = True
            except ImportError:
                print("Warning: anthropic package not installed. Run: pip install anthropic")
                self.client = None
                self.enabled = False
        else:
            self.client = None
            self.enabled = False
            if self.use_ai:
                print("Claude API key not configured. Using rule-based matching.")

    def _default_profile(self) -> Dict:
        """Default user profile (Ido's background)"""
        return {
            "name": "Ido Appel",
            "current_role": "Senior VLSI Engineer",
            "background": "5 years in VLSI verification and design, team leadership experience",
            "education": "BS Electrical Engineering, Tel Aviv University",
            "skills": [
                "VLSI design and verification",
                "SystemVerilog UVM",
                "RISC-V architecture",
                "SoC design",
                "Memory subsystems (LPDDR)",
                "Team leadership",
                "Robotics vision systems",
                "AI hardware accelerators"
            ],
            "target_roles": ["Product Manager in Deep Tech", "Venture Capital in Deep Tech"],
            "preferences": {
                "industries": ["Robotics", "AI Hardware", "Semiconductors", "Deep Tech"],
                "locations": ["London", "Remote", "UK"],
                "company_stage": ["Series A+", "Established VC funds"]
            }
        }

    def analyze_job(self, job: Dict, company: Dict = None) -> Dict:
        """
        Analyze a job and return relevance score (0-100) with reasoning

        Returns:
        {
            "score": 85,
            "role_type": "pm" | "vc" | "other",
            "reasoning": "This role matches because...",
            "pros": [...],
            "cons": [...],
            "recommendation": "apply" | "consider" | "skip"
        }
        """
        if self.enabled:
            return self._ai_analyze(job, company)
        else:
            return self._rule_based_analyze(job, company)

    def _ai_analyze(self, job: Dict, company: Dict = None) -> Dict:
        """Use Claude API to analyze job match"""
        try:
            prompt = self._build_analysis_prompt(job, company)

            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse JSON response
            try:
                analysis = json.loads(response_text)
                return analysis
            except json.JSONDecodeError:
                # Fallback if response isn't valid JSON
                return self._rule_based_analyze(job, company)

        except Exception as e:
            print(f"Error analyzing job with AI: {str(e)}")
            return self._rule_based_analyze(job, company)

    def _build_analysis_prompt(self, job: Dict, company: Dict = None) -> str:
        """Build prompt for Claude to analyze job match"""
        company_info = f"Company: {company['name']} ({company.get('industry', 'Unknown industry')})" if company else ""

        return f"""Analyze this job posting for relevance to the candidate profile below.

CANDIDATE PROFILE:
{json.dumps(self.user_profile, indent=2)}

JOB POSTING:
{company_info}
Title: {job['title']}
Location: {job.get('location', 'Not specified')}
Description:
{job.get('description', 'No description available')[:2000]}

SCORING CRITERIA:
- Role alignment with target roles (PM in deep tech or VC in deep tech): 40 points
- Industry relevance (robotics, AI hardware, semiconductors): 25 points
- Technical depth requirement (needs hardware/technical background): 20 points
- Location match (London, UK, Remote): 10 points
- Company stage match: 5 points

Return ONLY a JSON object (no other text) with this exact structure:
{{
  "score": <0-100>,
  "role_type": "<pm|vc|other>",
  "reasoning": "<2-3 sentence explanation of the score>",
  "pros": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "cons": ["<concern 1>", "<concern 2>"],
  "recommendation": "<apply|consider|skip>"
}}

Recommendations:
- "apply" if score >= 80
- "consider" if score 60-79
- "skip" if score < 60
"""

    def _rule_based_analyze(self, job: Dict, company: Dict = None) -> Dict:
        """Rule-based analysis (fallback when AI is not available)"""
        title_lower = job['title'].lower()
        description_lower = job.get('description', '').lower()
        location_lower = job.get('location', '').lower()

        # Also check title for location patterns (e.g., "US - City", "UK - City")
        title_and_location = title_lower + ' ' + location_lower

        score = 0
        role_type = "other"
        pros = []
        cons = []

        # Role type detection and scoring
        if any(keyword in title_lower for keyword in ['product manager', 'product lead', 'project manager', 'program manager', 'pm ', 'tpm']):
            role_type = "pm"
            score += 40

            if 'product' in title_lower:
                pros.append("Product Manager role - matches target")
            elif 'project' in title_lower:
                pros.append("Project Manager role - matches target")
            elif 'program' in title_lower:
                pros.append("Program Manager role - matches target")

            # Technical PM/Project Manager bonus
            if any(keyword in title_lower + description_lower for keyword in ['technical', 'hardware', 'platform', 'infrastructure', 'engineering']):
                score += 10
                pros.append("Technical/Hardware/Engineering PM focus")

        elif any(keyword in title_lower for keyword in ['venture', 'vc']) or \
             any(phrase in title_lower for phrase in ['investment analyst', 'investment associate', 'principal - investment', 'principal investor']):
            role_type = "vc"
            score += 40
            pros.append("VC role - matches target")
        else:
            cons.append("Role type doesn't match PM or VC targets")

        # Industry relevance
        industry_keywords = ['robotics', 'autonomous', 'ai hardware', 'chip', 'semiconductor', 'soc', 'vlsi', 'deep tech', 'hardware', 'edge ai']
        matched_industries = [kw for kw in industry_keywords if kw in title_lower + description_lower]

        if matched_industries:
            score += min(25, len(matched_industries) * 8)
            pros.append(f"Relevant industry: {', '.join(matched_industries[:2])}")
        else:
            cons.append("Industry may not be deep tech focused")

        # Technical requirements
        tech_keywords = ['vlsi', 'soc', 'risc-v', 'hardware', 'chip', 'technical background', 'engineering degree']
        if any(kw in description_lower for kw in tech_keywords):
            score += 15
            pros.append("Values technical/hardware background")

        # Location match - STRICT: London, UK, and nearby UK cities ONLY
        uk_locations = ['london', 'cambridge', 'bristol', 'oxford', 'manchester', 'edinburgh',
                       'glasgow', 'birmingham', 'uk', 'united kingdom', 'remote', 'hybrid']

        # Check if location is in UK/acceptable (check both title and location field)
        is_uk_location = any(loc in title_and_location for loc in uk_locations)

        # Check for REJECTED locations (non-UK) - check title and location
        rejected_locations = ['austin', 'texas', 'us ', 'usa', 'united states', 'california', 'new york',
                            'bengaluru', 'bangalore', 'india', 'china', 'singapore', 'taiwan', 'hsinchu',
                            'milpitas', 'san francisco', 'seattle']
        is_rejected = any(loc in title_and_location for loc in rejected_locations)

        if is_rejected:
            # Heavy penalty for non-UK locations
            score = max(0, score - 50)
            cons.append(f"Location NOT in London/UK: {job.get('location', '')}")
        elif is_uk_location:
            score += 10
            pros.append(f"Good location: {job.get('location', '')}")
        else:
            if location_lower and location_lower != 'not specified':
                cons.append(f"Location unclear: {job.get('location', '')}")

        # Company info bonus
        if company:
            company_industry = company.get('industry', '').lower()
            if any(kw in company_industry for kw in ['robotics', 'ai', 'semiconductor', 'deep tech']):
                score += 5
                pros.append(f"Strong company: {company.get('name')}")

        # Negative signals
        exclude_keywords = self.criteria.get('keywords_exclude', [])
        if any(kw.lower() in title_lower for kw in exclude_keywords):
            score = max(0, score - 30)
            cons.append("Contains excluded keywords")

        # Cap score at 100
        score = min(100, score)

        # Recommendation
        if score >= 80:
            recommendation = "apply"
        elif score >= 60:
            recommendation = "consider"
        else:
            recommendation = "skip"

        reasoning = f"Scored {score}/100. " + (pros[0] if pros else "Limited match to criteria")

        return {
            "score": score,
            "role_type": role_type,
            "reasoning": reasoning,
            "pros": pros,
            "cons": cons,
            "recommendation": recommendation
        }
