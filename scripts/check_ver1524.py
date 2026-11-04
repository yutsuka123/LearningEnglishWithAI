"""ver1.5.24 の検査(2026-11-04): 無料範囲外の語・フレーズの「1日の無料再生枠」(ログイン済みは1日10件)+登録の安心文言。

背景(オーナー決定 11/4「最優先案入れる・10件にしましょう」「安心して登録してもらえる文言・ニックネームや捨てアドレスでもよいので積極的に」):
  調べものに来た訪問者の目当ての語は無料範囲の外にあることが多く、無料登録しても聴けない=登録の理由が無かった。
  そこで**ログイン済みの人**は、**事前作成済み(保存済み)の音声に限り**、無料範囲外の語・フレーズを1日10件まで無料で聴けるようにした。

使い方(.envの無いこのworktreeで・本番には触れない・DATA_DIRは使い捨てを推奨):
  PY=<repo>/.venv/bin/python ; S=$(mktemp -d)
  DATA_DIR=$S OPENAI_API_KEY= $PY scripts/check_ver1524.py            # 全部(単体+静的)
  DATA_DIR=$S OPENAI_API_KEY= $PY scripts/check_ver1524.py --static   # 辞書・HTMLの静的検査だけ(DB不要)

  U (コード単体・実際の tts_item / charge_playback_if_needed を呼ぶ):
    U1 無料登録(残高0): 無料範囲外の保存済み音声10件は無料(合成なし・残高変化なし) → 11件目は402で「使い切りました」
    U2 同じ語の聴き直しは枠を使わない(枠が尽きた後でも聴ける) / 無料範囲内は常に無料
    U3 保存されていない音声(未作成の語・声)は枠の対象外=402のまま・枠を消費しない・合成は走らない
    U4 課金ユーザー: 最初の10件は無料(残高不変)・11件目から0.5ptを控除 / 管理者は枠を消費しない
    U5 ゲスト: 範囲外は402で「登録すると1日10件まで」を案内・枠の記録は作られない
    U6 日付の切り替わり(日本時間): 昨日の行は数えず、消費時に自分の古い行だけ消える
    U7 同時実行: 30件を同時に消費しても成功はちょうど10件
    U8 /my-usage の枠の項目・退会時の削除対象
  S (静的): 辞書4言語・HTML・メッセージの整合
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESULTS: list[tuple[bool, str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    RESULTS.append((bool(cond), name, detail))
    print(("  OK   " if cond else "  NG   ") + name + (f"  [{detail}]" if detail and not cond else ""))
    return bool(cond)


# ----------------------------------------------------------------------------- U: コード単体
def unit() -> None:
    from app.database import db, init_db
    from app.routers import auth_routes, learn, system
    from app.services import access_tiers, ai, audio_store, auth

    init_db()
    LIMIT = access_tiers.OUTRANGE_FREE_DAILY_LIMIT
    check("[U0] 枠の上限は10件(オーナー決定 11/4)", LIMIT == 10, str(LIMIT))
    # テストを軽くするため無料範囲を小さくする(判定は呼び出し時にモジュール変数を読む)
    access_tiers.GUEST_WORDS_LIMIT = 3
    access_tiers.FREE_WORDS_LIMIT = 5

    synth_calls: list[dict] = []
    real_synth = ai.synthesize_speech

    def fake_synth(text, voice="alloy", **kw):
        synth_calls.append({"text": text, "voice": voice})
        return b"\xff\xfb\x90\x64" + b"\x00" * 413, None

    ai.synthesize_speech = fake_synth
    skind = audio_store.storage_kind("word", "learn")
    try:
        with db() as conn:
            rows = conn.execute("SELECT id, english FROM words WHERE example != '' ORDER BY id LIMIT 400").fetchall()
            out_ids = [r["id"] for r in rows if not access_tiers.is_free_range(conn, "word", r["id"])][:40]
            in_ids = [r["id"] for r in rows if access_tiers.is_free_range(conn, "word", r["id"])][:2]
            text_of = {r["id"]: r["english"] for r in rows}
            guest_uid = auth.ensure_guest_user_id(conn)
            uF = auth.create_user(conn, "claude-verify-free@example.test", "Passw0rd!x", email="claude-verify-free@example.test", display_name="free")
            uF2 = auth.create_user(conn, "claude-verify-free2@example.test", "Passw0rd!x", email="claude-verify-free2@example.test", display_name="free2")
            uP = auth.create_user(conn, "claude-verify-paid@example.test", "Passw0rd!x", email="claude-verify-paid@example.test", display_name="paid")
            auth.add_balance(conn, uP, 100.0, reason="admin_grant", note="check_ver1524")
            # 保存済み(事前作成)の音声: out_ids の先頭30件に ash を置く。末尾10件は未作成のまま。
            for wid in out_ids[:30] + in_ids:
                audio_store.put(conn, "word", wid, skind, "ash", text_of[wid], b"AUDIO-%d" % wid)
        cached_ids, uncached_ids = out_ids[:30], out_ids[30:40]
        check("[U0] 無料範囲外の語が40件、範囲内の語が2件ある(テストの前提)", len(out_ids) == 40 and len(in_ids) == 2, f"{len(out_ids)}/{len(in_ids)}")

        def play(uid: int, wid: int, voice: str = "ash"):
            auth.set_current_user_id(uid)
            return learn.tts_item(item_type="word", item_id=wid, voice=voice, kind="word", speed="learn")

        def balance(uid: int) -> float:
            with db() as conn:
                return float(auth.get_user(conn, uid)["balance_jpy"] or 0)

        def used_count(uid: int) -> int:
            with db() as conn:
                return access_tiers.outrange_free_status(conn, uid)[0]

        # ---- U1 無料登録(残高0)
        synth_calls.clear()
        res = [play(uF, w) for w in cached_ids[:LIMIT]]
        check("[U1] 無料登録: 無料範囲外の保存済み音声10件が全部200で、中身は保存済みのもの",
              all(r.status_code == 200 for r in res) and all(r.body == b"AUDIO-%d" % w for r, w in zip(res, cached_ids)),
              str([r.status_code for r in res]))
        check("[U1] 合成は1回も走らない・残高も変わらない", not synth_calls and balance(uF) == 0.0, f"{synth_calls} bal={balance(uF)}")
        check("[U1] 残り枠が0になる", used_count(uF) == 0, str(used_count(uF)))
        r11 = play(uF, cached_ids[LIMIT])
        body = r11.body.decode("utf-8", "replace")
        check("[U1] 11件目は402(無料枠を使い切りました+上限の数字+リセット案内)",
              r11.status_code == 402 and "使い切りました" in body and "10" in body and "0時" in body, f"{r11.status_code} {body[:90]}")
        check("[U1] 11件目の拒否では何も消費・記録しない(行は10のまま)", _rows(uF) == LIMIT, str(_rows(uF)))

        # ---- U2 聴き直し・範囲内
        r = play(uF, cached_ids[0])
        check("[U2] 枠が尽きた後でも、今日すでに聴いた語は何度でも200(聴き直しは消費しない)",
              r.status_code == 200 and r.body == b"AUDIO-%d" % cached_ids[0] and _rows(uF) == LIMIT, f"{r.status_code} rows={_rows(uF)}")
        r = play(uF, in_ids[0])
        check("[U2] 無料範囲内の語は枠と無関係に200", r.status_code == 200, str(r.status_code))

        # ---- U3 保存されていない音声は対象外
        synth_calls.clear()
        r = play(uF2, uncached_ids[0])
        body = r.body.decode("utf-8", "replace")
        check("[U3] 未作成の語(保存なし): 402でチャージ案内・合成は走らない", r.status_code == 402 and "チャージ" in body and not synth_calls,
              f"{r.status_code} {body[:60]} synth={len(synth_calls)}")
        r = play(uF2, cached_ids[0], voice="echo")
        check("[U3] 別の声(echo)は保存なし=枠の対象外(402・合成なし)", r.status_code == 402 and not synth_calls, f"{r.status_code} synth={len(synth_calls)}")
        check("[U3] 拒否された再生では枠を消費しない(10件のまま)", used_count(uF2) == LIMIT and _rows(uF2) == 0, f"left={used_count(uF2)}")

        # ---- U4 課金ユーザー・管理者
        res = [play(uP, w) for w in cached_ids[:LIMIT]]
        check("[U4] 課金ユーザー: 最初の10件は無料(残高100のまま)", all(r.status_code == 200 for r in res) and balance(uP) == 100.0, f"bal={balance(uP)}")
        r = play(uP, cached_ids[LIMIT])
        check("[U4] 11件目から従来どおり少額を控除(残高が減る・200)", r.status_code == 200 and 99.0 < balance(uP) < 100.0, f"{r.status_code} bal={balance(uP)}")
        bal_after = balance(uP)
        play(uP, cached_ids[LIMIT])
        check("[U4] 直後の聴き直しは再課金なし(5分ルール)", balance(uP) == bal_after, f"{bal_after}->{balance(uP)}")
        before = _rows(1)
        r = play(1, cached_ids[20])
        check("[U4] 管理者は200で枠を消費しない", r.status_code == 200 and _rows(1) == before == 0, f"{r.status_code} rows={_rows(1)}")

        # ---- U5 ゲスト
        r = play(guest_uid, cached_ids[25])
        body = r.body.decode("utf-8", "replace")
        check("[U5] ゲスト: 範囲外は402で『登録すると1日10件まで』を案内", r.status_code == 402 and "登録" in body and "10件" in body, f"{r.status_code} {body[:80]}")
        check("[U5] ゲストでは枠の記録が作られない", _rows(guest_uid) == 0, str(_rows(guest_uid)))

        # ---- U6 日付の切り替わり(日本時間)
        with db() as conn:
            conn.execute("UPDATE outrange_free_plays SET day = date(day, '-1 day') WHERE user_id = ?", (uF,))
        check("[U6] 昨日の行は数えない(残り枠が10に戻る)", used_count(uF) == LIMIT, str(used_count(uF)))
        r = play(uF, cached_ids[LIMIT])
        with db() as conn:
            days = [x[0] for x in conn.execute("SELECT DISTINCT day FROM outrange_free_plays WHERE user_id = ?", (uF,)).fetchall()]
            today = conn.execute("SELECT date('now','+9 hours')").fetchone()[0]
        check("[U6] 翌日の再生は200で、昨日の行は数えない(昨日の行は効果測定用に残り、今日の行が増える)", r.status_code == 200 and sorted(days) == sorted({today, days[0]}) and today in days and used_count(uF) == LIMIT - 1, f"{r.status_code} {days} left={used_count(uF)}")
        import datetime as dt
        jst_today = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=9)).strftime("%Y-%m-%d")
        check("[U6] 『今日』は日本時間の日付(Pythonで独立に計算した値と一致)", today == jst_today, f"{today} vs {jst_today}")

        # ---- U7 同時実行
        with db() as conn:
            uC = auth.create_user(conn, "claude-verify-conc@example.test", "Passw0rd!x", email="claude-verify-conc@example.test", display_name="conc")
        results: list[bool] = []
        lock = threading.Lock()
        barrier = threading.Barrier(30)

        def worker(wid: int) -> None:
            barrier.wait()
            with db() as c:
                ok = access_tiers.try_use_outrange_free_play(c, uC, "word", wid)
            with lock:
                results.append(ok)

        ths = [threading.Thread(target=worker, args=(w,)) for w in cached_ids[:30]]
        [t.start() for t in ths]
        [t.join() for t in ths]
        check("[U7] 30件を同時に消費しても成功はちょうど10件(上限を超えない)", results.count(True) == LIMIT and _rows(uC) == LIMIT,
              f"ok={results.count(True)} rows={_rows(uC)}")

        # ---- U8 /my-usage・退会
        auth.set_current_user_id(uF)
        mu = system.my_usage()
        check("[U8] /my-usage: 上限10・残りと今日の使用済み一覧を返す", mu["outrange_free_limit"] == 10 and mu["outrange_free_left"] == LIMIT - 1
              and mu["outrange_free_used"] == [f"word:{cached_ids[LIMIT]}"], str({k: mu[k] for k in mu if k.startswith("outrange")}))
        auth.set_current_user_id(guest_uid)
        mu = system.my_usage()
        check("[U8] ゲストは残り0・一覧は空(枠が無い)", mu["outrange_free_left"] == 0 and mu["outrange_free_used"] == [] and mu["outrange_free_limit"] == 10, str(mu["outrange_free_left"]))
        check("[U8] 退会時の削除対象に枠の表が入っている", "outrange_free_plays" in auth_routes._WITHDRAW_PERSONAL_TABLES)
        with db() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(outrange_free_plays)")]
        check("[U8] 枠の表にuser_id列がある(退会の一括削除が効く)", "user_id" in cols, str(cols))

        # ---- U9 退会(独立照査HIGH-1): メールアドレス・氏名・アンケートが本当に消える
        with db() as conn:
            uW = auth.create_user(conn, "claude-verify-wd@example.test", "Passw0rd!x", email="claude-verify-wd@example.test", display_name="wd",
                                  full_name="山田太郎", furigana="ヤマダタロウ", display_name_furigana="タロ", survey_age_group="30s", survey_free_text="自由記入")
            conn.execute("INSERT INTO login_log (username, success) VALUES (?, 1)", ("claude-verify-wd@example.test",))
        auth.set_current_user_id(uW)
        play(uW, cached_ids[0])   # 枠を1件使っておく(退会で消えること)
        resp = auth_routes.withdraw(auth_routes.WithdrawIn(reasons=[next(iter(auth_routes.WITHDRAW_REASONS))], detail="claude-verify"))
        check("[U9] 退会が成功する", getattr(resp, "status_code", 200) == 200, str(getattr(resp, "body", resp))[:80])
        with db() as conn:
            ur = dict(conn.execute("SELECT * FROM users WHERE id = ?", (uW,)).fetchone())
            wd = dict(conn.execute("SELECT * FROM account_withdrawals WHERE user_id = ?", (uW,)).fetchone())
            ll = [r[0] for r in conn.execute("SELECT username FROM login_log WHERE username LIKE '%wd@example.test%' OR username LIKE ?", (f"withdrawn_{uW}_%",)).fetchall()]
            rows_left = conn.execute("SELECT COUNT(*) FROM outrange_free_plays WHERE user_id = ?", (uW,)).fetchone()[0]
        blob = json.dumps({k: v for k, v in ur.items() if k not in ("password_hash",)}, ensure_ascii=False) + json.dumps(wd, ensure_ascii=False)
        check("[U9] usersに元のメールアドレス・氏名・フリガナ・アンケートが残らない", all(w not in blob for w in ("wd@example.test", "山田太郎", "ヤマダ", "タロ", "自由記入", "30s")), blob[:200])
        check("[U9] 退会理由の記録に元のメールアドレスを残さない(匿名化後の名前)", wd["username_at_withdrawal"].startswith("withdrawn_") and "example.test" not in wd["username_at_withdrawal"], wd["username_at_withdrawal"])
        check("[U9] ログイン履歴の元のメールアドレスも匿名化される", ll and all(x.startswith("withdrawn_") for x in ll), str(ll))
        check("[U9] 無料再生枠の記録も消える", rows_left == 0, str(rows_left))

        # ---- U10 事前作成が無い声・速度は専用の案内(枠の対象外であることが分かる)
        r = play(uF2, cached_ids[0], voice="echo")
        body = r.body.decode("utf-8", "replace")
        check("[U10] 保存されていない声: 402で『事前に用意されていない・無料枠の対象外』を案内(チャージが要るだけの文ではない)",
              r.status_code == 402 and "事前に用意されていない" in body and "無料枠の対象外" in body, body[:90])
        r = play(uF2, uncached_ids[0])
        check("[U10] 未作成の語も同じ専用の案内", r.status_code == 402 and "事前に用意されていない" in r.body.decode("utf-8", "replace"))

        # ---- U11 枠が尽きた後の拒否は書き込まない(独立照査LOW-1)
        with db() as conn:
            seq0 = conn.execute("SELECT seq FROM sqlite_sequence WHERE name='outrange_free_plays'").fetchone()
        for w in cached_ids[LIMIT + 1: LIMIT + 6]:
            play(uC, w)   # uCは同時実行テストで10件使い切り済み
        with db() as conn:
            seq1 = conn.execute("SELECT seq FROM sqlite_sequence WHERE name='outrange_free_plays'").fetchone()
        check("[U11] 枠を使い切った人の拒否では、行の追加も削除(連番の進み)も起きない", seq0 and seq1 and seq0[0] == seq1[0], f"{seq0 and seq0[0]}->{seq1 and seq1[0]}")

        # ---- U12 効果測定: 枠の使用記録は90日保持(昨日の行は残る)・90日超は掃除される
        with db() as conn:
            conn.execute("INSERT INTO outrange_free_plays (user_id, day, item_type, item_id) VALUES (?, date('now','+9 hours','-100 days'), 'word', 999999)", (uF2,))
            conn.execute("INSERT INTO outrange_free_plays (user_id, day, item_type, item_id) VALUES (?, date('now','+9 hours','-1 day'), 'word', 999998)", (uF2,))
        play(uF2, cached_ids[0])
        with db() as conn:
            kept = {r[0] for r in conn.execute("SELECT item_id FROM outrange_free_plays WHERE user_id = ?", (uF2,)).fetchall()}
        check("[U12] 枠の使用記録: 昨日の行は残り(効果測定用)・100日前の行は消費時に掃除される", 999998 in kept and 999999 not in kept and cached_ids[0] in kept, str(kept))
        check("[U12] 昨日の行は今日の残り枠に数えない", used_count(uF2) == LIMIT - 1, str(used_count(uF2)))

    finally:
        ai.synthesize_speech = real_synth


def _rows(uid: int) -> int:
    from app.database import db
    with db() as conn:
        return conn.execute("SELECT COUNT(*) FROM outrange_free_plays WHERE user_id = ?", (uid,)).fetchone()[0]


# ----------------------------------------------------------------------------- S: 静的
def lang_values(src: str, key: str) -> list[str]:
    out = []
    for m in re.finditer(r'^\s*"' + re.escape(key) + r'":\s*(".*"),\s*$', src, re.M):
        out.append(json.loads(m.group(1)))
    return out


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def static() -> None:
    d = (ROOT / "static/js/i18n_dict.js").read_text(encoding="utf-8")
    a = (ROOT / "static/js/i18n_dict_about.js").read_text(encoding="utf-8")
    login = (ROOT / "static/login.html").read_text(encoding="utf-8")
    about = (ROOT / "static/about.html").read_text(encoding="utf-8")
    cat = (ROOT / "app/services/messages_catalog.py").read_text(encoding="utf-8")
    sys.path.insert(0, str(ROOT))
    from app.services import access_tiers
    LIM = access_tiers.OUTRANGE_FREE_DAILY_LIMIT

    print("S1 新しい辞書キーが4言語そろっている・埋め込み変数が全言語にある")
    for key, var in (("voice.lockedNote", "{limit}"), ("voice.lockedNoteUsed", "{limit}"), ("voice.allowanceNote", "{left}"), ("voice.allowanceReplayNote", None), ("voice.allowanceUsedToast", "{left}")):
        v = lang_values(d, key)
        check(f"{key}: 4言語", len(v) == 4, str(len(v)))
        if var and len(v) == 4:
            check(f"{key}: 4言語とも {var} を含む", all(var in x for x in v))
    for key, var in (("ai.tts_outside_free", "{limit}"), ("ai.tts_allowance_used", "{limit}"), ("ai.tts_not_precreated", "{need}")):
        i = cat.index(f'_m("{key}"'); blk = cat[i:cat.index("\n_m(", i + 5)]
        check(f"{key}: 4言語とも {var} を含む", blk.count(var) == 4, str(blk.count(var)))

    print("S2 静的ページの『10』は枠の定数と一致する(画面の数字と実際の上限の食い違い防止)")
    for key, f in (("signup.benefits", d), ("about.sec.signup.8", a), ("about.sec.tiers.10", a), ("about.sec.tiers.24", a), ("about.sec.tiers.25", a),
                   ("about.sec.tiers.30", a), ("about.sec.tiers.32", a), ("settings.chargeKeyNote", d), ("vocabList.helpText", d), ("list.voiceIconHelp", d)):
        v = lang_values(f, key)
        check(f"{key}: 4言語とも『{LIM}』を含む", len(v) == 4 and all(str(LIM) in x for x in v), str([str(LIM) in x for x in v]))

    print("S3 HTMLの日本語と辞書(ja)が同じ文言")
    for key, html in (("signup.benefits", login), ("signup.safeNote", login), ("signup.emailHint", login), ("about.sec.signup.8", about),
                      ("about.sec.tiers.10", about), ("about.sec.tiers.24", about), ("about.sec.tiers.25", about),
                      ("about.sec.tiers.30", about), ("about.sec.tiers.32", about)):
        src = d if key.startswith(("signup.",)) else a
        ja = lang_values(src, key)[0]
        m = re.search(r'data-i18n(?:-html)?="' + re.escape(key) + r'"[^>]*>(.*?)</(?:p|li)>', html, re.S)
        check(f"{key}: HTMLとjaが同じ", bool(m) and norm(m.group(1).replace('\\"', '"')) == norm(ja), "" if m else "HTMLに無い")

    print("S4 安心文言(signup.safeNote)の中身: 事実だけ・正直な注意・おすすめ")
    for lang, s in zip(("ja", "en", "zh-CN", "zh-TW"), lang_values(d, "signup.safeNote")):
        if lang == "ja":
            need = ["ニックネーム", "使い捨て", "確認メール", "営業・宣伝のメール", "決済情報", "ハッシュ化", "退会", "法令上・運営上必要なものを除く", "絶対に漏れないとは言い切れません", "同じパスワードは使わないで", "おすすめ", "取り戻せないことがある"]
        elif lang == "en":
            need = ["nickname", "throwaway", "confirmation email", "marketing", "payment details", "hashed", "close your account", "legal or operational", "can’t promise", "reuse a password", "recommend", "lose access"]
        elif lang == "zh-CN":
            need = ["昵称", "一次性邮箱", "确认邮件", "营销", "支付信息", "哈希", "退出账号", "法律上或运营上必须保留", "不能保证", "不要使用与其他服务相同的密码", "推荐", "无法找回账号"]
        else:
            need = ["暱稱", "拋棄式信箱", "確認信", "行銷", "付款資訊", "雜湊", "退出帳號", "法律上或營運上必須保留", "無法保證", "不要使用與其他服務相同的密碼", "建議", "無法找回帳號"]
        miss = [w for w in need if w not in s]
        check(f"safeNote[{lang}]: 必要な要素がそろっている", not miss, str(miss))
    banned = ["絶対安全", "完全に安全", "100%安全", "万全", "暗号化して保存", "一切漏れ", "決して漏れ", "必ず守", "absolutely safe", "100% safe", "completely secure", "encrypted"]
    allsafe = " ".join(lang_values(d, "signup.safeNote") + lang_values(d, "signup.benefits") + lang_values(d, "signup.emailHint"))
    check("安心文言に過大な断定(絶対安全・万全・暗号化して保存 など)が無い", not [w for w in banned if w in allsafe], str([w for w in banned if w in allsafe]))
    pp = norm((ROOT / "static/privacy.html").read_text(encoding="utf-8"))
    pp_need = ("本名である必要はなく", "営業・勧誘・宣伝・課金の催促等のメールをお送りすることはありません", "取得・保持しません", "ハッシュ化して保存", "大企業と同等の管理体制を保証するものではありません")
    check("プライバシーポリシーの事実と一致: 『本名でなくてよい』『営業・宣伝メールを送らない』『決済情報を保持しない』『ハッシュ化』『大企業と同等の管理を保証しない(=絶対はない)』",
          all(norm(w) in pp for w in pp_need), str([w for w in pp_need if norm(w) not in pp]))
    check("設定画面の退会説明と一致: 学習データ削除・メールアドレス等の個人情報を消去(法令上・運営上必要なものの例外つき)", "個人情報も消去します" in lang_values(d, "settings.withdrawDesc")[0] and "法令上・運営上必要なもの" in lang_values(d, "settings.withdrawDesc")[0])

    print("S5 簡体字・繁体字の混在が無い(OpenCCがあれば)")
    try:
        import opencc  # type: ignore
        t2s, s2t = opencc.OpenCC("t2s"), opencc.OpenCC("s2t")
        keys_d = ["voice.lockedNote", "voice.lockedNoteUsed", "voice.allowanceNote", "voice.allowanceReplayNote", "voice.allowanceUsedToast", "settings.withdrawDesc", "list.voiceIconHelp", "signup.benefits", "signup.safeNote", "signup.emailHint",
                  "settings.chargeKeyNote", "vocabList.helpText", "flashcard.freeRangeQuestion"]
        keys_a = ["about.sec.signup.8", "about.sec.tiers.10", "about.sec.tiers.24", "about.sec.tiers.25", "about.sec.tiers.30", "about.sec.tiers.32"]
        flagged = []
        for src, keys in ((d, keys_d), (a, keys_a)):
            for k in keys:
                v = lang_values(src, k)
                strip = lambda x: re.sub(r"<[^>]+>|[A-Za-z0-9_{}.,:;!?()’“”\-/ ]", "", x)
                if t2s.convert(strip(v[2])) != strip(v[2]): flagged.append((k, "zh-CN"))
                if s2t.convert(strip(v[3])) != strip(v[3]): flagged.append((k, "zh-TW"))
        check("zh-CN/zh-TWの文字が混ざっていない(OpenCC・要目視のヒットがあれば下に出す)", not flagged, str(flagged))
    except ImportError:
        print("  --   opencc未導入のためS5はスキップ(.venvに opencc-python-reimplemented を入れると検査できる)")

    print("S6 バージョン表記")
    cfg = (ROOT / "app/config.py").read_text(encoding="utf-8")
    ver = re.search(r'^APP_VERSION\s*=\s*"(ver[\d.]+)"', cfg, re.M).group(1)
    check("APP_VERSION=ver1.5.24", ver == "ver1.5.24", ver)
    check("CHANGELOG.mdに見出しがある", f"## {ver}" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    rn = json.loads((ROOT / "release_notes.json").read_text(encoding="utf-8"))["versions"]
    check("release_notes.jsonの先頭がAPP_VERSIONと同じ", rn[0]["version"] == ver, rn[0]["version"])
    check("release_notesのpublicに内部の機能名・実装用語を書いていない",
          all(not re.search(r"fail2ban|jail|iptables|cron|キャッシュ|DB|テーブル|API", t, re.I) for t in rn[0]["public"]), str(rn[0]["public"]))


def main() -> int:
    only_static = "--static" in sys.argv
    if not only_static:
        if "DATA_DIR" not in os.environ:
            os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="c1524_")
            print("DATA_DIR(使い捨て):", os.environ["DATA_DIR"])
        os.environ.setdefault("OPENAI_API_KEY", "")
        print("U コード単体")
        unit()
    print("S 静的")
    static()
    bad = [r for r in RESULTS if not r[0]]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} 項目OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
