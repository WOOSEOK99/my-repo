import os
import subprocess

untracked_files = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', 'files/']).decode('utf-8').splitlines()

print("1. Committing tracked files...")
subprocess.run(['git', 'add', '-u'])
subprocess.run(['git', 'commit', '-m', 'Update support_game_list and editor script'])
subprocess.run(['git', 'push', 'origin', 'main'])

chunk = []
chunk_size = 0
chunk_idx = 1

for f in untracked_files:
    if not os.path.exists(f):
        continue
    size = os.path.getsize(f)
    chunk.append(f)
    chunk_size += size
    
    if chunk_size > 200 * 1024 * 1024:
        print(f"\n============= Committing chunk {chunk_idx} =============\nFiles: {len(chunk)}, Size: {chunk_size/1024/1024:.2f} MB")
        for cf in chunk:
            subprocess.run(['git', 'add', cf])
        subprocess.run(['git', 'commit', '-m', f'Add ROMs chunk {chunk_idx}'])
        r = subprocess.run(['git', 'push', 'origin', 'main'])
        if r.returncode != 0:
            print(f"Error pushing chunk {chunk_idx}. Halting.")
            exit(1)
        chunk = []
        chunk_size = 0
        chunk_idx += 1

if chunk:
    print(f"\n============= Committing chunk {chunk_idx} =============\nFiles: {len(chunk)}, Size: {chunk_size/1024/1024:.2f} MB")
    for cf in chunk:
        subprocess.run(['git', 'add', cf])
    subprocess.run(['git', 'commit', '-m', f'Add ROMs chunk {chunk_idx}'])
    subprocess.run(['git', 'push', 'origin', 'main'])

print("\nDone! All files have been pushed in chunks.")
