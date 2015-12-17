# Helper library for venv metadata analysis

# Why does this currently invoke pip via a subprocess?
# * Python packaging ecosystem is currently in flux
# * pip abstracts over a lot of those messy details
# * programmatic API is also in flux while the evolution is in progress
# * pip's CLI is thus the most robust way of querying the packaging metadata
# * we can also use peep for hashing on pip < 8.0
from subprocess import check_output
import parse
import packaging.version
import os.path
import tempfile

@parse.with_pattern(r'\S+')
def _parse_version(text):
    return packaging.version.parse(text)

def _make_line_parser(line_format):
    return parse.compile(line_format, dict(version=_parse_version)).parse

##################################
# Listings of venv contents
##################################

def _run_list_command(parse_line, extra_args=()):
    command = ["pip", "list"]
    command.extend(extra_args)
    lines = check_output(command).splitlines()
    parsed = (parse_line(line) for line in lines)
    return (entry.named for entry in parsed if entry is not None)

# All components
_installed_format = "{name} ({version:version})"
_installed_line_parser = _make_line_parser(_installed_format)

def installed_distributions():
    return _run_list_command(_installed_line_parser)

# Outdated components
_outdated_format = "{name} (Current: {version:version} Latest: {available:version}{has_wheel})"
_outdated_line_parser = _make_line_parser(_outdated_format)

def outdated_distributions():
    return _run_list_command(_outdated_line_parser, ["--outdated"])

##################################
# Downloading source tarballs
##################################

def _run_download_command(download_path, specifiers):
    command = ["pip", "install",
               "--download", download_path,
               "--no-binary", ":all:"]
    command.extend(specifiers)
    return check_output(command)

_collected_format = "Collecting {name}=={version:version}"
_collected_line_parser = _make_line_parser(_collected_format)
_saved_format = "  Saved {filename}"
_saved_line_parser = _make_line_parser(_saved_format)
_cached_format = "  File was already downloaded {filename}"
_cached_line_parser = _make_line_parser(_cached_format)

def download_sources(distributions=None):
    if distributions is None:
        distributions = installed_distributions()
    download_path = os.path.abspath(".pip_sources")
    try:
        os.makedirs(download_path)
    except OSError:
        pass # Assume this was an "already exists" error
    expected_versions = dict((dist["name"], dist["version"]) for dist in distributions)
    specifiers = ("{}=={}".format(name, ver) for name, ver in expected_versions.items())
    download_details = _run_download_command(download_path, specifiers)
    current_dist = None
    downloaded = []
    for line in download_details.splitlines():
        if current_dist is None:
            parsed_line = _collected_line_parser(line)
            if parsed_line is None:
                # Skip to next line to keep looking for a package name
                continue
            new_dist = parsed_line.named
            current_dist = new_dist["name"]
            dist_version = new_dist["version"]
            if dist_version != expected_versions[current_dist]:
                msg = "Expected {}=={}, not {}"
                raise RuntimeError(msg.format(current_dist,
                                              expected_versions[current_dist],
                                              dist_version))
            # Skip to next line to look for a filename
            continue
        if current_dist is not None: # and we have a filename...
            downloaded.append((current_dist, dist_version))
            current_dist = None
    return downloaded
