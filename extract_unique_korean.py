import os
import re
from collections import Counter

filepath = r'd:\301_GUI\my_repo\my-repo\support\cheat.dat'

korean_pattern = re.compile(r'[가-힣]+(?:\s+[가-힣]+)*')

counter = Counter()

def run():
    try:
        with open(filepath, 'r', encoding='cp949', errors='ignore') as f:
            for line in f:
                matches = korean_pattern.findall(line)
                for m in matches:
                    counter[m] += 1

        with open(r'd:\301_GUI\my_repo\my-repo\unique_korean.txt', 'w', encoding='utf-8') as out:
            for k, v in counter.most_common(1000):
                out.write(f"{k}: {v}\n")
    except Exception as e:
        print(f"Error: {e}")

run()
