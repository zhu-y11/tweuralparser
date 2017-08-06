import argparse
import codecs
import os
import re
import sys
import time


if __name__ == '__main__':
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if not line.startswith('Unlabeled') or not line.endswith('%'):
          continue
        eq_idx = line.rfind(' = ')
        print line[eq_idx + 3:]
