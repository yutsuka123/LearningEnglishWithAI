# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add programming-language names, control-flow keywords, naming
conventions, and code-review/technical-interview vocabulary to the
existing "ソフトウェア工学" domain, authored by Claude (2026-08-10・
ユーザー要望).

対象語彙:
- プログラミング言語の名称: C, C++, C#, Java, JavaScript, TypeScript,
  Fortran, Swift, Go (programming language), COBOL, assembler。
  （assembly language / python / rust は既存のため対象外）
- 制御構文・予約語: if文、forループ、whileループ、switch文、case句、
  void型、main関数、do-whileループ、break文、continue文、三項演算子。
- 命名規約: naming convention、getter/setter、is接頭辞、camelCase、
  snake_case、PascalCase。
- コードレビュー・技術面接まわりの語彙: code reviewer、technical
  interview、whiteboard coding、take-home assignment、live coding、
  big-O notation、time complexity、edge case、readability、
  maintainability、magic number、rubber duck debugging、
  scope(programming)、wrapper function、abstraction layer。

**見出しを複合語にした理由（既存語との衝突回避・学習者の混乱防止）**:
このDBのdedupは英単語(見出し)をドメイン非依存で小文字完全一致判定する
ため、`if`/`for`/`while`/`switch`/`case`/`void`/`main`/`break`のような
一般英単語と紛らわしい語をそのまま見出しにすると、(a) 既に別ドメイン・
別語義で登録済みならサイレントにスキップされる、(b) 仮に未登録でも
プログラミング文脈だと分かりにくく学習者が混乱する。そのため
`if statement`, `for loop`, `while loop`, `switch statement`,
`case clause`, `void (return type)`, `main function`,
`do-while loop`, `break statement`, `continue statement` のように
プログラミング文脈だと明示する複合見出しにした。実際に事前調査した結果、
`continue`（ドメイン空欄で既存）, `switch`（鉄道ドメインの「分岐器」の
意味で既存）, `abstraction`（ソフトウェア工学ドメインで既存）は単独見出しでは
衝突が確認できたため、それぞれ `continue statement`, `switch statement`,
`abstraction layer` とした。`pair programming` は既にソフトウェア工学
ドメインに存在するため今回は追加していない。他の候補（言語名・キーワード・
命名規約・レビュー語彙）はすべて事前に
`SELECT english, domain FROM words WHERE LOWER(english) IN (...)` で
衝突が無いことを確認済み。

No app / OpenAI API calls — everything is hand-written and inserted
directly into the SQLite DB. Duplicates are skipped by english
(lowercased).

Run:  python scripts/add_programming_languages.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

