"""
Database management for AI Job Finder
Handles SQLite database operations for storing jobs and companies
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class JobDatabase:
    """Manages job and company data in SQLite database"""

    def __init__(self, db_path: str = "data/jobs.db"):
        """Initialize database connection and create tables if needed"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self.create_tables()

    def create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()

        # Companies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                url TEXT,
                career_page_url TEXT,
                industry TEXT,
                location TEXT,
                company_type TEXT,  -- 'vc_firm', 'company', 'startup'
                funding_stage TEXT,
                discovered_date TEXT,
                last_scraped TEXT,
                notes TEXT
            )
        """)

        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                title TEXT NOT NULL,
                url TEXT UNIQUE,
                description TEXT,
                location TEXT,
                role_type TEXT,  -- 'pm', 'vc', 'other'
                relevance_score INTEGER,  -- 0-100
                ai_analysis TEXT,  -- JSON with AI reasoning
                status TEXT DEFAULT 'new',  -- 'new', 'interested', 'applied', 'interview', 'rejected', 'offer'
                discovered_date TEXT,
                applied_date TEXT,
                notes TEXT,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        """)

        # Search history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                results_count INTEGER,
                timestamp TEXT
            )
        """)

        self.conn.commit()

    def add_company(self, name: str, url: str = None, career_page_url: str = None,
                    industry: str = None, location: str = None, company_type: str = None,
                    funding_stage: str = None) -> int:
        """Add a company to the database, return company ID"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO companies (name, url, career_page_url, industry, location,
                                     company_type, funding_stage, discovered_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, url, career_page_url, industry, location, company_type,
                  funding_stage, datetime.now().isoformat()))

            self.conn.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            # Company already exists, return existing ID
            cursor.execute("SELECT id FROM companies WHERE name = ?", (name,))
            result = cursor.fetchone()
            return result[0] if result else None

    def add_job(self, company_id: int, title: str, url: str, description: str = None,
                location: str = None, role_type: str = None, relevance_score: int = 0,
                ai_analysis: Dict = None) -> Optional[int]:
        """Add a job to the database, return job ID"""
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO jobs (company_id, title, url, description, location, role_type,
                                relevance_score, ai_analysis, discovered_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (company_id, title, url, description, location, role_type,
                  relevance_score, json.dumps(ai_analysis) if ai_analysis else None,
                  datetime.now().isoformat()))

            self.conn.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            # Job URL already exists, skip
            return None

    def get_jobs(self, status: str = None, min_score: int = 0,
                 role_type: str = None, limit: int = 100) -> List[Dict]:
        """Get jobs from database with optional filters"""
        cursor = self.conn.cursor()

        query = """
            SELECT j.*, c.name as company_name, c.url as company_url, c.industry
            FROM jobs j
            JOIN companies c ON j.company_id = c.id
            WHERE j.relevance_score >= ?
        """
        params = [min_score]

        if status:
            query += " AND j.status = ?"
            params.append(status)

        if role_type:
            query += " AND j.role_type = ?"
            params.append(role_type)

        query += " ORDER BY j.relevance_score DESC, j.discovered_date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """Get a single job by ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT j.*, c.name as company_name, c.url as company_url, c.industry
            FROM jobs j
            JOIN companies c ON j.company_id = c.id
            WHERE j.id = ?
        """, (job_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def update_job_status(self, job_id: int, status: str, notes: str = None):
        """Update job application status"""
        cursor = self.conn.cursor()

        if status == 'applied':
            cursor.execute("""
                UPDATE jobs
                SET status = ?, applied_date = ?, notes = COALESCE(?, notes)
                WHERE id = ?
            """, (status, datetime.now().isoformat(), notes, job_id))
        else:
            cursor.execute("""
                UPDATE jobs
                SET status = ?, notes = COALESCE(?, notes)
                WHERE id = ?
            """, (status, notes, job_id))

        self.conn.commit()

    def get_companies(self, company_type: str = None) -> List[Dict]:
        """Get all companies from database"""
        cursor = self.conn.cursor()

        if company_type:
            cursor.execute("""
                SELECT * FROM companies
                WHERE company_type = ?
                ORDER BY discovered_date DESC
            """, (company_type,))
        else:
            cursor.execute("SELECT * FROM companies ORDER BY discovered_date DESC")

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def update_company_last_scraped(self, company_id: int):
        """Update the last scraped timestamp for a company"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE companies
            SET last_scraped = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), company_id))
        self.conn.commit()

    def get_stats(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'new'")
        new_jobs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'applied'")
        applied_jobs = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(relevance_score) FROM jobs")
        avg_score = cursor.fetchone()[0] or 0

        return {
            "total_companies": total_companies,
            "total_jobs": total_jobs,
            "new_jobs": new_jobs,
            "applied_jobs": applied_jobs,
            "avg_relevance_score": round(avg_score, 1)
        }

    def close(self):
        """Close database connection"""
        self.conn.close()
