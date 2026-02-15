# AI Job Finder

An autonomous AI-powered job discovery system that finds and matches Product Manager and Venture Capital roles in deep tech.

## Features

- **Autonomous Company Discovery**: Automatically finds relevant deep tech companies and VC firms
- **Smart Web Scraping**: Uses Firecrawl.ai to scrape job postings from company career pages
- **AI-Powered Matching**: Uses Claude API to analyze and score job relevance
- **Intelligent Filtering**: Only surfaces highly relevant opportunities
- **Portable & Extensible**: Run on any computer, customize search criteria

## Target Roles

- **Product Manager** (Technical/Hardware PM in robotics, AI hardware, semiconductors)
- **Venture Capital** (Analyst, Associate roles in deep tech funds)

## Prerequisites

- Python 3.8+
- Firecrawl API key (sign up at [firecrawl.dev](https://firecrawl.dev))
- Anthropic API key (optional, for AI matching - sign up at [console.anthropic.com](https://console.anthropic.com))

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ai-job-finder.git
cd ai-job-finder
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API keys

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` and add your API keys:

```yaml
firecrawl_api_key: "your-firecrawl-key-here"
anthropic_api_key: "your-anthropic-key-here"  # Optional
```

### 4. Customize search criteria

Edit `config.yaml` to match your preferences:

```yaml
criteria:
  roles:
    - "Product Manager"
    - "Venture Capital"
  industries:
    - "Robotics"
    - "AI Hardware"
    - "Semiconductors"
    - "Deep Tech"
  locations:
    - "London"
    - "Remote"
  company_stage:
    - "Series A+"
    - "Established VC funds"
```

## Usage

### Run job discovery

```bash
python src/main.py discover
```

This will:
1. Search for relevant companies based on your criteria
2. Find their career pages
3. Scrape job postings
4. Analyze and score each job with AI
5. Store matches in the database

### View matched jobs

```bash
python src/main.py list
```

### View job details

```bash
python src/main.py show <job_id>
```

### Mark jobs as applied/interested/rejected

```bash
python src/main.py update <job_id> --status applied
```

### Run automated daily scan

```bash
python src/main.py scan --schedule daily
```

## Project Structure

```
ai-job-finder/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── config.example.yaml    # Configuration template
├── config.yaml           # Your config (gitignored)
├── .gitignore            # Git ignore rules
├── src/
│   ├── main.py           # CLI interface
│   ├── discover.py       # Company discovery logic
│   ├── scrape.py         # Firecrawl integration
│   ├── analyze.py        # AI job matching
│   ├── database.py       # SQLite database management
│   └── notify.py         # Notifications (email/CLI)
└── data/
    └── jobs.db           # SQLite database (created on first run)
```

## How It Works

1. **Discovery**: Searches the web for companies matching your criteria (deep tech VCs, robotics companies, etc.)
2. **Scraping**: Uses Firecrawl to scrape career pages and extract job postings
3. **Analysis**: Uses Claude AI to read job descriptions and score relevance (0-100)
4. **Filtering**: Only jobs scoring 70+ are stored
5. **Tracking**: Manage application status, notes, and follow-ups

## Customization

### Add Custom Company Lists

Edit `config.yaml`:

```yaml
custom_companies:
  - name: "Wayve"
    url: "https://wayve.ai/careers"
  - name: "Graphcore"
    url: "https://www.graphcore.ai/jobs"
```

### Adjust AI Matching Criteria

Edit `src/analyze.py` to customize how jobs are scored.

### Add Notifications

Configure email or Slack notifications in `config.yaml`:

```yaml
notifications:
  email: your-email@example.com
  slack_webhook: "https://hooks.slack.com/..."
```

## Development

### Run tests

```bash
python -m pytest tests/
```

### Add new features

1. Create a new branch: `git checkout -b feature/new-feature`
2. Make changes
3. Test locally
4. Commit: `git commit -m "Add new feature"`
5. Push: `git push origin feature/new-feature`

## Roadmap

- [ ] Web interface for easier job browsing
- [ ] Docker support for one-command deployment
- [ ] Integration with LinkedIn for automatic applications
- [ ] Learning from user feedback (mark jobs as relevant/not)
- [ ] Company similarity search (find companies like ones you liked)
- [ ] Salary data integration

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - feel free to use and modify for your own job search.

## Author

**Ido Appel**
- Senior VLSI Engineer transitioning to PM/VC in deep tech
- Background: Robotics vision SoCs, AI hardware, RISC-V architecture
- Location: London, UK

## Acknowledgments

- Built with [Firecrawl.ai](https://firecrawl.dev) for intelligent web scraping
- Powered by [Claude](https://anthropic.com) for AI job matching
