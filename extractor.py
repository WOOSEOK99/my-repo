import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class GameDataExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("부모 롬(Parent Rom) 추출기")
        self.root.geometry("750x550")
        
        # 추출된 데이터를 저장할 리스트
        self.extracted_data = []

        # --- UI 레이아웃 구성 ---
        
        # 1. 상단: 폴더 선택 영역
        frame_top = tk.Frame(self.root, pady=10, padx=10)
        frame_top.pack(fill=tk.X)

        self.lbl_folder = tk.Label(frame_top, text="선택된 폴더: 없음", width=55, anchor="w", bg="white", relief="sunken")
        self.lbl_folder.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        btn_browse = tk.Button(frame_top, text="폴더 찾기", command=self.select_folder)
        btn_browse.pack(side=tk.LEFT)

        btn_extract = tk.Button(frame_top, text="추출 시작", command=self.start_extraction, bg="#4CAF50", fg="white", font=("", 10, "bold"))
        btn_extract.pack(side=tk.LEFT, padx=(10, 0))

        # 2. 상단 2: 제외 필터링 입력 영역
        frame_filter = tk.Frame(self.root, pady=5, padx=10)
        frame_filter.pack(fill=tk.X)

        lbl_exclude = tk.Label(frame_filter, text="제외할 키워드 (쉼표 ','로 구분):", font=("", 9, "bold"))
        lbl_exclude.pack(side=tk.LEFT, padx=(0, 5))

        self.ent_exclude = tk.Entry(frame_filter, width=50)
        self.ent_exclude.insert(0, "GAME_NOT_WORKING,GAME_NO_SOUND,GAME_UNEMULATED_PROTECTION")
        self.ent_exclude.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 3. 중단: 결과 출력 텍스트 영역
        frame_mid = tk.Frame(self.root, padx=10, pady=5)
        frame_mid.pack(fill=tk.BOTH, expand=True)

        self.txt_result = scrolledtext.ScrolledText(frame_mid, wrap=tk.WORD, font=("Consolas", 10))
        self.txt_result.pack(fill=tk.BOTH, expand=True)

        # 4. 하단: 저장 및 종료 버튼 영역
        frame_bottom = tk.Frame(self.root, pady=10, padx=10)
        frame_bottom.pack(fill=tk.X)

        btn_save = tk.Button(frame_bottom, text="결과를 텍스트 파일로 저장", command=self.save_to_file)
        btn_save.pack(side=tk.LEFT)

        btn_exit = tk.Button(frame_bottom, text="종료", command=self.root.quit)
        btn_exit.pack(side=tk.RIGHT)

        # 내부 상태 변수
        self.target_folder = ""

    def select_folder(self):
        """폴더 선택 대화상자를 엽니다."""
        folder_path = filedialog.askdirectory(title="탐색할 폴더를 선택하세요")
        if folder_path:
            self.target_folder = folder_path
            self.lbl_folder.config(text=f"선택된 폴더: {self.target_folder}")

    def start_extraction(self):
        """폴더에서 데이터를 추출하고, 3번째 인자가 0인 경우만 2번째 인자를 출력합니다."""
        if not self.target_folder:
            messagebox.showwarning("경고", "먼저 대상 폴더를 선택해주세요.")
            return

        exclude_input = self.ent_exclude.get()
        exclude_keywords = [kw.strip() for kw in exclude_input.split(",") if kw.strip()]

        self.txt_result.delete(1.0, tk.END)
        self.txt_result.insert(tk.END, f"추출을 시작합니다... (제외 키워드: {exclude_keywords})\n\n")
        self.root.update()

        self.extracted_data = []
        pattern = re.compile(r'(GAME|GAMEX|GAMEC)\s*\((.*?)\)')
        
        file_count = 0
        match_count = 0
        filtered_count = 0
        ignored_count = 0 # 3번째 인자가 0이 아니라서 건너뛴 개수

        for root_dir, dirs, files in os.walk(self.target_folder):
            for file in files:
                file_path = os.path.join(root_dir, file)
                file_count += 1
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        
                        for game_type, data in matches:
                            # 1. 제외 키워드 필터링
                            if any(kw in data for kw in exclude_keywords):
                                filtered_count += 1
                                continue
                            
                            # 2. 쉼표(,)를 기준으로 인자값 분리
                            args = data.split(',')
                            
                            # 인자가 3개 이상인지 확인 (안전성 검사)
                            if len(args) >= 3:
                                # 파이썬 리스트는 0부터 시작하므로 인덱스 1이 두번째, 2가 세번째 인자입니다.
                                rom_name = args[1].strip()
                                is_parent = args[2].strip()
                                
                                # 3. 세 번째 인자가 '0'인지 확인
                                if is_parent == '0':
                                    self.extracted_data.append(rom_name)
                                    self.txt_result.insert(tk.END, rom_name + "\n")
                                    match_count += 1
                                else:
                                    ignored_count += 1
                                    
                except Exception as e:
                    self.txt_result.insert(tk.END, f"[오류] {file} 읽기 실패: {e}\n")

        # 결과 요약 출력
        summary = (f"\n=== 추출 완료 ===\n"
                   f"탐색한 파일 수: {file_count}개\n"
                   f"추출된 부모 롬: {match_count}개\n"
                   f"제외됨(키워드 필터): {filtered_count}개\n"
                   f"제외됨(자식 롬/3번째 인자 0 아님): {ignored_count}개")
        self.txt_result.insert(tk.END, summary)
        self.txt_result.see(tk.END)
        
        if match_count > 0:
            messagebox.showinfo("완료", f"추출이 완료되었습니다.\n총 {match_count}개의 부모 롬을 찾았습니다.")
        else:
            messagebox.showinfo("완료", "조건에 맞는 데이터가 없습니다.")

    def save_to_file(self):
        """추출된 데이터를 txt 파일로 저장합니다."""
        if not self.extracted_data:
            messagebox.showwarning("경고", "저장할 데이터가 없습니다. 먼저 추출을 진행해주세요.")
            return

        save_path = filedialog.asksaveasfilename(
            title="저장할 위치 지정",
            defaultextension=".txt",
            initialfile="parent_roms.txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    for line in self.extracted_data:
                        f.write(line + "\n")
                messagebox.showinfo("저장 완료", f"파일이 성공적으로 저장되었습니다.\n{save_path}")
            except Exception as e:
                messagebox.showerror("저장 오류", f"파일 저장 중 오류가 발생했습니다:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GameDataExtractorApp(root)
    root.mainloop()