"""
Google Sheets Export Module
Exports job data to Google Sheets for easy viewing and tracking
"""

import csv
from typing import List, Dict
from pathlib import Path


def export_to_csv(jobs: List[Dict], output_file: str = "output/jobs_export.csv"):
    """
    Export jobs to CSV file (can be imported to Google Sheets)

    Args:
        jobs: List of job dictionaries from database
        output_file: Path to output CSV file
    """
    if not jobs:
        print("No jobs to export")
        return None

    # Define CSV columns
    fieldnames = [
        'ID',
        'Score',
        'Title',
        'Company',
        'Industry',
        'Location',
        'Role Type',
        'Status',
        'URL',
        'Recommendation',
        'Reasoning',
        'Discovered Date',
        'Applied Date',
        'Notes'
    ]

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure output dir exists

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for job in jobs:
            # Parse AI analysis if available
            import json
            analysis = {}
            if job.get('ai_analysis'):
                try:
                    analysis = json.loads(job['ai_analysis'])
                except:
                    pass

            writer.writerow({
                'ID': job['id'],
                'Score': job['relevance_score'],
                'Title': job['title'],
                'Company': job.get('company_name', ''),
                'Industry': job.get('industry', ''),
                'Location': job.get('location', ''),
                'Role Type': job.get('role_type', '').upper(),
                'Status': job['status'],
                'URL': job['url'],
                'Recommendation': analysis.get('recommendation', '').upper(),
                'Reasoning': analysis.get('reasoning', ''),
                'Discovered Date': job.get('discovered_date', ''),
                'Applied Date': job.get('applied_date', ''),
                'Notes': job.get('notes', '')
            })

    print(f"\nOK: Exported {len(jobs)} jobs to: {output_path.absolute()}")
    print(f"\nTo import to Google Sheets:")
    print(f"1. Go to: https://sheets.google.com")
    print(f"2. Create new spreadsheet or open existing")
    print(f"3. File > Import > Upload")
    print(f"4. Select: {output_path.absolute()}")
    print(f"5. Import location: Replace spreadsheet")

    return output_path


def print_google_sheets_instructions():
    """Print instructions for manual Google Sheets setup"""
    print("\n" + "="*80)
    print("GOOGLE SHEETS EXPORT INSTRUCTIONS")
    print("="*80)
    print("\nOption 1: Import CSV")
    print("-" * 40)
    print("1. Run: python src/main.py export")
    print("2. Open: https://sheets.google.com")
    print("3. File > Import > Upload the CSV file")
    print("4. Done! Your jobs are in Google Sheets")

    print("\nOption 2: Manual Copy-Paste")
    print("-" * 40)
    print("1. Run: python src/main.py list")
    print("2. Copy the output")
    print("3. Paste into Google Sheets")

    print("\nOption 3: Google Sheets API (Advanced)")
    print("-" * 40)
    print("Requires Google Cloud setup and credentials")
    print("See: https://developers.google.com/sheets/api/quickstart/python")
    print("="*80 + "\n")
