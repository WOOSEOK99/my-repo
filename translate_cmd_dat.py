import os
import re

input_file = r'd:\301_GUI\my_repo\my-repo\support\command.dat'
output_file = r'd:\301_GUI\my_repo\my-repo\support\command_en.dat'

translations = {
    "기본 조작 방법에 대해": "Basic Controls",
    "캐릭터의 이동": "Character Movement",
    "치트에 대해": "About Cheats",
    "필살기술 커멘드 표기에 대해": "Special Move Commands",
    "기본 무기": "Basic Weapon",
    "모으고": "Charge",
    "모아서": "Hold",
    "연타": "Rapidly",
    "버튼": "Button",
    "레버": "Joystick",
    "레바": "Joystick",
    "필살기": "Special Move",
    "필살기술": "Special Move",
    "초필살기": "Super Special Move",
    "특수기": "Special Attack",
    "특수기술": "Special Attack",
    "연속기술": "Combo Move",
    "점프": "Jump",
    "공격": "Attack",
    "접근해서": "Close Range",
    "접근해": "Close",
    "공중가능": "In Air OK",
    "공중에서": "In Mid-air",
    "공중": "Mid-air",
    "지상": "Ground",
    "주포": "Main Cannon",
    "부포": "Sub Cannon",
    "회전": "Rotate",
    "발칸": "Vulcan",
    "쇼트": "Shot",
    "킥": "Kick",
    "펀치": "Punch",
    "폭탄": "Bomb",
    "발": "Kick",
    "메가 크래쉬": "Mega Crash",
    "왼쪽": "Left",
    "오른쪽": "Right",
    "슬라이딩": "Sliding",
    "데쉬": "Dash",
    "대시": "Dash",
    "전방": "Forward",
    "후방": "Backward",
    "던지기": "Throw",
    "잡기": "Grab",
    "기관총": "Machine Gun",
    "미사일": "Missile",
    "도발": "Taunt",
    "라운드": "Round",
    "수류탄을 던진다": "Throw Grenade",
    "메탈 슬러그": "Metal Slug",
    "게이지": "Gauge",
    "체력": "Health",
    "신장": "Height",
    "체중": "Weight",
    "혈액형": "Blood Type",
    "태클": "Tackle",
    "베기": "Slash",
    "비행형": "Flight Type",
    "방향": "Direction",
    "기술": "Skill",
    "캐논": "Cannon",
    "입력": "Input",
    "상단": "High",
    "중단": "Mid",
    "하단": "Low",
    "가까이": "Close",
    "어퍼": "Upper",
    "약펀치": "Light Punch",
    "약킥": "Light Kick",
    "강킥": "Heavy Kick",
    "강펀치": "Heavy Punch",
    "소펀치": "Light Punch",
    "대펀치": "Heavy Punch",
    "소킥": "Light Kick",
    "대킥": "Heavy Kick",
    "중펀치": "Medium Punch",
    "중킥": "Medium Kick",
    "약": "Light",
    "중": "Medium",
    "강": "Heavy",
    "소": "Light",
    "대": "Heavy",
    "수비시": "While Defending",
    "공격시": "While Attacking",
    "취미": "Hobby",
    "성우": "Voice Actor",
    "출신지": "Birthplace",
    "기타": "Other",
    "스테이지": "Stage",
    "파동권": "Hadouken",
    "승룡권": "Shoryuken",
    "용권선풍각": "Tatsumaki Senpukyaku",
    "동시 밀기": "Press Together",
    "동시 누름": "Press Together",
    "동시": "Together",
    "가까이서": "Close Range",
    "대공격": "Heavy Attack",
    "소공격": "Light Attack",
    "중공격": "Medium Attack"
}

# compile regexes for exact word replacement without matching sub-words
# we use lookbehind and lookahead to ensure we don't break other Korean words
regexes = []
for k, v in translations.items():
    # If the key contains spaces, it's safer. If single char, we must be strict.
    pattern = r'(?<![가-힣])' + re.escape(k) + r'(?![가-힣])'
    regexes.append((re.compile(pattern), v))

def run():
    try:
        with open(input_file, 'r', encoding='cp949', errors='ignore') as f_in, open(output_file, 'w', encoding='cp949', errors='ignore') as f_out:
            for line in f_in:
                new_line = line
                for regex, replacement in regexes:
                    new_line = regex.sub(replacement, new_line)
                f_out.write(new_line)
    except Exception as e:
        print(f"Error: {e}")

run()
