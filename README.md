# 中国古代榫卯结构知识图谱

三维交互式知识图谱：榫卯类型、古建、典籍、工艺与跨文化关联。

## 快速开始

### 方式一（推荐）
进入 `比赛提交包/`，双击 `启动预览.bat`。

### 方式二
在项目根目录或提交包目录执行：

```bash
python -c "import http.server,socketserver; socketserver.TCPServer(('127.0.0.1',8080), http.server.SimpleHTTPRequestHandler).serve_forever()"
```

浏览器打开：http://127.0.0.1:8080/

> 请通过本地 HTTP 服务打开（WebGL），勿直接双击 `index.html`。

## 仓库结构

| 路径 | 说明 |
|------|------|
| `index.html` | 单页应用（开发/完整版入口） |
| `assets/` | favicon、Three.js、3d-force-graph |
| `data/sunmao-graph.source.js` | 图谱数据源 |
| `data/illus/` | 榫卯示意图 |
| `比赛提交包/` | 开箱即用编译成品（无脚手架） |

## 操作

- 鼠标：左键旋转 · 滚轮缩放 · 右键平移
- 触屏：单指旋转 · 双指缩放平移
- 点击节点查看知识卡片；顶栏可检索定位
