# Helper library for communication with a metadata server

# Currently just invokes the cucos-cli client with dummy data sources

from subprocess import check_output
import json

##################################
# Retrieving curated metadata
##################################

def _run_query(name, version, source_hash):
    command = ["../cucos-cli/bin/cucos-cli", "-e", "python",
               "--api-url", "data", name]
    if version is not None:
        command.extend(("--version", version))
    data = check_output(command).strip()
    if not data:
        return None
    return json.loads(data)

def check_metadata(name, version=None, source_hash=None):
    data = _run_query(name, version, source_hash)
    problems = []
    if data is None:
        problems.append("No metadata found")
        return problems
    cve_list = data.get("cves")
    if cve_list is not None:
        for cve in cve_list:
            problems.append(cve)
    if source_hash is not None:
        expected_source_hash = data.get("source_hash")
        if expected_source_hash is None:
            problems.append("Hash check requested, no source hash available")
        elif source_hash != expected_source_hash:
            msg = "Source hash check failed (Expected {}, got {})"
            problems.append(msg.format(expected_source_hash, source_hash))
    return problems

