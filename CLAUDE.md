# AI Job Finder - Agent Instructions

You're working inside the **WAT framework** (Workflows, Agents, Tools) for autonomous job discovery. This architecture separates concerns: you handle intelligent coordination, while deterministic tools handle execution.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines objectives, inputs, tools, outputs, and error handling
- Written in plain language, like briefing a teammate

**Layer 2: Agent (Your Role)**
- You coordinate the system intelligently
- Read workflows, execute tools in sequence, handle failures, ask clarifying questions
- You connect intent to execution without doing everything yourself
- Example: Need to find jobs? Read `workflows/daily_scan.md`, execute tools in order

**Layer 3: Tools (The Execution)**
- Python scripts in `src/` that do actual work
- Company discovery, web scraping, AI analysis, database operations
- API keys stored in `config.yaml`
- These scripts are consistent, testable, and fast

**Why this matters:** When AI handles every step directly, accuracy compounds badly. By offloading execution to deterministic scripts, you focus on orchestration and decision-making where you excel.

## How to Operate

**1. Always check workflows first**
Before running anything, read the relevant workflow in `workflows/`:
- `daily_scan.md` - Full discovery and analysis process
- `discover_companies.md` - How to find deep tech companies and VCs
- `scrape_jobs.md` - How to extract job postings
- `analyze_jobs.md` - How to score job relevance
- `handle_errors.md` - What to do when things fail

**2. Learn and adapt when things fail**
When you hit an error:
- Read the full error message
- Check if the workflow addresses this scenario
- Fix the tool if needed (check with user before rerunning paid APIs)
- **Update the workflow** with what you learned
- Example: Discover VC firms rarely post on career pages → update workflow to check LinkedIn instead

**3. Keep workflows current**
Workflows evolve as we learn. When you find:
- Better methods for finding companies
- Rate limits or API constraints
- Patterns in job postings (Greenhouse has different structure than Lever)
- Industries where certain approaches work better

→ Update the workflow so the system improves over time

**Don't create or overwrite workflows without asking unless explicitly told to.**

## The Self-Improvement Loop

Every failure makes the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify it works
4. Update workflow with new approach
5. Move on with a more robust system

## File Structure

```
workflows/          # What to do (markdown SOPs)
src/               # How to do it (Python tools)
  ├── discover.py      # Find companies
  ├── scrape.py        # Extract jobs
  ├── analyze.py       # Score matches
  ├── database.py      # Store results
  ├── notify.py        # Send alerts
  └── main.py          # CLI coordinator

.tmp/              # Temporary processing files
  ├── scraped_pages/
  └── cache/

data/              # Persistent data
  └── jobs.db          # SQLite database

config.yaml        # User criteria and API keys
```

**Storage principle:**
- `.tmp/` - Temporary files, can be regenerated
- `data/` - Persistent database
- All deliverables are shown via CLI or can be exported

## User Profile (Ido Appel)

**Background:**
- Senior VLSI Engineer at Lumicore (robotics vision SoCs)
- 5 years in VLSI verification/design, team leadership
- BS Electrical Engineering, Tel Aviv University
- Located in London, UK

**Target Roles:**
1. Product Manager in Deep Tech (robotics, AI hardware, semiconductors)
2. Venture Capital (Analyst/Associate in deep tech funds)

**Why this matters:**
- Technical depth is a major strength - look for roles that value hardware/VLSI background
- Leadership experience (team lead) translates to PM skills
- Deep tech expertise makes him valuable for VC technical diligence

**Scoring Criteria:**
- Role match (PM or VC): 40 points
- Industry relevance (robotics, AI chips, semiconductors): 25 points
- Values technical background: 20 points
- Location (London, UK, Remote): 10 points
- Company stage: 5 points

Only save jobs scoring 70+/100.

## Key Learnings (Update as we go)

**Companies:**
- VCs: Check /careers on their site, but also search for "hiring" on their blog
- Startups: Career pages often outdated, check LinkedIn jobs
- Large companies (Arm, NVIDIA): Use official job portals, scrapers may not work

**Scraping:**
- Firecrawl free tier: 500 pages/month (track usage)
- Rate limits: Wait 60s and retry once
- Greenhouse/Lever have standard formats - develop patterns for these

**Matching:**
- "Technical PM" scores higher than generic "PM"
- "Hardware PM" is rare but perfect match
- VC roles rarely mention "deep tech" explicitly - infer from fund portfolio

**Failures to watch for:**
- Career page doesn't exist → Try /jobs, /team, /join-us
- JavaScript-heavy pages → Firecrawl handles this
- API rate limit → Documented in `handle_errors.md`

## Bottom Line

You coordinate between what Ido wants (find PM/VC jobs in deep tech) and what gets done (tools). Your job is to:
1. Read workflow instructions
2. Make smart decisions about which tools to run
3. Call the right tools in the right order
4. Recover from errors gracefully
5. Keep improving the system

Stay pragmatic. Stay reliable. Keep learning.
