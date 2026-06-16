# 本番(VPS相乗り)用イメージ。軽量・非root・ヘルスチェック付き。
# データ(vocabulary.db / 音声)はイメージに焼かず、ボリュームでマウントする
# （= イメージは小さく、データは rsync で転送・バックアップしやすい）。
FROM python:3.12-slim

# 実行時の最小限のOS依存（curl はヘルスチェック/デバッグ用・任意）。
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

# 依存だけ先に入れてレイヤキャッシュを効かせる。
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体のみコピー（docs/ data/ .env .venv .git は .dockerignore で除外）。
COPY app ./app
COPY static ./static
COPY scripts ./scripts
COPY run.py ./run.py

# 非rootユーザーで実行（セキュリティ）。/data はマウント先なので所有権付与。
RUN useradd -r -u 10001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8000

# ヘルスチェック（/api/health）。Caddy/監視からの死活確認に。
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=3).status==200 else sys.exit(1)"

CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
