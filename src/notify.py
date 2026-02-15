"""
Notification Module
Sends notifications about new jobs via email, CLI, or Slack
"""

from typing import List, Dict
from datetime import datetime


class Notifier:
    """Handles notifications for new jobs"""

    def __init__(self, config: Dict):
        """Initialize notifier with configuration"""
        self.config = config
        self.notification_config = config.get('notifications', {})
        self.enabled = self.notification_config.get('enabled', False)

    def send_job_digest(self, jobs: List[Dict]):
        """Send a digest of new jobs"""
        if not jobs:
            print("No new jobs to notify about")
            return

        # Always print to console
        self._print_console_digest(jobs)

        if not self.enabled:
            return

        # Send email if configured
        email = self.notification_config.get('email')
        if email:
            self._send_email_digest(jobs, email)

        # Send Slack if configured
        slack_webhook = self.notification_config.get('slack_webhook')
        if slack_webhook:
            self._send_slack_digest(jobs, slack_webhook)

    def _print_console_digest(self, jobs: List[Dict]):
        """Print job digest to console"""
        print("\n" + "="*80)
        print(f"  NEW JOB MATCHES - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*80 + "\n")

        for i, job in enumerate(jobs, 1):
            score = job.get('relevance_score', 0)
            company = job.get('company_name', 'Unknown Company')

            print(f"{i}. [{score}/100] {job['title']}")
            print(f"   Company: {company}")
            print(f"   Location: {job.get('location', 'Not specified')}")
            print(f"   URL: {job.get('url', 'N/A')}")

            # Parse AI analysis if available
            analysis = job.get('ai_analysis')
            if analysis and isinstance(analysis, str):
                try:
                    import json
                    analysis = json.loads(analysis)
                    print(f"   Reason: {analysis.get('reasoning', 'N/A')}")
                except:
                    pass

            print()

        print("="*80)
        print(f"Total: {len(jobs)} new job(s)")
        print("="*80 + "\n")

    def _send_email_digest(self, jobs: List[Dict], email: str):
        """
        Send email digest of jobs

        TODO: Implement email sending using:
        - SMTP (Gmail, SendGrid)
        - Email service API (Mailgun, Postmark)
        """
        print(f"TODO: Would send email digest to {email}")
        print(f"Jobs: {len(jobs)}")

    def _send_slack_digest(self, jobs: List[Dict], webhook_url: str):
        """
        Send Slack notification

        TODO: Implement Slack webhook posting
        """
        print(f"TODO: Would send Slack notification")
        print(f"Jobs: {len(jobs)}")

    def notify_new_job(self, job: Dict):
        """Send notification for a single new job"""
        self._print_single_job(job)

        # TODO: Implement instant notifications for high-score jobs

    def _print_single_job(self, job: Dict):
        """Print single job notification"""
        score = job.get('relevance_score', 0)
        print(f"\n🎯 NEW HIGH-MATCH JOB [{score}/100]")
        print(f"   {job['title']} at {job.get('company_name', 'Unknown')}")
        print(f"   {job.get('url', 'N/A')}\n")
