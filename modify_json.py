import json

file_path = r"d:\301_GUI\my_repo\my-repo\support\support_game_list.json"

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for game_id, game_data in data.items():
    game_data["year"] = 0
    game_data["developer"] = ""

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
    f.write('\n')

print("All 'year' values set to 0, and 'developer' values set to empty string.")
