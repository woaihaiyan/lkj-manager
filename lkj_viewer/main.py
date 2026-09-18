# -*- coding: utf-8 -*-
"""兰州局工务类 LKJ 基硎数据可视化查看与编辑工具
基于 tkinter 的桌面 GUI，支持分类浏览、搜索筛选、单元格编辑、增删行、保存回 Excel。
"""

import os
import sys
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from excel_handler import ExcelHandler, SheetData
from import_dialog import ImportDialog


SHEET_CATEGORIES = [
    ("线路信息", ["1.线路名称表", "12.起讫里程"]),
    ("车站信息", ["2.车站表", "3.股道表", "4.道岔表"]),
    ("速度信息", ["5.线路允许速度表", "5.23吨轴重货车专用线路允许速度表"]),
    ("线路特征", ["6.坡道表", "7.曲线表", "8.桥梁表", "9.隧道表", "10道口表", "11.断链表"]),
]

DEFAULT_FILE = r"k:\huawei\keshihua\demo\兰州局工务类LKJ基础数据2026.2.24.xlsx"


class EditableTreeview(ttk.Treeview):
    """支持双击整行编辑、点击表头排序的 Treeview"""

    def __init__(self, master, app, **kw):
        super().__init__(master, **kw)
        self.app = app
        self.bind("<Double-1>", self._on_double_click)
        self._sort_state = {}

    def _on_double_click(self, event):
        region = self.identify("region", event.x, event.y)
        if region != "cell":
            return
        row = self.identify("row", event.x, event.y)
        if not row:
            return
        self.selection_set(row)
        self.app._edit_row()

    def sort_by_column(self, col, descending=False):
        data = [(self.set(k, col), k) for k in self.get_children("")]
        try:
            data.sort(key=lambda x: (float(x[0]) if x[0] and x[0] != "None" else float("inf")), reverse=descending)
        except (ValueError, TypeError):
            data.sort(key=lambda x: (str(x[0]) if x[0] else ""), reverse=descending)
        for index, (val, k) in enumerate(data):
            self.move(k, "", index)
        self.heading(col, command=lambda: self.sort_by_column(col, not descending))
        self._sort_state[col] = not descending


