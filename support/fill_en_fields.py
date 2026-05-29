"""
support_game_list.json의 title_en / genre_en / series_en 필드를
MAME 공식 영문 명칭으로 채우는 스크립트.
이미 값이 있는 경우 덮어쓰지 않는다.
"""
import json, os

JSON_PATH = os.path.join(os.path.dirname(__file__), "support_game_list.json")

# -------------------------------------------------------------------------
# 장르 한글 → 영문 매핑
# -------------------------------------------------------------------------
GENRE_MAP = {
    "슈팅": "Shoot 'em up",
    "횡스크롤 액션": "Side-scrolling Action",
    "벨트스크롤 액션": "Beat 'em up",
    "대전 액션": "Fighting",
    "퍼즐": "Puzzle",
    "스포츠": "Sports",
    "레이싱": "Racing",
    "어드벤쳐": "Adventure",
    "아케이드": "Arcade",
    "액션": "Action",
}

# -------------------------------------------------------------------------
# 게임 키 → (title_en, series_en)  매핑
# series_en이 비어 있으면 한글 series와 같은 키의 series를 기준으로 설정됨
# -------------------------------------------------------------------------
GAME_MAP = {
    # ── 19XX 계열 ──────────────────────────────
    "19xx":         ("19XX: The War Against Destiny", ""),
    # ── Metal Slug ────────────────────────────
    "mslug":        ("Metal Slug", "Metal Slug"),
    "mslugrmpl02":  ("Metal Slug (Hack)", "Metal Slug"),
    "mslug2t":      ("Metal Slug 2: Super Vehicle-001/II (Turbo)", "Metal Slug 2"),
    "mslug3":       ("Metal Slug 3", "Metal Slug 3"),
    "mslug3hek04":  ("Metal Slug 3 (Hack)", "Metal Slug 3"),
    "mslug4":       ("Metal Slug 4", "Metal Slug 4"),
    "mslug4ek01":   ("Metal Slug 4 (Hack)", "Metal Slug 4"),
    "mslug5":       ("Metal Slug 5", "Metal Slug 5"),
    "mslug5dh72":   ("Metal Slug 5 (Hack)", "Metal Slug 5"),
    "mslugx":       ("Metal Slug X", "Metal Slug X"),
    "mslugxsp2":    ("Metal Slug X (Hack)", "Metal Slug X"),
    # ── Warriors of Fate / WOF ───────────────
    "wofk":         ("Warriors of Fate", "Tenchi wo Kurau II"),
    "tk2c21k":      ("Warriors of Fate (Zhao Yun Hack)", "Tenchi wo Kurau II"),
    "tk2h10k":      ("Warriors of Fate (Hack)", "Tenchi wo Kurau II"),
    "wofchk":       ("Warriors of Fate (Changer)", "Tenchi wo Kurau II Changer"),
    # ── Cadillacs & Dinosaurs ────────────────
    "dino":         ("Cadillacs and Dinosaurs", "Cadillacs and Dinosaurs"),
    "dinoslice":    ("Cadillacs and Dinosaurs (Boss Select)", "Cadillacs and Dinosaurs"),
    # ── Gunbird ──────────────────────────────
    "gunbirdkp":    ("Gunbird", "Gunbird"),
    # ── Puzzle & Action / Ichidant-R ─────────
    "ichirk":       ("Puzzle & Action: Ichidant-R", "Puzzle & Action: Ichidant-R"),
    # ── Wonder Boy ───────────────────────────
    "wbmlkb":       ("Wonder Boy in Monster Land", ""),
    # ── Black Tiger ──────────────────────────
    "blkdrgonk":    ("Black Tiger", ""),
    # ── Suchie-Pai / Search Eye ──────────────
    "searcheya":    ("Search Eye", "Search Eye"),
    "searchp2":     ("Search Eye Plus", "Search Eye"),
    # ── Tengai / Sengoku Blade ───────────────
    "tengaik":      ("Tengai / Sengoku Blade: Sengoku Ace Episode II", ""),
    # ── Sengoku 3 ────────────────────────────
    "sengoku3":     ("Sengoku 3", "Sengoku"),
    "sengoku3e3":   ("Sengoku 3 (Hack)", "Sengoku"),
    # ── KOF ──────────────────────────────────
    "kof95":        ("The King of Fighters '95", "The King of Fighters '95"),
    "kof96":        ("The King of Fighters '96", "The King of Fighters '96"),
    "kof97":        ("The King of Fighters '97", "The King of Fighters '97"),
    "kof98":        ("The King of Fighters '98: The Slugfest", "The King of Fighters '98"),
    "kof99":        ("The King of Fighters '99: Millennium Battle", "The King of Fighters '99"),
    "kof2000":      ("The King of Fighters 2000", "The King of Fighters 2000"),
    "kof2001":      ("The King of Fighters 2001", "The King of Fighters 2001"),
    "kof2002":      ("The King of Fighters 2002: Challenge to Ultimate Battle", "The King of Fighters 2002"),
    "kof2003":      ("The King of Fighters 2003", "The King of Fighters 2003"),
    "kof2k4se":     ("The King of Fighters 2004 (Bootleg)", ""),
    # ── Samurai Shodown ───────────────────────
    "samsho":       ("Samurai Shodown", ""),
    "samsho2":      ("Samurai Shodown II", ""),
    "samsho3":      ("Samurai Shodown III: Blades of Blood", ""),
    "samsho4":      ("Samurai Shodown IV: Amakusa's Revenge", ""),
    "samsho5":      ("Samurai Shodown V", ""),
    # ── 194x Series ──────────────────────────
    "1941":         ("1941: Counter Attack", ""),
    "1942":         ("1942", ""),
    "1943":         ("1943: The Battle of Midway", ""),
    "1943mii":      ("1943: The Battle of Midway Mark II", ""),
    "1943kai":      ("1943 Kai: Midway Kaisen", ""),
    "1944":         ("1944: The Loop Master", ""),
    "1945kiii":     ("1945k III", ""),
    # ── Final Fight ──────────────────────────
    "ffight":       ("Final Fight", "Final Fight"),
    "ffightb":      ("Final Fight (Hack)", "Final Fight"),
    "ffightae":     ("Final Fight (3-Players)", "Final Fight"),
    # ── Dynasty / KOV / Three Kingdoms ───────
    "kov":          ("Knights of Valour", "Knights of Valour"),
    "kov115s02":    ("Knights of Valour (Hidden Chars)", "Knights of Valour"),
    "kovplus":      ("Knights of Valour Plus", "Knights of Valour"),
    # ── Misc Arcade ──────────────────────────
    "robby":        ("Robby Roto!", ""),
    "targ":         ("Targ", ""),
    "Spectar":      ("Spectar", ""),
    "Gridlee":      ("Gridlee", ""),
    "riotcity":     ("Riot City", ""),
    "mightguy":     ("Mighty Guy", ""),
    "madmotor":     ("Mad Motor", ""),
    "fightrol":     ("Fighting Roller", ""),
    "tshingen":     ("Shingen the Ruler", ""),
    "nastar":       ("Nastar Warrior / Rastan Saga II", ""),
    "gaiapols":     ("Gaiapolis", ""),
    "jailbrek":     ("Jail Break", ""),
    "theroes":      ("Thunder Heroes", ""),
    "mwarr":        ("Mighty Warriors", ""),
    "fitfight":     ("Fit of Fighting (Bootleg)", "Art of Fighting"),
    "blandia":      ("Blandia", ""),
    "ultraman":     ("Ultraman", ""),
    "killbld":      ("The Killing Blade", ""),
    "solfigtr":     ("Solitary Fighter", ""),
    "mcatadv":      ("Magical Cat Adventure", ""),
    "fantland":     ("Fantasy Land", ""),
    "devilw":       ("Devil World", ""),
    "recalh":       ("Recalhorn", ""),
    "suprtrio":     ("Super Trio", ""),
    "jjsquawk":     ("J. J. Squawkers", ""),
    "drgnbstr":     ("Dragon Buster", ""),
    "hardhea2":     ("Hard Head 2", "Hard Head"),
    "tkmmpzdm":     ("Tokimeki Memorial Taisen Puzzle-dama", ""),
    "teddybb":      ("Teddy Boy Blues", ""),
    "ldrun3":       ("Lode Runner III", "Lode Runner"),
    "ldrun4":       ("Lode Runner IV", "Lode Runner"),
    "losttomb":     ("Lost Tomb", ""),
    "hopprobo":     ("Hopper Robo", ""),
    "kangaroo":     ("Kangaroo", ""),
    "berlwall":     ("Berlin Wall", ""),
    "docastle":     ("Mr. Do's Castle", ""),
    "pandoras":     ("Pandora's Palace", ""),
    "rainbow":      ("Rainbow Islands: The Story of Bubble Bobble 2", ""),
    "cbtime":       ("BurgerTime", ""),
    "blocken":      ("Blocken", ""),
    "tutankhm":     ("Tutankham", ""),
    "rodland":      ("Rod Land", ""),
    "iceclimb":     ("VS. Ice Climber", ""),
    "elevator":     ("Elevator Action", ""),
    "nrallyx":      ("New Rally-X", ""),
    "ghouls":       ("Ghouls'n Ghosts", ""),
    "forgottn":     ("Forgotten Worlds / Lost Worlds", ""),
    "striderjrk":   ("Strider Hiryu", ""),
    "dw":           ("Dynasty Wars", ""),
    "willow":       ("Willow", ""),
    "unsquad":      ("Area 88 / U.N. Squadron", ""),
    "mercs":        ("Mercs / Senjou no Ookami II", ""),
    "mtwins":       ("Mega Twins / Chiki Chiki Boys", ""),
    "msword":       ("Magic Sword: Heroic Fantasy", ""),
    "cawing":       ("Carrier Air Wing", ""),
    "nemo":         ("Little Nemo: The Dream Master", ""),
    "sf2":          ("Street Fighter II: The World Warrior", "Street Fighter II"),
    "3wonders":     ("Three Wonders", ""),
    "kod":          ("The King of Dragons", ""),
    "captcomjk":    ("Captain Commando", "Captain Commando"),
    "captcomek1k":  ("Captain Commando (Hack)", "Captain Commando"),
    "knightsk":     ("Knights of the Round", ""),
    "sf2ce":        ("Street Fighter II': Champion Edition", "Street Fighter II'"),
    "sf2rb":        ("Street Fighter II': Rainbow Edition (Hack)", "Street Fighter II'"),
    "sf2red":       ("Street Fighter II': Red Wave (Hack)", "Street Fighter II'"),
    "sf2yyc":       ("Street Fighter II': YYC (Hack)", "Street Fighter II'"),
    "sf2koryu":     ("Street Fighter II': Koryu (Hack)", "Street Fighter II'"),
    "sf2t":         ("Street Fighter II': Hyper Fighting", "Street Fighter II'"),
    "varth":        ("Varth: Operation Thunderstorm", ""),
    "cworld2j":     ("Capcom World 2", ""),
    "megaman":      ("Mega Man: The Power Battle", ""),
    "punisher":     ("The Punisher", ""),
    "slammast":     ("Saturday Night Slam Masters", "Saturday Night Slam Masters"),
    "pnickj":       ("Pnickies", ""),
    "pang3":        ("Pang! 3", ""),
    "ssf2":         ("Super Street Fighter II: The New Challengers", ""),
    "ddsomak":      ("Dungeons & Dragons: Shadow over Mystara", ""),
    "sfa":          ("Street Fighter Alpha: Warriors' Dreams", "Street Fighter Alpha"),
    "sfzjk":        ("Street Fighter Zero (Japan)", "Street Fighter Alpha"),
    "ecofghtr":     ("Eco Fighters", ""),
    "ssf2t":        ("Super Street Fighter II Turbo", ""),
    "xmcota":       ("X-Men: Children of the Atom", ""),
    "armwar":       ("Armored Warriors", ""),
    "avsp":         ("Alien vs. Predator", ""),
    "dstlk":        ("Darkstalkers: The Night Warriors", ""),
    "ringdest":     ("Ring of Destruction: Slam Masters II", "Saturday Night Slam Masters"),
    "cybots":       ("Cyberbots: Full Metal Madness", ""),
    "msh":          ("Marvel Super Heroes", ""),
    "nwarr":        ("Night Warriors: Darkstalkers' Revenge", ""),
    "megaman2":     ("Mega Man 2: The Power Fighters", ""),
    "sfa2":         ("Street Fighter Alpha 2", ""),
    "spf2t":        ("Super Puzzle Fighter II Turbo", ""),
    "xmvsf":        ("X-Men vs. Street Fighter", ""),
    "batcir":       ("Battle Circuit", ""),
    "csclubk":      ("Capcom Sports Club", ""),
    "bublbobl":     ("Bubble Bobble", "Bubble Bobble"),
    "sboblbob":     ("Super Bubble Bobble", "Bubble Bobble"),
    "bublboblu":    ("Bubble Bobble (Ultra Version)", "Bubble Bobble"),
    "bublcave":     ("Bubble Bobble Lost Cave", "Bubble Bobble"),
    "bublbob2":     ("Bubble Bobble 2 / Bubble Symphony", "Bubble Bobble"),
    "bubblem":      ("Bubble Memories: The Story of Bubble Bobble III", "Bubble Bobble"),
    "tokio":        ("Tokio / Scramble Formation", ""),
    "88games":      ("'88 Games", ""),
    "pspikes":      ("Power Spikes", ""),
    "aerofgt":      ("Aero Fighters / Sonic Wings", ""),
    "grdnstrm":     ("Guardian Storm", ""),
    "airbustr":     ("Air Buster: Trouble Specialty Raid Unit", ""),
    "timesold":     ("Time Soldiers", ""),
    "goldmedl":     ("Gold Medalist", ""),
    "gangwars":     ("Gang Wars", ""),
    "sbasebal":     ("Super Champion Baseball", ""),
    "atetris":      ("Tetris (Atari)", ""),
    "bloodbro":     ("Blood Bros. / Cabal II", ""),
    "cabal":        ("Cabal", ""),
    "rungun":       ("Run and Gun", ""),
    "spdodgeb":     ("Super Dodgeball / Nekketsu Koukou Dodgeball-bu", ""),
    "vbowl":        ("Virtua Bowling", ""),
    "mjleague":     ("Major League", ""),
    "bodyslam":     ("Body Slam: Super Pro Wrestling", ""),
    "alexkida":     ("Alex Kidd: The Lost Stars", ""),
    "fantzone":     ("Fantasy Zone", ""),
    "shinobi":      ("Shinobi", ""),
    "sdi":          ("SDI: Strategic Defense Initiative", ""),
    "aliensyn":     ("Alien Syndrome", ""),
    "altbeast":     ("Altered Beast: Rise from your Grave", ""),
    "bayroute":     ("Bay Route", ""),
    "dduxbl":       ("Dynamite Dux", ""),
    "eswatbl":      ("E-SWAT: Cyber Police", ""),
    "goldnaxe":     ("Golden Axe", ""),
    "wb3":          ("Wonder Boy III: Monster Lair", ""),
    "heberpop":     ("Hebereke no Popoon", ""),
    "pbobble":      ("Puzzle Bobble", "Puzzle Bobble"),
    "pbobble2":     ("Puzzle Bobble 2", "Puzzle Bobble"),
    "pbobble3":     ("Puzzle Bobble 3", "Puzzle Bobble"),
    "pbobble4":     ("Puzzle Bobble 4", "Puzzle Bobble"),
    "rambo3":       ("Rambo III", ""),
    "crimec":       ("Crime City", ""),
    "viofight":     ("Violence Fight", ""),
    "ashura":       ("Ashura Blaster", ""),
    "hitice":       ("Hit the Ice", ""),
    "selfeena":     ("Sel Feena", ""),
    "silentd":      ("Silent Dragon", ""),
    "ryujin":       ("Ryujin", ""),
    "tcobra2":      ("Twin Cobra II", ""),
    "grdnstrm":     ("Guardian Storm", ""),
}

# -------------------------------------------------------------------------
with open(JSON_PATH, "r", encoding="utf-8-sig") as f:
    data = json.load(f)

changed = 0
for key, val in data.items():
    # title_en
    if not val.get("title_en") and key in GAME_MAP:
        val["title_en"] = GAME_MAP[key][0]
        changed += 1

    # genre_en
    if not val.get("genre_en"):
        kor_genre = val.get("genre", "")
        if kor_genre in GENRE_MAP:
            val["genre_en"] = GENRE_MAP[kor_genre]
            changed += 1

    # series_en
    if not val.get("series_en") and key in GAME_MAP:
        series_en = GAME_MAP[key][1]
        if series_en:
            val["series_en"] = series_en
            changed += 1

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"완료: {changed}개 필드 업데이트됨 (총 항목 수: {len(data)})")
