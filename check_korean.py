import os
import re

filepath = r'd:\301_GUI\my_repo\my-repo\support\cheat_en.dat'

korean_pattern = re.compile(r'[가-힣]')

def run():
    korean_count = 0
    try:
        with open(filepath, 'r', encoding='cp949', errors='ignore') as f:
            for line in f:
                if korean_pattern.search(line):
                    korean_count += 1
        print(f"Remaining Korean lines: {korean_count}")
    except Exception as e:
        print(f"Error: {e}")

run()
