#!/usr/bin/python3

import json
import requests
import sys

response = requests.get(
    "https://api.github.com/repos/apache-superset/superset-ui/commits?path=plugins/plugin-chart-echarts",
    headers={"accept": "application/vnd.github.v3+json"},
)

if response.status_code == 200:
    commits = response.json()
    if not commits:
        print("Commits list is empty", file=sys.stderr)
    elif commits[0]["sha"] == "7142c9ab7eb61c119b205aed31615651e640d771":
        print("No changes were made to the echarts plugin")
    else:
        print("Changes were made to the echarts plugin", file=sys.stderr)
else:
    print("Unable to request commits history from github", file=sys.stderr)
