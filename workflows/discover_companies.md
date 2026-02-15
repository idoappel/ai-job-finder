# Workflow: Discover Companies

## Objective
Find relevant deep tech companies and VC firms that might have PM or VC roles suitable for Ido.

## Inputs
- Search queries from `config.yaml`
- Custom companies from `config.yaml`
- Existing companies in database (to avoid duplicates)

## Tools Required
- `src/discover.py`

## Process

### Current Implementation (v1)
Returns manually curated lists of companies:
- London/UK VC firms (Atomico, Balderton, Index, Accel, IQ Capital)
- Deep tech companies (Wayve, Graphcore, Oxbotica, Arm, Cerebras)

**This is a starting point.** Future versions will use web search or APIs.

### Future Implementation (v2+)

**Option 1: Web Search**
- Use search queries from config
- Example: "London deep tech venture capital firms"
- Extract company names and URLs from results
- Use Firecrawl to scrape company directories

**Option 2: Curated Databases**
- Scrape Crunchbase for deep tech companies in UK
- Scrape AngelList for relevant job postings
- Use VC firm databases (Dealroom, Pitchbook)

**Option 3: Firecrawl Agent Mode**
- Use Firecrawl's autonomous agent
- Give it search query and extraction criteria
- Let it find and extract company information

### Search Queries to Use

**For VC Firms:**
- "London deep tech venture capital firms"
- "UK robotics AI hardware VC investors"
- "European semiconductor venture capital"
- "Deep tech VC funds London"

**For Companies:**
- "London robotics companies hiring"
- "UK AI chip startups"
- "Autonomous vehicle companies UK"
- "Semiconductor companies hiring product managers"
- "Hardware PM jobs robotics"

### Company Data to Extract

Required:
- Name
- Website URL
- Career page URL (or infer: /careers, /jobs, etc.)

Optional:
- Industry/sector
- Location
- Funding stage
- Company type (vc_firm, company, startup)

### Quality Checks

**Include if:**
- Operates in deep tech (robotics, AI hardware, semiconductors)
- Based in or has office in London/UK or remote-friendly
- Actively hiring (has career page or recent job posts)
- Series A+ for companies, $100M+ AUM for VCs

**Exclude if:**
- Pure software companies (no hardware component)
- Consumer social apps
- Gaming companies
- Outside target geography (unless major player in field)

### Deduplication
- Check company name against database
- Ignore if already in database (don't re-add)
- Update career page URL if better one found

## Expected Output

List of companies with:
```python
{
    'name': 'Wayve',
    'url': 'https://wayve.ai',
    'career_page_url': 'https://wayve.ai/careers',
    'company_type': 'company',
    'industry': 'Autonomous Vehicles',
    'location': 'London',
    'funding_stage': 'Series C',
    'source': 'discovery'
}
```

## Known Issues

**Current limitations:**
- Uses hardcoded company lists (needs real search implementation)
- No automatic discovery yet
- Limited to manually researched companies

**To improve:**
- Implement real web search or API integration
- Add Crunchbase/AngelList scraping
- Use Firecrawl agent mode for autonomous discovery
- Learn from which companies have good job matches (find similar ones)

## Error Handling

**No companies found:**
- Check config.yaml has search_queries or custom_companies
- Fall back to hardcoded example list
- Warn user to add custom companies

**Invalid URLs:**
- Skip companies with missing URLs
- Try to construct career page URL from base URL

**API/Search limits:**
- If using paid search API, respect rate limits
- Cache results for 24 hours

## Success Metrics
- Discover 10-20 new companies per week
- 80% of companies have valid career pages
- 50% of companies yield at least one job posting
- Mix of VCs and companies (not all one type)

## Improvements to Track
- Which search queries yield best companies
- Patterns in company names/URLs
- Industries with most opportunities
- Geographic distribution of matches
