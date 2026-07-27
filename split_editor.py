import ast
import os

source_file = "editor_supportGameList.py"
with open(source_file, "r", encoding="utf-8") as f:
    source_code = f.read()

categories = {
    "ui_setup": ["setup_ui", "bind_paste_cleaning", "on_paste", "clean_url_input", "update_listbox", "load_image", "load_marquee_image", "show_scrollable_info", "update_version_display", "update_json_version"],
    "data_ops": ["_normalize_data", "auto_load_default", "delete_item", "delete_selected", "load_file", "save_file", "append_json", "batch_link_roms", "batch_set_year", "batch_set_dev", "add_new_game", "copy_item"],
    "list_ops": ["perform_search", "go_next_search", "update_search_display", "select_listbox_key", "on_select", "apply_changes", "refresh_series_list", "refresh_parent_list", "refresh_genre_list", "refresh_genre_en_list", "refresh_developer_list", "refresh_all_lists"],
    "cheat_ops": ["_parse_cheat_dat", "load_cheat_data", "cheat_replace_all", "save_cheat_dat", "_save_cheat_dat_internal", "update_cheat_dat_version"],
    "command_ops": ["_parse_command_dat", "load_command_data", "save_command_dat", "_save_command_dat_internal", "update_command_dat_version"],
    "search_dialog": ["open_cheat_search", "open_command_search", "_open_dat_search"]
}

common_imports = """import json
import os
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
import urllib.request
from io import BytesIO
from PIL import Image, ImageTk
"""

out_dir = "editor_v2"
os.makedirs(os.path.join(out_dir, "mixins"), exist_ok=True)
with open(os.path.join(out_dir, "mixins", "__init__.py"), "w", encoding="utf-8") as f:
    pass
with open(os.path.join(out_dir, "__init__.py"), "w", encoding="utf-8") as f:
    pass

class MethodExtractor(ast.NodeVisitor):
    def __init__(self):
        self.methods = {}
    def visit_FunctionDef(self, node):
        self.methods[node.name] = node
        self.generic_visit(node)

tree = ast.parse(source_code)
game_class = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GameJsonEditor"][0]

extractor = MethodExtractor()
extractor.visit(game_class)

lines = source_code.splitlines()
def get_method_source(node):
    start = node.lineno - 1
    if node.decorator_list:
        start = node.decorator_list[0].lineno - 1
    end = node.end_lineno
    return chr(10).join(lines[start:end])

extracted = set()

for cat, methods in categories.items():
    mixin_name = cat.title().replace("_", "") + "Mixin"
    file_path = os.path.join(out_dir, "mixins", f"{cat}.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(common_imports + "\n\n")
        f.write(f"class {mixin_name}:\n")
        
        has_methods = False
        for m in methods:
            if m in extractor.methods:
                has_methods = True
                f.write(get_method_source(extractor.methods[m]) + "\n\n")
                extracted.add(m)
        
        if not has_methods:
            f.write("    pass\n")

# Process leftovers
leftovers = []
for m in extractor.methods:
    if m not in extracted and m not in ["__init__", "get_base_dir"]:
        leftovers.append(m)

if leftovers:
    cat = "misc_ops"
    mixin_name = "MiscOpsMixin"
    categories[cat] = leftovers
    file_path = os.path.join(out_dir, "mixins", f"{cat}.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(common_imports + "\n\n")
        f.write(f"class {mixin_name}:\n")
        for m in leftovers:
            f.write(get_method_source(extractor.methods[m]) + "\n\n")

main_imports = []
main_mixins = []
for cat in categories.keys():
    mixin_name = cat.title().replace("_", "") + "Mixin"
    main_imports.append(f"from mixins.{cat} import {mixin_name}")
    main_mixins.append(mixin_name)

main_py_str = f'''{common_imports}

{chr(10).join(main_imports)}

class GameJsonEditor(
    {", ".join(main_mixins)}
):
'''

init_src = get_method_source(extractor.methods["__init__"])
get_base_dir_src = get_method_source(extractor.methods["get_base_dir"])
get_base_dir_src = get_base_dir_src.replace('os.path.abspath(__file__)', 'os.path.dirname(os.path.abspath(__file__))')

main_py_str += init_src + "\n\n" + get_base_dir_src + "\n"

main_py_str += '''
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1450x700")
    app = GameJsonEditor(root)
    root.mainloop()
'''

with open(os.path.join(out_dir, "main.py"), "w", encoding="utf-8") as f:
    f.write(main_py_str)

print(f"Refactoring complete. Output in {out_dir}")
