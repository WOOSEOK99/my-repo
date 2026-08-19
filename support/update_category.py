import json
import os

filepath = 'd:/301_GUI/apps/appl/my-repo/support/support_game_list.json'

with open(filepath, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

for key, value in data.items():
    value['category'] = 'arcade'

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
print("Updated successfully.")
