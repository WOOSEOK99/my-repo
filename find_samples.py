import os
import re
import json

target_samples = [
    "005", "3bagfull", "astrof", "battles", "bbc", "blockade", "bowl3d",
    "circus", "clowns", "cosmica", "cosmicg", "crash", "dai3wksi", "depthch",
    "equites", "fantasy", "fruitsamples", "ftaerobi", "gaplus", "genpin", "gmissile",
    "gridlee", "homerun", "ifslots", "ipminvad", "journey", "kst25", "ktmnt2", "ktopgun2",
    "lrescue", "lupin3", "mmagic", "moepro", "moepro88", "moepro90", "monsterb",
    "mpsaikyo", "mptennis", "natodef", "nsub", "ozmawars", "panic", "ptrmj",
    "redclash", "relay", "ripcord", "robotbwl", "safarir", "sasuke", "sharkatt",
    "smoepro", "spacefb", "spaceod", "tattack", "terao", "thehand", "thief",
    "triplhnt", "turbo", "twotiger", "zerohour"
]

src_dir = r"D:\301_GUI\apps\core\mame-2003-plus-kaze\src"

files_content = {}
for root, dirs, files in os.walk(src_dir):
    for f in files:
        if f.endswith(".c") or f.endswith(".h") or f.endswith(".cpp") or f.endswith(".mak"):
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as file:
                    files_content[path] = file.read()
            except:
                pass


final_mappings = []

for ts in target_samples:
    array_name = None
    array_file = None
    # match 1: static const char *const array_name[] = { "*ts", ... }
    pattern1 = r'([A-Za-z0-9_]+)\s*\[\]\s*=\s*\{[^}]*"\*' + re.escape(ts) + r'"'
    for path, content in files_content.items():
        m = re.search(pattern1, content, re.MULTILINE)
        if m:
            array_name = m.group(1)
            array_file = path
            break
            
    if not array_name:
        # fallback: search for "*ts" directly
        pattern1b = r'([A-Za-z0-9_]+).*"\*' + re.escape(ts) + r'"'
        for path, content in files_content.items():
            m = re.search(pattern1b, content)
            if m:
                array_name = m.group(1)
                array_file = path
                break

    if not array_name:
        final_mappings.append((ts, ts))
        continue

    # Find struct or interface containing array_name
    interface_names = set([array_name])
    for path, content in files_content.items():
        # struct Samplesinterface interface_name = { ..., array_name ... }
        matches = re.finditer(r'([A-Za-z0-9_]+)\s*=\s*\{[^}]*' + re.escape(array_name) + r'[^}]*\}', content)
        for m in matches:
            interface_names.add(m.group(1))
            
    # Find MACHINE_DRIVER_START
    machine_names = set()
    for path, content in files_content.items():
        matches = re.finditer(r'(?:MACHINE_DRIVER_START|MACHINE_CONFIG_START)\s*\(\s*([A-Za-z0-9_]+)\s*\)(.*?)(?:MACHINE_DRIVER_START|MACHINE_CONFIG_START|GAME|$)', content, re.DOTALL)
        for m in matches:
            mach = m.group(1)
            body = m.group(2)
            for itf in interface_names:
                if itf in body:
                    machine_names.add(mach)
                    
    # Find GAMES
    games = set()
    for path, content in files_content.items():
        game_matches = re.finditer(r'(?:GAME|GAMEX|COMP|CONS|SYST)\s*\(\s*[^,]+,\s*([^,]+),\s*([^,]+),\s*([^, \t\r\n\)]+)', content)
        for m in game_matches:
            g_name = m.group(1).strip()
            g_mach = m.group(3).strip()
            if g_mach in machine_names:
                games.add(g_name)
                
    if games:
        for g in games:
            final_mappings.append((g, ts))
    else:
        # fallback
        content = files_content.get(array_file, "")
        games_fallback = re.findall(r'(?:GAME|GAMEX|COMP|CONS|SYST)\s*\(\s*[^,]+,\s*([^, \t\r\n]+)', content)
        if games_fallback:
            for g in games_fallback:
                final_mappings.append((g, ts))
        else:
            final_mappings.append((ts, ts))

res_dict = {}
for g, s in final_mappings:
    if g and s:
        res_dict[g] = s

with open('D:/301_GUI/apps/appl/my-repo/final_mappings.json', 'w', encoding='utf-8') as f:
    json.dump(res_dict, f, indent=4)
