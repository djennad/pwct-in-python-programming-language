"""Builds and runs a generated program in its own console, then waits before closing.

usage:  runner.py job.json
job = {"cwd": folder, "title": "...", "steps": [{"title": "Build", "cmd": [...]},
                                                 {"title": "Run", "cmd": [...]}]}
The last step is the program; the steps before it must succeed (exit code 0).
"""

import json
import os
import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        print("usage: runner.py job.json")
        return
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        job = json.load(f)
    cwd = job.get("cwd") or os.getcwd()
    steps = job.get("steps", [])
    if os.name == "nt" and job.get("title"):
        os.system("title " + job["title"].replace("&", "and"))
    code = 0
    for k, step in enumerate(steps):
        last = k == len(steps) - 1
        if not last:
            print("[ PyPWCT ] %s : %s" % (step.get("title", "Build"), " ".join(step["cmd"])), flush=True)
        try:
            code = subprocess.call(step["cmd"], cwd=cwd)
        except OSError as ex:
            print("[ PyPWCT ] Error : %s" % ex, flush=True)
            code = -1
        except KeyboardInterrupt:
            code = -1
        if not last and code != 0:
            print("\n[ PyPWCT ] %s failed (exit code %s)" % (step.get("title", "Build"), code), flush=True)
            break
        if not last:
            print("[ PyPWCT ] %s done\n" % step.get("title", "Build"), flush=True)
    try:
        input("\n[ PyPWCT ] Program finished (exit code %s) - press Enter to close..." % code)
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
