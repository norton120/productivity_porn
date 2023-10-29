import logging
import os
import click

from kindle_scribe_ingester.kindle import Kindle
from confluence_ingester.confluence import ConfluenceIngester
from logseq import Logseq

logging.basicConfig(level=logging.WARNING)
app_logger = logging.getLogger('app')

@click.group()
@click.option('--debug/--no-debug', default=False)
@click.option('--pull-first/--no-pull-first', default=True)
def cli(debug, pull_first):
    if debug:
        click.echo('Debug mode is on')
    app_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    if pull_first:
        click.echo('Pulling from s3 to ensure latest files...')
        Logseq().pull_from_s3()
        click.echo('Pull complete')

@cli.command()
@click.option('--filetype', default=None)
def extract_load_kindle_emails(filetype:str):
    message = f"Extracting and loading kindle emails {'' if filetype is None else 'of type ' + filetype}"
    click.echo(message)
    k = Kindle()
    download_links = k.extract_email_links(filetype)
    click.echo(f"found {len(download_links)} links")
    for link in download_links:
        k.route_kindle_file_within_logseq(link)
    push_to_s3()

@cli.command()
@click.option('--days', default=1)
def extract_load_confluence_pages(days:int):
    click.echo("extracting and loading confluence pages")
    c = ConfluenceIngester()
    page_count = c.capture_confluence_pages_in_logseq(days)
    click.echo(f"wrote {page_count} Confluence pages to logseq")
    push_to_s3()


def push_to_s3():
    click.echo("pushing changes up to s3...")
    Logseq().push_to_s3()
    click.echo("push complete")

if __name__ == "__main__":
    cli()