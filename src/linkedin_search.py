"""
LinkedIn Job Search Module
Searches LinkedIn for jobs matching criteria using Firecrawl
"""

from typing import List, Dict
import re
from urllib.parse import quote


class LinkedInJobSearcher:
    """Searches LinkedIn for job postings using Firecrawl"""

    def __init__(self, scraper):
        """
        Initialize with a JobScraper instance (for Firecrawl access)

        Args:
            scraper: JobScraper instance with Firecrawl client
        """
        self.scraper = scraper

    def search_jobs(self, query: str, location: str = "London, UK", limit: int = 25) -> List[Dict]:
        """
        Search LinkedIn for jobs matching query and location

        Args:
            query: Job search query (e.g., "Product Manager deep tech")
            location: Location to search (default: "London, UK")
            limit: Max results to return

        Returns:
            List of job dictionaries with title, company, location, url
        """
        if not self.scraper.enabled:
            print("Firecrawl not enabled. Cannot search LinkedIn.")
            return []

        # Build LinkedIn job search URL
        encoded_query = quote(query)
        encoded_location = quote(location)

        # LinkedIn Jobs search URL format
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}&location={encoded_location}&f_TPR=r604800"  # Jobs from last 7 days

        print(f"Searching LinkedIn: '{query}' in '{location}'")
        print(f"URL: {search_url}")

        try:
            # Use Firecrawl to scrape the search results page
            result = self.scraper.client.scrape(
                search_url,
                formats=['markdown']
            )

            if not result or not hasattr(result, 'markdown') or not result.markdown:
                print(f"Failed to scrape LinkedIn search results")
                return []

            markdown = result.markdown

            # Extract job listings from markdown
            jobs = self._extract_jobs_from_search_results(markdown, limit)

            print(f"Found {len(jobs)} jobs on LinkedIn")
            return jobs

        except Exception as e:
            print(f"Error searching LinkedIn: {str(e)}")
            return []

    def _extract_jobs_from_search_results(self, markdown: str, limit: int) -> List[Dict]:
        """
        Extract job postings from LinkedIn search results markdown

        LinkedIn search results typically have format:
        [Job Title](job_url)
        Company Name
        Location
        """
        jobs = []
        lines = markdown.split('\n')

        # Look for job links - LinkedIn job URLs contain /jobs/view/
        job_link_pattern = r'\[(.*?)\]\((https://[^)]*linkedin\.com/jobs/view/[^)]+)\)'

        i = 0
        while i < len(lines) and len(jobs) < limit:
            line = lines[i]

            # Try to find job title link
            match = re.search(job_link_pattern, line)
            if match:
                title = match.group(1).strip()
                url = match.group(2).strip()

                # Next few lines usually contain company and location
                company = ''
                location = ''

                # Look ahead for company and location info
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_line = lines[j].strip()

                    if not next_line or next_line.startswith('#') or next_line.startswith('['):
                        break

                    # Check if line looks like a location (contains city/country)
                    if any(loc in next_line for loc in ['London', 'UK', 'United Kingdom', 'Remote', 'Cambridge', 'Bristol']):
                        location = next_line
                    # Otherwise, assume it's company name if we haven't found one yet
                    elif not company and len(next_line) > 2:
                        company = next_line

                jobs.append({
                    'title': title,
                    'company': company if company else 'Unknown Company',
                    'location': location if location else 'Not specified',
                    'url': url,
                    'description': f'LinkedIn job posting: {title} at {company}'
                })

            i += 1

        return jobs

    def search_multiple_queries(self, queries: List[str], location: str = "London, UK") -> List[Dict]:
        """
        Search LinkedIn with multiple queries and combine results

        Args:
            queries: List of search queries
            location: Location to search

        Returns:
            Combined list of unique jobs from all queries
        """
        all_jobs = []
        seen_urls = set()

        for query in queries:
            jobs = self.search_jobs(query, location, limit=25)

            # Deduplicate by URL
            for job in jobs:
                if job['url'] not in seen_urls:
                    all_jobs.append(job)
                    seen_urls.add(job['url'])

        return all_jobs
