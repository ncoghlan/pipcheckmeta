# Helper library for venv metadata analysis

# Why does this currently invoke pip via a subprocess?
# * Python packaging ecosystem is currently in flux
# * pip abstracts over a lot of those messy details
# * programmatic API is also in flux while the evolution is in progress
# * pip's CLI is thus the most robust way of querying the packaging metadata
from subprocess import check_output
import parse
import packaging.version
import os.path

@parse.with_pattern(r'\S+')
def _parse_version(text):
    return packaging.version.parse(text)

def _make_line_parser(line_format):
    return parse.compile(line_format, dict(version=_parse_version)).parse

def _run_list_command(parse_line, extra_args=()):
    command = ["pip", "list"]
    command.extend(extra_args)
    lines = check_output(command).splitlines()
    parsed = (parse_line(line) for line in lines)
    return (entry.named for entry in parsed if entry is not None)

_installed_format = "{name} ({version:version})"
_installed_line_parser = _make_line_parser(_installed_format)

def installed_distributions():
    return _run_list_command(_installed_line_parser)

_outdated_format = "{name} (Current: {version:version} Latest: {available:version}{has_wheel})"
_outdated_line_parser = _make_line_parser(_outdated_format)

def outdated_distributions():
    return _run_list_command(_outdated_line_parser, ["--outdated"])

def _run_download_command(download_path, specifiers):
    command = ["pip", "install",
               "--download", download_path,
               "--no-binary", ":all:"]
    command.extend(specifiers)
    return check_output(command)

def download_sources(distributions=None):
    if distributions is None:
        distributions = installed_distributions()
    download_path = os.path.abspath(".pip_sources")
    try:
        os.makedirs(download_path)
    except OSError:
        pass # Assume this was an "already exists" error
    specifiers = ("{0[name]}=={0[version]}".format(info) for info in distributions)
    return _run_download_command(download_path, specifiers)
