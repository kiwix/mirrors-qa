import click

from speedtest.__about__ import __version__
from speedtest.main import check_download_speed, fmt


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="speedtest")
def speedtest():
    speed = check_download_speed()
    click.echo(f"Speed: {fmt(speed)}/s")
