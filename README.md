# 个人记账工作台

纯 Python 的 NiceGUI 工作台。界面、交互和图表配置全部写在 Python 里，不使用独立的 HTML / CSS / JavaScript 文件。

- 左侧：对话 / 分析台切换
- 对话页：消息显示 + 输入框；默认不自动回复
- 分析台：日 / 周 / 月 / 年统计、日期选择、柱状图、环形图、折线图
- 饼图直接显示分类和百分比；柱状图分类名称使用加粗大字号
- 默认使用 `demo_data.py` 的本地演示数据；可在 `backend.py` 接入真实后端

## 项目背景与需求

**1.确定统一使用的开发语言和数据库**
- 前端:NiceGUI
- 后端:python开发
- 数据库:mysql

**2.确定智能体赛道开发的项目和要实现的功能**

选题 *A：个人记账与消费分析 AI 助手*

1. *自然语言记账 + 小票 / 截图 OCR 录入*
   - 支持一句话记账，例如「午饭 25，和同事 AA」
   - 支持上传小票或支付截图，识别出金额、商户、时间
   - 识别结果允许用户确认或修正后再入库
2. *消费自动分类与统计*
   - 对每笔消费给出类别（餐饮、交通、购物等），类别体系自行设计
   - 按类别、按时间维度统计，结果可查询
3. *自然语言查账*
   - 例如「我上个月吃饭花了多少？」「这个月哪类花得最多？」
   - 需要真正解析时间范围与类别，而不是把问题原样丢给模型自由回答

## 运行

需要 Python 3.10+。先安装依赖：

```bash
python -m pip install -r requirements.txt
```

启动：

```bash
python app.py
```

默认地址为 <http://127.0.0.1:8080/>。不想自动打开浏览器时：

```bash
python app.py --no-open
```

也可以自定义监听地址和端口：

```bash
python app.py --host 127.0.0.1 --port 8090
```

## Docker

需要安装 Docker Desktop 或 Docker Engine。镜像默认使用 `Asia/Shanghai` 时区。

使用 Docker Compose 构建并启动：

```bash
docker compose up --build -d
```

然后访问 <http://127.0.0.1:8080/>。停止：

```bash
docker compose down
```

默认把宿主机 `8080` 映射到容器 `8080`。如果端口已被占用，可以通过 `APP_PORT` 修改宿主机端口：

```bash
# macOS / Linux
APP_PORT=8090 docker compose up --build -d

# Windows PowerShell
$env:APP_PORT="8090"; docker compose up --build -d
```

然后访问 <http://127.0.0.1:8090/>。

也可以直接使用 Docker：

```bash
docker build -t ledger-workbench .
docker run --rm --init -p 8080:8080 ledger-workbench
```

如果宿主机端口不同：

```bash
docker run --rm --init -p 8090:8080 ledger-workbench
```

构建时也可以覆盖时区：

```bash
docker build --build-arg TZ=Asia/Shanghai -t ledger-workbench .
```

当前数据在内存中生成，容器重启后会恢复演示数据，不需要额外挂载数据卷。

## GitHub Actions 自动构建镜像

仓库包含 [.github/workflows/docker-publish.yml](.github/workflows/docker-publish.yml)。推送到 `main` 或 `master` 分支、创建 `v*` 标签，或手动运行工作流时，会自动构建并发布多架构 Docker 镜像到 GitHub Container Registry：

```text
ghcr.io/<你的用户名>/<仓库名>:latest
```

推送后：

1. 打开 GitHub 仓库的 **Actions** 页面，运行或等待 **Docker image** 工作流完成。
2. 如果希望其他人无需登录即可拉取镜像，需要在仓库的 **Packages** 设置中把该镜像可见性设为 **Public**。
3. 使用者可以运行：

```bash
docker pull ghcr.io/<你的用户名>/<仓库名>:latest
docker run --rm --init -p 8080:8080 ghcr.io/<你的用户名>/<仓库名>:latest
```

镜像名统一转为小写。该应用没有登录鉴权，不要把带有真实数据的实例直接暴露到公网。

## 接入后端

默认 `backend.py` 中的开关为 `False`，页面只读取本地演示数据，不发送网络请求。

需要接后端时，打开 [backend.py](backend.py)，替换文件开头的所有 `****`：

```python
USE_BACKEND_STATS = True
USE_BACKEND_CHAT = True

BASE_URL = "http://127.0.0.1:8000"
STATS_PATH = "/api/stats"
CHAT_PATH = "/api/chat"
```

然后按你的实际接口修改三部分：

1. **请求格式**：`build_stats_params()` 和 `build_chat_payload()`。
2. **响应格式**：`parse_stats_response()` 和 `parse_chat_response()`。
3. **鉴权头**：如需要，在 `HEADERS` 中配置 `Authorization` 等字段。

默认请求约定：

```text
GET  {BASE_URL}{STATS_PATH}?period=month&date=2026-11-21
POST {BASE_URL}{CHAT_PATH}
Body: {"message": "..."}
```

统计接口的返回字段说明写在 [backend.py](backend.py) 的 `parse_stats_response()` 注释中。接口可以返回数据对象本身，也可以返回 `{"data": {...}}`。聊天接口的回复字段支持 `reply`、`message`、`content`、`text`，或直接返回字符串。

可以单独启用统计或聊天：

```python
USE_BACKEND_STATS = True
USE_BACKEND_CHAT = False
```

- 统计开关打开：分析台通过后端获取数据。
- 聊天开关打开：发送消息后请求后端并显示回复。
- 两个开关都关闭：完全使用本地演示数据，聊天不自动回复。

`BACKEND_BASE_URL`、接口路径和请求/响应格式都集中在 `backend.py` 中，不需要改 `app.py`。

## 文件说明

```text
.
├── app.py                              # NiceGUI 界面、导航、聊天、筛选和 ECharts 图表
├── demo_data.py                        # 演示账目数据与统计计算
├── backend.py                          # 后端地址、请求格式、响应解析模板
├── requirements.txt                    # Python 依赖
├── Dockerfile                          # Docker 镜像定义
├── docker-compose.yml                  # Docker Compose 启动配置
├── .dockerignore
├── .gitignore
├── .github/workflows/docker-publish.yml # 自动构建并发布 GHCR 镜像
├── README.md
└── screenshots/
    ├── final-chat.png
    ├── final-analysis.png
    ├── mobile-chat.png
    └── mobile-analysis.png
```

## 界面行为

- **对话**：默认只显示用户消息；开启 `USE_BACKEND_CHAT` 后会请求后端 `CHAT_PATH` 并显示回复。
- **分析台**：
  - 在「日 / 周 / 月 / 年」之间切换统计粒度；
  - 使用日期选择器跳转，或通过左右按钮切换周期，点击「今天」回到当前周期；
  - 总支出、日均、笔数、主要分类随筛选更新；
  - 分类支出柱状图、支出结构环形图和消费趋势折线图同步刷新；
  - 饼图标签同时展示分类名称和百分比。

## 说明

- 当前默认是本地演示模式，没有启动后端服务，也不会自动调用外部接口。
- 所有本地账目为演示数据，刷新页面或重启应用后会重新生成。
- NiceGUI 会在浏览器中渲染页面，ECharts 静态资源由 NiceGUI 本地提供，不依赖外部图表 CDN。
- Docker 镜像包含 `backend.py`；如果在 Docker 中启用后端，请确保容器能访问对应的后端地址。