D = "ソフトウェア工学"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- プログラミング言語の名称 ---
    ("C", "C言語", "固有名詞", "C is still widely used for operating systems and embedded software.", D, "500"),
    ("C++", "C++(シープラスプラス)", "固有名詞", "C++ adds object-oriented features on top of C.", D, "550"),
    ("C#", "C#(シーシャープ)", "固有名詞", "C# is commonly used for Windows applications and Unity games.", D, "550"),
    ("Java", "Java(ジャバ)", "固有名詞", "Java runs on the Java Virtual Machine, so it's portable across platforms.", D, "500"),
    ("JavaScript", "JavaScript(ジャバスクリプト)", "固有名詞", "JavaScript is the main language for interactive web pages.", D, "450"),
    ("TypeScript", "TypeScript(タイプスクリプト)", "固有名詞", "TypeScript adds static types on top of JavaScript.", D, "550"),
    ("Fortran", "Fortran(フォートラン)", "固有名詞", "Fortran is still used for scientific and numerical computing.", D, "700"),
    ("Swift", "Swift(スウィフト)", "固有名詞", "Swift is Apple's language for iOS and macOS development.", D, "600"),
    ("Go (programming language)", "Go言語", "固有名詞", "Go, the programming language, was designed at Google for simplicity and concurrency.", D, "600"),
    ("COBOL", "COBOL(コボル)", "固有名詞", "Many banks still run legacy systems written in COBOL.", D, "700"),
    ("assembler", "アセンブラ(アセンブリ言語をマシン語に変換するツール)", "名詞", "An assembler translates assembly language into machine code.", D, "700"),
    # --- 制御構文・予約語 ---
    ("if statement", "if文", "名詞", "An if statement lets your program branch based on a condition.", D, "400"),
    ("for loop", "forループ", "名詞", "Use a for loop to repeat an action a fixed number of times.", D, "400"),
    ("while loop", "whileループ", "名詞", "A while loop keeps running as long as the condition is true.", D, "400"),
    ("switch statement", "switch文", "名詞", "A switch statement is often cleaner than a long chain of if statements.", D, "500"),
    ("case clause", "case句", "名詞", "Each case clause in a switch statement handles one possible value.", D, "500"),
    ("void (return type)", "void型(戻り値なし)", "名詞", "A function declared as void doesn't return a value.", D, "550"),
    ("main function", "main関数(プログラムの開始点)", "名詞", "Execution starts at the main function in most C-like languages.", D, "450"),
    ("do-while loop", "do-whileループ", "名詞", "A do-while loop always runs its body at least once.", D, "550"),
    ("break statement", "break文", "名詞", "A break statement exits the loop immediately.", D, "450"),
    ("continue statement", "continue文", "名詞", "A continue statement skips to the next iteration of the loop.", D, "450"),
    ("ternary operator", "三項演算子", "名詞", "The ternary operator is a compact way to write a simple if-else.", D, "650"),
    # --- 命名規約 ---
    ("naming convention", "命名規則", "名詞", "Following a consistent naming convention makes code easier to read.", D, "500"),
    ("getter", "ゲッター(値を取得するメソッド)", "名詞", "The getter returns the current value of a private field.", D, "500"),
    ("setter", "セッター(値を設定するメソッド)", "名詞", "The setter validates the input before updating the field.", D, "500"),
    ("is-prefix", "is接頭辞(真偽値を返す関数の命名慣習)", "名詞", "Functions that return a boolean often use an is-prefix, like isValid.", D, "600"),
    ("camelCase", "キャメルケース(先頭を小文字にし単語の区切りを大文字にする記法)", "名詞", "JavaScript variables are usually written in camelCase.", D, "500"),
    ("snake_case", "スネークケース(単語をアンダースコアで区切る記法)", "名詞", "Python variables are usually written in snake_case.", D, "500"),
    ("PascalCase", "パスカルケース(各単語の先頭を大文字にする記法)", "名詞", "Class names are typically written in PascalCase.", D, "500"),
    # --- その他の概念 ---
    ("wrapper function", "ラッパー関数", "名詞", "A wrapper function adds extra behavior around an existing function.", D, "600"),
    ("abstraction layer", "抽象化層", "名詞", "An abstraction layer hides the complexity of the underlying system.", D, "700"),
    # --- コードレビュー・技術面接まわりの語彙 ---
    ("code reviewer", "コードレビュアー", "名詞", "The code reviewer left several comments on the pull request.", D, "500"),
    ("technical interview", "技術面接", "名詞", "She prepared for weeks before the technical interview.", D, "550"),
    ("whiteboard coding", "ホワイトボードコーディング(面接で口頭説明しながら書くコーディング)", "名詞", "Whiteboard coding can feel stressful even for experienced engineers.", D, "700"),
    ("take-home assignment", "持ち帰り課題(採用選考で出される課題)", "名詞", "The company sent a take-home assignment instead of a live coding round.", D, "650"),
    ("live coding", "ライブコーディング", "名詞", "The interviewer watched him solve the problem through live coding.", D, "600"),
    ("big-O notation", "O記法(アルゴリズムの計算量を表す記法)", "名詞", "Big-O notation describes how an algorithm's runtime grows with input size.", D, "750"),
    ("time complexity", "時間計算量", "名詞", "This sorting algorithm has a time complexity of O(n log n).", D, "700"),
    ("edge case", "エッジケース(境界的な特殊ケース)", "名詞", "Don't forget to handle the edge case of an empty list.", D, "600"),
    ("readability", "可読性", "名詞", "The team values readability over clever one-liners.", D, "550"),
    ("maintainability", "保守性", "名詞", "Good tests improve the maintainability of a codebase.", D, "600"),
    ("magic number", "マジックナンバー(意味の分からないハードコードされた数値)", "名詞", "Replace that magic number with a named constant.", D, "650"),
    ("rubber duck debugging", "ラバーダックデバッグ(人や物に説明しながらバグを見つける手法)", "名詞", "He solved the bug through rubber duck debugging before anyone even answered.", D, "800"),
    ("scope (programming)", "スコープ(変数の有効範囲)", "名詞", "A variable declared inside a function is out of scope outside it.", D, "550"),
]

