# BodyLens

[English](README.md) · [Español](README_ES.md) · [Català](README_CA.md) · [Français](README_FR.md) · [Italiano](README_IT.md) ·
[Deutsch](README_DE.md) · [Português](README_PT.md) · [Nederlands](README_NL.md) · **中文** ·
[日本語](README_JA.md)

**BodyLens** 是一款可自行托管的多用户个人健康网页应用。它把 **Withings** 体重秤测得的体重和身体成分，与手机和手表记录的数据（睡眠、活动、心率、HRV、SpO2、VO2 max、心电图、生理周期、情绪……）汇集在一起，数据来自 **Apple 健康**或 **Android Health Connect**。它在你自己的服务器上用 Docker 运行，数据自动到达，每个人只能看到自己的数据。

## 功能

- **概览：** 趋势体重、计划进度、“今日一览”（准备度、睡眠、睡眠平衡、HRV、步数），以及自动生成的结论和提醒。
- **体重：** 平滑趋势、带目标速率的计划、预测、周视图、日历和里程碑；多年的体重历史、减重尝试和反弹。
- **身体：** 身体成分（脂肪、肌肉、水分、骨量）、按年龄和性别划分范围的 BMI/FFMI、围度测量、心脏（静息心率、HRV、SpO2、VO2 max、心电图、心率提醒）和身心状态。
- **活动：** 步数、卡路里和运动分钟数（含圆环和目标）、锻炼及其与体重的关系。
- **睡眠：** 昨晚的睡眠分期、7 晚睡眠平衡、小睡、目标作息和分析。AutoSleep 和 Apple Watch 的数据按专门的规则合并（17:00 到 17:00 的时间窗口、夜间醒来、小睡）。
- **饮食：** 根据你的饮食、饮水和运动给出每日评分，并估算其对体重的影响。
- **私密：** 生理周期（含预测）、性生活和情绪，由私人 PIN 码保护。
- **帮助**就在应用内：各模块的帮助、本 README 和更新日志，使用你的语言。
- 所选时间段的 **PDF 报告**，以及 JSON 和 CSV 格式的**完整备份**。
- **界面：** 浅色和深色主题，为手机设计（可从浏览器安装为应用），支持滑动手势，宽屏布局最宽可达 1600 px。
- **语言：** 英语（默认）、西班牙语、加泰罗尼亚语、法语、意大利语、德语、葡萄牙语、荷兰语、中文和日语。每个账户选择自己的语言；邮件会以收件人的语言发送。

### 账户

- **多个账户**，各有各的数据，使用用户名和密码登录。
- **注册：** 在登录页提交访问申请，由管理员批准（附邮件通知），或使用一次性邀请链接。
- **情侣：** 两个账户可以关联，共同共享和编辑生理周期与亲密记录。
- **档案：** 每个账户可以有多个档案（可选 PIN 码），在*你的账户*中管理。
- **管理：** 用户（用户名、姓名、邮箱、密码、启用开关、管理员角色）、访问申请、邀请、邮件 (SMTP)、Withings 应用凭据、备份和数据源。

### 自动到达的数据

- **Withings：** 每个账户通过 OAuth 连接；称重、身体成分、活动、锻炼、睡眠、SpO2、VO2 max 和心电图每隔几分钟获取一次，Withings 通知有新测量时则立即获取。
- **Apple 健康：** iPhone 应用 *Health Auto Export* 把数据发送到每个账户专属的地址。
- **Android：** BodyLens Android 应用（位于 `android/`）读取 Health Connect，并每小时以相同格式发送一次。
- 每天 03:30 对数据库进行**每日备份**（保留最近 30 份）。

## 架构

```
browser / phone (PWA) ── HTTPS (reverse proxy) ──► BodyLens container
                                                   FastAPI + SQLite + scheduler
Withings (OAuth + webhook) ───────────────────────►│
Health Auto Export (iPhone) / Android app ────────►│  POST /api/ingest/hae/<token>
```

