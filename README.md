# Instagram Graph Visualizer 📸🕸️

Instagramのフォロワー同士の「横のつながり（相互フォロー関係）」を分析し、インタラクティブなネットワークグラフとして可視化するツールです。

![Graph Visualization](https://github.com/user-attachments/assets/placeholder.png)
*(ここに完成したグラフのスクリーンショットを貼ると良いでしょう)*

## ✨ 特徴

- **🚀 爆速スクレイピング**: Selenium（ブラウザ操作）を廃止し、**内部APIへの直接アクセス**に切り替えることで、数百倍のデータ収集速度を実現しました。
- **🛡️ 高度な検知回避**: `curl_cffi` を使用してChromeのTLSフィンガープリント（JA3）を偽装。さらに「安全運転モード」を搭載し、人間らしい挙動でBANリスクを低減します。
- **📊 リッチな可視化**: フロントエンドには React + Cytoscape.js を採用。数千ノード規模のネットワークをサクサク操作・探索できます。

## 🛠️ 技術スタック

- **Backend**: Python 3.11+, `curl_cffi` (HTTP Client), `selenium` (Login only)
- **Frontend**: React, TypeScript, Vite, Cytoscape.js
- **Data**: JSON based storage

## 🚀 使い方

### 1. セットアップ

```bash
# Backend dependencies
pip install curl_cffi selenium webdriver-manager

# Frontend dependencies
cd frontend
npm install
```

### 2. データ収集 (Backend)

データ収集は以下の3ステップで行います。すべて `backend/` ディレクトリ内のスクリプトを使用します。

#### Step 1: 認証 (Cookie保存)
Chromeを自動起動してログインし、認証情報（Cookie）を `data/cookies.json` に保存します。

```bash
python backend/auth_helper.py
```

#### Step 2: フォロワー全取得
あなたのフォロワーリストを高速に取得し、`data/followers.json` に保存します。
※ 安全のため、50件ごとに長めの休憩を挟みます。

```bash
python backend/fetch_followers.py
```

#### Step 3: 関係性データの構築 (共通の知り合い検索)
リストアップされたユーザーの「共通のフォロワー」をAPI経由で取得し、`data/graph_data.json` を構築します。
※ **最も時間がかかる工程です。** 中断しても続きから再開可能です。

```bash
python backend/fetch_relationships.py
```

### 3. 可視化 (Frontend)

収集した `data/graph_data.json` を読み込んでグラフを描画します。

```bash
cd frontend
npm run dev
```
ブラウザで `http://localhost:5173` にアクセスしてください。

## ⚠️ 注意事項

- **自己責任でご利用ください**: スクレイピングはInstagramの利用規約に抵触する可能性があります。過度なアクセスはアカウントの一時制限（アクションブロック）や凍結のリスクがあります。
- **安全運転モード**: デフォルトで低速モード（Safe Mode）になっています。設定ファイルやコード内の待機時間を短くするとリスクが高まりますのでご注意ください。

## 📂 ディレクトリ構成

```
.
├── backend/
│   ├── auth_helper.py         # ログイン・Cookie保存
│   ├── fetch_followers.py     # フォロワー取得スクリプト
│   └── fetch_relationships.py # 関係性取得・グラフ構築スクリプト
├── data/                      # 生成されたデータ (JSON)
└── frontend/                  # 可視化用 Webアプリケーション
```
