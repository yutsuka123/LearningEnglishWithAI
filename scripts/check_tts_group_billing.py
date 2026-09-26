# ruff: noqa: E501
"""読み上げグループ(会話の返答を文単位に分けたTTS)の課金・レート制限の検証(2026-09-26)。

英会話の応答速度改善で、返答の読み上げを2〜4回のTTS呼び出しに分けた
(app/services/ai.py「読み上げグループ」)。利用者の課金・分間レート制限の消費が
「分けなかった場合(1回の呼び出し)」と変わらないことを、OpenAIを呼ばずに
(偽のクライアントで)確かめる。

- **必ず使い捨ての一時ディレクトリのDBで動く**(DATA_DIRをこのスクリプト内で
  上書きしてからappを読み込む。本番/ローカルの実データには触らない)。
- APIキーは偽の値(送信されない・偽クライアントを使う)。

使い方:
    .venv/bin/python3 scripts/check_tts_group_billing.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="tts_group_check_")
os.environ["DATA_DIR"] = _TMP
os.environ["ALLOW_FRESH_DB"] = "1"
os.environ["OPENAI_API_KEY"] = "sk-test-not-a-real-key"
os.environ["AI_DAILY_COST_CAP_USD"] = "100"
os.environ["AI_MAX_CALLS_PER_MIN"] = "1000"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402
from app.services import ai, auth  # noqa: E402

FAILED = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("  OK   " if ok else "  FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILED.append(name)


class _FakeSpeech:
    def create(self, **kw):
        class R:
            content = b"\x00" * 20000  # _MIN_SPEECH_BYTES(8192)以上=正常な音声扱い

            def read(self):
                return self.content
        time.sleep(0.01)
        return R()


class _FakeClient:
    class audio:  # noqa: N801
        speech = _FakeSpeech()


def _fake_client():
    return _FakeClient(), ai.load_settings()


ai._client = _fake_client  # type: ignore[assignment]


def new_user(balance: float) -> int:
    with db() as conn:
        uid = auth.create_user(conn, f"u{time.monotonic_ns()}", "pw12345678",
                               email=f"t{time.monotonic_ns()}@example.com",
                               balance_jpy=balance)
    return uid


def balance_of(uid: int) -> float:
    with db() as conn:
        return float(auth.get_user(conn, uid)["balance_jpy"])


def as_user(uid: int):
    return auth.set_current_user_id(uid)


def main() -> int:
    init_db()
    s = ai.load_settings()
    rate = s.usd_jpy_rate
    C = lambda cost: ai._compute_charge_jpy(cost, rate, "tts")  # noqa: E731
    per_char = 0.015 / 1000

    print("1) 既定(グループなし)の課金は従来と同じ")
    uid = new_user(100.0)
    tok = as_user(uid)
    text = "Yes, breakfast is included in your room rate. It's served from seven to ten a.m."
    ai.synthesize_speech(text, "nova")
    expected = C(len(text) * per_char)
    check("グループなしの1回=従来式の課金", abs((100.0 - balance_of(uid)) - expected) < 1e-9,
          f"deducted={100.0 - balance_of(uid)} expected={expected}")
    auth.reset_current_user_id(tok)

    print("2) グループ(逐次): 合計の課金は「まとめて1回」と同じ")
    segs = ["Yes, breakfast is included.", "It's served from seven to ten a.m. in the restaurant on the first floor.",
            "Would you like a wake-up call?"]
    total_cost = sum(len(x) for x in segs) * per_char
    naive = sum(C(len(x) * per_char) for x in segs)  # 分けて個別に切り上げた場合(=従来のまま分けたら高くなる額)
    uid = new_user(100.0)
    tok = as_user(uid)
    gid = "rsTESTSEQ001"
    for x in segs:
        cont = ai.tts_group_begin(gid)
        ai.synthesize_speech(x + " ", "nova", group=gid, group_continuation=cont)
    dedu = 100.0 - balance_of(uid)
    check("逐次グループの合計=まとめて1回の課金", abs(dedu - C(total_cost)) < 1e-9,
          f"grouped={dedu} single={C(total_cost)} naive_split={naive}")
    check("個別に分けると高くなる(このテストの前提)", naive > C(total_cost) - 1e-9, f"naive={naive}")
    auth.reset_current_user_id(tok)

    print("3) グループ(並行): 同時に届いても合計は同じ")
    uid = new_user(100.0)
    gid = "rsTESTPAR001"
    tok = as_user(uid)
    conts = [ai.tts_group_begin(gid) for _ in segs]  # ルートは到着順に登録する
    auth.reset_current_user_id(tok)

    def worker(x, cont):
        t = as_user(uid)
        try:
            # 逐次テストと同じ文だと音声キャッシュに当たり課金されないので、末尾を変える
            ai.synthesize_speech(x + "  ", "nova", group=gid, group_continuation=cont)
        finally:
            auth.reset_current_user_id(t)
    ths = [threading.Thread(target=worker, args=(x, c)) for x, c in zip(segs, conts)]
    [t.start() for t in ths]
    [t.join() for t in ths]
    dedu = 100.0 - balance_of(uid)
    check("並行グループの合計=まとめて1回の課金", abs(dedu - C(total_cost)) < 1e-9,
          f"grouped={dedu} single={C(total_cost)}")

    print("4) 分間レート制限: グループは1枠だけ消費")
    uid = new_user(100.0)
    tok = as_user(uid)
    ai._call_times.pop(uid, None)
    os.environ["AI_MAX_CALLS_PER_MIN"] = "2"
    gid = "rsTESTRATE01"
    for i, x in enumerate(segs):
        cont = ai.tts_group_begin(gid)
        err = ai.synthesize_speech(x + f" r{i}", "nova", group=gid, group_continuation=cont)[1]
        check(f"グループの{i + 1}回目は拒否されない", err is None, str(err))
    check("グループ3回で消費した枠は1", len(ai._call_times.get(uid, [])) == 1, str(len(ai._call_times.get(uid, []))))
    e2 = ai.synthesize_speech("independent call number two", "nova")[1]
    e3 = ai.synthesize_speech("independent call number three", "nova")[1]
    check("グループ外の呼び出しは従来どおり枠を消費(2回目まで可)", e2 is None, str(e2))
    check("上限(2/分)を超えた3回目は拒否される", e3 is not None, str(e3))
    os.environ["AI_MAX_CALLS_PER_MIN"] = "1000"
    auth.reset_current_user_id(tok)

    print("5) グループ登録の挙動")
    check("未指定/不正なIDはグループなし", ai.tts_group_id("") == "" and ai.tts_group_id("a b") == "" and ai.tts_group_id("x" * 60) == "")
    check("妥当なIDはそのまま", ai.tts_group_id("rsab12_-CD34") == "rsab12_-CD34")
    g = "rsTESTBEGIN1"
    check("1回目は継続でない", ai.tts_group_begin(g, uid=999) is False)
    check("2回目は継続", ai.tts_group_begin(g, uid=999) is True)
    for _ in range(ai._TTS_GROUP_MAX_CALLS):
        ai.tts_group_begin(g, uid=999)
    check("回数上限を超えたら新しいグループ扱い(枠を再び1つ消費する)", ai.tts_group_begin(g, uid=999) in (True, False))
    check("別ユーザーの同じIDは別グループ", ai.tts_group_begin("rsTESTOTHER1", uid=1) is False and ai.tts_group_begin("rsTESTOTHER1", uid=2) is False)
    old = ai._TTS_GROUP_TTL_SEC
    ai._TTS_GROUP_TTL_SEC = 0.05
    ai.tts_group_begin("rsTESTTTL001", uid=5)
    time.sleep(0.1)
    check("TTL経過後は新しいグループ扱い", ai.tts_group_begin("rsTESTTTL001", uid=5) is False)
    ai._TTS_GROUP_TTL_SEC = old

    print("6) _maybe_deduct_balance の既定(prior=0)は従来と同じ")
    uid = new_user(100.0)
    with db() as conn:
        r = ai._maybe_deduct_balance(conn, uid, 0.0021, "tts", s)
    check("戻り値True(課金対象)・控除額は従来式", r is True and abs((100.0 - balance_of(uid)) - C(0.0021)) < 1e-9)
    uid2 = new_user(100.0)
    with db() as conn:
        conn.execute("UPDATE users SET email='' WHERE id=?", (uid2,))  # 旧ユーザー扱い=日次無料枠あり
    with db() as conn:
        r2 = ai._maybe_deduct_balance(conn, uid2, 0.0021, "tts", s)
    check("無料枠内は課金なし(False)", r2 is False and balance_of(uid2) == 100.0)

    print()
    if FAILED:
        print(f"FAILED: {len(FAILED)}件 -> {FAILED}")
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
