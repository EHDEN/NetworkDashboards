#!/usr/bin/python3

import json
import requests
import sys

response = requests.get(
    "https://api.github.com/repos/apache/superset/commits?path=superset-frontend/src/visualizations/presets/MainPreset.js",
    headers={"accept": "application/vnd.github.v3+json"},
)

if response.status_code == 200:
    commits = response.json()
    if not commits:
        print("Commits list is empty", file=sys.stderr)
    elif commits[0]["sha"] == "e466066229ec8262583bc118af1f39e2dbf77bcf":
        print("No changes were made to the MainPresets file")
    else:
        print("Changes were made to the MainPresets file", file=sys.stderr)
else:
    print("Unable to request commits history from github", file=sys.stderr)
