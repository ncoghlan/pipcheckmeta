# -*- coding: utf-8 -*-
import sys
import click
from . import venvmeta
from . import curated

# Commands:
#   * Check metadata for a single file
#   * Check metadata, including source tarball hash
#   * Check all packages in the current venv


@click.group()
def cli():
    pass

@cli.command()
@click.argument("name")
@click.option("--version")
@click.option("--hash", "source_hash")
def query(name, version=None, source_hash=None):
    problems = curated.check_metadata(name, version, source_hash)
    if problems:
        click.echo(problems)
        sys.exit("Metadata validation failed")

@cli.command()
@click.option("--check-hashes")
def scan(check_hashes=False):
    flawed = []
    if check_hashes:
        raise NotImplementedError("Hash checking on scan not yet supported")
    for dist in venvmeta.installed_distributions():
        name = dist["name"]
        version = str(dist["version"])
        source_hash = None
        problems = curated.check_metadata(name, version, source_hash)
        if problems:
            flawed.append((name, version, problems))
    if flawed:
        for entry in flawed:
            click.echo(entry)
        sys.exit("Metadata validation failed")
