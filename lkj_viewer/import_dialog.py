# -*- coding: utf-8 -*-
"""导入新线路数据对话框
解析 PDF/Word/Excel 文档，预览提取的数据，确认后追加到当前 Excel 工作簿。
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from doc_parser import parse_document, get_summary


class ImportDialog(tk.Toplevel):
    """添加新线路数据对话框"""

    def __init__(self, parent, handler, sheet_data, on_imported=None):
        super().__init__(parent)
        self.title("添加新线路 - 从文档导入数据")
        self.geometry("1100x700")
        self.handler = handler
        self.sheet_data = sheet_data
        self.on_imported = on_imported
        self.parsed_data = {}
        self.check_vars = {}

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=8, pady=4)

        ttk.Button(top_frame, text="选择文档...", command=self._select_file).pack(side="left")
        self.file_label = ttk.Label(top_frame, text="未选择文件", foreground="gray")
        self.file_label.pack(side="left", padx=8)

        self.summary_label = ttk.Label(top_frame, text="", foreground="blue")
        self.summary_label.pack(side="left", padx=8)

        main_pane = ttk.PanedWindow(self, orient="horizontal")
        main_pane.pack(fill="both", expand=True, padx=8, pady=4)

        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=0)

        ttk.Label(left_frame, text="检测到的数据表", font=("Microsoft YaHei", 10, "bold"),
                  padding=4).pack(fill="x")
        self.sheet_list = ttk.Frame(left_frame)
        self.sheet_list.pack(fill="both", expand=True)
        self.empty_label = ttk.Label(self.sheet_list, text="请先选择文档\n(PDF / Word / Excel)",
                                     foreground="gray", padding=20, justify="center")
        self.empty_label.pack()

        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=1)

        ttk.Label(right_frame, text="数据预览", font=("Microsoft YaHei", 10, "bold"),
                  padding=4).pack(fill="x")

        preview_container = ttk.Frame(right_frame)
        preview_container.pack(fill="both", expand=True)

        self.preview_tree = ttk.Treeview(preview_container, show="headings")
        py_scroll = ttk.Scrollbar(preview_container, orient="vertical",
                                  command=self.preview_tree.yview)
        px_scroll = ttk.Scrollbar(preview_container, orient="horizontal",
                                  command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=py_scroll.set,
                                    xscrollcommand=px_scroll.set)
        self.preview_tree.grid(row=0, column=0, sticky="nsew")
        py_scroll.grid(row=0, column=1, sticky="ns")
        px_scroll.grid(row=1, column=0, sticky="ew")
        preview_container.grid_rowconfigure(0, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=8, pady=4)

        self.import_mode = tk.StringVar(value="append")
        ttk.Radiobutton(bottom_frame, text="追加到现有数据末尾", variable=self.import_mode,
                        value="append").pack(side="left")
        ttk.Radiobutton(bottom_frame, text="替换现有数据", variable=self.import_mode,
                        value="replace").pack(side="left", padx=8)

        ttk.Button(bottom_frame, text="取消", command=self.destroy).pack(side="right", padx=4)
        self.import_btn = ttk.Button(bottom_frame, text="导入选中数据", command=self._do_import,
                                     state="disabled")
        self.import_btn.pack(side="right", padx=4)

        self.status_var = tk.StringVar(value="")
        ttk.Label(bottom_frame, textvariable=self.status_var, foreground="gray").pack(side="left", padx=12)

    def _select_file(self):
        filepath = filedialog.askopenfilename(
            title="选择要导入的文档",
            filetypes=[
                ("所有支持的格式", "*.pdf;*.docx;*.doc;*.xlsx;*.xls"),
                ("PDF 文件", "*.pdf"),
                ("Word 文件", "*.docx;*.doc"),
                ("Excel 文件", "*.xlsx;*.xls"),
            ]
        )
        if not filepath:
            return
        self.file_label.config(text=os.path.basename(filepath), foreground="black")
        self.status_var.set("正在解析...")
        self.update_idletasks()
        try:
            self.parsed_data = parse_document(filepath)
        except Exception as e:
            messagebox.showerror("解析失败", str(e))
            self.status_var.set("解析失败")
            return
        if not self.parsed_data:
            messagebox.showwarning("提示", "未从文档中识别到有效的 LKJ 数据表")
            self.status_var.set("未识别到数据")
            return
        self.status_var.set("")
        self._populate_sheet_list()

    def _populate_sheet_list(self):
        for w in self.sheet_list.winfo_children():
            w.destroy()

        available = set(self.handler.sheet_names) if self.handler else set()

        for sheet_name, data in self.parsed_data.items():
            row_count = len(data["rows"])
            exists = sheet_name in available
            var = tk.BooleanVar(value=True)
            self.check_vars[sheet_name] = var

            item_frame = ttk.Frame(self.sheet_list)
            item_frame.pack(fill="x", padx=4, pady=2)
            cb = ttk.Checkbutton(item_frame, variable=var,
                                 command=self._on_check_change)
            cb.pack(side="left")
            label_text = f"{sheet_name} ({row_count}行)"
            if not exists:
                label_text += " [新]"
                color = "orange"
            else:
                color = "black"
            lbl = ttk.Label(item_frame, text=label_text, foreground=color,
                            cursor="hand2")
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, sn=sheet_name: self._show_preview(sn))

        self.summary_label.config(text=f"共 {len(self.parsed_data)} 个表, "
                                       f"{sum(len(d['rows']) for d in self.parsed_data.values())} 行数据")
        self.import_btn.config(state="normal")

        first_sheet = next(iter(self.parsed_data))
        self._show_preview(first_sheet)

    def _on_check_change(self):
        any_checked = any(v.get() for v in self.check_vars.values())
        self.import_btn.config(state="normal" if any_checked else "disabled")

    def _show_preview(self, sheet_name):
        if sheet_name not in self.parsed_data:
            return
        data = self.parsed_data[sheet_name]
        headers = data["headers"]
        rows = data["rows"]

        self.preview_tree.delete(*self.preview_tree.get_children())
        cols = [f"c{i}" for i in range(len(headers))]
        self.preview_tree["columns"] = cols
        for i, h in enumerate(headers):
            self.preview_tree.heading(f"c{i}", text=h)
            self.preview_tree.column(f"c{i}", width=100, minwidth=50)
        for row in rows:
            display = [str(v) if v is not None else "" for v in row]
            while len(display) < len(headers):
                display.append("")
            self.preview_tree.insert("", "end", values=display)
        self.status_var.set(f"预览: {sheet_name} - {len(rows)} 行")

    def _do_import(self):
        selected = [name for name, var in self.check_vars.items() if var.get()]
        if not selected:
            return
        mode = self.import_mode.get()
        total_imported = 0
        for sheet_name in selected:
            data = self.parsed_data[sheet_name]
            if sheet_name not in self.sheet_data:
                self.sheet_data[sheet_name] = self.handler.read_sheet(sheet_name)
            sd = self.sheet_data[sheet_name]
            target_cols = sd.max_col
            source_cols = len(data["headers"])
            col_count = min(target_cols, source_cols)

            if mode == "replace":
                sd.rows.clear()

            for row in data["rows"]:
                new_row = [None] * target_cols
                for c in range(col_count):
                    new_row[c] = row[c] if c < len(row) else None
                sd.rows.append(new_row)
                sd.dirty = True
                total_imported += 1

        if self.on_imported:
            self.on_imported()
        messagebox.showinfo("导入成功",
            f"已导入 {total_imported} 行数据到 {len(selected)} 个工作簿\n\n"
            f"请点击\"保存\"按钮将修改写入 Excel 文件")
        self.destroy()