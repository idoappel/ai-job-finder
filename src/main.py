"""
AI Job Finder - Main CLI
Autonomous job discovery and matching for PM and VC roles in deep tech
"""

import click
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import json

from database import JobDatabase
from discover import CompanyDiscovery
from scrape import JobScraper
from analyze import JobAnalyzer
from notify import Notifier
from export_sheets import export_to_csv, print_google_sheets_instructions
from linkedin_search import LinkedInJobSearcher
from export_companies import export_companies_directory


console = Console()


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    config_file = Path(config_path)

    if not config_file.exists():
        console.print(f"[red]Error: {config_path} not found![/red]")
        console.print("[yellow]Run: cp config.example.yaml config.yaml[/yellow]")
        console.print("[yellow]Then add your API keys to config.yaml[/yellow]")
        exit(1)

    with open(config_file) as f:
        return yaml.safe_load(f)


@click.group()
def cli():
    """AI Job Finder - Autonomous job discovery for PM/VC roles in deep tech"""
    pass


@cli.command()
def discover():
    """Discover companies and scrape job postings"""
    config = load_config()

    console.print("\n[bold blue]AI Job Finder - Discovery Mode[/bold blue]\n")

    # Initialize components
    db = JobDatabase()
    discovery = CompanyDiscovery(config)
    scraper = JobScraper(config.get('firecrawl_api_key'), config)
    analyzer = JobAnalyzer(config.get('anthropic_api_key'), config)
    notifier = Notifier(config)

    min_score = config.get('matching', {}).get('min_score', 70)

    # Step 1: Discover companies
    console.print("[yellow]Step 1: Discovering companies...[/yellow]")
    companies = discovery.discover_companies()
    console.print(f"[green]OK: Found {len(companies)} companies[/green]\n")

    # Step 2: Scrape and analyze jobs
    console.print("[yellow]Step 2: Scraping job postings and analyzing matches...[/yellow]")

    new_jobs = []
    total_scraped = 0

    for company in companies:
        console.print(f"  Checking {company['name']}...")

        # Add company to database
        company_id = db.add_company(
            name=company['name'],
            url=company.get('url'),
            career_page_url=company.get('career_page_url'),
            industry=company.get('industry'),
            location=company.get('location'),
            company_type=company.get('company_type'),
            funding_stage=company.get('funding_stage')
        )

        # Scrape jobs
        career_url = company.get('career_page_url') or company.get('url')
        if not career_url:
            continue

        jobs = scraper.scrape_career_page(career_url, company['name'])
        total_scraped += len(jobs)

        # Analyze each job
        for job in jobs:
            analysis = analyzer.analyze_job(job, company)

            # Only save jobs meeting minimum score
            if analysis['score'] >= min_score:
                job_id = db.add_job(
                    company_id=company_id,
                    title=job['title'],
                    url=job['url'],
                    description=job.get('description'),
                    location=job.get('location'),
                    role_type=analysis['role_type'],
                    relevance_score=analysis['score'],
                    ai_analysis=analysis
                )

                if job_id:  # New job (not duplicate)
                    new_jobs.append({
                        'id': job_id,
                        'title': job['title'],
                        'company_name': company['name'],
                        'location': job.get('location'),
                        'url': job['url'],
                        'relevance_score': analysis['score'],
                        'ai_analysis': json.dumps(analysis)
                    })

        db.update_company_last_scraped(company_id)

    console.print(f"\n[green]OK: Scraped {total_scraped} jobs from {len(companies)} companies[/green]")
    console.print(f"[green]OK: Found {len(new_jobs)} new high-quality matches (score >= {min_score})[/green]\n")

    # Step 3: Show results
    if new_jobs:
        notifier.send_job_digest(new_jobs)

    # Show stats
    stats = db.get_stats()
    console.print(f"[cyan]Database stats:[/cyan]")
    console.print(f"  Total companies: {stats['total_companies']}")
    console.print(f"  Total jobs: {stats['total_jobs']}")
    console.print(f"  New jobs: {stats['new_jobs']}")
    console.print(f"  Average score: {stats['avg_relevance_score']}/100\n")

    db.close()


