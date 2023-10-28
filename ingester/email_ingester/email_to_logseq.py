import datetime
from pathlib    import Path
from .email import GmailIngester


class EmailToLogseq:
    """emails with a +logseq tag are ingested into logseq as blocks for the day's journal"""


    def ingest_logseq_emails(self) -> None:
        client = GmailIngester()
        emails = client.get_today_emails_from("ethan.m.knox+logseq@gmail.com")

        journal = self.get_current_logseq_journal()

        for email in emails:
            body = self.get_raw_body_from_email(email)
            self.convert_content_to_logseq_block(body)
            self.write_block_to_logseq_journal(body, journal)


    def get_current_logseq_journal(self) -> Path:
        """returns the path to today's journal"""
        today_file = datetime.date.today().strftime("%Y-%m-%d") + ".md"
        return Path(f"/logseq/journals/{today_file}")