class App:
    """主应用程序"""

    def __init__(self, root):
        self.root = root
        self.root.title("兰州局工务类 LKJ 基硎数据管理工具")
        self.root.geometry("1400x850")
        self.root.minsize(1000, 600)

        self.handler = None
        self.current_sheet = None
        self.sheet_data = {}
        self.filtered_indices = []

        self._build_style()
        self._build_menu()
        self._build_layout()
        self._build_statusbar()

        if os.path.exists(DEFAULT_FILE):
            self.open_file(DEFAULT_FILE)

    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=24, font=("Microsoft YaHei", 10))
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Sidebar.Treeview", rowheight=26, font=("Microsoft YaHei", 10))

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开 Excel 文件...", command=self._menu_open)
        file_menu.add_command(label="保存", command=self._menu_save, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为...", command=self._menu_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="添加新线路(从文档导入)...", command=self._import_document,
                              accelerator="Ctrl+I")
        file_menu.add_separator()
        file_menu.add_command(label="导出当前工作簿为 CSV...", command=self._export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="编辑选中行", command=self._edit_row, accelerator="Ctrl+E")
        edit_menu.add_separator()
        edit_menu.add_command(label="添加空行", command=self._add_row, accelerator="Ctrl+N")
        edit_menu.add_command(label="删除选中行", command=self._delete_rows, accelerator="Ctrl+D")
        edit_menu.add_command(label="复制选中行", command=self._duplicate_row)
        menubar.add_cascade(label="编辑", menu=edit_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menubar)
        self.root.bind("<Control-s>", lambda e: self._menu_save())
        self.root.bind("<Control-n>", lambda e: self._add_row())
        self.root.bind("<Control-d>", lambda e: self._delete_rows())
        self.root.bind("<Control-i>", lambda e: self._import_document())
        self.root.bind("<Control-e>", lambda e: self._edit_row())

    def _build_layout(self):
        main_pane = ttk.PanedWindow(self.root, orient="horizontal")
        main_pane.pack(fill="both", expand=True)

        left_frame = ttk.Frame(main_pane, width=260)
        main_pane.add(left_frame, weight=0)

        ttk.Label(left_frame, text="工作簿分类", font=("Microsoft YaHei", 11, "bold"),
                  padding=8).pack(fill="x")

        list_container = ttk.Frame(left_frame)
        list_container.pack(fill="both", expand=True, padx=4, pady=4)

        self.sidebar = ttk.Treeview(list_container, style="Sidebar.Treeview", show="tree")
        sb_scroll = ttk.Scrollbar(list_container, orient="vertical", command=self.sidebar.yview)
        self.sidebar.configure(yscrollcommand=sb_scroll.set)
        self.sidebar.pack(side="left", fill="both", expand=True)
        sb_scroll.pack(side="right", fill="y")
        self.sidebar.bind("<<TreeviewSelect>>", self._on_sidebar_select)

        self.sheet_info_label = ttk.Label(left_frame, text="", font=("Microsoft YaHei", 9),
                                          foreground="gray", padding=4, wraplength=240)
        self.sheet_info_label.pack(fill="x", padx=4, pady=4)

        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=1)

        toolbar = ttk.Frame(right_frame)
        toolbar.pack(fill="x", padx=4, pady=4)

        ttk.Label(toolbar, text="搜索:").pack(side="left", padx=(4, 2))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=2)

        ttk.Label(toolbar, text="筛选列:").pack(side="left", padx=(12, 2))
        self.filter_col_var = tk.StringVar(value="全列")
        self.filter_col_combo = ttk.Combobox(toolbar, textvariable=self.filter_col_var,
                                              width=14, state="readonly")
        self.filter_col_combo.pack(side="left", padx=2)
        self.filter_col_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        ttk.Label(toolbar, text="值:").pack(side="left", padx=(8, 2))
        self.filter_val_var = tk.StringVar()
        self.filter_val_var.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(toolbar, textvariable=self.filter_val_var, width=16).pack(side="left", padx=2)

        ttk.Button(toolbar, text="清除筛选", command=self._clear_filter).pack(side="left", padx=8)
        ttk.Button(toolbar, text="添加新线路", command=self._import_document).pack(side="left", padx=8)

        ttk.Button(toolbar, text="添加行", command=self._add_row).pack(side="right", padx=2)
        ttk.Button(toolbar, text="编辑行", command=self._edit_row).pack(side="right", padx=2)
        ttk.Button(toolbar, text="删除行", command=self._delete_rows).pack(side="right", padx=2)
        ttk.Button(toolbar, text="保存", command=self._menu_save).pack(side="right", padx=2)

        table_container = ttk.Frame(right_frame)
        table_container.pack(fill="both", expand=True, padx=4, pady=4)

        self.tree = EditableTreeview(table_container, self, show="headings")
        y_scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Button-1>", self._on_header_click, add="+")
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="就绪")
        bar = ttk.Frame(self.root, relief="sunken")
        bar.pack(fill="x", side="bottom")
        ttk.Label(bar, textvariable=self.status_var, padding=6).pack(side="left")
        self.count_var = tk.StringVar(value="")
        ttk.Label(bar, textvariable=self.count_var, padding=6).pack(side="right")

    def open_file(self, filepath):
        try:
            self.handler = ExcelHandler(filepath)
            self.handler.load()
        except Exception as e:
            messagebox.showerror("错误", f"打开文件失败:\n{e}")
            return
        self.sheet_data = {}
        self._populate_sidebar()
        self.root.title(f"兰州局工务类 LKJ 基硎数据管理工具 - {os.path.basename(filepath)}")
        self.status_var.set(f"已加载: {os.path.basename(filepath)}")
        for cat_name, sheets in SHEET_CATEGORIES:
            if sheets and sheets[0] in self.handler.sheet_names:
                self._select_sheet(sheets[0])
                break

    def _populate_sidebar(self):
        self.sidebar.delete(*self.sidebar.get_children())
        available = set(self.handler.sheet_names)
        categorized = set()
        for cat_name, sheets in SHEET_CATEGORIES:
            cat_id = self.sidebar.insert("", "end", text=cat_name, open=True,
                                         tags=("category",))
            for s in sheets:
                if s in available:
                    self.sidebar.insert(cat_id, "end", text=s, tags=("sheet",))
                    categorized.add(s)
        uncategorized = [s for s in self.handler.sheet_names if s not in categorized]
        if uncategorized:
            cat_id = self.sidebar.insert("", "end", text="其他", open=True, tags=("category",))
            for s in uncategorized:
                self.sidebar.insert(cat_id, "end", text=s, tags=("sheet",))
        self.sidebar.tag_configure("category", font=("Microsoft YaHei", 10, "bold"),
                                   foreground="#1a4f8a")
        self.sidebar.tag_configure("sheet", font=("Microsoft YaHei", 10))

    def _on_sidebar_select(self, event):
        sel = self.sidebar.selection()
        if not sel:
            return
        item = sel[0]
        tags = self.sidebar.item(item, "tags")
        if "sheet" not in tags:
            return
        sheet_name = self.sidebar.item(item, "text")
        self._select_sheet(sheet_name)

    def _select_sheet(self, sheet_name):
        if sheet_name not in self.handler.sheet_names:
            return
        if sheet_name not in self.sheet_data:
            self.sheet_data[sheet_name] = self.handler.read_sheet(sheet_name)
        self.current_sheet = sheet_name
        self._render_table()
        sd = self.sheet_data[sheet_name]
        self.sheet_info_label.config(
            text=f"标题: {sd.title}\n编号: {sd.code}\n数据行: {sd.row_count()}\n列数: {sd.max_col}"
        )
        self.status_var.set(f"当前工作簿: {sheet_name}")

    def _render_table(self):
        sd = self.sheet_data[self.current_sheet]
        self.tree.delete(*self.tree.get_children())
        cols = [f"col{i}" for i in range(sd.max_col)]
        self.tree["columns"] = cols
        for i, h in enumerate(sd.headers):
            self.tree.heading(f"col{i}", text=h,
                              command=lambda c=f"col{i}": self.tree.sort_by_column(c, False))
            self.tree.column(f"col{i}", width=110, minwidth=60)
        self._apply_filter()

    def _apply_filter(self):
        if self.current_sheet is None:
            return
        sd = self.sheet_data[self.current_sheet]
        search = self.search_var.get().strip().lower()
        filter_col = self.filter_col_var.get()
        filter_val = self.filter_val_var.get().strip().lower()

        col_options = ["全列"] + sd.headers
        if self.filter_col_combo["values"] != col_options:
            self.filter_col_combo["values"] = col_options

        filter_col_idx = -1
        if filter_col != "全列" and filter_col in sd.headers:
            filter_col_idx = sd.headers.index(filter_col)

        self.tree.delete(*self.tree.get_children())
        shown = 0
        for i, row in enumerate(sd.rows):
            row_strs = [str(v) if v is not None else "" for v in row]
            if search:
                if not any(search in s.lower() for s in row_strs):
                    continue
            if filter_val and filter_col_idx >= 0:
                cell = row_strs[filter_col_idx] if filter_col_idx < len(row_strs) else ""
                if filter_val not in cell.lower():
                    continue
            display_vals = [str(v) if v is not None else "" for v in row]
            if len(display_vals) < sd.max_col:
                display_vals += [""] * (sd.max_col - len(display_vals))
            self.tree.insert("", "end", iid=str(i), values=display_vals)
            shown += 1
        self.count_var.set(f"显示 {shown} / {sd.row_count()} 行")

    def _clear_filter(self):
        self.search_var.set("")
        self.filter_val_var.set("")
        self.filter_col_var.set("全列")

    def _on_header_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            col = self.tree.identify("column", event.x, event.y)
            if col:
                self.tree.sort_by_column(col, False)

    def on_cell_edited(self, item_index, col_index, new_val):
        if self.current_sheet is None:
            return
        sd = self.sheet_data[self.current_sheet]
        if item_index >= len(sd.rows):
            return
        old_val = sd.rows[item_index][col_index] if col_index < len(sd.rows[item_index]) else None
        try:
            if old_val is not None and not isinstance(old_val, str):
                if isinstance(old_val, int):
                    new_val = int(new_val)
                elif isinstance(old_val, float):
                    new_val = float(new_val)
        except (ValueError, TypeError):
            pass
        while col_index >= len(sd.rows[item_index]):
            sd.rows[item_index].append(None)
        sd.rows[item_index][col_index] = new_val
        sd.dirty = True
        self.status_var.set(f"已修改: {self.current_sheet} 第{item_index + 1}行 第{col_index + 1}列")

    def _edit_row(self):
        if self.current_sheet is None:
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选中要编辑的行")
            return
        iid = selected[0]
        row_index = int(iid)
        sd = self.sheet_data[self.current_sheet]
        if row_index >= len(sd.rows):
            return
        dialog = RowEditDialog(self.root, sd.headers, sd.rows[row_index],
                               self.current_sheet, row_index)
        if dialog.result is not None:
            sd.rows[row_index] = dialog.result
            sd.dirty = True
            self._apply_filter()
            self.status_var.set(f"已编辑: {self.current_sheet} 第{row_index + 1}行")

    def _show_context_menu(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.tree.identify("row", event.x, event.y)
        if row_id:
            self.tree.selection_set(row_id)
        ctx_menu = tk.Menu(self.tree, tearoff=0)
        ctx_menu.add_command(label="编辑此行 (Ctrl+E)", command=self._edit_row)
        ctx_menu.add_command(label="复制此行", command=self._duplicate_row)
        ctx_menu.add_separator()
        ctx_menu.add_command(label="删除此行 (Ctrl+D)", command=self._delete_rows)
        ctx_menu.add_separator()
        ctx_menu.add_command(label="添加空行 (Ctrl+N)", command=self._add_row)
        ctx_menu.tk_popup(event.x_root, event.y_root)

    def _add_row(self):
        if self.current_sheet is None:
            return
        sd = self.sheet_data[self.current_sheet]
        new_row = [None] * sd.max_col
        sd.rows.append(new_row)
        sd.dirty = True
        self._apply_filter()
        self.count_var.set(f"显示 {sd.row_count()} / {sd.row_count()} 行")
        self.status_var.set(f"已添加新行到: {self.current_sheet}")

    def _delete_rows(self):
        if self.current_sheet is None:
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选中要删除的行")
            return
        if not messagebox.askyesno("确认", f"确定删除 {len(selected)} 行数据?"):
            return
        sd = self.sheet_data[self.current_sheet]
        indices_to_delete = sorted([int(iid) for iid in selected], reverse=True)
        for idx in indices_to_delete:
            if idx < len(sd.rows):
                del sd.rows[idx]
        sd.dirty = True
        self._apply_filter()
        self.status_var.set(f"已删除 {len(indices_to_delete)} 行")

    def _duplicate_row(self):
        if self.current_sheet is None:
            return
        selected = self.tree.selection()
        if not selected:
            return
        sd = self.sheet_data[self.current_sheet]
        for iid in selected:
            idx = int(iid)
            if idx < len(sd.rows):
                sd.rows.append(list(sd.rows[idx]))
        sd.dirty = True
        self._apply_filter()
        self.status_var.set("已复制选中行")

    def _menu_open(self):
        filepath = filedialog.askopenfilename(
            title="选择 Excel 文件",
            filetypes=[("Excel 文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if filepath:
            self.open_file(filepath)

    def _menu_save(self):
        if self.handler is None:
            return
        dirty_sheets = [name for name, sd in self.sheet_data.items() if sd.dirty]
        if not dirty_sheets:
            self.status_var.set("没有需要保存的修改")
            return
        try:
            for name in dirty_sheets:
                self.handler.write_sheet(self.sheet_data[name])
            self.handler.save()
            self.status_var.set(f"已保存 {len(dirty_sheets)} 个工作簿的修改")
            messagebox.showinfo("成功", f"已保存 {len(dirty_sheets)} 个工作簿的修改")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def _menu_save_as(self):
        if self.handler is None:
            return
        filepath = filedialog.asksaveasfilename(
            title="另存为",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")]
        )
        if not filepath:
            return
        try:
            for name, sd in self.sheet_data.items():
                if sd.dirty:
                    self.handler.write_sheet(sd)
            self.handler.save(filepath)
            self.status_var.set(f"已另存为: {os.path.basename(filepath)}")
            messagebox.showinfo("成功", f"已保存到:\n{filepath}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def _import_document(self):
        if self.handler is None:
            messagebox.showinfo("提示", "请先打开一个 Excel 文件")
            return
        ImportDialog(self.root, self.handler, self.sheet_data,
                     on_imported=self._on_data_imported)

    def _on_data_imported(self):
        if self.current_sheet:
            self._render_table()
        self.status_var.set("数据已导入，请保存到 Excel 文件")

    def _export_csv(self):
        if self.current_sheet is None:
            return
        sd = self.sheet_data[self.current_sheet]
        filepath = filedialog.asksaveasfilename(
            title="导出 CSV",
            defaultextension=".csv",
            initialfile=f"{self.current_sheet}.csv",
            filetypes=[("CSV 文件", "*.csv")]
        )
        if not filepath:
            return
        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(sd.headers)
                for row in sd.rows:
                    writer.writerow([str(v) if v is not None else "" for v in row])
            self.status_var.set(f"已导出: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _show_help(self):
        help_text = (
            "使用说明:\n\n"
            "1. 左侧栏按分类列出各工作簿，点击即可查看数据\n"
            "2. 双击单元格可编辑内容，回车确认，Esc 取消\n"
            "3. 搜索框输入文字可全列实时搜索\n"
            "4. 选择筛选列并输入值可按指定列筛选\n"
            "5. 点击表头可排序\n"
            "6. 选中行后 Ctrl+E 或右键菜单可整行编辑\n"
            "7. 添加行/删除行按钮可增删数据\n"
            "8. Ctrl+S 保存修改回 Excel 文件\n"
            "9. 可导出当前工作簿为 CSV\n"
            "10. 添加新线路: 从 PDF/Word/Excel 文档导入数据\n"
            "   支持 LKJ 基硎数据格式，自动识别各表并归类\n"
            "   导入后可预览确认，追加或替换现有数据\n"
        )
        messagebox.showinfo("使用说明", help_text)

    def _show_about(self):
        messagebox.showinfo("关于",
            "兰州局工务类 LKJ 基硎数据管理工具\n"
            "基于 Python + tkinter 开发\n"
            "支持 Excel 数据的可视化浏览与编辑")


class RowEditDialog(tk.Toplevel):
    """整行编辑对话框：显示该行所有列的标签和输入框"""

    def __init__(self, parent, headers, row_data, sheet_name, row_index):
        super().__init__(parent)
        self.title(f"编辑行 - {sheet_name} 第{row_index + 1}行")
        self.result = None
        self.headers = headers
        self.entries = []
        self.original_row = row_data

        self.transient(parent)
        self.grab_set()

        main_frame = ttk.Frame(self, padding=12)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text=f"工作簿: {sheet_name}    行号: {row_index + 1}",
                  font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", pady=(0, 8))

        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, header in enumerate(headers):
            cell_frame = ttk.Frame(scrollable)
            cell_frame.pack(fill="x", padx=4, pady=2)
            ttk.Label(cell_frame, text=header, width=14, anchor="e").pack(side="left", padx=(0, 6))
            val = row_data[i] if i < len(row_data) else None
            entry = ttk.Entry(cell_frame, width=40)
            entry.insert(0, str(val) if val is not None else "")
            entry.pack(side="left", fill="x", expand=True)
            self.entries.append(entry)

        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(btn_frame, text="确定", command=self._confirm).pack(side="right", padx=4)

        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"500x{min(h, 600)}+{(sw - 500) // 2}+{(sh - min(h, 600)) // 2}")

        if self.entries:
            self.entries[0].focus_set()

    def _confirm(self):
        self.result = []
        for i, entry in enumerate(self.entries):
            raw = entry.get().strip()
            if raw == "":
                self.result.append(None)
                continue
            orig = self.original_row[i] if i < len(self.original_row) else None
            if isinstance(orig, str):
                self.result.append(raw)
            elif isinstance(orig, int):
                try:
                    self.result.append(int(raw))
                except ValueError:
                    self.result.append(raw)
            elif isinstance(orig, float):
                try:
                    self.result.append(float(raw))
                except ValueError:
                    self.result.append(raw)
            else:
                try:
                    self.result.append(int(raw))
                except ValueError:
                    try:
                        self.result.append(float(raw))
                    except ValueError:
                        self.result.append(raw)
        self.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()