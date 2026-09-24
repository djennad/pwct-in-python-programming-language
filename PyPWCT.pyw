"""PyPWCT - Programming Without Coding Technology (Python Edition).

Double click this file (or run:  python PyPWCT.pyw [file.pwct]).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pwct.ui.mainwindow import main  # noqa: E402

if __name__ == "__main__":
    main(sys.argv[1:])
