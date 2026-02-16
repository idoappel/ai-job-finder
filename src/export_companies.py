"""
Company Directory Export Module
Exports discovered companies to clean CSV format for manual exploration
"""

import csv
from typing import List, Dict
from pathlib import Path
from datetime import datetime


def export_companies_directory(companies: List[Dict], output_file: str = "output/companies_directory.csv") -> Path:
    """
    Export companies to directory CSV format (one row per company)

    Args:
        companies: List of company dictionaries from database
        output_file: Path to output CSV file

    Returns:
        Path to the exported CSV file
    """
    if not companies:
        print("No companies to export")
        return None

    # Define CSV columns for company directory
    fieldnames = [
        'Company Name',
        'Description',
        'Industry',
        'Location',
        'Website',
        'Careers Page',
        'Funding Stage',
        'Type',
        'Last Checked'
    ]

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure output dir exists

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for company in companies:
            writer.writerow({
                'Company Name': company.get('name', ''),
                'Description': company.get('description', '')[:200] if company.get('description') else '',  # Limit to 200 chars
                'Industry': company.get('industry', ''),
                'Location': company.get('location', ''),
                'Website': company.get('url', ''),
                'Careers Page': company.get('career_page_url', ''),
                'Funding Stage': company.get('funding_stage', ''),
                'Type': company.get('company_type', ''),
                'Last Checked': company.get('last_scraped', company.get('discovered_date', ''))
            })

    print(f"\nOK: Exported {len(companies)} companies to: {output_path.absolute()}")
    print(f"\nTo import to Google Sheets:")
    print(f"1. Go to: https://sheets.google.com")
    print(f"2. Create new spreadsheet or open existing")
    print(f"3. File > Import > Upload")
    print(f"4. Select: {output_path.absolute()}")
    print(f"5. Import location: Replace spreadsheet")

    return output_path
