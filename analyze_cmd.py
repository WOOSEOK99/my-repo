import os
import re
from collections import Counter

filepath = r'd:\301_GUI\my_repo\my-repo\support\command.dat'
output_filepath = r'd:\301_GUI\my_repo\my-repo\unique_korean_cmd.txt'

korean_pattern = re.compile(r'[가-힣]+(?:\s*[가-힣]+)*')

counter = Counter()

def run():
    total_lines = 0
    korean_lines = 0
    try:
        sz = os.path.getsize(filepath)
        with open(filepath, 'r', encoding='cp949', errors='ignore') as f:
            for line in f:
                total_lines += 1
                matches = korean_pattern.findall(line)
                if matches:
                    korean_lines += 1
                    for m in matches:
                        # strip whitespace and store
                        m_clean = m.strip()
                        if m_clean:
                            counter[m_clean] += 1

        print(f"Size: {sz} bytes")
        print(f"Total lines: {total_lines}")
        print(f"Korean lines: {korean_lines}")
        
        with open(output_filepath, 'w', encoding='utf-8') as out:
            for k, v in counter.most_common(2000):
                out.write(f"{k}: {v}\n")
    except Exception as e:
        print(f"Error: {e}")

run()
