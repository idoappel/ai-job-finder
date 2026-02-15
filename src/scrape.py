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

        This is a heuristic approach - looks for patterns like:
        - Headings followed by job titles
        - Links to job pages
        - Location and description text
        """
        jobs = []

        # Split by lines
        lines = markdown.split('\n')

        current_job = None

        for i, line in enumerate(lines):
            # Look for job titles (usually in headings or bold)
            if re.match(r'^#+\s+', line) or re.match(r'^\*\*.*\*\*', line):
                title = re.sub(r'^#+\s+|\*\*', '', line).strip()

                # Check if this looks like a job title (contains role keywords)
                if self._is_job_title(title):
                    # Save previous job if exists
                    if current_job:
                        jobs.append(current_job)

                    # Start new job
                    current_job = {
                        'title': title,
                        'description': '',
                        'url': base_url,  # Default to career page URL
                        'location': ''
                    }

            # Look for URLs (job links)
            elif current_job and re.search(r'\[.*?\]\((https?://[^\)]+)\)', line):
                match = re.search(r'\[.*?\]\((https?://[^\)]+)\)', line)
                if match:
                    current_job['url'] = match.group(1)

            # Look for location keywords
            elif current_job and any(loc in line for loc in ['Location:', 'Remote', 'London', 'UK', 'United Kingdom']):
                current_job['location'] = line.strip()

            # Accumulate description
            elif current_job and line.strip():
                current_job['description'] += line + '\n'

        # Add last job
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
