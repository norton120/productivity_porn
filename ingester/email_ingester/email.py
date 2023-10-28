import os
from datetime import date, timedelta
from abc import ABC
from typing import TYPE_CHECKING
from imap_tools import MailBox, A
from imaplib import IMAP4


if TYPE_CHECKING:
    from gcsa.free_busy import TimeRange


class Credentials:
    host: str
    port: int
    username: str
    password: str

    def __init__(self):
        for prop in ("host", "port", "username", "password"):
            envar = f"IMAP_{prop.upper()}"
            try:
                setattr(self, prop, os.environ[envar])
            except KeyError:
                raise Exception(f"Missing {envar} environment variable")

class EmailIngester(ABC):

    ALL_MAILBOX = "All Mail"

    def __init__(self):
        self.conn = self.Conn()

    class Conn:
        def __init__(self):
            self.credentials = Credentials()
            self._refresh_mailbox()

        def _refresh_mailbox(self):
            self.mailbox = MailBox(self.credentials.host)

        def _login(self):
            self.mailbox.login(self.credentials.username, self.credentials.password)
            return self.mailbox

        def __enter__(self):
            try:
                return self._login()
            except IMAP4.error:
                self._refresh_mailbox()
                return self._login()

        def __exit__(self, exc_type, exc_value, traceback):
            self.mailbox.logout()


    def get_mailboxes(self) -> list:
        """get all mailboxes"""
        with self.conn as mailbox:
            box_list = mailbox.folder.list()
            return [f.name for f in list(filter(lambda x: "\\Noselect" not in x.flags, box_list))]

    def get_emails_headers_since(self, since: int|None = 1) -> list:
        """get all emails since n days, do not mark them read (yet)"""
        with self.conn as mailbox:
            mailbox.folder.set(self.ALL_MAILBOX)
            return [m for m in mailbox.fetch(A(date_gte=date.today() - timedelta(days=since)),
                                             headers_only=True,
                                             bulk=True,
                                             mark_seen=False)]

    def get_today_emails_from(self, sender:str) -> list:
        """get all emails from today from a sender"""
        with self.conn as mailbox:
            mailbox.folder.set(self.ALL_MAILBOX)
            return [m for m in mailbox.fetch(A(date_gte=date.today(), from_=sender),
                                             headers_only=False,
                                             bulk=True,
                                             mark_seen=False)]

    def get_today_emails_to(self, recipient:str) -> list:
        """get all emails to today to a recipient"""
        with self.conn as mailbox:
            mailbox.folder.set(self.ALL_MAILBOX)
            return [m for m in mailbox.fetch(A(date_gte=date.today(), to=recipient),
                                             headers_only=False,
                                             bulk=True,
                                             mark_seen=False)]

class GmailIngester(EmailIngester):
    ALL_MAILBOX = "[Gmail]/All Mail"