"""
Company Discovery Module
Uses web search to find relevant companies and VC firms
"""

import requests
from typing import List, Dict
from urllib.parse import quote_plus


class CompanyDiscovery:
    """Discovers companies and VC firms based on search criteria"""

    def __init__(self, config: Dict):
        """Initialize with configuration"""
        self.config = config
        self.criteria = config.get('criteria', {})
        self.search_queries = config.get('search_queries', {})

    def discover_companies(self) -> List[Dict]:
        """
        Discover companies based on search queries
        Returns list of companies with name, url, type
        """
        companies = []

        # Get custom companies from config
        custom_companies = self.config.get('custom_companies', [])
        if custom_companies:
            for company in custom_companies:
                companies.append({
                    'name': company['name'],
                    'url': company.get('url', ''),
                    'career_page_url': company.get('url', ''),  # Assume URL is career page
                    'company_type': 'custom',
                    'source': 'config'
                })

        # Discover VC firms
        vc_queries = self.search_queries.get('vc_firms', [])
        for query in vc_queries:
            results = self._search_web(query, company_type='vc_firm')
            companies.extend(results)

        # Discover companies
        company_queries = self.search_queries.get('companies', [])
        for query in company_queries:
            results = self._search_web(query, company_type='company')
            companies.extend(results)

        # Deduplicate by name
        seen = set()
        unique_companies = []
        for company in companies:
            if company['name'] not in seen:
                seen.add(company['name'])
                unique_companies.append(company)

        return unique_companies

    def _search_web(self, query: str, company_type: str = 'company') -> List[Dict]:
        """
        Search the web for companies

        Note: This is a placeholder implementation. In production, you would:
        1. Use Firecrawl's search feature
        2. Use a search API (Google Custom Search, SerpAPI)
        3. Scrape curated lists (Crunchbase, AngelList)

        For now, returns manually curated companies as examples
        """
        # TODO: Implement actual web search using Firecrawl or search API
        # For now, return example companies based on query type

        if 'vc' in query.lower() or 'venture capital' in query.lower():
            return self._get_example_vc_firms()
        else:
            return self._get_example_companies()

    def _get_example_vc_firms(self) -> List[Dict]:
        """Return example VC firms in London/UK (to be replaced with real search)"""
        return [
            {
                'name': 'Atomico',
                'url': 'https://atomico.com',
                'career_page_url': 'https://atomico.com/careers',
                'company_type': 'vc_firm',
                'industry': 'Deep Tech VC',
                'location': 'London',
                'source': 'discovery'
            },
            {
                'name': 'Balderton Capital',
                'url': 'https://www.balderton.com',
                'career_page_url': 'https://www.balderton.com/careers',
                'company_type': 'vc_firm',
                'industry': 'Technology VC',
                'location': 'London',
                'source': 'discovery'
            },
            {
                'name': 'Index Ventures',
                'url': 'https://www.indexventures.com',
                'career_page_url': 'https://www.indexventures.com/careers',
                'company_type': 'vc_firm',
                'industry': 'Technology VC',
                'location': 'London',
                'source': 'discovery'
            },
            {
                'name': 'Accel',
                'url': 'https://www.accel.com',
                'career_page_url': 'https://www.accel.com/careers',
                'company_type': 'vc_firm',
                'industry': 'Technology VC',
                'location': 'London',
                'source': 'discovery'
            },
            {
                'name': 'IQ Capital',
                'url': 'https://iqcapital.vc',
                'career_page_url': 'https://iqcapital.vc/careers',
                'company_type': 'vc_firm',
                'industry': 'Deep Tech VC',
                'location': 'London',
                'source': 'discovery'
            }
        ]

    def _get_example_companies(self) -> List[Dict]:
        """Return example deep tech companies (to be replaced with real search)"""
        return [
            {
                'name': 'Wayve',
                'url': 'https://wayve.ai',
                'career_page_url': 'https://wayve.ai/careers',
                'company_type': 'company',
                'industry': 'Autonomous Vehicles',
                'location': 'London',
                'funding_stage': 'Series C',
                'source': 'discovery'
            },
            {
                'name': 'Graphcore',
                'url': 'https://www.graphcore.ai',
                'career_page_url': 'https://www.graphcore.ai/jobs',
                'company_type': 'company',
                'industry': 'AI Hardware',
                'location': 'Bristol, UK',
                'funding_stage': 'Series E',
                'source': 'discovery'
            },
            {
                'name': 'Oxbotica',
                'url': 'https://www.oxbotica.com',
                'career_page_url': 'https://www.oxbotica.com/careers',
                'company_type': 'company',
                'industry': 'Autonomous Vehicles',
                'location': 'Oxford, UK',
                'funding_stage': 'Series C',
                'source': 'discovery'
            },
            {
                'name': 'FiveAI',
                'url': 'https://five.ai',
                'career_page_url': 'https://five.ai/careers',
                'company_type': 'company',
                'industry': 'Autonomous Vehicles',
                'location': 'London',
                'funding_stage': 'Series B',
                'source': 'discovery'
            },
            {
                'name': 'Arm',
                'url': 'https://www.arm.com',
                'career_page_url': 'https://careers.arm.com',
                'company_type': 'company',
                'industry': 'Semiconductors',
                'location': 'Cambridge, UK',
                'funding_stage': 'Public',
                'source': 'discovery'
            },
            {
                'name': 'Cerebras',
                'url': 'https://www.cerebras.net',
                'career_page_url': 'https://www.cerebras.net/careers',
                'company_type': 'company',
                'industry': 'AI Hardware',
                'location': 'Remote',
                'funding_stage': 'Series F',
                'source': 'discovery'
            }
        ]

    def find_career_page(self, company_url: str) -> str:
        """
        Find the career/jobs page URL for a company

        TODO: Implement smart career page discovery
        Common patterns: /careers, /jobs, /join-us, /team, /work-with-us
        """
        common_paths = ['/careers', '/jobs', '/join-us', '/team', '/work-with-us', '/opportunities']

        for path in common_paths:
            career_url = company_url.rstrip('/') + path
            # TODO: Check if URL exists
            # For now, just return first pattern
            return career_url

        return company_url
