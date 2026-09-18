# -*- coding: utf-8 -*-
"""LKJ 数据管理 - Flask Web 版本
PC 运行后，手机浏览器访问 http://<PC_IP>:5000 即可使用。
适配手机触屏操作，支持查看/搜索/编辑/保存。
"""

import os
import sys
import json
import socket
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, jsonify, send_file
from excel_handler import ExcelHandler
from doc_parser import parse_document, get_summary

app = Flask(__name__)

DEFAULT_FILE = r"k:\huawei\keshihua\demo\兰州局工务类LKJ基础数据2026.2.24.xlsx"

SHEET_CATEGORIES = [
    {"category": "线路信息", "sheets": ["1.线路名称表", "12.起讫里程"]},
    {"category": "车站信息", "sheets": ["2.车站表", "3.股道表", "4.道岔表"]},
    {"category": "速度信息", "sheets": ["5.线路允许速度表", "5.23吨轴重货车专用线路允许速度表"]},
    {"category": "线路特征", "sheets": ["6.坡道表", "7.曲线表", "8.桥梁表", "9.隧道表", "10道口表", "11.断链表"]},
]

handler = None
sheet_cache = {}


def init_handler(filepath=None):
    global handler, sheet_cache
    path = filepath or DEFAULT_FILE
    if not os.path.exists(path):
        return False
    handler = ExcelHandler(path)
    handler.load()
    sheet_cache = {}
    return True


def get_sheet_data(sheet_name):
    if sheet_name not in sheet_cache:
        sheet_cache[sheet_name] = handler.read_sheet(sheet_name)
    return sheet_cache[sheet_name]


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


@app.route("/")
def index():
    ip = get_local_ip()
    return render_template("index.html", server_ip=ip, categories=SHEET_CATEGORIES)


@app.route("/api/sheets")
def api_sheets():
    if handler is None:
        return jsonify({"error": "未加载文件"}), 500
    info = handler.get_sheet_info()
    return jsonify({"sheets": info, "names": handler.sheet_names})


@app.route("/api/data/<sheet_name>")
def api_data(sheet_name):
    if handler is None:
        return jsonify({"error": "未加载文件"}), 500
    if sheet_name not in handler.sheet_names:
        return jsonify({"error": "工作簿不存在"}), 404

    sd = get_sheet_data(sheet_name)
    search = request.args.get("search", "").strip().lower()
    page = int(request.args.get("page", "1"))
    per_page = int(request.args.get("per_page", "50"))

    filtered = []
    for i, row in enumerate(sd.rows):
        if search:
            row_str = " ".join(str(v) if v is not None else "" for v in row).lower()
            if search not in row_str:
                continue
        filtered.append({"index": i, "values": [str(v) if v is not None else "" for v in row]})

    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    page_data = filtered[start:end]

    return jsonify({
        "title": sd.title,
        "code": sd.code,
        "headers": sd.headers,
        "rows": page_data,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "dirty": sd.dirty,
    })


@app.route("/api/row/<sheet_name>/<int:row_index>", methods=["GET"])
def api_get_row(sheet_name, row_index):
    sd = get_sheet_data(sheet_name)
    if row_index >= len(sd.rows):
        return jsonify({"error": "行不存在"}), 404
    return jsonify({
        "headers": sd.headers,
        "values": [str(v) if v is not None else "" for v in sd.rows[row_index]],
    })


@app.route("/api/row/<sheet_name>/<int:row_index>", methods=["POST"])
def api_update_row(sheet_name, row_index):
    sd = get_sheet_data(sheet_name)
    if row_index >= len(sd.rows):
        return jsonify({"error": "行不存在"}), 404
    data = request.get_json()
    new_values = data.get("values", [])
    for i, val in enumerate(new_values):
        if i >= sd.max_col:
            break
        orig = sd.rows[row_index][i] if i < len(sd.rows[row_index]) else None
        if val == "":
            new_val = None
        elif isinstance(orig, str):
            new_val = val
        elif isinstance(orig, int):
            try:
                new_val = int(val)
            except ValueError:
                new_val = val
        elif isinstance(orig, float):
            try:
                new_val = float(val)
            except ValueError:
                new_val = val
        else:
            try:
                new_val = int(val)
            except ValueError:
                try:
                    new_val = float(val)
                except ValueError:
                    new_val = val
        while i >= len(sd.rows[row_index]):
            sd.rows[row_index].append(None)
        sd.rows[row_index][i] = new_val
    sd.dirty = True
    return jsonify({"success": True})


