"""
support_game_list.json 에 title_en, genre_en, series_en 필드를 일괄 추가하는 스크립트.
기존에 이미 존재하는 필드는 건드리지 않고, 없는 것만 빈 문자열로 추가함.
필드 순서: title → title_en, genre → genre_en, series → series_en
"""
import json
import os

json_path = os.path.join(os.path.dirname(__file__), "support_game_list.json")

with open(json_path, "r", encoding="utf-8-sig") as f:
    data = json.load(f)

updated = {}
for key, val in data.items():
    new_val = {}
    for field, v in val.items():
        new_val[field] = v
        if field == "title" and "title_en" not in val:
            new_val["title_en"] = ""
        if field == "genre" and "genre_en" not in val:
            new_val["genre_en"] = ""
        if field == "series" and "series_en" not in val:
            new_val["series_en"] = ""
    updated[key] = new_val

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(updated, f, indent=4, ensure_ascii=False)

print(f"완료: {len(updated)}개 항목에 title_en/genre_en/series_en 필드 추가됨.")
