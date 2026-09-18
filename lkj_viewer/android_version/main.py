# -*- coding: utf-8 -*-
"""LKJ 数据管理 - Kivy 安卓应用
可在安卓手机上独立运行，支持查看/搜索/编辑/保存 LKJ 基硎数据。
"""

import os
import sys

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from excel_handler import ExcelHandler

SHEET_CATEGORIES = [
    ("线路信息", ["1.线路名称表", "12.起讫里程"]),
    ("车站信息", ["2.车站表", "3.股道表", "4.道岔表"]),
    ("速度信息", ["5.线路允许速度表", "5.23吨轴重货车专用线路允许速度表"]),
    ("线路特征", ["6.坡道表", "7.曲线表", "8.桥梁表", "9.隧道表", "10道口表", "11.断链表"]),
]

DEFAULT_FILE = "/sdcard/LKJ数据/兰州局工务类LKJ基础数据2026.2.24.xlsx"


class LKJApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.handler = None
        self.sheet_cache = {}
        self.current_sheet = None
        self.current_page = 0
        self.page_size = 20
        self.filtered_rows = []
        self.selected_row_index = None

    def build(self):
        self.title = "LKJ 数据管理"
        Window.clearcolor = (0.95, 0.95, 0.95, 1)

        root = BoxLayout(orientation="vertical")

        header = BoxLayout(size_hint_y=0.08)
        with header.canvas.before:
            Color(0.1, 0.3, 0.55, 1)
            self._header_rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=self._update_rect, size=self._update_rect)
        header.add_widget(Label(text="LKJ 数据管理", font_size=dp(20),
                                color=(1, 1, 1, 1)))
        root.add_widget(header)

        self.content = BoxLayout(orientation="horizontal")
        root.add_widget(self.content)

        self.sidebar = ScrollView(size_hint_x=0.35)
        self.sidebar_layout = BoxLayout(orientation="vertical", size_hint_y=None)
        self.sidebar_layout.bind(minimum_height=self.sidebar_layout.setter("height"))
        self.sidebar.add_widget(self.sidebar_layout)
        self.content.add_widget(self.sidebar)

        right_panel = BoxLayout(orientation="vertical", size_hint_x=0.65)

        toolbar = BoxLayout(size_hint_y=0.1, spacing=dp(4), padding=dp(4))
        self.search_input = TextInput(hint_text="搜索", multiline=False,
                                       size_hint_x=0.4)
        self.search_input.bind(on_text_validate=lambda *_: self._do_search())
        toolbar.add_widget(self.search_input)
        toolbar.add_widget(Button(text="搜索", size_hint_x=0.15,
                                  on_press=lambda *_: self._do_search()))
        toolbar.add_widget(Button(text="编辑", size_hint_x=0.15,
                                  on_press=lambda *_: self._edit_row()))
        toolbar.add_widget(Button(text="+行", size_hint_x=0.1,
                                  on_press=lambda *_: self._add_row()))
        toolbar.add_widget(Button(text="删行", size_hint_x=0.1,
                                  on_press=lambda *_: self._delete_row()))
        toolbar.add_widget(Button(text="保存", size_hint_x=0.1,
                                  on_press=lambda *_: self._save()))
        right_panel.add_widget(toolbar)

        self.info_label = Label(text="请选择工作簿", size_hint_y=0.06,
                                font_size=dp(13), color=(0.1, 0.3, 0.55, 1))
        right_panel.add_widget(self.info_label)

        self.table_scroll = ScrollView()
        self.table_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(1))
        self.table_layout.bind(minimum_height=self.table_layout.setter("height"))
        self.table_scroll.add_widget(self.table_layout)
        right_panel.add_widget(self.table_scroll)

        self.page_bar = BoxLayout(size_hint_y=0.08, spacing=dp(4))
        self.page_bar.add_widget(Button(text="上一页", size_hint_x=0.3,
                                        on_press=lambda *_: self._change_page(-1)))
        self.page_label = Label(text="0/0", size_hint_x=0.4)
        self.page_bar.add_widget(self.page_label)
        self.page_bar.add_widget(Button(text="下一页", size_hint_x=0.3,
                                        on_press=lambda *_: self._change_page(1)))
        right_panel.add_widget(self.page_bar)

        self.content.add_widget(right_panel)

        self._try_load_file()
        return root

    def _update_rect(self, instance, value):
        if hasattr(self, "_header_rect"):
            self._header_rect.pos = instance.pos
            self._header_rect.size = instance.size

    def _try_load_file(self):
        paths_to_try = [
            DEFAULT_FILE,
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "兰州局工务类LKJ基础数据2026.2.24.xlsx"),
            "/sdcard/Download/兰州局工务类LKJ基础数据2026.2.24.xlsx",
        ]
        for path in paths_to_try:
            if os.path.exists(path):
                self._load_file(path)
                return
        self._show_popup("提示", "未找到Excel文件\n请将文件放到 /sdcard/LKJ数据/ 目录")

    def _load_file(self, filepath):
        try:
            self.handler = ExcelHandler(filepath)
            self.handler.load()
            self._populate_sidebar()
        except Exception as e:
            self._show_popup("错误", f"加载失败:\n{e}")

    def _populate_sidebar(self):
        self.sidebar_layout.clear_widgets()
        available = set(self.handler.sheet_names)
        for cat_name, sheets in SHEET_CATEGORIES:
            cat_label = Label(text=cat_name, size_hint_y=None, height=dp(32),
                              font_size=dp(15), bold=True,
                              color=(0.1, 0.3, 0.55, 1))
            self.sidebar_layout.add_widget(cat_label)
            for s in sheets:
                if s in available:
                    btn = Button(text=s, size_hint_y=None, height=dp(40),
                                 font_size=dp(12))
                    btn.bind(on_press=lambda inst, name=s: self._select_sheet(name))
                    self.sidebar_layout.add_widget(btn)
        uncategorized = [s for s in self.handler.sheet_names
                         if s not in {s2 for _, lst in SHEET_CATEGORIES for s2 in lst}]
        if uncategorized:
            self.sidebar_layout.add_widget(
                Label(text="其他", size_hint_y=None, height=dp(32),
                      font_size=dp(15), bold=True, color=(0.1, 0.3, 0.55, 1)))
            for s in uncategorized:
                btn = Button(text=s, size_hint_y=None, height=dp(40), font_size=dp(12))
                btn.bind(on_press=lambda inst, name=s: self._select_sheet(name))
                self.sidebar_layout.add_widget(btn)

    def _get_sheet_data(self, sheet_name):
        if sheet_name not in self.sheet_cache:
            self.sheet_cache[sheet_name] = self.handler.read_sheet(sheet_name)
        return self.sheet_cache[sheet_name]

    def _select_sheet(self, sheet_name):
        self.current_sheet = sheet_name
        self.current_page = 0
        self.selected_row_index = None
        self._do_search()

    def _do_search(self):
        if not self.current_sheet:
            return
        sd = self._get_sheet_data(self.current_sheet)
        search = self.search_input.text.strip().lower()
        self.filtered_rows = []
        for i, row in enumerate(sd.rows):
            if search:
                row_str = " ".join(str(v) if v is not None else "" for v in row).lower()
                if search not in row_str:
                    continue
            self.filtered_rows.append((i, row))
        self.current_page = 0
        self._render_table()

    def _render_table(self):
        if not self.current_sheet:
            return
        sd = self._get_sheet_data(self.current_sheet)
        headers = sd.headers
        num_cols = len(headers)

        self.table_layout.clear_widgets()
        self.table_layout.cols = num_cols

        for h in headers:
            hl = Label(text=str(h), font_size=dp(11),
                       color=(1, 1, 1, 1), size_hint_y=None, height=dp(36))
            with hl.canvas.before:
                Color(0.1, 0.3, 0.55, 1)
                r = Rectangle(pos=hl.pos, size=hl.size)
            hl.bind(pos=lambda inst, val, rect=r: setattr(rect, "pos", val),
                    size=lambda inst, val, rect=r: setattr(rect, "size", val))
            self.table_layout.add_widget(hl)

        start = self.current_page * self.page_size
        end = min(start + self.page_size, len(self.filtered_rows))
        for idx in range(start, end):
            orig_index, row = self.filtered_rows[idx]
            for c in range(num_cols):
                val = row[c] if c < len(row) else None
                cell_text = str(val) if val is not None else ""
                cell = Button(text=cell_text, font_size=dp(10),
                              size_hint_y=None, height=dp(32))
                cell.bind(on_press=lambda inst, ri=orig_index: self._on_row_select(ri))
                self.table_layout.add_widget(cell)

        total = len(self.filtered_rows)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.page_label.text = f"{self.current_page + 1}/{total_pages}"
        dirty = " [未保存]" if sd.dirty else ""
        self.info_label.text = f"{sd.title} | {total}行{dirty}"

    def _on_row_select(self, row_index):
        self.selected_row_index = row_index
        self._edit_row()

    def _change_page(self, delta):
        total = len(self.filtered_rows)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        new_page = self.current_page + delta
        if 0 <= new_page < total_pages:
            self.current_page = new_page
            self._render_table()

    def _edit_row(self):
        if self.selected_row_index is None:
            self._show_popup("提示", "请先点击选择一行")
            return
        sd = self._get_sheet_data(self.current_sheet)
        if self.selected_row_index >= len(sd.rows):
            return
        row = sd.rows[self.selected_row_index]

        content = BoxLayout(orientation="vertical", spacing=dp(4), padding=dp(8))
        scroll = ScrollView()
        form = GridLayout(cols=2, size_hint_y=None, spacing=dp(4))
        form.bind(minimum_height=form.setter("height"))
        entries = []
        for i, h in enumerate(sd.headers):
            form.add_widget(Label(text=str(h), font_size=dp(12), size_hint_y=None,
                                  height=dp(32)))
            val = row[i] if i < len(row) else None
            entry = TextInput(text=str(val) if val is not None else "",
                               font_size=dp(13), size_hint_y=None, height=dp(32),
                               multiline=False)
            entries.append(entry)
            form.add_widget(entry)
        scroll.add_widget(form)
        content.add_widget(scroll)

        btn_row = BoxLayout(size_hint_y=0.12, spacing=dp(4))
        btn_row.add_widget(Button(text="取消", on_press=lambda *_: popup.dismiss()))
        def do_save(_):
            for i, entry in enumerate(entries):
                raw = entry.text.strip()
                orig = row[i] if i < len(row) else None
                if raw == "":
                    new_val = None
                elif isinstance(orig, str):
                    new_val = raw
                elif isinstance(orig, int):
                    try: new_val = int(raw)
                    except ValueError: new_val = raw
                elif isinstance(orig, float):
                    try: new_val = float(raw)
                    except ValueError: new_val = raw
                else:
                    try: new_val = int(raw)
                    except ValueError:
                        try: new_val = float(raw)
                        except ValueError: new_val = raw
                while i >= len(row):
                    row.append(None)
                row[i] = new_val
            sd.dirty = True
            popup.dismiss()
            self._render_table()
            self._show_popup("成功", "行已修改，请点击保存按钮写入文件")
        btn_row.add_widget(Button(text="确定", on_press=do_save))
        content.add_widget(btn_row)

        popup = Popup(title=f"编辑行 - {self.current_sheet} 第{self.selected_row_index+1}行",
                      content=content, size_hint=(0.9, 0.8))
        popup.open()

    def _add_row(self):
        if not self.current_sheet:
            return
        sd = self._get_sheet_data(self.current_sheet)
        sd.rows.append([None] * sd.max_col)
        sd.dirty = True
        self._do_search()
        self._show_popup("成功", "已添加空行")

    def _delete_row(self):
        if self.selected_row_index is None:
            self._show_popup("提示", "请先选择一行")
            return
        sd = self._get_sheet_data(self.current_sheet)
        if self.selected_row_index < len(sd.rows):
            del sd.rows[self.selected_row_index]
            sd.dirty = True
            self.selected_row_index = None
            self._do_search()
            self._show_popup("成功", "已删除")

    def _save(self):
        if not self.handler:
            return
        dirty_count = 0
        for name, sd in self.sheet_cache.items():
            if sd.dirty:
                self.handler.write_sheet(sd)
                dirty_count += 1
        if dirty_count == 0:
            self._show_popup("提示", "没有需要保存的修改")
            return
        try:
            self.handler.save()
            self._show_popup("成功", f"已保存{dirty_count}个工作簿")
            self._render_table()
        except Exception as e:
            self._show_popup("错误", f"保存失败:\n{e}")

    def _show_popup(self, title, message):
        content = BoxLayout(orientation="vertical")
        content.add_widget(Label(text=message, font_size=dp(14)))
        btn = Button(text="确定", size_hint_y=0.25)
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        btn.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    LKJApp().run()
