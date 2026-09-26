# ruff: noqa: E501
"""読み上げグループ(会話の返答を文単位に分けたTTS)の課金・レート制限の検証(2026-09-26)。

英会話の応答速度改善で、返答の読み上げを2〜4回のTTS呼び出しに分けた
(app/services/ai.py「読み上げグループ」)。利用者の課金・分間レート制限の消費が
「分けなかった場合(1回の呼び出し)」と変わらないこと、グループIDを悪用して分間
レート制限を回避できないことを、OpenAIを呼ばずに(偽のクライアントで)確かめる。

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
_API_CALLS = [0]


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("  OK   " if ok else "  FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILED.append(name)


class _FakeSpeech:
    def create(self, **kw):
        _API_CALLS[0] += 1

        class R:
            content = b"\x00" * 20000  # _MIN_SPEECH_BYTES(8192)以上=正常な音声扱い

            def read(self):
                return self.content
        time.sleep(0.01)
        return R()


class _FakeClient:
    class audio:  # noqa: N801
        speech = _FakeSpeech()


ai._client = lambda: (_FakeClient(), ai.load_settings())  # type: ignore[assignment]

_SEQ = [0]


def uniq(text: str) -> str:
    """音声キャッシュ(文面で当たる)に当たらないよう、毎回違う文面にする。"""
    _SEQ[0] += 1
    return f"{text} #{_SEQ[0]}"


def new_user(balance: float, *, legacy: bool = False, daily_cap_usd: float | None = None) -> int:
    with db() as conn:
        uid = auth.create_user(
            conn, f"u{time.monotonic_ns()}", "pw12345678",
            email="" if legacy else f"t{time.monotonic_ns()}@example.com",
            balance_jpy=balance, daily_cap_usd=daily_cap_usd)
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
    segs = ["Yes, breakfast is included.", "It's served from seven to ten a.m. in the restaurant on the first floor.",
            "Would you like a wake-up call?"]

    print("1) 既定(グループなし)の課金は従来と同じ")
    uid = new_user(100.0)
    tok = as_user(uid)
    text = uniq("Yes, breakfast is included in your room rate. It's served from seven to ten a.m.")
    ai.synthesize_speech(text, "nova")
    check("グループなしの1回=従来式の課金", abs((100.0 - balance_of(uid)) - C(len(text) * per_char)) < 1e-9,
          f"deducted={100.0 - balance_of(uid)} expected={C(len(text) * per_char)}")
    auth.reset_current_user_id(tok)

    print("2) グループ(逐次): 合計の課金は「まとめて1回」と同じ")
    texts = [uniq(x) for x in segs]
    total_cost = sum(len(x) for x in texts) * per_char
    naive = sum(C(len(x) * per_char) for x in texts)  # 分けて個別に切り上げた場合(=従来のまま分けたら高くなる額)
    uid = new_user(100.0)
    tok = as_user(uid)
    for x in texts:
        ai.synthesize_speech(x, "nova", group="rsTESTSEQ001")
    dedu = 100.0 - balance_of(uid)
    check("逐次グループの合計=まとめて1回の課金", abs(dedu - C(total_cost)) < 1e-9,
          f"grouped={dedu} single={C(total_cost)} naive_split={naive}")
    check("個別に分けると高くなる(このテストの前提)", naive > C(total_cost) - 1e-9, f"naive={naive}")
    auth.reset_current_user_id(tok)

    print("3) グループ(並行): 同時に届いても合計は同じ")
    texts = [uniq(x) for x in segs]
    total_cost = sum(len(x) for x in texts) * per_char
    uid = new_user(100.0)

    def worker(x):
        t = as_user(uid)
        try:
            ai.synthesize_speech(x, "nova", group="rsTESTPAR001")
        finally:
            auth.reset_current_user_id(t)
    ths = [threading.Thread(target=worker, args=(x,)) for x in texts]
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
    for i in range(3):
        err = ai.synthesize_speech(uniq(segs[i]), "nova", group="rsTESTRATE01")[1]
        check(f"グループの{i + 1}回目は拒否されない", err is None, str(err))
    check("グループ3回で消費した枠は1", len(ai._call_times.get(uid, [])) == 1, str(len(ai._call_times.get(uid, []))))
    e2 = ai.synthesize_speech(uniq("independent call two"), "nova")[1]
    e3 = ai.synthesize_speech(uniq("independent call three"), "nova")[1]
    check("グループ外の呼び出しは従来どおり枠を消費(2回目まで可)", e2 is None, str(e2))
    check("上限(2/分)を超えた3回目は拒否される", e3 is not None, str(e3))
    auth.reset_current_user_id(tok)

    print("5) レート制限の回避ができない(レビュー指摘: 1回目がキャッシュ命中/拒否でも継続扱いにしない)")
    uid = new_user(100.0)
    tok = as_user(uid)
    ai._call_times.pop(uid, None)
    os.environ["AI_MAX_CALLS_PER_MIN"] = "2"
    cached = uniq("This sentence is cached")
    ai.synthesize_speech(cached, "nova")  # キャッシュを作る(枠を1つ消費)
    ai._call_times.pop(uid, None)
    allowed = 0
    for g in range(5):  # 毎回グループIDを変え、1回目はキャッシュ命中→続く新しい文
        gid = f"rsTESTBYPASS{g}"
        ai.synthesize_speech(cached, "nova", group=gid)
        for k in range(3):
            if ai.synthesize_speech(uniq(f"new sentence {g} {k}"), "nova", group=gid)[1] is None:
                allowed += 1
    used = len(ai._call_times.get(uid, []))
    check("グループIDを変えても枠は消費される(上限2/分=2グループ分まで)", used == 2 and allowed == 6, f"slots used={used} allowed uncached calls={allowed} (2 groups x 3)")
    # 1回目が拒否されたグループは開かない
    ai._call_times.pop(uid, None)
    os.environ["AI_MAX_CALLS_PER_MIN"] = "1"
    ai.synthesize_speech(uniq("uses the only slot"), "nova")
    r1 = ai.synthesize_speech(uniq("group first, refused"), "nova", group="rsTESTREFUSE1")[1]
    r2 = ai.synthesize_speech(uniq("group second, must be refused too"), "nova", group="rsTESTREFUSE1")[1]
    check("枠が無いとき、グループの1回目は拒否され2回目も拒否される(拒否がグループを開かない)", r1 is not None and r2 is not None, f"{r1!r} / {r2!r}")
    os.environ["AI_MAX_CALLS_PER_MIN"] = "1000"
    auth.reset_current_user_id(tok)

    print("6) 無料枠の境界: 分けても返答全体の扱いは変わらない(旧ユーザー・レビュー指摘)")
    long_texts = [uniq("A" * 200) for _ in range(3)]
    total_cost = sum(len(x) for x in long_texts) * per_char
    # 枠の残りが小さい旧ユーザー(日次0.001USD・使用前): まとめて1回なら「呼び出し前の累計<枠」で無料
    uid_a = new_user(100.0, legacy=True, daily_cap_usd=0.001)
    tok = as_user(uid_a)
    ai.synthesize_speech(uniq("B" * 600), "nova")
    unsplit = 100.0 - balance_of(uid_a)
    auth.reset_current_user_id(tok)
    uid_b = new_user(100.0, legacy=True, daily_cap_usd=0.001)
    tok = as_user(uid_b)
    for x in long_texts:
        ai.synthesize_speech(x, "nova", group="rsTESTQUOTA01")
    grouped = 100.0 - balance_of(uid_b)
    check("枠を跨いでも、分けた返答の課金=まとめて1回の課金(どちらも0)", abs(grouped - unsplit) < 1e-9 and grouped == 0.0, f"grouped={grouped} unsplit={unsplit}")
    auth.reset_current_user_id(tok)
    # 既に枠超過の旧ユーザー: 従来の課金式どおり(=email無しでも枠0にして超過扱い)
    uid_c = new_user(100.0, legacy=True, daily_cap_usd=0.0)
    tok = as_user(uid_c)
    for x in [uniq(x) for x in segs]:
        ai.synthesize_speech(x, "nova", group="rsTESTQUOTA02")
    dedu_c = 100.0 - balance_of(uid_c)
    exp_c = C(sum(len(x) for x in segs) * per_char + 3 * len(" #1") * per_char)
    check("枠0の旧ユーザー: 分けた合計=まとめて1回", abs(dedu_c - exp_c) < 0.5 + 1e-9 and dedu_c > 0, f"grouped={dedu_c} single~{exp_c}")
    auth.reset_current_user_id(tok)

    print("7) 再生数(playイベント)は、グループで最初に成功した1回だけ")
    check("グループなしは毎回True", ai.tts_group_first_success(1, "") is True and ai.tts_group_first_success(1, "") is True)
    check("グループは1回目だけTrue", ai.tts_group_first_success(7, "rsTESTPLAY001") is True and ai.tts_group_first_success(7, "rsTESTPLAY001") is False)
    check("別ユーザーの同じIDは別グループ", ai.tts_group_first_success(8, "rsTESTPLAY001") is True)

    print("8) グループ登録の挙動")
    check("未指定/不正なIDはグループなし", ai.tts_group_id("") == "" and ai.tts_group_id("a b") == "" and ai.tts_group_id("x" * 60) == "")
    check("妥当なIDはそのまま", ai.tts_group_id("rsab12_-CD34") == "rsab12_-CD34")
    check("ガードを通っていないグループは免除にならない", ai.tts_group_can_skip_rate_limit(9, "rsTESTSKIP001") is False)
    ai.tts_group_note_call(9, "rsTESTSKIP001", consumed_slot=True)
    check("枠を消費した後は免除", ai.tts_group_can_skip_rate_limit(9, "rsTESTSKIP001") is True)
    for _ in range(ai._TTS_GROUP_MAX_CALLS):
        ai.tts_group_note_call(9, "rsTESTSKIP001", consumed_slot=False)
    check("回数上限を超えたら免除しない", ai.tts_group_can_skip_rate_limit(9, "rsTESTSKIP001") is False)
    old = ai._TTS_GROUP_TTL_SEC
    ai._TTS_GROUP_TTL_SEC = 0.05
    ai.tts_group_note_call(5, "rsTESTTTL001", consumed_slot=True)
    time.sleep(0.1)
    check("TTL経過後は免除しない", ai.tts_group_can_skip_rate_limit(5, "rsTESTTTL001") is False)
    ai._TTS_GROUP_TTL_SEC = old
    for i in range(ai._TTS_GROUP_MAX_ENTRIES + 50):
        ai.tts_group_first_success(1000 + i, f"rsTESTFLOOD{i:06d}")
    check("状態の件数に上限がある(ゲストが大量のIDで肥大させられない)", len(ai._tts_groups) <= ai._TTS_GROUP_MAX_ENTRIES, str(len(ai._tts_groups)))

    print("9) _maybe_deduct_balance の既定は従来と同じ")
    uid = new_user(100.0)
    with db() as conn:
        r = ai._maybe_deduct_balance(conn, uid, 0.0021, "tts", s)
    check("戻り値True(課金対象)・控除額は従来式", r is True and abs((100.0 - balance_of(uid)) - C(0.0021)) < 1e-9)
    uid2 = new_user(100.0, legacy=True)
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
