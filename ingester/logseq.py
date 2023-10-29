from pathlib import Path
from datetime import date
from logging import getLogger

from settings import Settings

logger = getLogger(__name__)

class Logseq:

    def __init__(self):
        settings = Settings()
        self._root_path = Path(settings.sync_dir) / "logseq"
        assert self._root_path.exists()
        self.journals = self._root_path / "journals"
        self.assets = self._root_path / "assets"
        self.pages = self._root_path / "pages"

    def write_journal_block(self, block:str) -> None:
        """write block to today's journal"""
        todays_journal = self.journals / f"{date.today()}.md"
        logger.debug(f"Writing block to {todays_journal}")
        if not todays_journal.exists():
            logger.debug(f"Journal {todays_journal} does not exist, creating")
            todays_journal.write_text(block)
            return
        logger.debug(f"Journal {todays_journal} exists, appending")
        current_journal = todays_journal.read_text()
        todays_journal.write_text(  current_journal
                                  + "\n"
                                  + block)