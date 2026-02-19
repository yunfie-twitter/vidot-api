# vidot-api

Python FastAPI yt-dlp ダウンロード API サーバー（Redis キューイング対応）

## 概要

vidot-api は、yt-dlp を使用した動画・音声ダウンロード機能を提供する非同期 API サーバーです。Redis ベースのジョブキューシステムにより、大量のダウンロードリクエストを効率的に処理できます。

### 主な機能

- **非同期ダウンロード**: ダウンロード処理はキューイングされ、バックグラウンドで実行
- **進捗トラッキング**: リアルタイムでダウンロード進捗を確認可能
- **フォーマット対応**: MP4（動画）と MP3（音声）の出力に対応
- **スケーラブル**: Worker プロセスを増やすことで同時ダウンロード数を調整可能
- **Docker 完全対応**: すべてのコンポーネントをコンテナ化

## システム構成

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐     ┌─────────────┐
│  API Server │────▶│    Redis    │
│  (FastAPI)  │     │   (Queue)   │
└─────────────┘     └──────┬──────┘
                           │ Jobs
                           ▼
                    ┌─────────────┐
                    │   Worker    │
                    │   (RQ)      │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   yt-dlp    │
                    └─────────────┘
```

### コンポーネント

- **API Server**: FastAPI ベースの REST API（ポート 8000）
- **Redis**: ジョブキューおよび状態管理
- **Worker**: RQ（Redis Queue）ワーカー、yt-dlp を実行
- **yt-dlp**: 動画ダウンロードエンジン（ffmpeg 連携）

## 必要要件

- Docker 20.10+
- Docker Compose 2.0+

または、ローカル実行の場合：

- Python 3.11+
- Redis 6.0+
- ffmpeg
- yt-dlp

## クイックスタート

### 1. リポジトリをクローン

```bash
git clone https://github.com/yunfie-twitter/vidot-api.git
cd vidot-api
git checkout feature/python-api
```

### 2. 環境変数を設定

```bash
cp .env.example .env
# 必要に応じて .env を編集
```

### 3. Docker Compose で起動

```bash
docker-compose up -d
```

これにより以下が起動します：

- API サーバー: `http://localhost:8000`
- Redis: `localhost:6379`
- Worker: バックグラウンドで実行

### 4. 動作確認

```bash
curl http://localhost:8000/health
```

## API 仕様

### ヘルスチェック

```bash
GET /health
```

レスポンス:
```json
{
  "status": "healthy"
}
```

### ダウンロードジョブの作成

```bash
POST /download
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format": "mp4"
}
```

レスポンス:
```json
{
  "jobId": "abc123-def456-ghi789"
}
```

#### パラメータ

- `url` (required): ダウンロード対象の URL
- `format` (required): 出力フォーマット（`mp4` または `mp3`）

### ジョブステータスの確認

```bash
GET /download/{jobId}
```

レスポンス:
```json
{
  "status": "finished",
  "progress": 100.0,
  "filePath": "/app/downloads/video_title.mp4",
  "error": null
}
```

#### ステータス値

- `queued`: キューに追加済み、処理待ち
- `started`: ダウンロード処理中
- `finished`: ダウンロード完了
- `failed`: ダウンロード失敗

## 使用例

### 動画をダウンロード（MP4）

```bash
# 1. ジョブを作成
JOB_ID=$(curl -s -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","format":"mp4"}' \
  | jq -r '.jobId')

echo "Job ID: $JOB_ID"

# 2. ステータスを確認
curl http://localhost:8000/download/$JOB_ID | jq

# 3. 完了まで待機（ポーリング例）
while true; do
  STATUS=$(curl -s http://localhost:8000/download/$JOB_ID | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" = "finished" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done

# 4. 結果を確認
curl http://localhost:8000/download/$JOB_ID | jq
```

### 音声をダウンロード（MP3）

```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","format":"mp3"}' \
  | jq
```

## 設定

### 環境変数

`.env` ファイルで以下の設定が可能です：

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `PORT` | `8000` | API サーバーのポート番号 |
| `DOWNLOAD_DIR` | `/app/downloads` | ダウンロードファイルの保存先 |
| `YTDLP_PATH` | `yt-dlp` | yt-dlp の実行パス |
| `REDIS_HOST` | `redis` | Redis のホスト名 |
| `REDIS_PORT` | `6379` | Redis のポート番号 |
| `REDIS_PASSWORD` | _(空)_ | Redis の認証パスワード（オプション） |
| `REDIS_DB` | `0` | Redis のデータベース番号 |
| `QUEUE_CONCURRENCY` | `2` | Worker の同時実行ジョブ数 |
| `QUEUE_NAME` | `download_queue` | Redis キューの名前 |

### Worker の並列数を調整

同時ダウンロード数を増やす場合は、`.env` ファイルを編集：

```bash
QUEUE_CONCURRENCY=4
```

または、docker-compose.yml で worker をスケールアウト：

```bash
docker-compose up -d --scale worker=3
```

## ディレクトリ構成

```
vidot-api/
├── app/
│   ├── __init__.py         # パッケージ初期化
│   ├── main.py             # FastAPI アプリケーション
│   ├── config.py           # 設定管理（Pydantic Settings）
│   ├── models.py           # リクエスト/レスポンスモデル
│   ├── queue.py            # Redis キュー操作
│   └── worker.py           # yt-dlp ダウンロード処理
├── .env.example            # 環境変数テンプレート
├── .gitignore              # Git 除外設定
├── .dockerignore           # Docker ビルド除外設定
├── Dockerfile              # コンテナイメージ定義
├── docker-compose.yml      # マルチコンテナ構成
├── requirements.txt        # Python 依存パッケージ
├── LICENSE                 # ライセンス
└── README.md               # このファイル
```

## 開発

### ローカル環境でのセットアップ

```bash
# Python 仮想環境を作成
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# Redis を起動（別ターミナルまたは Docker で）
redis-server

# API サーバーを起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Worker を起動（別ターミナル）
rq worker --with-scheduler download_queue
```

### ログの確認

```bash
# すべてのコンテナのログ
docker-compose logs -f

# API サーバーのみ
docker-compose logs -f api

# Worker のみ
docker-compose logs -f worker
```

### コンテナの停止と削除

```bash
# 停止
docker-compose down

# データボリュームも削除
docker-compose down -v
```

## トラブルシューティング

### ダウンロードが失敗する

- Worker のログを確認: `docker-compose logs worker`
- yt-dlp が最新版か確認: コンテナを再ビルド
- URL が有効か確認: yt-dlp で直接テスト

### Redis に接続できない

- Redis が起動しているか確認: `docker-compose ps`
- ヘルスチェックの状態を確認: `docker-compose ps redis`
- ネットワーク設定を確認: `docker network inspect vidot-api_vidot-network`

### Worker が起動しない

- 環境変数が正しく設定されているか確認
- Redis への接続情報を確認
- Worker ログでエラーメッセージを確認

## ライセンス

Apache License 2.0 - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 貢献

Issue や Pull Request を歓迎します。

## 技術スタック

- **Language**: Python 3.11
- **Framework**: FastAPI 0.109+
- **Queue**: Redis + RQ (Redis Queue)
- **Downloader**: yt-dlp
- **Media Processing**: ffmpeg
- **Container**: Docker + Docker Compose
- **Validation**: Pydantic 2.5+
