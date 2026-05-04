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
        self.default_base = "https://github.com/WOOSEOK99/my-repo/blob/main/files/"
        self.img_base = "https://raw.githubusercontent.com/WOOSEOK99/my-Images/main/"
        
        # 자동 완성을 위한 사전 정의 데이터
        self.genre_list = ["슈팅", "액션", "벨트스크롤 액션", "격투", "퍼즐", "스포츠", "레이싱"]
        self.dev_list = ["캡콤", "나즈카", "SNK", "세가", "타이토", "코나미", "데이터 이스트"]
        self.series_list = []
        self.parent_list = []
        self.version_var = tk.StringVar(value="Version: -")

        self.setup_ui()
        self.auto_load_default()

    def auto_load_default(self):
        """dist 폴더 기준 support/support_game_list.json 자동 로드"""
        default_path = os.path.join(os.getcwd(), "support", "support_game_list.json")
        if os.path.exists(default_path):
            self.file_path = default_path
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.refresh_series_list()
            self.refresh_parent_list()
            self.update_listbox()
            self.update_version_display()

    def setup_ui(self):
        # 상단 메뉴
        menubar = tk.Menu(self.root)
        menubar.add_command(label="파일 열기", command=self.load_file)
        menubar.add_command(label="저장하기", command=self.save_file)
        self.root.config(menu=menubar)

        # 메인 프레임 (가로 배치 대신 세로 중심 배치로 변경하여 폭을 줄임)
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- 좌측: 리스트박스 (폭 최적화) ---
        list_frame = tk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        self.listbox = tk.Listbox(list_frame, width=25, font=("Malgun Gothic", 9))
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # --- 우측: 편집 및 이미지 (세로로 쌓기) ---
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # [1] 데이터 입력 구역 (격자 배치 최적화)
        edit_frame = tk.LabelFrame(right_frame, text="게임 정보", pady=5)
        edit_frame.pack(fill=tk.X)

        self.entries = {}
        self.bool_vars = {}
        self.current_selected_key = ""

        # URL(파일명) - 가장 상단에 강조
        tk.Label(edit_frame, text="파일명:").grid(row=0, column=0, sticky="e", padx=2)
        url_ent = tk.Entry(edit_frame, fg="blue", font=("Consolas", 10, "bold"), width=45)
        url_ent.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        url_ent.bind("<FocusOut>", self.clean_url_input)
        self.entries["url"] = url_ent

        # 주요 텍스트 필드 (1열 배치로 정리)
        tk.Label(edit_frame, text="title").grid(row=1, column=0, sticky="e", padx=2)
        self.entries["title"] = tk.Entry(edit_frame, width=45)
        self.entries["title"].grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(edit_frame, text="series").grid(row=2, column=0, sticky="e", padx=2)
        self.entries["series"] = ttk.Combobox(edit_frame, values=self.series_list, width=45)
        self.entries["series"].grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        self.entries["series"].set("")

        tk.Label(edit_frame, text="desc").grid(row=3, column=0, sticky="e", padx=2)
        self.entries["desc"] = tk.Entry(edit_frame, width=45)
        self.entries["desc"].grid(row=3, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(edit_frame, text="parent").grid(row=4, column=0, sticky="e", padx=2)
        self.entries["parent"] = ttk.Combobox(edit_frame, values=self.parent_list, width=45)
        self.entries["parent"].grid(row=4, column=1, sticky="ew", padx=5, pady=2)
        self.entries["parent"].set("")

        # 선택형 필드
        tk.Label(edit_frame, text="genre").grid(row=5, column=0, sticky="e", padx=2)
        self.entries["genre"] = ttk.Combobox(edit_frame, values=self.genre_list, width=15)
        self.entries["genre"].grid(row=5, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(edit_frame, text="year").grid(row=6, column=0, sticky="e", padx=2)
        self.entries["year"] = tk.Spinbox(edit_frame, from_=1980, to=2030, width=15)
        self.entries["year"].grid(row=6, column=1, sticky="ew", padx=5, pady=2)

        self.bool_vars["portrait"] = tk.BooleanVar()
        tk.Checkbutton(edit_frame, text="portrait", variable=self.bool_vars["portrait"]).grid(row=7, column=1, sticky="w", padx=5, pady=2)

        tk.Label(edit_frame, text="buttons").grid(row=8, column=0, sticky="e", padx=2)
        self.entries["buttons"] = tk.Spinbox(edit_frame, from_=0, to=8, width=15)
        self.entries["buttons"].grid(row=8, column=1, sticky="ew", padx=5, pady=2)

        self.bool_vars["LRbuttons"] = tk.BooleanVar()
        tk.Checkbutton(edit_frame, text="LRbuttons", variable=self.bool_vars["LRbuttons"]).grid(row=9, column=1, sticky="w", padx=5, pady=2)

        # [2] 이미지 미리보기 (크기를 줄이고 하단 배치)
        img_container = tk.Frame(right_frame, bd=1, relief="sunken", bg="white", height=170)
        img_container.pack(fill=tk.X, pady=5)
        img_container.pack_propagate(False)
        
        # 이미지 크기를 200x200 정도로 제한하여 UI 비대화 방지
        self.img_label = tk.Label(img_container, text="미리보기", bg="white")
        self.img_label.pack(expand=True, fill=tk.BOTH)

        # [3] 하단 버튼 (한 줄로 배치)
        btn_frame = tk.Frame(right_frame)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="새로운게임추가", command=self.add_new_game, bg="#c8e6c9").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="복사", command=self.copy_item, bg="#e1f5fe").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="적용", command=self.apply_changes, bg="#e8f5e9").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="삭제", command=self.delete_item, bg="#ffebee").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # 버전 표시를 우측 프레임 최상단(LabelFrame 위)에 배치하여 항상 보이게 함
        version_frame = tk.Frame(right_frame)
        version_frame.pack(fill=tk.X, pady=(0, 2))
        tk.Label(version_frame, textvariable=self.version_var, font=("Malgun Gothic", 9, "bold"), fg="#1976d2").pack(side=tk.RIGHT)
        
        # [1] 데이터 입력 구역 (격자 배치 최적화)
        edit_frame = tk.LabelFrame(right_frame, text="게임 정보", pady=5)
        edit_frame.pack(fill=tk.X)

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
                self.update_listbox()
                # 입력창 초기화
                for widget in self.entries.values():
                    if isinstance(widget, (tk.Entry, ttk.Combobox, tk.Spinbox)):
                        widget.delete(0, tk.END)
                self.img_label.config(image="", text="미리보기")
                messagebox.showinfo("성공", f"'{selected_key}' 항목이 삭제되었습니다.", parent=self.root)

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

    def on_select(self, event):
        if not self.listbox.curselection(): return
        raw_text = self.listbox.get(self.listbox.curselection())
        selected_key = raw_text.replace("   └─ ", "").strip()
        self.current_selected_key = selected_key
        item_data = self.data.get(selected_key)

        for field, widget in self.entries.items():
            if isinstance(widget, (tk.Entry, ttk.Combobox, tk.Spinbox)):
                widget.delete(0, tk.END)
                widget.insert(0, str(item_data.get(field, "")))
        
        for field in self.bool_vars:
            self.bool_vars[field].set(item_data.get(field, False))

        self.load_image(selected_key)

    def select_listbox_key(self, key):
        for idx in range(self.listbox.size()):
            if self.listbox.get(idx).strip() == key:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(idx)
                self.listbox.see(idx)
                return

    def apply_changes(self):
        """데이터 업데이트 시 URL 형식 확인"""
        if not self.listbox.curselection():
            if not self.current_selected_key:
                return
            selected_key = self.current_selected_key
        else:
            raw_text = self.listbox.get(self.listbox.curselection())
            selected_key = raw_text.replace("   └─ ", "").strip()

        for field, widget in self.entries.items():
            val = widget.get().strip()
            
            # url 필드인데 파일명만 있다면 전체 경로로 보정 후 저장
            if field == "url" and val and not val.startswith("http"):
                import os
                val = f"{self.default_base}{os.path.basename(val)}"
            
            # 숫자형 변환
            if field in ["year", "buttons"] or (isinstance(val, str) and val.isdigit()):
                try: val = int(val)
                except: val = 0
                
            self.data[selected_key][field] = val
        
        for field in self.bool_vars:
            self.data[selected_key][field] = self.bool_vars[field].get()
        
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

    def load_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not self.file_path: return
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.refresh_series_list()
        self.refresh_parent_list()
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
                dest_dir = os.path.join(os.getcwd(), "files")
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
                messagebox.showwarning("경고", f"'{new_key}' 키가 이미 존재합니다.", parent=dialog)
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
            "desc": "",
            "genre": "",
            "series": "",
            "parent": parent_key,
            "year": 0,
            "developer": "",
            "portrait": False,
            "buttons": 0,
            "LRbuttons": False
        }
        self.refresh_series_list()
        self.refresh_parent_list()
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
                
                dest_dir = os.path.join(os.getcwd(), "files")
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
                messagebox.showwarning("경고", f"'{new_key}' 키가 이미 존재합니다.", parent=dialog)
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
            
            self.refresh_series_list()
            self.refresh_parent_list()
            self.update_listbox()
            self.select_listbox_key(new_key)
            self.on_select(None)

    def save_file(self):
        if not self.file_path: return
        
        # 저장 전 데이터 검증: url이 파일명만 있다면 전체 경로로 변환
        for key in self.data:
            url_val = str(self.data[key].get("url", ""))
            if url_val and not url_val.startswith("http"):
                import os
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
        
        self.update_json_version()
        messagebox.showinfo("성공", "파일이 저장되고 updates.json이 갱신되었습니다.", parent=self.root)

    def update_json_version(self):
        """update/updates.json 갱신 및 UI 표시"""
        import datetime
        updates_path = os.path.join(os.getcwd(), "update", "updates.json")
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
        updates_path = os.path.join(os.getcwd(), "update", "updates.json")
        if os.path.exists(updates_path):
            with open(updates_path, 'r', encoding='utf-8') as f:
                try:
                    updates_data = json.load(f)
                    version = updates_data.get("support_game_list.json", "-")
                    self.version_var.set(f"Version: {version}")
                except:
                    self.version_var.set("Version: Error")
        else:
            self.version_var.set("Version: N/A")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("620x520")
    app = GameJsonEditor(root)
    root.mainloop()