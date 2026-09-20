"""撮影用の隔離アプリ起動(一時DATA_DIR + uvicorn)。

本番・本体のdata/には一切触れない。手順:
  1. 一時ディレクトリを作る(DATA_DIR)。
  2. 本体ローカルの content.db(語彙・フレーズ)を **読み取り専用** で開き、
     SQLiteのbackup APIで一時DATA_DIRへ複製する(本体側は変更しない)。
  3. 一時DATA_DIR/audio を、本体のdata/audio(実際のAI音声mp3)へのシンボリック
     リンクにする(アプリは保存済みmp3を読んで返すだけ。OPENAI_API_KEYは
     「本物ではないダミー値」で、外部通信も遮断するので合成も課金も起きない。
     詳細は start() のコメント)。
  4. core.db/logs.db は空のまま(ALLOW_FRESH_DB=1)=ユーザー0人・未登録ゲスト視点。
  5. 空きポート(8790番台)でuvicornを起動し、疎通を確認する。

.envは読まない。環境変数は明示的に渡し、リポジトリ直下に.envが無いworktreeで
動かす想定(あっても読まれるのはアプリ側のload_dotenvのみ)。
"""

from __future__ import annotations

import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

# このファイル = <repo>/scripts/videos/lib/appserver.py
REPO_ROOT = Path(__file__).resolve().parents[3]


# 本体(メインのチェックアウト)のデータ置き場。worktreeからでも参照できるよう、
# 環境変数で上書き可能にしつつ、既定はworktreeの親をたどって探す。
def _find_main_data_dir() -> Path:
    env = os.environ.get("VIDEO_SRC_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    # <main>/.claude/worktrees/<name>/ から3つ上が本体のリポジトリルート
    for cand in (REPO_ROOT, *REPO_ROOT.parents):
        if (cand / "data" / "content.db").exists():
            return cand / "data"
    raise RuntimeError(
        "本体のdata/content.dbが見つかりません。環境変数 VIDEO_SRC_DATA_DIR に"
        "本体のdataディレクトリを指定してください。"
    )


def _find_venv_python() -> str:
    env = os.environ.get("VIDEO_PYTHON")
    if env:
        return env
    for cand in (REPO_ROOT, *REPO_ROOT.parents):
        p = cand / ".venv" / "bin" / "python"
        if p.exists():
            return str(p)
    return sys.executable


def _free_port(start: int = 8790, end: int = 8890) -> int:
    for port in range(start, end):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("空きポートがありません")


class AppServer:
    """with 文で使う。`.url` にアプリのベースURL、`.data_dir` に一時DATA_DIR。"""

    def __init__(self, keep: bool = False):
        self.src_data = _find_main_data_dir()
        self.data_dir = Path(tempfile.mkdtemp(prefix="nyangai_video_"))
        self.keep = keep
        self.port = 0
        self.proc: subprocess.Popen | None = None
        self.log_path = self.data_dir / "uvicorn.log"

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def _prepare_data(self) -> None:
        src = self.src_data / "content.db"
        dst = self.data_dir / "content.db"
        # 読み取り専用URIで開いてbackup(WALがあっても整合したコピーになる)。
        ro = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
        try:
            out = sqlite3.connect(dst)
            try:
                ro.backup(out)
            finally:
                out.close()
        finally:
            ro.close()
        audio_src = self.src_data / "audio"
        if not audio_src.is_dir():
            raise RuntimeError(f"音声ディレクトリがありません: {audio_src}")
        os.symlink(audio_src, self.data_dir / "audio")

    def start(self) -> "AppServer":
        self._prepare_data()
        self.port = _free_port()
        # OPENAI_API_KEY について: 空のままだとサーバーが ai_enabled=false と
        # 答え、フロント(speech.js)は保存済みmp3を取りに行かずブラウザの
        # 合成音声にフォールバックし、画面にも「⚠️ AI未設定」が出てしまう
        # (本番の見た目・音と食い違う)。そこで「本物ではないダミー値」を渡す。
        # 保存済みmp3を返すだけなら外部通信は起きない。万一未保存の音声を
        # 要求しても、①ダミー鍵なので課金されず ②下の死んだプロキシで
        # 外部へ出られない(=失敗して終わる)。実際の鍵は一切使わない。
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "DATA_DIR": str(self.data_dir),
            "MULTIUSER": "1",
            "OPENAI_API_KEY": "sk-video-shoot-dummy-not-a-real-key",
            "SESSION_SECRET": "x",
            "ALLOW_FRESH_DB": "1",
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "http_proxy": "http://127.0.0.1:9",
            "https_proxy": "http://127.0.0.1:9",
            "NO_PROXY": "127.0.0.1,localhost",
        }
        logf = open(self.log_path, "wb")
        self.proc = subprocess.Popen(
            [_find_venv_python(), "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", str(self.port)],
            cwd=str(REPO_ROOT), env=env, stdout=logf, stderr=subprocess.STDOUT,
        )
        deadline = time.time() + 60
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(
                    "アプリの起動に失敗しました:\n"
                    + self.log_path.read_text(errors="replace")[-2000:])
            try:
                with urllib.request.urlopen(self.url + "/", timeout=2) as r:
                    if r.status == 200:
                        return self
            except Exception:
                time.sleep(0.5)
        raise RuntimeError("アプリの起動待ちがタイムアウトしました")

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if not self.keep:
            # symlinkを先に外す(rmtreeが本体のaudioに入らないように)
            link = self.data_dir / "audio"
            if link.is_symlink():
                link.unlink()
            shutil.rmtree(self.data_dir, ignore_errors=True)

    def __enter__(self) -> "AppServer":
        try:
            return self.start()
        except BaseException:
            self.stop()   # 起動失敗でも一時dir・プロセスを残さない
            raise

    def __exit__(self, *exc) -> None:
        self.stop()
