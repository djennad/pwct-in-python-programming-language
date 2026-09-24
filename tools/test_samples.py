"""Test: generate, build and run the samples of every Visual Programming Language.

Usage:  python tools/test_samples.py            (all the languages)
        python tools/test_samples.py C Java     (some languages)

Uses the real compilers (gcc/clang, csc, java, node) with piped input;
the GUI samples are skipped.  A language whose tools are missing is reported.
"""

import glob
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from pwct import codegen  # noqa: E402
from pwct.languages import Languages  # noqa: E402
from pwct.model import Project  # noqa: E402

GUESSES = "".join("%d\n" % i for i in range(1, 101))
INPUTS = {"01_Hello_World": "Ahmed\n", "02_Guess_The_Number": GUESSES}


def main():
    langs = Languages(os.path.join(BASE, "languages"))
    only = sys.argv[1:] or [x.id for x in langs.items]
    failed = 0
    for lang in langs.items:
        if lang.id not in only:
            continue
        for f in sorted(glob.glob(os.path.join(lang.samples_dir, "*.pwct"))):
            base = os.path.splitext(os.path.basename(f))[0]
            if "GUI" in base:
                continue
            files = {}
            code, linemap = codegen.generate(Project.load(f), lang=lang, files=files)
            err = codegen.check_syntax(code, linemap, files, lang)
            if err:
                print("%-11s %-26s SYNTAX ERROR %s" % (lang.id, base, err[:2]))
                failed += 1
                continue
            d = tempfile.mkdtemp(prefix="pypwct_test_")
            src = os.path.join(d, base + lang.extension)
            codegen.write_files(src, code, files)
            values = lang.placeholders(src, d)
            result = None
            if lang.build:
                cmd = lang.command(lang.build, values)
                if cmd is None:
                    result = "SKIPPED (build tool not found : %s)" % ", ".join(lang.missing_tools(lang.build))
                else:
                    r = subprocess.run(cmd, cwd=d, capture_output=True, text=True)
                    if r.returncode != 0:
                        result = "BUILD FAILED\n" + (r.stdout + r.stderr)[-1500:]
                        failed += 1
            if result is None:
                cmd = lang.command(lang.run, values)
                if cmd is None:
                    result = "SKIPPED (run tool not found : %s)" % ", ".join(lang.missing_tools(lang.run))
                else:
                    r = subprocess.run(cmd, cwd=d, input=INPUTS.get(base, ""), capture_output=True,
                                       text=True, timeout=120)
                    out = (r.stdout + r.stderr).strip().replace("\n", " | ")
                    ok = r.returncode == 0
                    failed += 0 if ok else 1
                    result = ("OK  " if ok else "RUN ERROR %s  " % r.returncode) + \
                        ("..." + out[-90:] if len(out) > 90 else out)
            print("%-11s %-26s %s" % (lang.id, base, result))
    print("\n%s" % ("ALL OK" if failed == 0 else "%d FAILED" % failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
