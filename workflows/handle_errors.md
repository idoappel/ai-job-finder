# Workflow: Error Handling

## Objective
Define how to gracefully handle failures and continue making progress.

## Principle
**Never crash the entire scan due to a single failure.** Skip the failed item, log it, and continue.

---

## Error Scenarios

### 1. Firecrawl Rate Limit

**Symptoms:**
- 429 status code
- "Rate limit exceeded" message
- Requests failing after X pages

**Response:**
1. Pause for 60 seconds
2. Retry the same request once
3. If still fails:
   - Log company name to `.tmp/rate_limited.log`
   - Skip this company
   - Continue with next company
4. At end of scan, notify user of skipped companies

**Prevention:**
- Track Firecrawl usage in database (pages_scraped counter)
- Stop at 450 pages/month on free tier (leave buffer)
- Upgrade to paid tier if consistently hitting limit

---

### 2. Invalid Career Page URL

**Symptoms:**
- 404 Not Found
- Page doesn't exist
- URL malformed

**Response:**
1. Try alternative URLs:
   - `/careers` → `/jobs`
   - `/jobs` → `/team`
   - `/team` → `/join-us`
2. If all fail:
   - Log to `.tmp/invalid_urls.log`
   - Mark company as "career_page_not_found"
   - Skip scraping
3. Continue with next company

**Future improvement:**
- Use Firecrawl search to find career page
- Check LinkedIn jobs for this company

---

### 3. API Key Not Configured

**Symptoms:**
- Firecrawl key = "YOUR_FIRECRAWL_API_KEY_HERE"
- Anthropic key not set

**Response:**

**Firecrawl not configured:**
- Print warning once: "Firecrawl API key not configured. Using mock data for testing."
- Return mock jobs (realistic examples)
- Continue with analysis using mock data

**Anthropic not configured:**
- Print warning once: "Claude API not configured. Using rule-based matching."
- Fall back to rule-based scoring
- Accuracy lower but system still works

**Don't crash or stop scan.**

---

### 4. Job Scraping Returns Empty

**Symptoms:**
- No jobs found on career page
- Empty list returned

**Response:**
1. This is often normal (company not hiring)
2. Log to `.tmp/no_jobs.log` with company name
3. Don't treat as error
4. Continue with next company

**Note:** If EVERY company returns empty, check:
- Scraping logic broken?
- Career page structure changed?
- Firecrawl issue?

---

### 5. Database Lock

**Symptoms:**
- "Database is locked" error
- Can't write to jobs.db

**Response:**
1. Wait 1 second
2. Retry 3 times with exponential backoff (1s, 2s, 4s)
3. If still fails:
   - Log the job data to `.tmp/failed_inserts.json`
   - Continue scan
   - Manually recover later

**Prevention:**
- Use WAL mode in SQLite (write-ahead logging)
- Ensure only one process writes to DB at a time

---

### 6. AI Analysis Fails

**Symptoms:**
- Claude API error
- Rate limit on Anthropic
- Invalid response format

**Response:**
1. Catch exception
2. Fall back to rule-based analysis for this job
3. Log to `.tmp/ai_failures.log`
4. Continue with next job

**Don't:**
- Retry immediately (wastes API quota)
- Stop entire scan

---

### 7. Network Timeout

**Symptoms:**
- Request takes >30 seconds
- Connection timeout

**Response:**
1. Retry once after 5 second wait
2. If still fails:
   - Log to `.tmp/network_errors.log`
   - Skip this item
   - Continue

---

### 8. Malformed Job Data

**Symptoms:**
- Job missing title
- Job missing URL
- Description is gibberish

**Response:**
1. Validate required fields: title, URL
2. If missing either:
   - Log to `.tmp/malformed_jobs.log`
   - Skip this job
   - Continue with next

**Don't save malformed jobs to database.**

---

## Logging Strategy

**Temporary logs** (in `.tmp/`):
- `rate_limited.log` - Companies skipped due to rate limits
- `invalid_urls.log` - Companies with broken career pages
- `no_jobs.log` - Companies with no jobs posted
- `ai_failures.log` - Jobs where AI analysis failed
- `network_errors.log` - Network/timeout issues
- `failed_inserts.json` - Jobs that failed to save to DB

**Review weekly:**
- Read logs to find patterns
- Update workflows with learnings
- Fix structural issues

**Clear monthly:**
- Archive or delete old logs
- Start fresh

---

## Recovery Procedures

### Recover Failed Inserts
If jobs failed to save to database:

```bash
# Read .tmp/failed_inserts.json
# Manually add to database or re-run analysis
python src/main.py recover-failed
```

### Retry Rate-Limited Companies
If companies were skipped due to rate limits:

```bash
# Wait 24 hours for quota reset
# Read .tmp/rate_limited.log
# Re-scrape those specific companies
python src/main.py retry-failed
```

---

## Success Metrics

**Good error handling means:**
- Scan completes even if 20% of companies fail
- Clear logs show exactly what failed and why
- User can review and manually recover if needed
- System improves over time (fewer errors as workflows update)

**Red flags:**
- Same errors repeating daily (fix the root cause)
- High failure rate (>50% of items failing)
- Crashes instead of graceful failures

---

## Improvements to Track

When errors happen:
1. **Document the pattern** - Update this workflow
2. **Fix the tool** - Improve error handling in Python code
3. **Prevent recurrence** - Add validation or checks
4. **Learn** - Update other workflows with insights

Example:
- Discover Greenhouse uses different HTML structure → Update scrape.py to handle Greenhouse pattern → Document in `scrape_jobs.md`
