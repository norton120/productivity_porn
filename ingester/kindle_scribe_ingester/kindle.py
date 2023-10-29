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

logger = getLogger("app").getChild(__name__)

class FileExists(Exception):
    pass

class Kindle:
    """consume Kindle scribe notebooks and pdfs in logseq"""
    REQUEST_PARAMS = {"allow_redirects":True,
                      "headers": {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9"}
    }

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
        if filename.endswith(".txt"):
            self.write_text_to_logseq_page(filename, link)
            return
        if filename.endswith(".pdf"):
            self.write_pdf_to_logseq_journal(filename, link)
            return
        raise ValueError(f"Unknown filetype for {filename}")

    def write_pdf_to_logseq_journal(self, filename:str, link:str) -> None:
        """write pdf to logseq journal"""
        # if file exists, skip it
        logseq = Logseq()
        try:
            asset_file = self._get_file_if_not_exists(filename)
        except FileExists:
            return
        asset_file.write_bytes(self.read_binary_from_link(link))
        logger.debug("Wrote pdf to logseq assets")
        logseq.set_permissions_on_file(asset_file)
        logseq.write_journal_block(f"- ![{filename}](../assets/{filename})")

    def write_text_to_logseq_page(self, filename:str, link:str) -> None:
        try:
            logseq_file = self._get_file_if_not_exists(filename)
        except FileExists:
            return
        response = requests.get(link, **self.REQUEST_PARAMS)
        if not response.ok:
            logger.error("Failed to download file %s, Amazon responded with %s", filename, response.status_code)
            return
        raw_text = response.text
        clean_text = self._clean_text(raw_text)
        bytes_ = logseq_file.write_text(clean_text)
        logger.debug("wrote %s bytes to file %s", bytes_, logseq_file.absolute())

        Logseq.set_permissions_on_file(logseq_file)

    def _get_file_if_not_exists(self, filename:str)-> bool:
        """Gets a non-existant file or raises FileExists"""
        logseq = Logseq()
        if self._is_a_pdf(filename):
            logseq_file = logseq.assets / filename
        if self._is_a_txt_file(filename):
            filename_stem = Path(filename).stem
            dateless_name = filename_stem[:
                (filename_stem.index(str(date.today().year)) -1)]
            logseq_stem = f"Kindle%2F{dateless_name}.md"
            logseq_file = logseq.pages / logseq_stem
        if logseq_file.exists():
            message = f"email content `{logseq_file.stem.replace('Kindle%2F','')}` exists, skipping"
            logger.info(message)
            raise FileExists(message)
        return logseq_file

    @classmethod
    def _is_a_pdf(cls, filename:str) -> bool:
        return filename.endswith(".pdf")

    @classmethod
    def _is_a_txt_file(cls, filename:str) -> bool:
        return filename.endswith(".txt")

    def read_binary_from_link(self, link:str) -> bytes:
        """read binary data from link"""
        response = requests.get(link, **self.REQUEST_PARAMS)
        if not response.ok:
            logger.error("Failed to download file %s, Amazon responded with %s", filename, response.status_code)
            return
        return response.content

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