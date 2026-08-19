"""BASE注文の自動同期（cron用・2026-08-19・Phase B）。

BASE API(OAuth連携済みが前提)から直近の注文を取得し、未登録かつ支払い済み
の注文を base_orders へ自動投入する。管理画面の「今すぐ同期」ボタン
(POST /api/fulfillment/base-sync)と同じロジックを、認証セッション無しで
定期実行できるようにしたもの（VPS上でcron実行を想定）。

使い方(VPS上、eigo-appコンテナの中のpython3で実行を想定):
  docker exec eigo-app python3 scripts/sync_base_orders.py

未連携(管理画面から「BASEと連携する」を未実行)の場合はその旨を出力して
終了する(エラー扱いにはしない。連携前は毎回この状態になるため)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402
from app.routers.fulfillment import sync_orders_from_base  # noqa: E402
from app.services import base_api  # noqa: E402


def main() -> int:
    init_db()
    with db() as conn:
        try:
            result = sync_orders_from_base(conn)
        except base_api.BaseApiError as e:
            print(f"未連携またはエラー: {e}")
            return 0
    print(
        f"確認: {result['checked']}件 / 新規登録: {result['new_orders']}件 "
        f"/ 期間: {result['window']['start']}〜{result['window']['end']}"
    )
    if result["skipped_status"]:
        print(f"対象外status: {result['skipped_status']}")
    if result["errors"]:
        print(f"エラー: {result['errors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
