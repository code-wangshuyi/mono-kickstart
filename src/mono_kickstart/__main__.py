"""
允许通过 python -m mono_kickstart 运行 CLI
"""

import sys
from mono_kickstart.cli import main

if __name__ == "__main__":
    sys.exit(main())
