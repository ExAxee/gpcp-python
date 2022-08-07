import os
import sys

# allows running `python3 test/XXX_test.py` from the root directory
# and the included `gpcp` module will be the local one
sys.path.append(os.path.dirname(os.path.realpath(__file__)))