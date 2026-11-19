# BodyLens

[English](README.md) · [Español](README_ES.md) · [Català](README_CA.md) · [Français](README_FR.md) · [Italiano](README_IT.md) ·
[Deutsch](README_DE.md) · [Português](README_PT.md) · [Nederlands](README_NL.md) · [中文](README_ZH.md) ·
**日本語**

**BodyLens** は、自分でホストできるマルチユーザー対応のパーソナル健康管理 Web アプリです。**Withings** の体重計で測った体重と体組成に、スマートフォンや時計が記録するデータ（睡眠、アクティビティ、心拍数、HRV、SpO2、VO2 max、心電図、周期、気分など）を、**Apple ヘルスケア**または **Android の Health Connect** から集約します。自分のサーバーで Docker 上で動作し、データは自動的に届き、各ユーザーには自分のデータだけが表示されます。

## 機能

- **サマリー：** トレンド体重、プランの進捗、「今日のひと目」（コンディション、睡眠、睡眠バランス、HRV、歩数）、自動で作られる気づきとアラート。
- **体重：** 平滑化したトレンド、目標ペース付きのプラン、予測、週、カレンダー、マイルストーン。年をまたぐ体重履歴、減量の試みとリバウンド。
- **身体：** 体組成（脂肪、筋肉、水分、骨）、年齢と性別ごとの範囲つき BMI/FFMI、メジャーによる採寸、心臓（安静時心拍数、HRV、SpO2、VO2 max、心電図、心拍数アラート）、ウェルビーイング。
- **アクティビティ：** リングと目標つきの歩数、カロリー、運動時間、ワークアウトと体重との関係。
- **睡眠：** 昨夜の睡眠ステージ、7 晩の睡眠バランス、昼寝、目標スケジュール、分析。AutoSleep と Apple Watch のデータは独自のルール（17:00 から 17:00 までの区間、中途覚醒、昼寝）で統合されます。
- **食事：** 食べるもの、飲むもの、運動をもとにした毎日のスコアと、体重への推定効果。
- **プライベート：** 周期（予測つき）、性生活、気分。プライベート PIN で保護されます。
- アプリ内の**ヘルプ**：各モジュールのヘルプ、この README、変更履歴を、あなたの言語で。
- 選んだ期間の **PDF レポート**と、JSON および CSV 形式の**完全バックアップ**。
- **インターフェース：** ライトとダークのテーマ、スマートフォン向けの設計（ブラウザからアプリとしてインストール可能）、スワイプ操作、最大 1600 px のワイド画面レイアウト。
- **言語：** 英語（デフォルト）、スペイン語、カタルーニャ語、フランス語、イタリア語、ドイツ語、ポルトガル語、オランダ語、中国語、日本語。言語はアカウントごとに選べ、メールは受信者の言語で届きます。

### アカウント

- **複数のアカウント**があり、それぞれが自分のデータを持ち、ユーザー名とパスワードでサインインします。
- **登録：** サインインページからのアクセスリクエスト（管理者が承認し、メールで通知）、または 1 回限りの招待リンク。
- **カップル：** 2 つのアカウントを連携して、周期とプライベートな記録を共有し、一緒に編集できます。
- **プロフィール：** 各アカウントは複数のプロフィール（PIN は任意）を持て、*アカウント*画面で管理します。
- **管理：** ユーザー（ユーザー名、名前、メール、パスワード、有効スイッチ、管理者ロール）、アクセスリクエスト、招待、メール (SMTP)、Withings アプリの認証情報、バックアップ、データソース。

### 自動で届くデータ

- **Withings：** 各アカウントが OAuth で接続します。体重測定、体組成、アクティビティ、ワークアウト、睡眠、SpO2、VO2 max、心電図は数分ごとに取得され、Withings が新しい測定を通知したときは即座に取得されます。
- **Apple ヘルスケア：** iPhone アプリ *Health Auto Export* が、アカウントごとの専用アドレスにデータを送信します。
- **Android：** BodyLens Android アプリ（`android/` 内）が Health Connect を読み取り、同じ形式で 1 時間ごとに送信します。
- 03:30 にデータベースを**毎日バックアップ**します（直近の 30 件を保持）。

## 構成

```
browser / phone (PWA) ── HTTPS (reverse proxy) ──► BodyLens container
                                                   FastAPI + SQLite + scheduler
Withings (OAuth + webhook) ───────────────────────►│
Health Auto Export (iPhone) / Android app ────────►│  POST /api/ingest/hae/<token>
```

- **フロントエンド：** 1 枚のページ（`src/frontend/app/`）で、もともとは claude.ai のアーティファクトでした。小さなレイヤー（`src/frontend/compat/claude-shim.js`）を通じて提供され、ページがかつて claude.ai に求めていた機能（`db`、`user`、`downloads` など）をサーバー API で実現します。
- **バックエンド：** Python 3.12、FastAPI、`/data` 内の SQLite (WAL)。スケジューラーを内蔵した単一プロセスです。
- **翻訳：** カタログは英語（`src/frontend/i18n/catalog.json`）で、各言語は `src/frontend/i18n/locales/<lang>.json` です。ページは `src/frontend/i18n/i18n.js` がブラウザ上で翻訳し、数値と日付の書式も整えます。サーバーはメールに同じファイルを使います。ヘルプ（`help/en/`）、この README、変更履歴は英語で書かれ、Claude API で各アカウントの言語に自動翻訳されます（キーは「管理 → 翻訳」で設定します）。各翻訳は英語の文章が変わるまで保持されます。
- **セキュリティ：** argon2 によるパスワード、サーバー側セッション（HttpOnly/Secure/SameSite クッキー）、すべての書き込みに付く CSRF 対策ヘッダー、レート制限、アカウントごとの分離、暗号化した OAuth トークン。シークレットは環境変数またはサーバーのデータベースにのみ置きます。

## リポジトリの構成

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

## 開発

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
最後のコマンドは http://localhost:8000 をホットリロード付きで起動します。ページは `src/` からそのまま配信され（再読み込みするだけ）、バックエンドは保存時に再起動します。`tools/dev-data.sh` はサーバーのデータを `data-dev/` にコピーします（開発中の変更が元に戻ることはありません）。`docker compose -f docker/compose.dev.yml up --build` も使えます。

## デプロイ

現在のバージョンのブランチ（例：`0.1.0`）に push するたびに、テストが実行され、イメージ `jaimetur/bodylens:latest`（amd64 と arm64）が Docker Hub に公開されます。`main` は `jaimetur/bodylens:main` を公開します。サーバーには `docker/compose.yml` と `.env` ファイルを置きます。NAS はスタックのフォルダーからコードをマウントするので、`tools/deploy.sh` なら新しいイメージを待たずに数秒でコミットをデプロイできます。詳しい手順：[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)（英語）。

## 翻訳への協力

必要なのは英語だけです。言語を追加したり改善したりするには、[`src/frontend/i18n/README.md`](src/frontend/i18n/README.md)（英語）を参照してください。ヘルプ、README、変更履歴は自動的に翻訳されます。編集するのは英語のファイルだけです。

## ドキュメント

- 使い方のヘルプ：[`help/`](help/en/README.md)（英語。アプリ内の*ヘルプ*にもあります）
- 各バージョンの変更点：[`CHANGELOG.md`](CHANGELOG.md)
- コーディングエージェント向けの指示：[`AGENTS.md`](AGENTS.md)

個人データがリポジトリに入ることはありません。データベース、JSON バックアップ、`.env` は `.gitignore` に入っています。
