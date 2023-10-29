from typing import Optional, TYPE_CHECKING
import requests
import re
import os
from datetime import date
from pathlib import Path
from logging import getLogger
import urllib
import bs4

from logseq import Logseq

if TYPE_CHECKING:
    from imap_tools.message import MailMessage

from email_ingester.email import GmailIngester

logger = getLogger(__name__)

class Kindle:
    """consume Kindle scribe notebooks and pdfs in logseq"""

    def extract_email_links(self, filetype:str|None=None) -> list[str]:
        emails = self.get_kindle_emails_for_the_day()
        links = [self.get_download_link_from_kindle_email(email) for email in emails]
        if filetype is None:
            return [link[0] for link in links]
        return [link[0] for link in links if link[1] == filetype]

    def get_kindle_emails_for_the_day(self) -> list:
        """get all emails from kindle email address for the day"""
        gmail = GmailIngester()
        return gmail.get_today_emails_from("do-not-reply@amazon.com")

    def get_download_link_from_kindle_email(self, email:"MailMessage") -> tuple | None:
        corpus = bs4.BeautifulSoup(email.html, 'html.parser')
        link_types = (
            ("Download PDF",".pdf",),
            ("Download text file",".txt"),
        )
        for link_text, link_type in link_types:
            download_link = corpus.find("a", text=link_text)
            if download_link:
                return download_link.get("href"), link_type

    def _get_filename_from_kindle_download_link(self, link:str) -> str:
        encoded_link = urllib.parse.parse_qs(link).get("U")
        if encoded_link:
            file_path = urllib.parse.urlparse(encoded_link[0]).path.split("/")[-1]
            ragged = urllib.parse.unquote(file_path)
            clean = re.sub(r"_+", "_",
                re.sub(r"[^\w-]", "_", ragged)
            ).lower()
            # fix the file type
            correct = f"{clean[:-5]}.{clean[-3:]}"
            return correct

    def route_kindle_file_within_logseq(self, link:str) -> None:
        """takes a given link and ingests it properly.
        text files are parsed and written to logseq as pages.
        pdfs are written to logseq as attachments to today's journal.
        """
        filename = self._get_filename_from_kindle_download_link(link)
        #title = self._get_filename_from_kindle_download_link(link)
        #if link_type == ".txt":
            #body = self.read_text_from_link(link)
            #self.write_notebook_to_logseq(title, link)
            #return
        if filename.endswith(".pdf"):
            self.write_pdf_to_logseq_journal(filename, link)
            return

    def write_pdf_to_logseq_journal(self, filename:str, link:str) -> None:
        """write pdf to logseq journal"""
        logseq = Logseq()
        asset_file = logseq.assets / filename
        if asset_file.exists():
            logger.info(f"{filename} already exists in logseq assets, skipping")
            return
        asset_file.write_bytes(self.read_binary_from_link(link))
        NON_ROOT_UID = 1000
        NON_ROOT_GID = 1000
        os.chown(asset_file, NON_ROOT_UID, NON_ROOT_GID)
        logseq.write_journal_block(f"- ![{filename}](../assets/{filename})")

    def read_binary_from_link(self, link:str) -> bytes:
        """read binary data from link"""
        return requests.get(link, allow_redirects=True).content

    def write_all_notebooks_to_logseq(self) -> int:
        """for each notebook in kindle notebook dir, write to logseq
        Returns:
            int: number of notebooks written
        """
        kindle_path = Path("/kindle")
        notebooks = list(kindle_path.glob("*.txt"))
        notebooks.sort(key=lambda x: x.stem)
        if not notebooks:
            return 0
        for index, notebook in enumerate(notebooks):
            self.write_notebook_to_logseq(notebook)
        return index + 1

    def write_notebook_to_logseq(self,
                       notebook:str|Path,
                       logseq_path:Optional[str|Path]=Path("/logseq/pages"),
                       purge_txt:bool|None=True) -> None:
        """prep kindle notebook file and write to logseq"""
        notebook = Path(notebook)
        logseq_path = Path(logseq_path)
        assert (notebook.exists() and logseq_path.exists())
        raw_text = notebook.read_text()
        clean_text = self._clean_text(raw_text)

        dateless_name = notebook.stem[:
            (notebook.stem.index(str(date.today().year)) -1)]
        logger.info(f"Writing {dateless_name}.md to Logseq"    )
        logseq_file = logseq_path / f"Kindle%2F{dateless_name}.md"
        logseq_file.write_text(clean_text)
        NON_ROOT_UID = 1000
        NON_ROOT_GID = 1000
        os.chown(logseq_file, NON_ROOT_UID, NON_ROOT_GID)
        if not purge_txt:
            return
        notebook.unlink()


    @classmethod
    def _clean_text(cls, text:str) -> str:
        """clean up kindle notebook text"""
        steps = [
            cls._strip_page_numbers,
            cls._fix_breaks,
            cls._convert_indents,
        ]
        for step in steps:
            text = step(text)
        return text

    @classmethod
    def _strip_page_numbers(cls, text:str) -> str:
        """remove page crap from text"""
        page_pattern = r'Page \d+\n'
        return re.sub(page_pattern, '', text)

    @classmethod
    def _fix_breaks(cls, text:str) -> str:
        """fix human-writing line breaks"""
        broken_string = r'(\w)\n(\w)'
        return re.sub(broken_string, r'\1 \2', text)

    @classmethod
    def _convert_indents(cls, text:str) -> str:
        steps = [
            (r'\n(\s*)-(\s*)(\w)', r'\n- \3'),
            (r'\n(\s*)+(\s*)(\w)', r'\n\t- \3'),
            (r'\n(\s*)*(\s*)(\w)', r'\n\t\t- \3'),
        ]
        for pattern, replacement in steps:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        return text