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

        self.setup_ui()

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
        
        tk.Button(btn_frame, text="적용", command=self.apply_changes, bg="#e8f5e9").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="복사", command=self.copy_item, bg="#e1f5fe").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="삭제", command=self.delete_item, bg="#ffebee").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        edit_frame.columnconfigure(0, minsize=70)
        edit_frame.columnconfigure(1, weight=1)

    def clean_url_input(self, event):
        """url 입력창에서 포커스가 나갈 때 파일명만 추출"""
        widget = event.widget
        val = widget.get().strip()
        if "/" in val or "\\" in val:
            # 주소나 경로가 포함되어 있다면 파일명만 남김
            filename = os.path.basename(val)
            widget.delete(0, tk.END)
            widget.insert(0, filename)

    def delete_item(self):
        """선택된 게임 항목을 삭제하는 기능"""
        if not self.listbox.curselection():
            messagebox.showwarning("경고", "삭제할 항목을 먼저 선택하세요.")
            return
        
        raw_text = self.listbox.get(self.listbox.curselection())
        selected_key = raw_text.replace("   └─ ", "").strip()
        
        # 삭제 확인 창
        confirm = messagebox.askyesno("삭제 확인", f"'{selected_key}' 항목을 정말로 삭제하시겠습니까?\n(메모리에서 즉시 삭제되며 저장 시 반영됩니다.)")
        
        if confirm:
            if selected_key in self.data:
                del self.data[selected_key]
                self.update_listbox()
                # 입력창 초기화
                for widget in self.entries.values():
                    if isinstance(widget, (tk.Entry, ttk.Combobox, tk.Spinbox)):
                        widget.delete(0, tk.END)
                self.img_label.config(image="", text="미리보기")
                messagebox.showinfo("성공", f"'{selected_key}' 항목이 삭제되었습니다.")

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
        if not self.listbox.curselection(): return
        
        raw_text = self.listbox.get(self.listbox.curselection())
        selected_key = raw_text.replace("   └─ ", "").strip()

        for field, widget in self.entries.items():
            val = widget.get().strip()
            
            # url 필드일 경우 경로가 포함되어 있다면 파일명만 추출
            if field == "url" and ("/" in val or "\\" in val):
                val = os.path.basename(val)
            
            # 숫자 필드 자동 변환 (year, buttons )
            if field in ["year", "buttons "] or val.isdigit():
                try: val = int(val)
                except: val = 0
                
            self.data[selected_key][field] = val
        
        # 불리언 필드 적용
        for field in self.bool_vars:
            self.data[selected_key][field] = self.bool_vars[field].get()

        self.refresh_series_list()
        self.refresh_parent_list()
        self.update_listbox()
        self.select_listbox_key(selected_key)
        messagebox.showinfo("완료", f"'{selected_key}' 데이터가 파일명 중심으로 업데이트되었습니다.")

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
        parents = sorted([k for k, v in self.data.items() if not v.get("parent")])
        clones = sorted([k for k, v in self.data.items() if v.get("parent")])
        for p in parents:
            self.listbox.insert(tk.END, p)
            for c in clones:
                if self.data[c].get("parent") == p:
                    self.listbox.insert(tk.END, f"   └─ {c}")

    def copy_item(self):
        if not self.listbox.curselection(): return
        raw_text = self.listbox.get(self.listbox.curselection())
        source_key = raw_text.replace("   └─ ", "").strip()
        new_key = simpledialog.askstring("복사", "새 Key(ID) 입력:", initialvalue=source_key+"_copy")
        if new_key and new_key not in self.data:
            self.data[new_key] = self.data[source_key].copy()
            self.update_listbox()
            self.select_listbox_key(new_key)
            self.on_select(None)

    def save_file(self):
        if not self.file_path: return
        # 부모-자식 순 정렬 저장
        ordered = {}
        parents = sorted([k for k, v in self.data.items() if not v.get("parent")])
        clones = sorted([k for k, v in self.data.items() if v.get("parent")])
        for p in parents:
            ordered[p] = self.data[p]
            for c in clones:
                if self.data[c].get("parent") == p:
                    ordered[c] = self.data[c]
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(ordered, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("성공", "파일이 저장되었습니다.")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("850x500")
    app = GameJsonEditor(root)
    root.mainloop()