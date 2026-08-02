from __future__ import annotations

import os
import sys


bundle_root = getattr(sys, "_MEIPASS", "")
if bundle_root:
    os.environ["PATH"] = bundle_root + os.pathsep + os.environ.get("PATH", "")

