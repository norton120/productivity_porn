import logging
import click

from kindle_scribe_ingester.kindle import Kindle

root_logger = logging.getLogger()
root_logger.addHandler(logging.StreamHandler())

@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    if debug:
        click.echo('Debug mode is on')
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

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

if __name__ == "__main__":
    cli()