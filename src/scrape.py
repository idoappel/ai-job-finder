"""
Web Scraping Module using Firecrawl
Scrapes career pages and extracts job postings
"""

from typing import List, Dict, Optional
import re


class JobScraper:
    """Scrapes job postings from company career pages using Firecrawl"""

    def __init__(self, api_key: str, config: Dict):
        """Initialize Firecrawl client"""
        self.api_key = api_key
        self.config = config
        self.scraping_config = config.get('scraping', {})

        # Import Firecrawl only if API key is provided
        if api_key and api_key != "YOUR_FIRECRAWL_API_KEY_HERE":
            try:
                from firecrawl import FirecrawlApp
                self.client = FirecrawlApp(api_key=api_key)
                self.enabled = True
            except ImportError:
                print("Warning: firecrawl-py not installed. Run: pip install firecrawl-py")
                self.client = None
                self.enabled = False
        else:
            self.client = None
            self.enabled = False
            print("Firecrawl API key not configured. Scraping disabled.")

    def scrape_career_page(self, url: str, company_name: str = None) -> List[Dict]:
        """
        Scrape a company's career page and extract job postings
        Returns list of jobs with title, description, url, location
        """
        if not self.enabled:
            print(f"Scraping disabled. Would scrape: {url}")
            return self._get_mock_jobs(company_name)

        try:
            # Use Firecrawl to scrape the page
            result = self.client.scrape(
                url,
                formats=['markdown']
            )

            if not result or not hasattr(result, 'markdown') or not result.markdown:
                print(f"Failed to scrape {url}")
                return []

            markdown_content = result.markdown

            # Extract job postings from markdown
            jobs = self._extract_jobs_from_markdown(markdown_content, url)

            print(f"Found {len(jobs)} jobs at {url}")
            return jobs

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return []

    def _extract_jobs_from_markdown(self, markdown: str, base_url: str) -> List[Dict]:
        """
        Extract job listings from markdown content

        Handles multiple formats:
        1. Markdown links: [Job Title\n\nDepartment Location](URL)
        2. Headings with job titles
        3. Greenhouse/Lever ATS systems
        """
        jobs = []

        # Pattern 1: Markdown links with job info
        # Example: [Senior ML Engineer\n\nEngineering - AI Bristol, UK](https://...)
        link_pattern = r'\[(.*?)\]\((https?://[^\)]+)\)'

        for match in re.finditer(link_pattern, markdown, re.DOTALL):
            link_text = match.group(1)
            url = match.group(2)

            # Skip navigation links, images, etc.
            if not url or 'job' not in url.lower():
                continue

            # Parse link text - format is often: Title\n\nDepartmentLocation
            parts = link_text.split('\\n')
            parts = [p.strip() for p in parts if p.strip()]

            if not parts:
                continue

            # First part is usually the title
            title = parts[0]

            # Clean up title - remove "Multiple Vacancies Available" and other noise
            title = re.sub(r'Multiple Vacancies Available.*$', '', title, flags=re.IGNORECASE).strip()
            title = re.sub(r'\\n|\\r', ' ', title).strip()  # Remove literal \n characters
            title = re.sub(r'\s+', ' ', title)  # Normalize whitespace

            # Check if this looks like a job title
            if not self._is_job_title(title):
                continue

            # Extract location from remaining parts
            location = ''
            department = ''

            for part in parts[1:]:
                # Check if part contains location keywords
                if any(loc in part for loc in ['UK', 'US', 'United States', 'Remote', 'London', 'Cambridge', 'Bristol', 'Austin', 'Bengaluru']):
                    location = part
                elif 'Engineering' in part or 'Research' in part or 'Operations' in part:
                    department = part

            # If we didn't find location in parts, try to extract from full text
            if not location:
                location_match = re.search(r'(London|Cambridge|Bristol|Remote|UK|United States|Austin|Bengaluru|[A-Z][a-z]+,\s*[A-Z]{2})', link_text)
                if location_match:
                    location = location_match.group(1)

            jobs.append({
                'title': title,
                'description': department if department else link_text[:200],
                'url': url,
                'location': location if location else 'Not specified'
            })

        # Pattern 2: Fallback - Look for headings that might be job titles
        if len(jobs) == 0:
            lines = markdown.split('\n')
            current_job = None

            for line in lines:
                # Look for job titles in headings
                if re.match(r'^#+\s+', line):
                    title = re.sub(r'^#+\s+', '', line).strip()

                    if self._is_job_title(title):
                        if current_job:
                            jobs.append(current_job)

                        current_job = {
                            'title': title,
                            'description': '',
                            'url': base_url,
                            'location': ''
                        }

                # Look for URLs
                elif current_job:
                    url_match = re.search(r'\(https?://[^\)]+\)', line)
                    if url_match:
                        current_job['url'] = url_match.group(0)[1:-1]

                    # Look for location
                    if any(loc in line for loc in ['Location:', 'Remote', 'London', 'UK', 'Cambridge']):
                        current_job['location'] = line.strip()

            if current_job:
                jobs.append(current_job)

        return jobs

    def _is_job_title(self, text: str) -> bool:
        """Check if text looks like a job title"""
        role_keywords = [
            'manager', 'engineer', 'analyst', 'associate', 'director', 'lead',
            'product', 'software', 'hardware', 'data', 'designer', 'researcher',
            'scientist', 'architect', 'developer', 'specialist', 'coordinator',
            'principal', 'senior', 'junior', 'staff', 'intern'
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in role_keywords)

    def _get_mock_jobs(self, company_name: str = None) -> List[Dict]:
        """
        Return mock jobs for testing (when Firecrawl is not configured)
        """
        if not company_name:
            return []

        # Return different mock jobs based on company name
        if 'vc' in company_name.lower() or 'capital' in company_name.lower():
            return [
                {
                    'title': 'Investment Associate - Deep Tech',
                    'description': f'Join {company_name} as an Investment Associate focusing on deep tech investments including robotics, AI hardware, and semiconductors.',
                    'url': f'https://example.com/{company_name.lower().replace(" ", "-")}/jobs/associate',
                    'location': 'London, UK'
                },
                {
                    'title': 'Venture Capital Analyst',
                    'description': f'{company_name} is looking for an analyst to support our deep tech investment thesis.',
                    'url': f'https://example.com/{company_name.lower().replace(" ", "-")}/jobs/analyst',
                    'location': 'London, UK'
                }
            ]
        else:
            return [
                {
                    'title': 'Senior Product Manager - Hardware',
                    'description': f'Lead product development at {company_name} for our next-generation hardware platform.',
                    'url': f'https://example.com/{company_name.lower().replace(" ", "-")}/jobs/pm-hardware',
                    'location': 'London, UK / Remote'
                },
                {
                    'title': 'Technical Product Manager - Robotics',
                    'description': f'{company_name} is seeking a technical PM with robotics or hardware experience.',
                    'url': f'https://example.com/{company_name.lower().replace(" ", "-")}/jobs/pm-robotics',
                    'location': 'Remote'
                }
            ]
