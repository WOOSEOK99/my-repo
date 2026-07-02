import os
import chardet

filepath = r'd:\301_GUI\my_repo\my-repo\support\cheat.dat'

with open(filepath, 'rb') as f:
    raw = f.read(500000)
    print(chardet.detect(raw))
