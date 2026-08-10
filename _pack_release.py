# -*- coding: utf-8 -*-
"""Pack a clean, ready-to-run competition build (no scaffolding)."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "比赛提交包"

SKIP_DIR_NAMES = {
    "__pycache__",
    "_liang",
    ".git",
    "比赛提交包",
}
SKIP_FILE_GLOBS = (
    "_*.py",
    "*.pyc",
    "*.pyo",
    ".DS_Store",
)


def should_skip(path: Path) -> bool:
    rel_parts = path.relative_to(ROOT).parts
    if any(p in SKIP_DIR_NAMES for p in rel_parts):
        return True
    name = path.name
    if name.startswith("_") and name.endswith(".py"):
        return True
    if name.endswith((".pyc", ".pyo")):
        return True
    if name == "_pack_release.py":
        return True
    return False


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # runtime tree
    (OUT / "assets" / "vendor").mkdir(parents=True)
    (OUT / "data" / "illus").mkdir(parents=True)

    shutil.copy2(ROOT / "index.html", OUT / "index.html")
    shutil.copy2(ROOT / "assets" / "favicon.svg", OUT / "assets" / "favicon.svg")
    shutil.copy2(ROOT / "assets" / "vendor" / "three.min.js", OUT / "assets" / "vendor" / "three.min.js")
    shutil.copy2(
        ROOT / "assets" / "vendor" / "3d-force-graph.min.js",
        OUT / "assets" / "vendor" / "3d-force-graph.min.js",
    )

    # compiled data name (drop .source)
    shutil.copy2(ROOT / "data" / "sunmao-graph.source.js", OUT / "data" / "sunmao-graph.js")
    for name in ("province-outlines.js", "liang-constellations.js", "astro-constellations.js"):
        shutil.copy2(ROOT / "data" / name, OUT / "data" / name)

    illus = ROOT / "data" / "illus"
    if illus.exists():
        for f in illus.iterdir():
            if f.is_file() and not should_skip(f):
                shutil.copy2(f, OUT / "data" / "illus" / f.name)

    html_path = OUT / "index.html"
    html = html_path.read_text(encoding="utf-8")
    html = re.sub(r"data/sunmao-graph\.source\.js\?v=[^\"]+", "data/sunmao-graph.js", html)
    html = re.sub(r"data/province-outlines\.js\?v=[^\"]+", "data/province-outlines.js", html)
    html = re.sub(r"data/liang-constellations\.js\?v=[^\"]+", "data/liang-constellations.js", html)
    html = re.sub(r"data/astro-constellations\.js\?v=[^\"]+", "data/astro-constellations.js", html)
    # quiet one noisy console line in release
    html = re.sub(
        r"\n\s*console\.log\('榫卯知识图谱 v3[\s\S]*?\);\n",
        "\n",
        html,
        count=1,
    )
    html_path.write_text(html, encoding="utf-8")

    bat = """@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  Sunmao Knowledge Graph - local preview
echo  Starting http://127.0.0.1:8080/
echo  Close this window to stop the server.
echo.
where py >nul 2>nul
if %ERRORLEVEL%==0 (set PY=py) else (set PY=python)
start "" http://127.0.0.1:8080/
%PY% -c "import http.server,socketserver; h=socketserver.TCPServer(('127.0.0.1',8080), http.server.SimpleHTTPRequestHandler); print('serving http://127.0.0.1:8080/'); h.serve_forever()"
pause
"""
    (OUT / "启动预览.bat").write_text(bat, encoding="utf-8")

    readme = """# 中国古代榫卯结构知识图谱 — 比赛提交包（开箱即用）

## 运行方式（推荐）
1. 双击 `启动预览.bat`
2. 浏览器自动打开 http://127.0.0.1:8080/

或在本目录执行：

```bash
python -m http.server 8080
```

> 建议通过本地 HTTP 服务打开（WebGL/静态资源），不要直接双击 `index.html`。

## 目录
- `index.html` — 单页入口
- `assets/` — favicon 与 Three.js / 3d-force-graph
- `data/sunmao-graph.js` — 已编译图谱数据
- `data/illus/` — 榫卯示意图
- `data/*-constellations.js` / `province-outlines.js` — 辅助数据

## 操作
- 鼠标：左键旋转 · 滚轮缩放 · 右键平移
- 触屏：单指旋转 · 双指缩放平移
- 点击节点打开知识卡片；顶部可检索定位

本包为静态成品，不含测试脚手架与数据修补脚本。
"""
    (OUT / "使用说明.md").write_text(readme, encoding="utf-8")

    files = [p for p in OUT.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    print("OUT", OUT)
    print("files", len(files), "MB", round(size / 1024 / 1024, 2))
    for p in sorted(files):
        print(" ", p.relative_to(OUT).as_posix())


if __name__ == "__main__":
    main()