@cli.command()
@click.option('--location', default='London, UK', help='Job location to search')
@click.option('--limit', default=50, help='Max results per query')
def linkedin(location, limit):
    """Search LinkedIn for PM/VC jobs in deep tech"""
    config = load_config()

    console.print("\n[bold blue]AI Job Finder - LinkedIn Search Mode[/bold blue]\n")

    # Initialize components
    db = JobDatabase()
    scraper = JobScraper(config.get('firecrawl_api_key'), config)
    analyzer = JobAnalyzer(config.get('anthropic_api_key'), config)
    linkedin = LinkedInJobSearcher(scraper)

    min_score = config.get('matching', {}).get('min_score', 70)

    # Build search queries from config roles and industries
    roles = config.get('criteria', {}).get('roles', [])
    industries_keywords = ['deep tech', 'robotics', 'AI hardware', 'semiconductors', 'autonomous vehicles']

    # Create search queries combining roles with industries
    search_queries = []
    for role in roles[:5]:  # Limit to first 5 roles to avoid too many searches
        # Add role + "deep tech" query
        search_queries.append(f"{role} deep tech")

    console.print(f"[yellow]Searching LinkedIn for {len(search_queries)} queries in {location}...[/yellow]\n")

    # Search LinkedIn
    all_jobs = linkedin.search_multiple_queries(search_queries, location)

    console.print(f"\n[green]Found {len(all_jobs)} total jobs from LinkedIn[/green]")
    console.print(f"[yellow]Analyzing and scoring jobs...[/yellow]\n")

    # Analyze and save jobs
    new_jobs = []
    for job in all_jobs:
        # Check if job already exists
        existing = db.get_jobs(url=job['url'])
        if existing:
            continue

        # Create or get company
        company_name = job.get('company', 'Unknown Company')
        company_id = db.add_company(
            name=company_name,
            url=None,  # LinkedIn jobs don't provide company website
            career_page_url=None,
            industry='Unknown'  # Could extract from job description later
        )

        # Analyze job
        analysis = analyzer.analyze_job(job, {'name': company_name})
        relevance_score = analysis['score']

        # Only save jobs above minimum score
        if relevance_score >= min_score:
            job_id = db.add_job(
                company_id=company_id,
                title=job['title'],
                url=job['url'],
                description=job.get('description', ''),
                location=job.get('location', ''),
                role_type=analysis['role_type'],
                relevance_score=relevance_score,
                ai_analysis=analysis  # Pass dict, not JSON string
            )
            new_jobs.append({**job, 'id': job_id, 'relevance_score': relevance_score, 'ai_analysis': analysis})

    console.print(f"\n[green]OK: Found {len(new_jobs)} new high-quality matches (score >= {min_score})[/green]\n")

    # Show new jobs
    if new_jobs:
        console.print("[bold]NEW JOB MATCHES - LinkedIn[/bold]\n")
        for i, job in enumerate(new_jobs[:10], 1):  # Show top 10
            score = job['relevance_score']
            console.print(f"{i}. [{score}/100] {job['title']}")
            console.print(f"   Company: {job.get('company', 'Unknown')}")
            console.print(f"   Location: {job.get('location', 'Not specified')}")
            console.print(f"   URL: {job['url']}\n")

    # Show stats
    stats = db.get_stats()
    console.print(f"[cyan]Database stats:[/cyan]")
    console.print(f"  Total jobs: {stats['total_jobs']}")
    console.print(f"  New jobs: {stats['new_jobs']}")
    console.print(f"  Average score: {stats['avg_relevance_score']}/100\n")

    db.close()


@cli.command()
@click.option('--status', default=None, help='Filter by status (new, applied, interview, etc.)')
@click.option('--min-score', default=70, help='Minimum relevance score (0-100)')
@click.option('--role-type', default=None, help='Filter by role type (pm, vc)')
@click.option('--limit', default=50, help='Maximum number of jobs to show')
def list(status, min_score, role_type, limit):
    """List matched jobs"""
    config = load_config()
    db = JobDatabase()

    jobs = db.get_jobs(status=status, min_score=min_score, role_type=role_type, limit=limit)

    if not jobs:
        console.print("[yellow]No jobs found matching your criteria[/yellow]")
        db.close()
        return

    # Create table
    table = Table(title=f"Matched Jobs ({len(jobs)} results)")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Score", style="green", width=8)
    table.add_column("Title", style="bold")
    table.add_column("Company", style="blue")
    table.add_column("Location", style="yellow")
    table.add_column("Status", style="magenta")

    for job in jobs:
        table.add_row(
            str(job['id']),
            f"{job['relevance_score']}/100",
            job['title'][:50],
            job['company_name'][:30],
            job['location'][:20] if job['location'] else 'N/A',
            job['status']
        )

    console.print(table)
    console.print(f"\n[dim]Use 'show <id>' to see details | 'update <id> --status applied' to track application[/dim]\n")

    db.close()


