# Workflow: Daily Job Scan

## Objective
Discover new companies and job postings matching Ido's criteria, analyze them with AI, and surface high-quality matches.

## Inputs
- User criteria from `config.yaml`
- Existing companies in database
- Firecrawl API key
- Anthropic API key (optional for AI matching)

## Tools Required
1. `src/discover.py` - Company discovery
2. `src/scrape.py` - Job scraping via Firecrawl
3. `src/analyze.py` - AI job matching
4. `src/database.py` - Store results
5. `src/notify.py` - Display matches

## Process

### 1. Discover Companies
**Tool:** `python src/main.py discover`

**What it does:**
- Searches for deep tech companies and VC firms
- Uses search queries from config
- Adds custom companies from config
- Stores in database

**Success criteria:**
- Find at least 5 new companies per scan
- Mix of VCs and companies
- Deduplicate by name

**If fails:**
- Check if custom_companies in config has entries
- Check internet connection
- Proceed with existing companies in database

### 2. Scrape Career Pages
**For each company discovered:**

**Tool:** Calls `scraper.scrape_career_page(url)`

**What it does:**
- Uses Firecrawl to scrape career/jobs page
- Extracts job listings (title, description, URL, location)
- Returns list of jobs

**Known patterns:**
- Career page URLs: `/careers`, `/jobs`, `/join-us`, `/team`
- ATS systems: Greenhouse, Lever, Workday (standard formats)
- Some companies use iframes (Firecrawl handles this)

**If fails:**
- Rate limit: Wait 60s, retry once, then skip and continue
- Page not found: Try alternative URLs (`/jobs`, `/team`)
- If still fails: Log company name, skip, continue with others
- Track failed companies in `.tmp/failed_scrapes.txt`

**Rate limit management:**
- Free tier: 500 pages/month
- Track usage in database (last_scraped timestamp)
- Don't scrape same company more than once per day

### 3. Analyze Each Job
**For each job scraped:**

**Tool:** Calls `analyzer.analyze_job(job, company)`

**What it does:**
- AI reads job description (if API key configured)
- OR rule-based matching (if no API key)
- Scores 0-100 based on criteria:
  - Role type (PM/VC): 40 points
  - Industry match: 25 points
  - Technical requirements: 20 points
  - Location: 10 points
  - Company stage: 5 points

**Thresholds:**
- Score >= 80: "apply" recommendation
- Score 60-79: "consider" recommendation
- Score < 60: Skip (don't save)
- **Minimum to save: 70**

**Output:**
- Relevance score
- Role type (pm, vc, other)
- Reasoning
- Pros and cons
- Recommendation

### 4. Store Results
**Tool:** `db.add_job()`

**What it does:**
- Saves jobs with score >= 70
- Deduplicates by URL
- Links to company record
- Marks as status="new"

**Data stored:**
- Job details (title, description, URL, location)
- Analysis (score, role_type, AI reasoning)
- Metadata (discovered_date, status)

### 5. Notify User
**Tool:** `notifier.send_job_digest(new_jobs)`

**What it does:**
- Prints console summary of new matches
- Shows score, title, company, reasoning
- Optionally sends email (if configured)

**Format:**
```
NEW JOB MATCHES - 2026-02-15
=====================================

1. [85/100] Senior Product Manager - Hardware
   Company: Wayve
   Location: London, UK
   Reason: Technical PM role in autonomous vehicles, values hardware background

2. [78/100] Investment Associate - Deep Tech
   Company: IQ Capital
   Location: London, UK
   Reason: VC role focused on robotics and AI hardware investments
```

## Expected Output
- X companies discovered (new and existing)
- Y jobs scraped
- Z new high-quality matches (score >= 70)
- Console digest showing new matches
- Updated database

## Error Handling

**Firecrawl rate limit:**
- Wait 60 seconds
- Retry once
- If still fails, skip company and continue
- Log in `.tmp/rate_limited.log`

**API key not configured:**
- Fall back to rule-based matching
- Warn user once (don't spam)
- Continue with reduced accuracy

**No companies found:**
- Check config.yaml has search_queries or custom_companies
- Check internet connection
- Warn user

**No jobs found:**
- Normal if companies aren't hiring
- Log companies with no jobs in `.tmp/no_jobs.log`
- Could indicate career page structure changed

## Success Metrics
- Find 5-15 new jobs per week
- Average score of saved jobs >= 75
- At least 2-3 "apply" recommendations per week
- Zero crashes due to errors

## Improvements to Track
- Which companies consistently have good matches (focus on similar ones)
- Which search queries yield best results (refine these)
- Patterns in job descriptions that correlate with high scores
- Industries or role types that appear frequently

## Next Steps
After daily scan:
1. Review new jobs: `python src/main.py list`
2. See details: `python src/main.py show <id>`
3. Mark applied: `python src/main.py update <id> --status applied`
4. Check stats: `python src/main.py stats`
