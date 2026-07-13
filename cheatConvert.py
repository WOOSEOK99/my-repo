import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import re

class CheatConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MAME Cheat Converter (XML to DAT)")
        self.root.geometry("900x600")
        self.root.minsize(700, 400)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._create_top_frame()
        self._create_main_frame()

    def _create_top_frame(self):
        top_frame = ttk.Frame(self.root)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ttk.Label(top_frame, text="ROM 이름 (예: 1942):", font=("맑은 고딕", 10, "bold")).pack(side="left")
        
        self.rom_name_var = tk.StringVar(value="1942")
        self.rom_entry = ttk.Entry(top_frame, textvariable=self.rom_name_var, width=15)
        self.rom_entry.pack(side="left", padx=10)
        
        convert_btn = ttk.Button(top_frame, text="변환하기 (Convert ➔)", command=self.convert_xml_to_dat)
        convert_btn.pack(side="right")

    def _create_main_frame(self):
        paned_window = ttk.PanedWindow(self.root, orient="horizontal")
        paned_window.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        left_frame = ttk.LabelFrame(paned_window, text="신규 치트 (XML 입력)")
        self.xml_text = tk.Text(left_frame, wrap="none", undo=True, font=("Consolas", 10))
        xml_scroll_y = ttk.Scrollbar(left_frame, orient="vertical", command=self.xml_text.yview)
        xml_scroll_x = ttk.Scrollbar(left_frame, orient="horizontal", command=self.xml_text.xview)
        self.xml_text.configure(yscrollcommand=xml_scroll_y.set, xscrollcommand=xml_scroll_x.set)
        
        xml_scroll_x.pack(side="bottom", fill="x")
        self.xml_text.pack(side="left", fill="both", expand=True)
        xml_scroll_y.pack(side="right", fill="y")
        
        right_frame = ttk.LabelFrame(paned_window, text="구버전 치트 (DAT 결과)")
        self.dat_text = tk.Text(right_frame, wrap="none", undo=True, font=("Consolas", 10), bg="#F0F0F0")
        dat_scroll_y = ttk.Scrollbar(right_frame, orient="vertical", command=self.dat_text.yview)
        dat_scroll_x = ttk.Scrollbar(right_frame, orient="horizontal", command=self.dat_text.xview)
        self.dat_text.configure(yscrollcommand=dat_scroll_y.set, xscrollcommand=dat_scroll_x.set)
        
        dat_scroll_x.pack(side="bottom", fill="x")
        self.dat_text.pack(side="left", fill="both", expand=True)
        dat_scroll_y.pack(side="right", fill="y")
        
        paned_window.add(left_frame, weight=1)
        paned_window.add(right_frame, weight=1)

    def parse_hex_value(self, val_str):
        val_str = val_str.replace("0x", "").replace("0X", "").strip()
        try:
            return str(val_str).upper().zfill(8)
        except:
            return "00000000"

    def extract_action(self, action_text):
        # XML 조건부 구문 제외하고 주소와 값만 정밀 추출
        match = re.search(r"@([0-9A-Fa-f]+)\s*=\s*(.+)", action_text)
        if match:
            addr = match.group(1).upper().zfill(8)
            val = match.group(2).strip()
            return addr, val
        return None, None

    def convert_xml_to_dat(self):
        xml_input = self.xml_text.get("1.0", tk.END).strip()
        rom_name = self.rom_name_var.get().strip()
        
        if not xml_input:
            messagebox.showwarning("경고", "XML 데이터를 입력해주세요.")
            return
            
        # [핵심 수정 1] 첫 번째 '<' 기호를 찾아 그 이전의 브라우저 텍스트 잘라내기
        start_idx = xml_input.find("<")
        if start_idx != -1:
            xml_input = xml_input[start_idx:]
            
        if not xml_input.strip().startswith("<mamecheat"):
            xml_input = f'<mamecheat version="1">\n{xml_input}\n</mamecheat>'
            
        try:
            root = ET.fromstring(xml_input)
            dat_lines = []
            
            # [핵심 수정 2] findall() 대신 iter()를 사용하여 트리의 깊이와 상관없이 모든 cheat 태그 검색
            for cheat in root.iter("cheat"):
                desc = cheat.get("desc", "Unknown").strip()
                if not desc: # <cheat desc=" "/> 같은 빈 태그는 안전하게 패스
                    continue
                    
                params = cheat.find("parameter")
                scripts = cheat.findall("script")
                
                actions = []
                for script in scripts:
                    state = script.get("state")
                    if state in ["run", "on"]:
                        actions.extend([a.text for a in script.findall("action") if a.text])
                
                if not actions:
                    continue
                
                if params is not None:
                    items = params.findall("item")
                    if params.get("min") and params.get("max"):
                        addr, _ = self.extract_action(actions[0])
                        if addr:
                            max_val = self.parse_hex_value(hex(int(params.get("max"))))
                            min_val = self.parse_hex_value(hex(int(params.get("min"))))
                            dat_lines.append(f":{rom_name}:00080300:{addr}:{max_val}:{min_val}:{desc}")
                    
                    elif items:
                        dat_lines.append(f":{rom_name}:62000000:0000:00000000:00000000:{desc}")
                        addr, _ = self.extract_action(actions[0])
                        if addr:
                            for item in items:
                                item_val = self.parse_hex_value(item.get("value"))
                                item_desc = item.text
                                dat_lines.append(f":{rom_name}:00010000:{addr}:{item_val}:FFFFFFFF:{item_desc}")
                else:
                    for i, action_text in enumerate(actions):
                        addr, val = self.extract_action(action_text)
                        # temp0 = maincpu.rd... 같은 변수 대입식은 필터링
                        if addr and val and not action_text.strip().startswith("temp"):
                            val_hex = self.parse_hex_value(val)
                            desc_text = desc if len(actions) == 1 else f"{desc} ({i+1}/{len(actions)})"
                            dat_lines.append(f":{rom_name}:00000000:{addr}:{val_hex}:FFFFFFFF:{desc_text}")
            
            self.dat_text.delete("1.0", tk.END)
            if dat_lines:
                self.dat_text.insert(tk.END, "\n".join(dat_lines))
            else:
                self.dat_text.insert(tk.END, "추출 가능한 유효한 치트 코드가 없습니다.")
            
        except ET.ParseError as e:
            messagebox.showerror("XML 파싱 오류", f"XML 형식이 올바르지 않습니다.\n{e}")
        except Exception as e:
            messagebox.showerror("오류", f"변환 중 오류가 발생했습니다.\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    elif "clam" in style.theme_names():
        style.theme_use("clam")
        
    app = CheatConverterApp(root)
    root.mainloop()