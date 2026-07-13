import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("고급 파일 검색 시스템")
        self.root.geometry("850x650")
        self.root.minsize(600, 400)
        
        # 전체 레이아웃의 크기 조절(Resizing) 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)  # 결과창 영역이 늘어나도록 설정

        self._create_folder_frame()
        self._create_search_frame()
        self._create_result_frame()
        self._create_context_menu()

    def _create_folder_frame(self):
        """폴더 선택 및 리스트 UI 구성"""
        folder_frame = ttk.LabelFrame(self.root, text="탐색할 폴더 목록 (다중 선택 가능)")
        folder_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        folder_frame.columnconfigure(0, weight=1)

        # 리스트박스 및 스크롤바
        list_scroll = ttk.Scrollbar(folder_frame, orient="vertical")
        self.folder_listbox = tk.Listbox(folder_frame, height=4, selectmode=tk.EXTENDED, yscrollcommand=list_scroll.set)
        list_scroll.config(command=self.folder_listbox.yview)
        
        self.folder_listbox.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        list_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)

        # 버튼 프레임
        btn_frame = ttk.Frame(folder_frame)
        btn_frame.grid(row=0, column=2, sticky="ns", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="폴더 추가", command=self.add_folder).pack(fill="x", pady=(0, 5))
        ttk.Button(btn_frame, text="선택 삭제", command=self.remove_folder).pack(fill="x")

    def _create_search_frame(self):
        """검색어 입력 및 옵션 UI 구성"""
        search_frame = ttk.LabelFrame(self.root, text="검색 조건")
        search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="파일 이름:").grid(row=0, column=0, padx=10, pady=15)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=15)
        self.search_entry.bind("<Return>", lambda event: self.search_files()) # 엔터키 지원

        self.exact_match_var = tk.BooleanVar(value=False)
        exact_check = ttk.Checkbutton(
            search_frame, 
            text="100% 일치 (확장자 제외 이름 또는 전체 이름 일치)", 
            variable=self.exact_match_var
        )
        exact_check.grid(row=0, column=2, padx=15, pady=15)

        search_btn = ttk.Button(search_frame, text="검색 (Search)", command=self.search_files)
        search_btn.grid(row=0, column=3, padx=10, pady=15)

    def _create_result_frame(self):
        """검색 결과 트리뷰(표) UI 구성"""
        result_frame = ttk.LabelFrame(self.root, text="검색 결과")
        result_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        # Treeview 구성
        columns = ("name", "path", "size")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings")
        self.tree.heading("name", text="파일 이름", anchor="w")
        self.tree.heading("path", text="폴더 경로", anchor="w")
        self.tree.heading("size", text="크기", anchor="e")

        self.tree.column("name", width=250, minwidth=150)
        self.tree.column("path", width=450, minwidth=200)
        self.tree.column("size", width=100, minwidth=80, anchor="e")

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)

        # 스크롤바
        tree_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=tree_scroll.set)
        tree_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)

        # 하단 상태 표시줄
        self.status_var = tk.StringVar(value="대기 중...")
        ttk.Label(result_frame, textvariable=self.status_var, foreground="gray").grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))

        # 이벤트 바인딩 (더블 클릭 및 우클릭)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu) # 우클릭

    def _create_context_menu(self):
        """우클릭 컨텍스트 메뉴 구성"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="열기 (Double Click)", command=self.open_selected)
        self.context_menu.add_command(label="파일 위치 열기", command=self.open_location)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="복사 (탐색기 붙여넣기용)", command=self.copy_selected)
        self.context_menu.add_command(label="삭제 (Delete)", command=self.delete_selected)

    # ==========================
    # 기능 구현 메서드
    # ==========================

    def add_folder(self):
        """폴더 브라우저를 통해 폴더 추가 (중복 방지)"""
        folder = filedialog.askdirectory(title="검색할 폴더 선택")
        if folder:
            existing_folders = self.folder_listbox.get(0, tk.END)
            if folder not in existing_folders:
                self.folder_listbox.insert(tk.END, folder)

    def remove_folder(self):
        """선택된 폴더 목록에서 제거"""
        selected_indices = self.folder_listbox.curselection()
        for index in reversed(selected_indices):
            self.folder_listbox.delete(index)

    def search_files(self):
        """지정된 조건으로 파일 검색"""
        # 기존 결과 초기화
        for item in self.tree.get_children():
            self.tree.delete(item)

        folders = self.folder_listbox.get(0, tk.END)
        if not folders:
            messagebox.showwarning("경고", "탐색할 폴더를 하나 이상 추가해주세요.")
            return

        search_term = self.search_var.get().strip().lower()
        if not search_term:
            messagebox.showwarning("경고", "검색할 파일 이름을 입력해주세요.")
            return

        exact_match = self.exact_match_var.get()
        self.status_var.set("검색 중...")
        self.root.update()

        found_count = 0
        for folder in folders:
            if not os.path.isdir(folder):
                continue
            
            for root_dir, _, files in os.walk(folder):
                for filename in files:
                    file_lower = filename.lower()
                    name_without_ext = os.path.splitext(file_lower)[0]

                    is_match = False
                    if exact_match:
                        # 100% 일치: 확장자를 포함한 전체 이름이 같거나, 확장자 제외 이름이 같은 경우
                        if search_term == file_lower or search_term == name_without_ext:
                            is_match = True
                    else:
                        # 부분 일치
                        if search_term in file_lower:
                            is_match = True

                    if is_match:
                        full_path = os.path.join(root_dir, filename)
                        try:
                            size_kb = os.path.getsize(full_path) / 1024
                            size_str = f"{size_kb:,.1f} KB"
                        except OSError:
                            size_str = "알 수 없음"
                        
                        self.tree.insert("", tk.END, values=(filename, root_dir, size_str))
                        found_count += 1

        self.status_var.set(f"검색 완료: 총 {found_count}개의 파일을 찾았습니다.")

    # ==========================
    # 파일 제어 및 컨텍스트 메뉴 메서드
    # ==========================

    def get_selected_filepath(self):
        """트리뷰에서 선택된 파일의 전체 절대 경로 반환"""
        selected = self.tree.selection()
        if not selected:
            return None
        item = self.tree.item(selected[0])
        filename = item['values'][0]
        directory = item['values'][1]
        return os.path.normpath(os.path.join(directory, filename))

    def show_context_menu(self, event):
        """우클릭 시 선택 항목 강제 지정 후 메뉴 표시"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def on_double_click(self, event):
        """더블 클릭 이벤트 (컬럼 리사이징 영역 클릭 시 무시)"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        self.open_selected()

    def open_selected(self):
        """파일 열기 (OS 기본 프로그램 연결)"""
        filepath = self.get_selected_filepath()
        if filepath and os.path.exists(filepath):
            try:
                if sys.platform == "win32":
                    os.startfile(filepath)
                else:
                    subprocess.call(('open', filepath))
            except Exception as e:
                messagebox.showerror("오류", f"파일을 열 수 없습니다:\n{e}")

    def open_location(self):
        """탐색기를 열고 해당 파일이 위치한 곳을 하이라이트"""
        filepath = self.get_selected_filepath()
        if filepath and os.path.exists(filepath):
            if sys.platform == "win32":
                subprocess.Popen(f'explorer /select,"{filepath}"')
            else:
                subprocess.call(('open', '-R', filepath))

    def copy_selected(self):
        """
        [전문가 팁] 파이썬 내장 기능만으로 탐색기 파일 복사 구현
        PowerShell 명령을 호출하여 파일 오브젝트 자체를 클립보드에 삽입합니다.
        """
        filepath = self.get_selected_filepath()
        if not filepath or not os.path.exists(filepath):
            return

        if sys.platform == "win32":
            # 파일 경로를 PowerShell Set-Clipboard로 전달하여 '파일 복사' 상태 생성
            cmd = f'powershell.exe -command "Set-Clipboard -Path \'{filepath}\'"'
            creation_flags = 0x08000000 # CREATE_NO_WINDOW (콘솔창 숨김)
            try:
                subprocess.run(cmd, shell=True, creationflags=creation_flags)
                self.status_var.set(f"클립보드에 복사됨 (Ctrl+V로 붙여넣기 가능): {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("복사 오류", str(e))
        else:
            # Mac/Linux의 경우 텍스트(경로) 복사로 대체
            self.root.clipboard_clear()
            self.root.clipboard_append(filepath)
            self.status_var.set("경로가 클립보드에 복사되었습니다.")

    def delete_selected(self):
        """파일 삭제 로직"""
        filepath = self.get_selected_filepath()
        if filepath and os.path.exists(filepath):
            filename = os.path.basename(filepath)
            if messagebox.askyesno("삭제 확인", f"'{filename}' 파일을 완전히 삭제하시겠습니까?\n(휴지통으로 가지 않고 영구 삭제됩니다)"):
                try:
                    os.remove(filepath)
                    selected = self.tree.selection()
                    self.tree.delete(selected[0])
                    self.status_var.set(f"삭제 완료: {filename}")
                except Exception as e:
                    messagebox.showerror("삭제 오류", f"파일을 삭제할 수 없습니다:\n{e}")

if __name__ == "__main__":
    # Windows에서 흐릿하게 나오는 현상 방지 (DPI 인지 활성화)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    
    # OS별 네이티브 테마 적용 (깔끔한 UI)
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    elif "clam" in style.theme_names():
        style.theme_use("clam")

    app = FileSearchApp(root)
    root.mainloop()