import json
import os
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
import urllib.request
from io import BytesIO
from PIL import Image, ImageTk

class GameJsonEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("EK Launcher - Advanced Editor")
        self.data = {}
        self.file_path = ""
        self.base_dir = self.get_base_dir()
        self.default_base = "https://github.com/WOOSEOK99/my-repo/blob/main/files/"
        self.img_base = "https://raw.githubusercontent.com/WOOSEOK99/my-Images/main/"
        self.marquee_base = "https://wooseok99.github.io/my-mrq/marquee/"
        
        # 자동 완성을 위한 사전 정의 데이터
        self.default_genres = ["슈팅", "액션", "벨트스크롤 액션", "격투", "퍼즐", "스포츠", "레이싱"]
        self.default_devs = ["캡콤", "나즈카", "SNK", "세가", "타이토", "코나미", "데이터 이스트"]
        self.genre_list = list(self.default_genres)
        self.genre_en_list = []
        self.dev_list = list(self.default_devs)
        self.series_list = []
        self.parent_list = []
        self.version_var = tk.StringVar(value="Version: -")
        
        # 검색 관련 상태
        self.search_results = []
        self.current_search_index = -1
        self.search_info_var = tk.StringVar(value="0/0")

        # cheat.dat 관련 상태
        self.cheat_dat_path = os.path.join(self.get_base_dir(), "support", "cheat.dat")
        self.cheat_cache = None  # {romkey: [line, ...]} 캐시 (최초 1회 파싱)

        # command.dat 관련 상태
        self.command_dat_path = os.path.join(self.get_base_dir(), "support", "command.dat")
        self.command_cache = None  # {romkey: str} 캐시 (최초 1회 파싱)
        
        self.newly_added_keys = set()

        self.setup_ui()
        self.bind_paste_cleaning()
        self.auto_load_default()

    def get_base_dir(self):
        import sys
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _normalize_data(self, data):
        """데이터 정규화: 'buttons ' 공백 제거 등"""
        normalized = {}
        if not isinstance(data, dict): return data
        
        for key, val in data.items():
            if isinstance(val, dict):
                # "buttons " 키 처리
                if "buttons " in val:
                    b_val = val.pop("buttons ")
                    if "buttons" not in val or val["buttons"] == 0:
                        val["buttons"] = b_val
                
                # developer 필드 보장
                if "developer" not in val:
                    val["developer"] = ""
                    
            normalized[key] = val
        return normalized

    def auto_load_default(self):
        """실행 파일 기준 support/support_game_list.json 자동 로드"""
        default_path = os.path.join(self.base_dir, "support", "support_game_list.json")
        if os.path.exists(default_path):
            self.file_path = default_path
            with open(self.file_path, 'r', encoding='utf-8-sig') as f:
                raw_data = json.load(f)
            self.data = self._normalize_data(raw_data)
            self.refresh_all_lists()
            self.update_listbox()
            self.update_version_display()

    def setup_ui(self):
        # 상단 메뉴
        menubar = tk.Menu(self.root)
        menubar.add_command(label="파일 열기", command=self.load_file)
        menubar.add_command(label="저장하기", command=self.save_file)
        self.root.config(menu=menubar)

        # 메인 프레임 (3열: 리스트 | 게임정보 | 치트)
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- 1열: 리스트박스 및 검색 ---
        list_frame = tk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        search_frame = tk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.search_entry = tk.Entry(search_frame, width=15)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", self.perform_search)
        
        tk.Button(search_frame, text="Next", command=self.go_next_search, font=("Malgun Gothic", 8)).pack(side=tk.LEFT, padx=2)
        tk.Label(search_frame, textvariable=self.search_info_var, font=("Consolas", 8), width=5).pack(side=tk.LEFT)
        
        self.listbox = tk.Listbox(list_frame, width=25, font=("Malgun Gothic", 9))
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # --- 2열: 게임 정보 편집 ---
        mid_frame = tk.Frame(main_frame)
        mid_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))

        edit_frame = tk.LabelFrame(mid_frame, text="게임 정보", pady=5)
        edit_frame.pack(fill=tk.X)

        self.entries = {}
        self.bool_vars = {}
        self.buttons_var = tk.IntVar(value=0)
        self.current_selected_key = ""

        # Key (ID)
        tk.Label(edit_frame, text="Key (ID):").grid(row=0, column=0, sticky="e", padx=2)
        self.key_entry = tk.Entry(edit_frame, fg="red", font=("Consolas", 10, "bold"), width=35)
        self.key_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        # URL(파일명)
        tk.Label(edit_frame, text="파일명:").grid(row=1, column=0, sticky="e", padx=2)
        url_ent = tk.Entry(edit_frame, fg="blue", font=("Consolas", 10, "bold"), width=35)
        url_ent.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        url_ent.bind("<FocusOut>", self.clean_url_input)
        self.entries["url"] = url_ent

        tk.Label(edit_frame, text="title").grid(row=2, column=0, sticky="e", padx=2)
        self.entries["title"] = tk.Entry(edit_frame, width=35)
        self.entries["title"].grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(edit_frame, text="title_en").grid(row=3, column=0, sticky="e", padx=2)
        self.entries["title_en"] = tk.Entry(edit_frame, width=35)
        self.entries["title_en"].grid(row=3, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(edit_frame, text="series").grid(row=4, column=0, sticky="e", padx=2)
        self.entries["series"] = ttk.Combobox(edit_frame, values=self.series_list, width=35)
        self.entries["series"].grid(row=4, column=1, sticky="ew", padx=5, pady=2)
        self.entries["series"].set("")

        tk.Label(edit_frame, text="series_en").grid(row=5, column=0, sticky="e", padx=2)
        self.entries["series_en"] = tk.Entry(edit_frame, width=35)
        self.entries["series_en"].grid(row=5, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(edit_frame, text="desc").grid(row=6, column=0, sticky="ne", padx=2, pady=2)
        self.entries["desc"] = tk.Text(edit_frame, width=35, height=4)
        self.entries["desc"].grid(row=6, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(edit_frame, text="parent").grid(row=7, column=0, sticky="e", padx=2)
        self.entries["parent"] = ttk.Combobox(edit_frame, values=self.parent_list, width=35)
        self.entries["parent"].grid(row=7, column=1, sticky="ew", padx=5, pady=2)
        self.entries["parent"].set("")

        tk.Label(edit_frame, text="genre").grid(row=8, column=0, sticky="e", padx=2)
        self.entries["genre"] = ttk.Combobox(edit_frame, values=self.genre_list, width=35)
        self.entries["genre"].grid(row=8, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(edit_frame, text="genre_en").grid(row=9, column=0, sticky="e", padx=2)
        self.entries["genre_en"] = ttk.Combobox(edit_frame, values=self.genre_en_list, width=35)
        self.entries["genre_en"].grid(row=9, column=1, sticky="ew", padx=5, pady=2)

        # tk.Label(edit_frame, text="year").grid(row=10, column=0, sticky="e", padx=2)
        self.entries["year"] = tk.Spinbox(edit_frame, from_=1980, to=2030, width=35)
        # self.entries["year"].grid(row=10, column=1, sticky="ew", padx=5, pady=2)

        self.bool_vars["portrait"] = tk.BooleanVar()
        tk.Checkbutton(edit_frame, text="portrait", variable=self.bool_vars["portrait"]).grid(row=10, column=1, sticky="w", padx=5, pady=2)

        tk.Label(edit_frame, text="buttons").grid(row=11, column=0, sticky="e", padx=2)
        btn_chk_frame = tk.Frame(edit_frame)
        btn_chk_frame.grid(row=11, column=1, sticky="w", padx=5, pady=2)
        tk.Checkbutton(btn_chk_frame, text="2", variable=self.buttons_var, onvalue=2, offvalue=0).pack(side=tk.LEFT, padx=2)
        tk.Checkbutton(btn_chk_frame, text="4", variable=self.buttons_var, onvalue=4, offvalue=0).pack(side=tk.LEFT, padx=2)
        tk.Checkbutton(btn_chk_frame, text="6", variable=self.buttons_var, onvalue=6, offvalue=0).pack(side=tk.LEFT, padx=2)

        self.bool_vars["LRbuttons"] = tk.BooleanVar()
        # tk.Checkbutton(edit_frame, text="LRbuttons(6버튼일때 R1 L1 사용)", variable=self.bool_vars["LRbuttons"]).grid(row=12, column=1, sticky="w", padx=5, pady=2)

        # tk.Label(edit_frame, text="developer").grid(row=13, column=0, sticky="e", padx=2)
        self.entries["developer"] = ttk.Combobox(edit_frame, values=self.dev_list, width=35)
        # self.entries["developer"].grid(row=13, column=1, sticky="ew", padx=5, pady=2)

        # 이미지 미리보기
        img_container = tk.Frame(mid_frame, bd=1, relief="sunken", bg="white", height=170)
        img_container.pack(fill=tk.X, pady=5)
        img_container.pack_propagate(False)
        self.img_label = tk.Label(img_container, text="미리보기", bg="white")
        self.img_label.pack(expand=True, fill=tk.BOTH)

        # 마키 이미지 미리보기
        marquee_container = tk.Frame(mid_frame, bd=1, relief="sunken", bg="black", height=80)
        marquee_container.pack(fill=tk.X, pady=(0, 5))
        marquee_container.pack_propagate(False)
        self.marquee_label = tk.Label(marquee_container, text="마키 이미지", bg="black", fg="white")
        self.marquee_label.pack(expand=True, fill=tk.BOTH)

        # 버전 + 하단 버튼
        version_frame = tk.Frame(mid_frame)
        version_frame.pack(fill=tk.X, pady=(0, 2))
        tk.Label(version_frame, textvariable=self.version_var, font=("Malgun Gothic", 9, "bold"), fg="#1976d2").pack(side=tk.RIGHT)

        btn_frame = tk.Frame(mid_frame)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="새로운게임추가", command=self.add_new_game, bg="#c8e6c9").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="복사", command=self.copy_item, bg="#e1f5fe").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="적용", command=self.apply_changes, bg="#e8f5e9").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="삭제", command=self.delete_item, bg="#ffebee").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        #batch_btn_frame = tk.Frame(mid_frame)
        #batch_btn_frame.pack(fill=tk.X, pady=(2, 0))
        #tk.Button(batch_btn_frame, text="모든 year=0", command=self.batch_set_year, bg="#fff3e0").#pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        #tk.Button(batch_btn_frame, text="모든 developer=''", command=self.batch_set_dev, #bg="#e0f7fa").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # --- 3열: Cheat Data ---
        cheat_frame = tk.LabelFrame(main_frame, text="Cheat Data", pady=5)
        cheat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 치트 텍스트 + 스크롤바
        cheat_text_frame = tk.Frame(cheat_frame)
        cheat_text_frame.pack(fill=tk.BOTH, expand=True)

        self.cheat_text = tk.Text(
            cheat_text_frame,
            font=("Consolas", 9),
            wrap=tk.NONE,
            undo=True,
        )
        cheat_yscroll = tk.Scrollbar(cheat_text_frame, command=self.cheat_text.yview)
        cheat_xscroll = tk.Scrollbar(cheat_text_frame, orient=tk.HORIZONTAL, command=self.cheat_text.xview)
        self.cheat_text.configure(yscrollcommand=cheat_yscroll.set, xscrollcommand=cheat_xscroll.set)

        cheat_yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        cheat_xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.cheat_text.pack(fill=tk.BOTH, expand=True)

        # Cheat 찾기/바꾸기 프레임
        cheat_replace_frame = tk.Frame(cheat_frame)
        cheat_replace_frame.pack(fill=tk.X, pady=(2, 0))
        
        tk.Label(cheat_replace_frame, text="찾을문자:", font=("Malgun Gothic", 8)).pack(side=tk.LEFT)
        self.cheat_find_entry = tk.Entry(cheat_replace_frame, width=8)
        self.cheat_find_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        tk.Label(cheat_replace_frame, text="바꿀문자:", font=("Malgun Gothic", 8)).pack(side=tk.LEFT)
        self.cheat_replace_entry = tk.Entry(cheat_replace_frame, width=8)
        self.cheat_replace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        tk.Button(
            cheat_replace_frame, 
            text="모두변경", 
            command=self.cheat_replace_all, 
            bg="#f0f0f0", 
            font=("Malgun Gothic", 8)
        ).pack(side=tk.LEFT, padx=2)

        # 저장 버튼
        cheat_btn_frame = tk.Frame(cheat_frame)
        cheat_btn_frame.pack(fill=tk.X, pady=(4, 0))
        tk.Button(
            cheat_btn_frame,
            text="검색",
            command=self.open_cheat_search,
            bg="#f0f0f0",
            font=("Malgun Gothic", 9)
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(
            cheat_btn_frame,
            text="cheat.dat 저장",
            command=self.save_cheat_dat,
            bg="#fff9c4",
            font=("Malgun Gothic", 9, "bold")
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # --- 4열: Command Data ---
        cmd_frame = tk.LabelFrame(main_frame, text="Command Data", pady=5)
        cmd_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cmd_text_frame = tk.Frame(cmd_frame)
        cmd_text_frame.pack(fill=tk.BOTH, expand=True)

        self.command_text = tk.Text(
            cmd_text_frame,
            font=("Consolas", 9),
            wrap=tk.NONE,
            undo=True,
        )
        cmd_yscroll = tk.Scrollbar(cmd_text_frame, command=self.command_text.yview)
        cmd_xscroll = tk.Scrollbar(cmd_text_frame, orient=tk.HORIZONTAL, command=self.command_text.xview)
        self.command_text.configure(yscrollcommand=cmd_yscroll.set, xscrollcommand=cmd_xscroll.set)

        cmd_yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        cmd_xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.command_text.pack(fill=tk.BOTH, expand=True)

        cmd_btn_frame = tk.Frame(cmd_frame)
        cmd_btn_frame.pack(fill=tk.X, pady=(4, 0))
        tk.Button(
            cmd_btn_frame,
            text="검색",
            command=self.open_command_search,
            bg="#f0f0f0",
            font=("Malgun Gothic", 9)
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        tk.Button(
            cmd_btn_frame,
            text="command.dat 저장",
            command=self.save_command_dat,
            bg="#e8f4ff",
            font=("Malgun Gothic", 9, "bold")
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
    def bind_paste_cleaning(self):
        """모든 입력 위젯에 붙여넣기 클리닝 바인딩"""
        widgets = [self.key_entry, self.cheat_text, self.command_text] + list(self.entries.values())
        for w in widgets:
            if getattr(w, "bind", None):
                w.bind("<Control-v>", self.on_paste)
                w.bind("<Shift-Insert>", self.on_paste)

    def on_paste(self, event):
        """붙여넣기 시 '출처' 이후 문구 자동 제거 및 줄바꿈 보정"""
        try:
            text = self.root.clipboard_get()
            if "출처" in text:
                text = text.split("출처")[0].strip()
            
            # 윈도우/맥/웹 등에서 복사한 줄바꿈 문자를 표준 \n으로 강제 통일
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            
            widget = event.widget
            if isinstance(widget, tk.Text):
                try: widget.delete("sel.first", "sel.last")
                except: pass
                widget.insert(tk.INSERT, text)
            elif isinstance(widget, (tk.Entry, ttk.Combobox, tk.Spinbox)):
                # 한 줄 입력창인 경우 붙여넣을 때 줄바꿈을 공백으로 교체 (한줄로 쭉 이어지게 방어)
                text = text.replace("\n", " ").strip()
                try: widget.delete("sel.first", "sel.last")
                except: pass
                widget.insert(tk.INSERT, text)
            
            return "break" # 기본 붙여넣기 동작 방지
        except:
            pass # 클립보드가 비어있거나 오류 시 기본 동작 수행

    def clean_url_input(self, event):
        """파일명만 입력하면 전체 경로로 자동 완성 (붙여넣기 대응)"""
        widget = event.widget
        val = widget.get().strip()
        if val and not val.startswith("http"):
            # 입력된 값이 파일명뿐이라면 기본 경로를 앞에 붙임
            import os
            filename = os.path.basename(val)
            full_url = f"{self.default_base}{filename}"
            widget.delete(0, tk.END)
            widget.insert(0, full_url)

    def delete_item(self):
        """선택된 게임 항목을 삭제하는 기능"""
        if not self.listbox.curselection():
            messagebox.showwarning("경고", "삭제할 항목을 먼저 선택하세요.")
            return
        
        raw_text = self.listbox.get(self.listbox.curselection())
        selected_key = raw_text.replace("   └─ ", "").strip()
        
        # 삭제 확인 창
        confirm = messagebox.askyesno("삭제 확인", f"'{selected_key}' 항목을 정말로 삭제하시겠습니까?\n(메모리에서 즉시 삭제되며 저장 시 반영됩니다.)", parent=self.root)
        
        if confirm:
            if selected_key in self.data:
                del self.data[selected_key]
                if selected_key in self.newly_added_keys:
                    self.newly_added_keys.remove(selected_key)
                self.update_listbox()
                # 입력창 초기화
                self.key_entry.delete(0, tk.END)
                for widget in self.entries.values():
                    if isinstance(widget, (tk.Entry, ttk.Combobox, tk.Spinbox)):
                        widget.delete(0, tk.END)
                    elif isinstance(widget, tk.Text):
                        widget.delete("1.0", tk.END)
                self.buttons_var.set(0)
                self.img_label.config(image="", text="미리보기")
                self.marquee_label.config(image="", text="마키 이미지")
                messagebox.showinfo("성공", f"'{selected_key}' 항목이 삭제되었습니다.", parent=self.root)

    def batch_set_year(self):
        """임시 버튼: 모든 항목의 year를 0으로 일괄 설정"""
        confirm = messagebox.askyesno("일괄 처리", "모든 게임의 year 값을 0으로 변경하시겠습니까?", parent=self.root)
        if confirm:
            count = 0
            for key in self.data:
                self.data[key]["year"] = 0
                count += 1
            if self.current_selected_key and "year" in self.entries:
                self.entries["year"].delete(0, tk.END)
                self.entries["year"].insert(0, "0")
            messagebox.showinfo("완료", f"총 {count}개의 항목이 year=0으로 변경되었습니다.\n메뉴에서 '저장하기'를 눌러 파일에 반영하세요.", parent=self.root)

    def batch_set_dev(self):
        """임시 버튼: 모든 항목의 developer를 ''로 일괄 설정"""
        confirm = messagebox.askyesno("일괄 처리", "모든 게임의 developer 값을 비우시겠습니까?", parent=self.root)
        if confirm:
            count = 0
            for key in self.data:
                self.data[key]["developer"] = ""
                count += 1
            if self.current_selected_key and "developer" in self.entries:
                if isinstance(self.entries["developer"], ttk.Combobox):
                    self.entries["developer"].set("")
                else:
                    self.entries["developer"].delete(0, tk.END)
            self.refresh_developer_list()
            messagebox.showinfo("완료", f"총 {count}개의 항목이 developer=''로 변경되었습니다.\n메뉴에서 '저장하기'를 눌러 파일에 반영하세요.", parent=self.root)

    def load_image(self, key):
        """GitHub에서 이미지를 가져와서 UI 크기에 맞게 조절"""
        try:
            img_url = f"{self.img_base}{key}.png"
            with urllib.request.urlopen(img_url) as url:
                img_data = url.read()
            
            img = Image.open(BytesIO(img_data))
            
            # UI가 커지는 것을 막기 위해 최대 크기를 200x150 정도로 제한
            # 슬림한 UI를 원하신다면 이 수치를 더 줄이셔도 됩니다.
            img.thumbnail((250, 150)) 
            
            self.photo = ImageTk.PhotoImage(img)
            self.img_label.config(image=self.photo, text="")
        except:
            # 이미지가 없거나 로드 실패 시 공간을 최소화
            self.img_label.config(image="", text="이미지 없음")

    def load_marquee_image(self, key):
        """GitHub에서 마키 이미지를 가져와서 UI 크기에 맞게 조절"""
        try:
            marquee_url = f"{self.marquee_base}{key}.png"
            with urllib.request.urlopen(marquee_url) as url:
                img_data = url.read()
            
            img = Image.open(BytesIO(img_data))
            
            # 마키 이미지의 특성에 맞게 가로로 길게 조절
            img.thumbnail((350, 75)) 
            
            self.marquee_photo = ImageTk.PhotoImage(img)
            self.marquee_label.config(image=self.marquee_photo, text="")
        except:
            self.marquee_label.config(image="", text="마키 없음")

    def perform_search(self, event=None):
        """Key(ID) 또는 Title로 검색"""
        query = self.search_entry.get().strip().lower()
        if not query:
            self.search_results = []
            self.current_search_index = -1
            self.search_info_var.set("0/0")
            return

        # 검색 결과 수집 (Key 또는 Title 매칭)
        self.search_results = []
        for key, val in self.data.items():
            title = str(val.get("title", "")).lower()
            if query in key.lower() or query in title:
                self.search_results.append(key)
        
        if self.search_results:
            self.current_search_index = 0
            self.update_search_display()
        else:
            self.current_search_index = -1
            self.search_info_var.set("0/0")
            messagebox.showinfo("검색", "검색 결과가 없습니다.")

    def go_next_search(self):
        """다음 검색 결과로 이동"""
        if not self.search_results:
            return
        
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self.update_search_display()

    def update_search_display(self):
        """현재 검색 결과 선택 및 정보 갱신"""
        idx = self.current_search_index
        total = len(self.search_results)
        self.search_info_var.set(f"{idx + 1}/{total}")
        
        key = self.search_results[idx]
        self.select_listbox_key(key)
        # on_select를 수동으로 호출하여 데이터 로드
        self.on_select(None)

    def select_listbox_key(self, key):
        """Listbox에서 해당 Key(부모/자식 무관)를 찾아 선택"""
        for idx in range(self.listbox.size()):
            lb_text = self.listbox.get(idx).replace("   └─ ", "").strip()
            if lb_text == key:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(idx)
                self.listbox.activate(idx)
                self.listbox.see(idx)
                return

    def on_select(self, event):
        if not self.listbox.curselection(): return
        raw_text = self.listbox.get(self.listbox.curselection())
        selected_key = raw_text.replace("   └─ ", "").strip()
        self.current_selected_key = selected_key
        item_data = self.data.get(selected_key)
        
        self.key_entry.delete(0, tk.END)
        self.key_entry.insert(0, selected_key)

        for field, widget in self.entries.items():
            if isinstance(widget, (tk.Entry, ttk.Combobox, tk.Spinbox)):
                widget.delete(0, tk.END)
                widget.insert(0, str(item_data.get(field, "")))
            elif isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
                text_val = str(item_data.get(field, ""))
                if field == "desc":
                    text_val = text_val.replace("\\n", "\n")
                widget.insert("1.0", text_val)
        
        for field in self.bool_vars:
            self.bool_vars[field].set(item_data.get(field, False))
            
        self.buttons_var.set(int(item_data.get("buttons") or 0))

        self.load_image(selected_key)
        self.load_marquee_image(selected_key)
        self.load_cheat_data(selected_key)
        self.load_command_data(selected_key)

    def apply_changes(self):
        """데이터 업데이트 시 URL 형식 확인"""
        if not self.listbox.curselection():
            if not self.current_selected_key:
                return
            selected_key = self.current_selected_key
        else:
            raw_text = self.listbox.get(self.listbox.curselection())
            selected_key = raw_text.replace("   └─ ", "").strip()

        # Key 변경 처리
        new_key = self.key_entry.get().strip()
        if not new_key:
            messagebox.showwarning("경고", "Key (ID) 값은 비워둘 수 없습니다.", parent=self.root)
            return
            
        if new_key != selected_key:
            if new_key in self.data:
                confirm = messagebox.askyesno("덮어쓰기 확인", f"'{new_key}' 키가 이미 존재합니다. 기존 데이터를 이 내용으로 덮어쓰시겠습니까?", parent=self.root)
                if not confirm:
                    # 원래 Key 값으로 입력칸 복구
                    self.key_entry.delete(0, tk.END)
                    self.key_entry.insert(0, selected_key)
                    return
            # Key 이름 변경
            self.data[new_key] = self.data.pop(selected_key)
            if selected_key in self.newly_added_keys:
                self.newly_added_keys.remove(selected_key)
                self.newly_added_keys.add(new_key)
            # 자식 게임들의 parent 참조 업데이트
            for k, v in self.data.items():
                if v.get("parent") == selected_key:
                    v["parent"] = new_key
            self.current_selected_key = new_key
            selected_key = new_key
            # 목록 갱신
            self.refresh_all_lists()
            self.update_listbox()
            self.select_listbox_key(selected_key)

        for field, widget in self.entries.items():
            if isinstance(widget, tk.Text):
                val = widget.get("1.0", tk.END).strip()
                if field == "desc":
                    # UI의 실제 줄바꿈을 JSON 저장 시 문자열 '\n'으로 자동 변환 (붙여넣기)
                    val = val.replace("\n", "\\n")
            else:
                val = widget.get().strip()
            
            # url 필드인데 파일명만 있다면 전체 경로로 보정 후 저장
            if field == "url" and val and not val.startswith("http"):
                import os
                val = f"{self.default_base}{os.path.basename(val)}"
            
            # 숫자형 변환
            if field in ["year"]:
                try: val = int(val)
                except: val = 0
                
            self.data[selected_key][field] = val
            
        self.data[selected_key]["buttons"] = self.buttons_var.get()
        
        for field in self.bool_vars:
            self.data[selected_key][field] = self.bool_vars[field].get()
        
        self.refresh_all_lists()
        
        self.select_listbox_key(selected_key)
        messagebox.showinfo("완료", "데이터가 전체 경로 형식으로 업데이트되었습니다.", parent=self.root)

    def refresh_series_list(self):
        series_values = sorted({
            str(v.get("series", "")).strip()
            for v in self.data.values()
            if v.get("series")
        })
        self.series_list = series_values
        if "series" in self.entries:
            self.entries["series"]["values"] = self.series_list

    def refresh_parent_list(self):
        parent_values = sorted({
            str(v.get("parent", "")).strip()
            for v in self.data.values()
            if v.get("parent")
        })
        self.parent_list = parent_values
        if "parent" in self.entries:
            self.entries["parent"]["values"] = self.parent_list

    def refresh_genre_list(self):
        genres = set(self.default_genres) # 기존 기본값 유지하며 추가
        for v in self.data.values():
            g = str(v.get("genre", "")).strip()
            if g:
                genres.add(g)
        self.genre_list = sorted(list(genres))
        if "genre" in self.entries:
            self.entries["genre"]["values"] = self.genre_list

    def refresh_genre_en_list(self):
        genres_en = set()
        for v in self.data.values():
            g = str(v.get("genre_en", "")).strip()
            if g:
                genres_en.add(g)
        self.genre_en_list = sorted(list(genres_en))
        if "genre_en" in self.entries:
            self.entries["genre_en"]["values"] = self.genre_en_list

    def refresh_developer_list(self):
        devs = set(self.default_devs) # 기존 기본값 유지하며 추가
        for v in self.data.values():
            d = str(v.get("developer", "")).strip()
            if d:
                devs.add(d)
        self.dev_list = sorted(list(devs))
        if "developer" in self.entries:
            self.entries["developer"]["values"] = self.dev_list

    def refresh_all_lists(self):
        self.refresh_series_list()
        self.refresh_parent_list()
        self.refresh_genre_list()
        self.refresh_genre_en_list()
        self.refresh_developer_list()

    def load_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not self.file_path: return
        with open(self.file_path, 'r', encoding='utf-8-sig') as f:
            raw_data = json.load(f)
        self.data = self._normalize_data(raw_data)
        self.refresh_all_lists()
        self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        parents = [k for k, v in self.data.items() if not v.get("parent")]
        clones = [k for k, v in self.data.items() if v.get("parent")]
        for p in parents:
            self.listbox.insert(tk.END, p)
            for c in clones:
                if self.data[c].get("parent") == p:
                    self.listbox.insert(tk.END, f"   └─ {c}")
        self.update_version_display()

    def add_new_game(self):
        """새로운 게임 항목을 추가하는 기능 (parent 또는 clone)"""
        import random
        import shutil
        import datetime

        # 커스텀 dialog 생성
        dialog = tk.Toplevel(self.root)
        dialog.title("새 게임 추가")
        dialog.geometry("400x200") # 크기를 약간 키움
        dialog.resizable(False, False)
        
        # 다이얼로그를 화면 중앙에 띄우기
        self.root.update_idletasks()
        width = 400
        height = 200
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        dialog.transient(self.root)
        dialog.grab_set()
        
        selected_file_name = tk.StringVar()

        # 게임 ID 입력
        tk.Label(dialog, text="게임 Key(ID):").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        id_entry = tk.Entry(dialog, width=20)
        id_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        id_entry.focus()
        
        # 부모 게임 입력
        tk.Label(dialog, text="부모 게임 Key:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        parent_entry = tk.Entry(dialog, width=20)
        parent_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # 게임파일 추가 버튼
        def pick_game_file():
            source_file = filedialog.askopenfilename(title="게임 파일 선택")
            if source_file:
                # 파일 처리
                dir_name = os.path.dirname(source_file)
                base_name = os.path.basename(source_file)
                name_only, ext = os.path.splitext(base_name)
                
                # 무작위 숫자 생성
                prefix = random.randint(1000, 9999)
                suffix = random.randint(1000, 9999)
                new_filename = f"{prefix}_{name_only}_{suffix}.bin"
                
                # files 폴더가 없으면 생성
                dest_dir = os.path.join(self.base_dir, "files")
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                
                dest_path = os.path.join(dest_dir, new_filename)
                shutil.copy2(source_file, dest_path)
                
                selected_file_name.set(new_filename)
                
                # Key가 비어 있으면 파일 이름(원본)을 기본값으로 제안
                if not id_entry.get():
                    id_entry.insert(0, name_only)
                
                messagebox.showinfo("성공", f"파일이 복사되었습니다: {new_filename}", parent=dialog)

        tk.Button(dialog, text="게임파일 추가", command=pick_game_file).grid(row=2, column=0, padx=10, pady=5, sticky="e")
        tk.Label(dialog, textvariable=selected_file_name, fg="darkgreen", font=("Consolas", 8)).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        result = {"new_key": None, "parent_key": None, "url_file": None}
        
        def on_ok():
            new_key = id_entry.get().strip()
            parent_key = parent_entry.get().strip()
            if not new_key:
                messagebox.showwarning("경고", "게임 Key를 입력하세요.", parent=dialog)
                return
            if new_key in self.data:
                confirm = messagebox.askyesno("덮어쓰기 확인", f"'{new_key}' 키가 이미 존재합니다. 덮어쓰시겠습니까?", parent=dialog)
                if not confirm:
                    return
            if parent_key and parent_key not in self.data:
                messagebox.showwarning("경고", f"'{parent_key}' 부모 게임이 존재하지 않습니다.", parent=dialog)
                return
            result["new_key"] = new_key
            result["parent_key"] = parent_key if parent_key else ""
            result["url_file"] = selected_file_name.get()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # 버튼
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="추가", command=on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="취소", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        self.root.wait_window(dialog)
        
        if not result["new_key"]:
            return
        
        new_key = result["new_key"]
        parent_key = result["parent_key"]
        
        # 기본 템플릿으로 새 게임 추가
        new_url = ""
        if result["url_file"]:
            new_url = f"{self.default_base}{result['url_file']}"

        self.data[new_key] = {
            "url": new_url,
            "title": "",
            "title_en": "",
            "desc": "",
            "genre": "",
            "genre_en": "",
            "series": "",
            "series_en": "",
            "parent": parent_key,
            "year": 0,
            "developer": "",
            "portrait": False,
            "buttons": 0,
            "LRbuttons": False
        }
        self.newly_added_keys.add(new_key)
        self.refresh_all_lists()
        self.update_listbox()
        self.select_listbox_key(new_key)
        self.on_select(None)
        # messagebox.showinfo("성공", f"'{new_key}' 게임이 추가되었습니다.", parent=self.root)

    def copy_item(self):
        """선택된 게임 항목을 복사하여 새로운 항목으로 추가하는 기능"""
        if not self.listbox.curselection():
            messagebox.showwarning("경고", "복사할 항목을 먼저 선택하세요.")
            return
        
        raw_text = self.listbox.get(self.listbox.curselection())
        source_key = raw_text.replace("   └─ ", "").strip()
        
        # 커스텀 dialog 생성
        dialog = tk.Toplevel(self.root)
        dialog.title("게임 복사")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        
        # 다이얼로그를 화면 중앙에 띄우기
        self.root.update_idletasks()
        width = 350
        height = 150
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        dialog.transient(self.root)
        dialog.grab_set()

        # 원본 Key 표시
        tk.Label(dialog, text=f"원본 Key: {source_key}", fg="gray").pack(pady=5)
        
        # 새 Key 입력 프레임
        input_frame = tk.Frame(dialog)
        input_frame.pack(pady=5)
        
        tk.Label(input_frame, text="새 Key(ID):").pack(side=tk.LEFT, padx=5)
        new_key_entry = tk.Entry(input_frame, width=20)
        new_key_entry.pack(side=tk.LEFT, padx=5)
        new_key_entry.insert(0, source_key + "_copy")
        new_key_entry.focus()
        new_key_entry.selection_range(0, tk.END)

        selected_file_name = tk.StringVar()

        # 게임파일 추가 버튼 (add_new_game의 로직과 동일)
        def pick_game_file():
            import random
            import shutil
            source_file = filedialog.askopenfilename(title="게임 파일 선택")
            if source_file:
                base_name = os.path.basename(source_file)
                name_only, ext = os.path.splitext(base_name)
                
                prefix = random.randint(1000, 9999)
                suffix = random.randint(1000, 9999)
                new_filename = f"{prefix}_{name_only}_{suffix}.bin"
                
                dest_dir = os.path.join(self.base_dir, "files")
                os.makedirs(dest_dir, exist_ok=True)
                
                dest_path = os.path.join(dest_dir, new_filename)
                shutil.copy2(source_file, dest_path)
                
                selected_file_name.set(new_filename)
                
                # 새 Key가 기본값(_copy)이면 파일 이름으로 제안
                if new_key_entry.get() == source_key + "_copy":
                    new_key_entry.delete(0, tk.END)
                    new_key_entry.insert(0, name_only)
                
                messagebox.showinfo("성공", f"파일이 복사되었습니다: {new_filename}", parent=dialog)

        file_frame = tk.Frame(dialog)
        file_frame.pack(pady=5)
        tk.Button(file_frame, text="게임파일 추가", command=pick_game_file).pack(side=tk.LEFT, padx=5)
        tk.Label(file_frame, textvariable=selected_file_name, fg="darkgreen", font=("Consolas", 8)).pack(side=tk.LEFT, padx=5)

        result = {"new_key": None, "url_file": None}

        def on_ok():
            new_key = new_key_entry.get().strip()
            if not new_key:
                messagebox.showwarning("경고", "새로운 Key를 입력하세요.", parent=dialog)
                return
            if new_key in self.data:
                confirm = messagebox.askyesno("덮어쓰기 확인", f"'{new_key}' 키가 이미 존재합니다. 덮어쓰시겠습니까?", parent=dialog)
                if not confirm:
                    return
            result["new_key"] = new_key
            result["url_file"] = selected_file_name.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # 버튼 프레임
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="복사", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="취소", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)

        if result["new_key"]:
            new_key = result["new_key"]
            self.data[new_key] = self.data[source_key].copy()
            
            # 파일이 선택된 경우 URL 업데이트
            if result["url_file"]:
                self.data[new_key]["url"] = f"{self.default_base}{result['url_file']}"

            # parent 게임을 복사하면 clone으로 만들고 parent 설정
            if self.data[source_key].get("parent") == "":
                self.data[new_key]["parent"] = source_key
            
            self.newly_added_keys.add(new_key)
            
            self.refresh_all_lists()
            self.update_listbox()
            self.select_listbox_key(new_key)
            self.on_select(None)

    def save_file(self):
        if not self.file_path: return
        
        # 저장 전 데이터 검증: url이 파일명만 있다면 전체 경로로 변환
        for key in self.data:
            url_val = str(self.data[key].get("url", ""))
            if url_val and not url_val.startswith("http"):
                filename = os.path.basename(url_val)
                self.data[key]["url"] = f"{self.default_base}{filename}"

        # 부모-자식 순서 유지
        ordered = {}
        parents = [k for k, v in self.data.items() if not v.get("parent")]
        clones = [k for k, v in self.data.items() if v.get("parent")]
        for p in parents:
            ordered[p] = self.data[p]
            for c in clones:
                if self.data[c].get("parent") == p:
                    ordered[c] = self.data[c]

        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(ordered, f, indent=4, ensure_ascii=False)
        
        if self.newly_added_keys:
            txt_path = os.path.join(self.base_dir, "newly_added_titles.txt")
            with open(txt_path, 'w', encoding='utf-8') as tf:
                for k in self.newly_added_keys:
                    item = self.data.get(k)
                    if item:
                        title_str = item.get('title', '')
                        title_en_str = item.get('title_en', '')
                        tf.write(f"title: {title_str}, title_en: {title_en_str}\n")
            self.newly_added_keys.clear()
        
        self.update_json_version()
        messagebox.showinfo("성공", "파일이 저장되고 updates.json이 갱신됨.\n(새로 추가된 게임 목록은 newly_added_titles.txt에 저장되었습니다.)", parent=self.root)

    def update_json_version(self):
        """update/updates.json 갱신 및 UI 표시"""
        import datetime
        updates_path = os.path.join(self.base_dir, "update", "updates.json")
        if not os.path.exists(updates_path):
            # 파일이 없으면 생성
            updates_data = {"support_game_list.json": ""}
        else:
            with open(updates_path, 'r', encoding='utf-8') as f:
                try:
                    updates_data = json.load(f)
                except:
                    updates_data = {"support_game_list.json": ""}

        today = datetime.datetime.now().strftime("%Y%m%d")
        current_val = str(updates_data.get("support_game_list.json", ""))
        
        new_val = today
        if current_val.startswith(today):
            # 오늘 이미 업데이트된 경우 접미사 숫자를 올림
            if "_" in current_val:
                prefix, count = current_val.split("_")
                try:
                    new_val = f"{today}_{int(count) + 1}"
                except:
                    new_val = f"{today}_1"
            else:
                new_val = f"{today}_1"
        
        updates_data["support_game_list.json"] = new_val
        
        # 폴더가 없으면 생성
        os.makedirs(os.path.dirname(updates_path), exist_ok=True)
        
        with open(updates_path, 'w', encoding='utf-8') as f:
            json.dump(updates_data, f, indent=4)
        
        self.update_version_display()

    def update_version_display(self):
        """UI에 현재 updates.json의 버전 표시"""
        updates_path = os.path.join(self.base_dir, "update", "updates.json")
        game_count = len(self.data) if hasattr(self, 'data') else 0
        if os.path.exists(updates_path):
            with open(updates_path, 'r', encoding='utf-8') as f:
                try:
                    updates_data = json.load(f)
                    version = updates_data.get("support_game_list.json", "-")
                    self.version_var.set(f"Version: {version} (총 게임 수: {game_count})")
                except:
                    self.version_var.set(f"Version: Error (총 게임 수: {game_count})")
        else:
            self.version_var.set(f"Version: N/A (총 게임 수: {game_count})")

    # ------------------------------------------------------------------ #
    #  Cheat.dat 관련 메서드                                               #
    # ------------------------------------------------------------------ #

    def _parse_cheat_dat(self):
        """cheat.dat 전체를 한 번만 파싱하여 {romkey: [lines]} 딕셔너리로 캐시."""
        cache = {}
        if not os.path.exists(self.cheat_dat_path):
            self.cheat_cache = cache
            return
        with open(self.cheat_dat_path, 'r', encoding='euc-kr', errors='replace') as f:
            lines = f.readlines()
        current_key = None
        for line in lines:
            stripped = line.rstrip('\n').rstrip('\r')
            # 치트 엔트리: 첫 문자가 ':' 이고 두 번째 ':' 까지 사이가 romkey
            if stripped.startswith(':'):
                parts = stripped.split(':')
                if len(parts) >= 3:
                    rk = parts[1].lower()
                    if rk not in cache:
                        cache[rk] = []
                    cache[rk].append(line)
                    current_key = rk
            elif stripped.startswith('; [') and current_key is not None:
                # 게임 구분 주석은 해당 키 블록에 포함
                pass
        self.cheat_cache = cache

    def load_cheat_data(self, key):
        """현재 선택된 key의 치트 라인을 Text 위젯에 표시."""
        if self.cheat_cache is None:
            self._parse_cheat_dat()
        self.cheat_text.delete("1.0", tk.END)
        lines = self.cheat_cache.get(key.lower(), [])
        if lines:
            self.cheat_text.insert(tk.END, "".join(lines))
        else:
            self.cheat_text.insert(tk.END, f"; '{key}' 에 대한 치트 데이터가 없습니다.\n")

    def cheat_replace_all(self):
        """Cheat Data 내의 특정 문자열을 일괄 변경"""
        find_str = self.cheat_find_entry.get()
        replace_str = self.cheat_replace_entry.get()
        
        if not find_str:
            messagebox.showwarning("경고", "찾을 문자를 입력하세요.", parent=self.root)
            return
            
        content = self.cheat_text.get("1.0", tk.END)
        # tk.Text가 붙이는 마지막 자동 개행 무시
        if content.endswith("\n"):
            content = content[:-1]
            
        if find_str in content:
            new_content = content.replace(find_str, replace_str)
            self.cheat_text.delete("1.0", tk.END)
            self.cheat_text.insert("1.0", new_content)
            messagebox.showinfo("완료", f"'{find_str}' 문자열이 모두 변경되었습니다.\n\n(아랫방향 '저장' 버튼을 눌러야 파일에 최종 반영됩니다.)", parent=self.root)
        else:
            messagebox.showinfo("결과", f"'{find_str}' 문자열을 찾을 수 없습니다.", parent=self.root)

    def save_cheat_dat(self):
        """Text 위젯의 내용으로 cheat.dat의 해당 key 블록을 교체 후 저장."""
        if not self.current_selected_key:
            messagebox.showwarning("경고", "선택된 게임이 없습니다.", parent=self.root)
            return
        
        new_content = self.cheat_text.get("1.0", tk.END)
        self._save_cheat_dat_internal(self.current_selected_key, new_content, self.root)
        
        self.load_cheat_data(self.current_selected_key)

    def _save_cheat_dat_internal(self, key, new_content, parent_window):
        if not os.path.exists(self.cheat_dat_path):
            messagebox.showerror("오류", f"cheat.dat 파일을 찾을 수 없습니다:\n{self.cheat_dat_path}", parent=parent_window)
            return

        # 빈 문자열이거나 '치트 데이터 없음' 메시지만 있으면 저장하지 않음
        if new_content.strip().startswith("; '") and "치트 데이터가 없습니다" in new_content:
            messagebox.showinfo("안내", "치트 내용이 없습니다. 저장을 건너뜁니다.", parent=parent_window)
            return

        # 원본 파일 읽기
        with open(self.cheat_dat_path, 'r', encoding='euc-kr', errors='replace') as f:
            orig_lines = f.readlines()

        key_lower = key.lower()
        prefix = f":{key_lower}:"

        # key 블록의 첫 줄과 마지막 줄 인덱스 탐색
        start_idx = None
        end_idx = None
        for i, line in enumerate(orig_lines):
            if line.lower().startswith(prefix):
                if start_idx is None:
                    start_idx = i
                end_idx = i

        new_lines_raw = new_content.splitlines(keepends=True)
        # 마지막에 빈 줄이 추가되지 않도록 정리
        if new_lines_raw and new_lines_raw[-1] in ('\n', '\r\n', ''):
            new_lines_raw = new_lines_raw[:-1]

        if start_idx is not None and end_idx is not None:
            # 기존 블록 교체
            result = orig_lines[:start_idx] + new_lines_raw + ['\n'] + orig_lines[end_idx + 1:]
        else:
            # 블록이 없으면 파일 끝에 추가
            result = orig_lines + ['\n'] + new_lines_raw + ['\n']

        with open(self.cheat_dat_path, 'w', encoding='euc-kr', errors='replace') as f:
            f.writelines(result)

        # 캐시 갱신
        self.cheat_cache = None
        self._parse_cheat_dat()

        self.update_cheat_dat_version()
        messagebox.showinfo("성공", "cheat.dat 저장 완료 및 updates.json 갱신되었습니다.", parent=parent_window)

    def update_cheat_dat_version(self):
        """updates.json 의 'cheat.dat' 키 날짜 값을 갱신."""
        import datetime
        updates_path = os.path.join(self.base_dir, "update", "updates.json")
        if os.path.exists(updates_path):
            with open(updates_path, 'r', encoding='utf-8') as f:
                try:
                    updates_data = json.load(f)
                except:
                    updates_data = {}
        else:
            updates_data = {}

        today = datetime.datetime.now().strftime("%Y%m%d")
        current_val = str(updates_data.get("cheat.dat", ""))

        if current_val.startswith(today):
            if "_" in current_val:
                prefix_d, count = current_val.split("_", 1)
                try:
                    new_val = f"{today}_{int(count) + 1}"
                except:
                    new_val = f"{today}_1"
            else:
                new_val = f"{today}_1"
        else:
            new_val = today

        updates_data["cheat.dat"] = new_val
        os.makedirs(os.path.dirname(updates_path), exist_ok=True)
        with open(updates_path, 'w', encoding='utf-8') as f:
            json.dump(updates_data, f, indent=4, ensure_ascii=False)

    # ------------------------------------------------------------------ #
    #  Command.dat 관련 메서드                                              #
    # ------------------------------------------------------------------ #

    def _parse_command_dat(self):
        """command.dat 전체를 한 번만 파싱하여 {romkey: str} 딕셔너리로 캐시.
        구조: $info=rom1,rom2  →  $cmd ... $end  (한 key에 여러 $cmd~$end 가능)
        """
        cache = {}
        if not os.path.exists(self.command_dat_path):
            self.command_cache = cache
            return
        with open(self.command_dat_path, 'r', encoding='euc-kr', errors='replace') as f:
            lines = f.readlines()

        current_keys = []
        buf = []

        for line in lines:
            stripped = line.rstrip('\r\n')
            lower = stripped.lower()

            if lower.startswith('$info='):
                # 이전 키 버퍼 저장
                if current_keys and buf:
                    content = ''.join(buf)
                    for k in current_keys:
                        cache[k] = content
                    buf = []
                current_keys = [k.strip() for k in stripped[6:].split(',')]
                buf.append(line)
            elif current_keys:
                buf.append(line)

        # 마지막 키 처리
        if current_keys and buf:
            content = ''.join(buf)
            for k in current_keys:
                cache[k] = content

        self.command_cache = cache

    def load_command_data(self, key):
        """현재 선택된 key의 $cmd 블록을 Text 위젯에 표시."""
        if self.command_cache is None:
            self._parse_command_dat()
        self.command_text.delete("1.0", tk.END)
        content = self.command_cache.get(key.lower(), "")
        if content:
            self.command_text.insert(tk.END, content)
        else:
            self.command_text.insert(tk.END, f"; '{key}' 에 대한 커맨드 데이터가 없습니다.\n")

    def save_command_dat(self):
        """Text 위젯의 내용으로 command.dat의 해당 key 블록을 교체 후 저장."""
        if not self.current_selected_key:
            messagebox.showwarning("경고", "선택된 게임이 없습니다.", parent=self.root)
            return
            
        new_content = self.command_text.get("1.0", tk.END)
        self._save_command_dat_internal(self.current_selected_key, new_content, self.root)
        
        self.load_command_data(self.current_selected_key)

    def _save_command_dat_internal(self, key, new_content, parent_window):
        if not os.path.exists(self.command_dat_path):
            messagebox.showerror("오류", f"command.dat 파일을 찾을 수 없습니다:\n{self.command_dat_path}", parent=parent_window)
            return

        if new_content.strip().startswith("; '") and "커맨드 데이터가 없습니다" in new_content:
            messagebox.showinfo("안내", "커맨드 내용이 없습니다. 저장을 건너뜁니다.", parent=parent_window)
            return

        with open(self.command_dat_path, 'r', encoding='euc-kr', errors='replace') as f:
            orig_lines = f.readlines()

        key_lower = key.lower()

        # $info=key 콤마 포함하여 검색
        start_idx = None
        for i, line in enumerate(orig_lines):
            stripped_line = line.strip().lower()
            if stripped_line.startswith('$info='):
                keys_in_line = [k.strip() for k in stripped_line[6:].split(',')]
                if key_lower in keys_in_line:
                    start_idx = i
                    break

        # 다음 $info= 를 만나기 직전까지를 한 블록으로 취급
        end_idx = len(orig_lines) - 1
        if start_idx is not None:
            for i in range(start_idx + 1, len(orig_lines)):
                if orig_lines[i].strip().lower().startswith('$info='):
                    end_idx = i - 1
                    break

        new_lines_raw = new_content.splitlines(keepends=True)
        if new_lines_raw and new_lines_raw[-1] in ('\n', '\r\n', ''):
            new_lines_raw = new_lines_raw[:-1]

        if start_idx is not None:
            result = orig_lines[:start_idx] + new_lines_raw + ['\n'] + orig_lines[end_idx + 1:]
        else:
            # 없으면 파일 끝에 추가
            result = orig_lines + ['\n'] + new_lines_raw + ['\n']

        with open(self.command_dat_path, 'w', encoding='euc-kr', errors='replace') as f:
            f.writelines(result)

        # 캐시 갱신
        self.command_cache = None
        self._parse_command_dat()

        self.update_command_dat_version()
        messagebox.showinfo("성공", "command.dat 저장 완료 및 updates.json 갱신되었습니다.", parent=parent_window)

    def update_command_dat_version(self):
        """updates.json 의 'command.dat' 키 날짜 값을 갱신."""
        import datetime
        updates_path = os.path.join(self.base_dir, "update", "updates.json")
        if os.path.exists(updates_path):
            with open(updates_path, 'r', encoding='utf-8') as f:
                try:
                    updates_data = json.load(f)
                except:
                    updates_data = {}
        else:
            updates_data = {}

        today = datetime.datetime.now().strftime("%Y%m%d")
        current_val = str(updates_data.get("command.dat", ""))

        if current_val.startswith(today):
            if "_" in current_val:
                prefix_d, count = current_val.split("_", 1)
                try:
                    new_val = f"{today}_{int(count) + 1}"
                except:
                    new_val = f"{today}_1"
            else:
                new_val = f"{today}_1"
        else:
            new_val = today

        updates_data["command.dat"] = new_val
        os.makedirs(os.path.dirname(updates_path), exist_ok=True)
        with open(updates_path, 'w', encoding='utf-8') as f:
            json.dump(updates_data, f, indent=4, ensure_ascii=False)

    # ------------------------------------------------------------------ #
    #  검색 다이얼로그 (Cheat / Command 공용)                             #
    # ------------------------------------------------------------------ #

    def open_cheat_search(self):
        self._open_dat_search("cheat.dat 검색", "cheat_cache", self._parse_cheat_dat)

    def open_command_search(self):
        self._open_dat_search("command.dat 검색", "command_cache", self._parse_command_dat)

    def _open_dat_search(self, title, cache_attr, parse_method):
        cache = getattr(self, cache_attr)
        if cache is None:
            parse_method()
            cache = getattr(self, cache_attr)

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("600x400")
        
        self.root.update_idletasks()
        width = 600
        height = 400
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        dialog.transient(self.root)
        
        top_frame = tk.Frame(dialog)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(top_frame, text="Key 검색:").pack(side=tk.LEFT)
        search_entry = tk.Entry(top_frame, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.focus()
        
        text_frame = tk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        result_text = tk.Text(text_frame, font=("Consolas", 9), wrap=tk.NONE, undo=True)
        yscroll = tk.Scrollbar(text_frame, command=result_text.yview)
        xscroll = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=result_text.xview)
        result_text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        result_text.pack(fill=tk.BOTH, expand=True)
        
        current_search_key = {"key": None}
        
        def do_search(*args):
            query = search_entry.get().strip().lower()
            result_text.delete("1.0", tk.END)
            if not query:
                current_search_key["key"] = None
                return
            
            current_search_key["key"] = query
            content = ""
            if "cheat" in cache_attr:
                lines = cache.get(query, [])
                if lines:
                    content = "".join(lines)
            else:
                content = cache.get(query, "")
                
            if content:
                result_text.insert(tk.END, content)
            else:
                if "cheat" in cache_attr:
                    result_text.insert(tk.END, f"; '{query}' 에 대한 치트 데이터가 없습니다.\n")
                else:
                    result_text.insert(tk.END, f"; '{query}' 에 대한 커맨드 데이터가 없습니다.\n")
                
        def do_save(*args):
            q = current_search_key["key"]
            if not q:
                messagebox.showwarning("경고", "먼저 검색을 통해 대상을 지정해주세요.", parent=dialog)
                return
                
            new_content = result_text.get("1.0", tk.END)
            if "cheat" in cache_attr:
                self._save_cheat_dat_internal(q, new_content, dialog)
                if getattr(self, "current_selected_key", None) == q:
                    self.load_cheat_data(q)
            else:
                self._save_command_dat_internal(q, new_content, dialog)
                if getattr(self, "current_selected_key", None) == q:
                    self.load_command_data(q)
                
        search_entry.bind("<Return>", do_search)
        tk.Button(top_frame, text="검색", command=do_search).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="저장", command=do_save, bg="#fff9c4", font=("Malgun Gothic", 9, "bold")).pack(side=tk.LEFT, padx=5)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1450x700")
    app = GameJsonEditor(root)
    root.mainloop()