PHRASES: list[tuple[str, str]] = [
    ("Could you take a look at my PR when you get a chance?", "手が空いたときに私のPRを見てもらえますか？"),
    ("I left a few comments on your diff.", "あなたの差分にいくつかコメントを残しました。"),
    ("This looks good to me, just one nit.", "良さそうです、ちょっとした指摘が一つだけあります。"),
    ("Can we pair on this for a bit?", "少しペアプログラミングしませんか？"),
    ("Let's rubber-duck this bug together.", "このバグを一緒にラバーダック(声に出して説明)してみましょう。"),
    ("I think this variable name could be clearer.", "この変数名はもっと分かりやすくできると思います。"),
    ("Could you extract this into a separate function?", "これを別の関数に切り出してもらえますか？"),
    ("Let's avoid magic numbers here.", "ここではマジックナンバーを避けましょう。"),
    ("What's the time complexity of this approach?", "このアプローチの時間計算量はどれくらいですか？"),
    ("Can you walk me through your thought process?", "あなたの思考プロセスを説明してもらえますか？"),
    ("Take your time, there's no rush.", "焦らなくて大丈夫です、急いでいません。"),
    ("How would you handle this edge case?", "このエッジケースにはどう対応しますか？"),
    ("I'm not sure about the naming convention here.", "ここの命名規則がこれでいいのか自信がありません。"),
    ("Should we use camelCase or snake_case for this?", "ここはcamelCaseとsnake_caseどちらを使うべきですか？"),
    ("Let's keep the function names consistent.", "関数名の一貫性を保ちましょう。"),
    ("I'll refactor this once the tests pass.", "テストが通ったらこれをリファクタリングします。"),
    ("Can you add a docstring here?", "ここにdocstringを追加してもらえますか？"),
    ("This function is doing too much.", "この関数はやりすぎています(責務が多すぎます)。"),
    ("Let's break this into smaller functions.", "これをもっと小さな関数に分割しましょう。"),
    ("I appreciate the detailed feedback.", "詳細なフィードバックをありがとうございます。"),
    ("Would you mind explaining your reasoning?", "あなたの考えの理由を説明してもらえますか？"),
    ("Let's whiteboard this before we start coding.", "コーディングを始める前にホワイトボードで整理しましょう。"),
    ("I have a take-home assignment due Friday.", "金曜日締め切りの持ち帰り課題があります。"),
    ("Feel free to push back if you disagree.", "意見が違うなら遠慮なく指摘してください。"),
    ("Let's align on the naming before we merge.", "マージする前に命名について認識を合わせましょう。"),
    ("I want to make sure this is readable for new team members.", "新しいメンバーにも読みやすいコードにしたいです。"),
    ("Could you add a comment explaining why, not just what?", "「何を」だけでなく「なぜ」を説明するコメントを追加してもらえますか？"),
    ("Let's write a quick test for this edge case.", "このエッジケース用に簡単なテストを書きましょう。"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, 'プログラミングの英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