@cli.command()
@click.argument('job_id', type=int)
def show(job_id):
    """Show detailed information about a job"""
    config = load_config()
    db = JobDatabase()

    job = db.get_job_by_id(job_id)

    if not job:
        console.print(f"[red]Job {job_id} not found[/red]")
        db.close()
        return

    console.print(f"\n[bold blue]Job #{job['id']} - {job['title']}[/bold blue]\n")
    console.print(f"[green]Score: {job['relevance_score']}/100[/green]")
    console.print(f"Company: {job['company_name']} ({job['industry'] or 'N/A'})")
    console.print(f"Location: {job['location'] or 'Not specified'}")
    console.print(f"Status: {job['status']}")
    console.print(f"URL: {job['url']}\n")

    # Show AI analysis
    if job['ai_analysis']:
        try:
            analysis = json.loads(job['ai_analysis'])
            console.print("[yellow]AI Analysis:[/yellow]")
            console.print(f"  Role Type: {analysis.get('role_type', 'N/A').upper()}")
            console.print(f"  Recommendation: {analysis.get('recommendation', 'N/A').upper()}")
            console.print(f"  Reasoning: {analysis.get('reasoning', 'N/A')}\n")

            if analysis.get('pros'):
                console.print("  Pros:")
                for pro in analysis['pros']:
                    console.print(f"    + {pro}")

            if analysis.get('cons'):
                console.print("  Cons:")
                for con in analysis['cons']:
                    console.print(f"    - {con}")

        except:
            pass

    # Show description
    if job['description']:
        console.print(f"\n[yellow]Description:[/yellow]")
        console.print(job['description'][:500] + "..." if len(job['description']) > 500 else job['description'])

    console.print()
    db.close()


@cli.command()
@click.argument('job_id', type=int)
@click.option('--status', required=True, help='New status (interested, applied, interview, rejected, offer)')
@click.option('--notes', default=None, help='Add notes')
def update(job_id, status, notes):
    """Update job application status"""
    config = load_config()
    db = JobDatabase()

    job = db.get_job_by_id(job_id)

    if not job:
        console.print(f"[red]Job {job_id} not found[/red]")
        db.close()
        return

    db.update_job_status(job_id, status, notes)
    console.print(f"[green]OK: Updated job #{job_id} status to: {status}[/green]")

    if notes:
        console.print(f"[dim]Notes: {notes}[/dim]")

    db.close()


@cli.command()
def stats():
    """Show database statistics"""
    config = load_config()
    db = JobDatabase()

    stats_data = db.get_stats()

    console.print("\n[bold blue]Database Statistics[/bold blue]\n")
    console.print(f"Total Companies: [cyan]{stats_data['total_companies']}[/cyan]")
    console.print(f"Total Jobs: [cyan]{stats_data['total_jobs']}[/cyan]")
    console.print(f"New Jobs: [green]{stats_data['new_jobs']}[/green]")
    console.print(f"Applied: [yellow]{stats_data['applied_jobs']}[/yellow]")
    console.print(f"Average Score: [green]{stats_data['avg_relevance_score']}/100[/green]\n")

    db.close()


@cli.command()
@click.option('--output', default='output/jobs_export.csv', help='Output CSV filename')
@click.option('--min-score', default=0, help='Minimum relevance score')
@click.option('--status', default=None, help='Filter by status')
def export(output, min_score, status):
    """Export jobs to CSV for Google Sheets import"""
    config = load_config()
    db = JobDatabase()

    jobs = db.get_jobs(status=status, min_score=min_score, limit=1000)

    if not jobs:
        console.print("[yellow]No jobs found to export[/yellow]")
        db.close()
        return

    # Export to CSV
    output_path = export_to_csv(jobs, output)

    if output_path:
        console.print(f"\n[green]Successfully exported {len(jobs)} jobs![/green]")
        console.print(f"[cyan]File location: {output_path.absolute()}[/cyan]\n")

        # Show import instructions
        console.print("[bold]To import to Google Sheets:[/bold]")
        console.print("1. Go to: [link]https://sheets.google.com[/link]")
        console.print("2. Create new spreadsheet")
        console.print("3. File > Import > Upload")
        console.print(f"4. Select: {output_path.name}")
        console.print("5. Import location: 'Replace spreadsheet'\n")

    db.close()


@cli.command()
@click.option('--type', default=None, help='Filter by type (vc_firm, company)')
@click.option('--industry', default=None, help='Filter by industry')
@click.option('--output', default='output/companies_directory.csv', help='Output CSV filename')
def companies(type, industry, output):
    """Export discovered companies to directory format"""
    config = load_config()
    db = JobDatabase()

    # Get all companies from database
    all_companies = db.get_companies(company_type=type)

    # Filter by industry if specified
    if industry:
        all_companies = [c for c in all_companies if industry.lower() in c.get('industry', '').lower()]

    if not all_companies:
        console.print("[yellow]No companies found[/yellow]")
        db.close()
        return

    console.print(f"\n[cyan]Found {len(all_companies)} companies[/cyan]\n")

    # Export to company directory CSV
    output_path = export_companies_directory(all_companies, output)

    if output_path:
        console.print(f"\n[green]Successfully exported {len(all_companies)} companies![/green]")
        console.print(f"[cyan]File location: {output_path.absolute()}[/cyan]\n")

    db.close()


if __name__ == '__main__':
    cli()