@app.route("/api/add_row/<sheet_name>", methods=["POST"])
def api_add_row(sheet_name):
    sd = get_sheet_data(sheet_name)
    sd.rows.append([None] * sd.max_col)
    sd.dirty = True
    return jsonify({"success": True, "index": len(sd.rows) - 1})


@app.route("/api/delete_row/<sheet_name>/<int:row_index>", methods=["POST"])
def api_delete_row(sheet_name, row_index):
    sd = get_sheet_data(sheet_name)
    if row_index < len(sd.rows):
        del sd.rows[row_index]
        sd.dirty = True
        return jsonify({"success": True})
    return jsonify({"error": "行不存在"}), 404


@app.route("/api/save", methods=["POST"])
def api_save():
    if handler is None:
        return jsonify({"error": "未加载文件"}), 500
    dirty_count = 0
    for name, sd in sheet_cache.items():
        if sd.dirty:
            handler.write_sheet(sd)
            dirty_count += 1
    if dirty_count == 0:
        return jsonify({"success": True, "message": "没有需要保存的修改"})
    try:
        handler.save()
        return jsonify({"success": True, "message": f"已保存 {dirty_count} 个工作簿的修改"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/import", methods=["POST"])
def api_import():
    if handler is None:
        return jsonify({"error": "未加载文件"}), 500
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "未上传文件"}), 400
    tmp_path = os.path.join("/tmp" if os.name != "nt" else os.environ.get("TEMP", "."), f.filename)
    f.save(tmp_path)
    try:
        parsed = parse_document(tmp_path)
    except Exception as e:
        return jsonify({"error": f"解析失败: {e}"}), 500
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
    result = {}
    for name, data in parsed.items():
        result[name] = {
            "headers": data["headers"],
            "row_count": len(data["rows"]),
            "preview": [[str(v) if v is not None else "" for v in r] for r in data["rows"][:5]],
        }
    return jsonify({"summary": get_summary(parsed), "details": result})


@app.route("/api/import_confirm", methods=["POST"])
def api_import_confirm():
    data = request.get_json()
    filepath = data.get("filepath")
    selected_sheets = data.get("sheets", [])
    mode = data.get("mode", "append")
    parsed = parse_document(filepath)
    total = 0
    for sheet_name in selected_sheets:
        if sheet_name not in parsed:
            continue
        sd = get_sheet_data(sheet_name)
        source = parsed[sheet_name]
        if mode == "replace":
            sd.rows.clear()
        for row in source["rows"]:
            new_row = [None] * sd.max_col
            for c in range(min(sd.max_col, len(row))):
                new_row[c] = row[c]
            sd.rows.append(new_row)
            sd.dirty = True
            total += 1
    return jsonify({"success": True, "imported": total})


@app.route("/api/open_file", methods=["POST"])
def api_open_file():
    data = request.get_json()
    path = data.get("path", "")
    if init_handler(path):
        return jsonify({"success": True, "sheets": handler.sheet_names})
    return jsonify({"error": "打开失败"}), 500


def run(host="0.0.0.0", port=5000):
    if not init_handler():
        print(f"警告: 默认文件不存在: {DEFAULT_FILE}")
    ip = get_local_ip()
    print(f"\n{'='*50}")
    print(f"  LKJ 数据管理 - 手机访问版")
    print(f"{'='*50}")
    print(f"  手机浏览器访问: http://{ip}:{port}")
    print(f"  本机访问:       http://127.0.0.1:{port}")
    print(f"{'='*50}\n")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run()