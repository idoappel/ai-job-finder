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

    console.print("\n[bold blue]🔍 AI Job Finder - Discovery Mode[/bold blue]\n")

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
    console.print(f"[green]✓ Found {len(companies)} companies[/green]\n")

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

    console.print(f"\n[green]✓ Scraped {total_scraped} jobs from {len(companies)} companies[/green]")
    console.print(f"[green]✓ Found {len(new_jobs)} new high-quality matches (score >= {min_score})[/green]\n")

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
    console.print(f"[green]✓ Updated job #{job_id} status to: {status}[/green]")

    if notes:
        console.print(f"[dim]Notes: {notes}[/dim]")

    db.close()


@cli.command()
def stats():
    """Show database statistics"""
    config = load_config()
    db = JobDatabase()

    stats_data = db.get_stats()

    console.print("\n[bold blue]📊 Database Statistics[/bold blue]\n")
    console.print(f"Total Companies: [cyan]{stats_data['total_companies']}[/cyan]")
    console.print(f"Total Jobs: [cyan]{stats_data['total_jobs']}[/cyan]")
    console.print(f"New Jobs: [green]{stats_data['new_jobs']}[/green]")
    console.print(f"Applied: [yellow]{stats_data['applied_jobs']}[/yellow]")
    console.print(f"Average Score: [green]{stats_data['avg_relevance_score']}/100[/green]\n")

    db.close()


if __name__ == '__main__':
    cli()
