"""未登録ゲスト向け「全語/全フレーズ一覧」の応答を短時間キャッシュする(2026-09-21)。

背景: `/api/words`はログイン不要で約9MB・本番で約0.6〜2秒かけて毎回組み立てる重いAPIで、
連打されるとアプリが飽和しうる(セキュリティ自己点検・DoS増幅)。ゲストの一覧は、
学習記録をゲストが保存しなくなった(=全員が進捗0)ため、**クエリの中身だけで決まる
全員共通の内容**になった。そこで、パラメータを正規化したキーで応答のバイト列を
短時間持ち回す。

前提と安全策:
- ゲストの学習記録を保存しないこと(progress.upsert_progress等のゲスト判定)が前提。
  登録ユーザーには使わない(進捗が人ごとに違うため)。
- キーは「関数が受け取るパラメータ」だけから作る(生のクエリ文字列は使わない)。
  未知のパラメータを付けてキャッシュを素通りさせる手が効かない。
- 件数・時間に上限(最大6件・300秒)。各応答は約9MBなので最大でも数十MBで、コンテナの
  メモリ上限(512MiB)に対して十分小さい。プロセスの再起動(デプロイ)で空になる。
- 管理者が語彙・無料範囲を変更しても、反映は最大300秒遅れる(許容)。
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict

TTL_SECONDS = 300.0
MAX_ENTRIES = 6

_lock = threading.Lock()
_store: "OrderedDict[tuple, tuple[float, bytes]]" = OrderedDict()


def make_key(kind: str, **params) -> tuple:
    """パラメータ(関数が受け取る正規化済みの値)から順序に依存しないキーを作る。"""
    return (kind, tuple(sorted(params.items())))


def get(key: tuple) -> bytes | None:
    now = time.monotonic()
    with _lock:
        hit = _store.get(key)
        if hit is None:
            return None
        expires, body = hit
        if now >= expires:
            del _store[key]
            return None
        _store.move_to_end(key)
        return body


def put(key: tuple, body: bytes) -> None:
    with _lock:
        _store[key] = (time.monotonic() + TTL_SECONDS, body)
        _store.move_to_end(key)
        while len(_store) > MAX_ENTRIES:
            _store.popitem(last=False)


def clear() -> None:
    """テスト用。"""
    with _lock:
        _store.clear()