- **前端：** 单页应用（`src/frontend/app/`），最初是 claude.ai 的 artifact，通过一个小的适配层（`src/frontend/compat/claude-shim.js`）提供服务，该层基于服务器 API 实现了页面过去向 claude.ai 请求的功能（`db`、`user`、`downloads`……）。
- **后端：** Python 3.12、FastAPI、位于 `/data` 的 SQLite (WAL)，单进程，调度器内置其中。
- **翻译：** 目录为英文（`src/frontend/i18n/catalog.json`），每种语言对应 `src/frontend/i18n/locales/<lang>.json`。页面由 `src/frontend/i18n/i18n.js` 在浏览器中翻译，它同时负责数字和日期的格式化；服务器使用相同的文件生成邮件。帮助（`help/en/`）、本 README 和更新日志以英文编写，并通过 Claude API 自动翻译成每个账户的语言（密钥在“管理 → 翻译器”中设置）；每个翻译会一直保留，直到英文文本发生变化。
- **安全：** argon2 密码、服务器端会话（HttpOnly/Secure/SameSite Cookie）、每次写入都带防 CSRF 请求头、频率限制、各账户相互隔离、OAuth 令牌加密；密钥只放在环境变量或服务器数据库中。

## 仓库结构

```
src/backend/app/        server (package "app"), one subpackage per module:
  core/                 settings, SQLite, security, languages, backups, route dependencies
  accounts/             accounts, sessions, invitations, access requests, admin CLI
  admin/                Administration panel
  couples/              couples
  data/                 documents of each account and backup import
  help/                 the Help module (help, README and changelog, translated automatically)
  sheets/               the data tables and the XLSX workbook the page reads
  sources/              Withings and Apple Health / Android ingestion
  sync/                 synchronisation and scheduler
  mail/                 SMTP email
  web/                  page assembly and static files
src/frontend/
  app/                  the app (app_a: styles and views, app_b: core, app_c: interface)
  compat/               window.claude layer
  accounts/ admin/ common/   sign-in, request, registration, Your account and Administration pages
  i18n/                 translator, English catalog and one file per language
android/                Android app (Health Connect → server)
assets/branding/        icons and logo
tests/<module>/         tests (pytest) and tests/frontend/*.mjs (page and translator in jsdom)
help/en/                user help, one file per module (English; translated automatically in the app)
docker/                 Dockerfile and compose files (NAS, hot reload, development)
docs/DEPLOYMENT.md      deployment on a Synology NAS
tools/                  deployment, development server and translation tools
```

## 开发

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e '.[test]'
```
```bash
.venv/bin/python -m pytest -q
```
```bash
(cd src/frontend && npm ci) && PYTHON=$PWD/.venv/bin/python node tests/frontend/smoke.mjs && node tests/frontend/i18n.mjs
```
```bash
tools/dev-data.sh && tools/dev.sh
```
最后一条命令会在 http://localhost:8000 启动带热重载的服务：页面直接从 `src/` 原样提供（刷新即可），后端在保存时自动重启。`tools/dev-data.sh` 会把服务器数据复制到 `data-dev/`（开发中所做的更改不会回传）。也可以使用 `docker compose -f docker/compose.dev.yml up --build`。

## 部署

每次推送到当前版本分支（例如 `0.1.0`）都会运行测试，并把镜像 `jaimetur/bodylens:latest`（amd64 和 arm64）发布到 Docker Hub；`main` 发布 `jaimetur/bodylens:main`。在服务器上：`docker/compose.yml` 加一个 `.env` 文件。NAS 从 stack 文件夹挂载代码，因此 `tools/deploy.sh` 几秒钟就能部署一次提交，无需等待新镜像。完整步骤：[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)（英文）。

## 参与翻译

你只需要懂英语：请参阅 [`src/frontend/i18n/README.md`](src/frontend/i18n/README.md)（英文）来添加或改进一种语言。帮助、README 和更新日志会自动翻译：你只需编辑英文文件。

## 文档

- 使用帮助：[`help/`](help/en/README.md)（英文；应用内的*帮助*中也有）
- 每个版本的更改：[`CHANGELOG.md`](CHANGELOG.md)
- 给编码代理的说明：[`AGENTS.md`](AGENTS.md)

个人数据绝不会进入仓库：数据库、JSON 备份和 `.env` 都在 `.gitignore` 中。
