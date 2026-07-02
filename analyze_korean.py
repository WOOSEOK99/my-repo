import sys
import os
import re

filepath = r'd:\301_GUI\my_repo\my-repo\support\cheat.dat'

korean_pattern = re.compile(r'[\u3131-\uD79D]')

def analyze():
    korean_lines = 0
    total_lines = 0
    try:
        sizes = os.path.getsize(filepath)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                total_lines += 1
                if korean_pattern.search(line):
                    korean_lines += 1

        print(f"Total lines: {total_lines}")
        print(f"Korean lines: {korean_lines}")
        print(f"File size: {sizes} bytes")
    except Exception as e:
        print(f"Error: {e}")

analyze()
