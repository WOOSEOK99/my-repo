import json
import os
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
import urllib.request
from io import BytesIO
from PIL import Image, ImageTk


class ListOpsMixin:
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
        sel = self.listbox.curselection()
        if not sel: return
        raw_text = self.listbox.get(sel[0])
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
            raw_text = self.listbox.get(self.listbox.curselection()[0])
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

