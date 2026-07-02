import os
import re

filepath = r'd:\301_GUI\my_repo\my-repo\support\cheat.dat'
output_filepath = r'd:\301_GUI\my_repo\my-repo\korean_lines_2.txt'

korean_pattern = re.compile(r'[\u3131-\uD79D]')

def extract_korean():
    try:
        with open(filepath, 'r', encoding='cp949', errors='ignore') as f, open(output_filepath, 'w', encoding='utf-8') as out:
            for i, line in enumerate(f, 1):
                if korean_pattern.search(line):
                    out.write(f"Line {i}: {line.strip()}\n")
    except Exception as e:
        print(f"Error: {e}")

extract_korean()
