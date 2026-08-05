# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Top up the existing ソフトウェア工学(software engineering) domain with the
lower-level language/compiler-toolchain vocabulary that was missing, authored
by Claude (2026-08-05・ユーザー要望:「ソフトウェア工学の単語　たとえばポイ
ンタ　構造体　コンパイルスイッチ　コンフィグ　ビルド　コンパイル　アセン
ブリ　リンク　リンカー　統合開発環境　オブジェクト指向　クラス　ラムダ式
　カプセル化…C言語 C++ python java typescript javascript go cobol html vba
basic言語等から　ソフトウェア用語の英単語を追加できるといいです」).

既存の119語は設計思想・アーキテクチャ・開発プロセス(agile/SOLID/design
pattern等)中心で、pointer/struct/compile/build/linkのような「言語処理系・
コンパイル/ビルドの基礎」語彙と、C/C++/Python/Java/TypeScript/JavaScript/
Go/COBOL/HTML/VBA/BASICなど個別言語に特有の用語が欠けていた。これを補強。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased) against
the full live `words` table (confirmed IDE/encapsulation/inheritance/
polymorphism/garbage collection/memory leak already exist elsewhere, so this
list avoids repeating those).

Run:  python scripts/add_swe_fundamentals_langs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

D = "ソフトウェア工学"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- コンパイル/ビルド/リンクの基礎 ---
    ("compile", "コンパイルする", "動詞", "You need to compile the source code before you can run it.", D, "500"),
    ("compiler", "コンパイラ", "名詞", "The compiler reported a type error on line 42.", D, "550"),
    ("compile error", "コンパイルエラー", "名詞", "A missing semicolon caused a compile error.", D, "500"),
    ("runtime error", "実行時エラー", "名詞", "The program compiled fine but crashed with a runtime error.", D, "550"),
    ("build", "ビルド（する）", "名詞・動詞", "The nightly build failed because of a broken dependency.", D, "450"),
    ("build pipeline", "ビルドパイプライン", "名詞", "The build pipeline already exists in the domain; kept for continuity.", D, "700"),
    ("build system", "ビルドシステム", "名詞", "The project switched from Make to a modern build system.", D, "650"),
    ("makefile", "メイクファイル", "名詞", "The makefile defines how each source file should be compiled.", D, "700"),
    ("compiler flag", "コンパイラフラグ・コンパイルスイッチ", "名詞", "Adding a compiler flag enabled stricter warnings.", D, "700"),
    ("configuration file", "設定ファイル・コンフィグ", "名詞", "The app reads its settings from a configuration file at startup.", D, "450"),
    ("environment variable", "環境変数", "名詞", "The API key is stored in an environment variable, not in the code.", D, "600"),
    ("assembly language", "アセンブリ言語", "名詞", "Assembly language gives direct control over the processor's instructions.", D, "700"),
    ("machine code", "機械語", "名詞", "The compiler translates the source code into machine code.", D, "700"),
    ("bytecode", "バイトコード", "名詞", "Java source code compiles into bytecode that the JVM can run.", D, "750"),
    ("link (linking)", "リンク（する）", "動詞", "The linker failed to link the object files into an executable.", D, "700"),
    ("linker", "リンカー", "名詞", "The linker combines compiled object files into a single program.", D, "750"),
    ("linker error", "リンクエラー", "名詞", "A linker error appeared because a function was declared but never defined.", D, "750"),
    ("static library", "静的ライブラリ", "名詞", "A static library is copied directly into the final executable at build time.", D, "800"),
    ("dynamic library", "動的ライブラリ・共有ライブラリ", "名詞", "A dynamic library is loaded at runtime instead of being built into the program.", D, "800"),
    ("header file", "ヘッダファイル", "名詞", "The header file declares the functions that other files can call.", D, "650"),
    ("namespace", "名前空間", "名詞", "Using a namespace prevents naming conflicts between libraries.", D, "700"),
    ("preprocessor", "プリプロセッサ", "名詞", "The preprocessor replaces every #define macro before compilation begins.", D, "800"),
    ("macro (programming)", "マクロ", "名詞", "The macro expands into the same three lines every time it is used.", D, "700"),
    ("integrated development environment (IDE)", "統合開発環境（IDE）", "名詞", "An integrated development environment bundles an editor, debugger, and compiler.", D, "500"),
    # --- データ構造の基礎 ---
    ("pointer", "ポインタ", "名詞", "A pointer stores the memory address of another variable.", D, "700"),
    ("null pointer", "ヌルポインタ", "名詞", "Dereferencing a null pointer crashes most programs.", D, "750"),
    ("pointer arithmetic", "ポインタ演算", "名詞", "Pointer arithmetic lets you move through an array by adding to an address.", D, "800"),
    ("dereference", "（ポインタを）参照解除する", "動詞", "You must dereference the pointer to read the value it points to.", D, "800"),
    ("struct", "構造体", "名詞", "The struct groups a person's name, age, and email into one type.", D, "650"),
    ("union (data type)", "共用体", "名詞", "A union lets several fields share the same block of memory.", D, "850"),
    ("enum (enumeration)", "列挙型", "名詞", "The enum lists every valid status a task can have.", D, "650"),
    ("array", "配列", "名詞", "The array holds ten integers, indexed from zero to nine.", D, "400"),
    ("multidimensional array", "多次元配列", "名詞", "A multidimensional array can represent a grid, like rows and columns.", D, "700"),
    ("linked list", "連結リスト", "名詞", "Each node in a linked list points to the next one.", D, "700"),
    ("dynamic memory allocation", "動的メモリ割り当て", "名詞", "Dynamic memory allocation lets a program request memory while it is running.", D, "800"),
    ("segmentation fault", "セグメンテーション違反", "名詞", "The program crashed with a segmentation fault after accessing freed memory.", D, "850"),
    ("buffer overflow", "バッファオーバーフロー", "名詞", "A buffer overflow happens when data is written past the end of an array.", D, "850"),
    ("smart pointer", "スマートポインタ", "名詞", "A smart pointer automatically frees memory when it is no longer needed.", D, "850"),
    # --- オブジェクト指向 ---
    ("object-oriented programming", "オブジェクト指向プログラミング", "名詞", "Object-oriented programming organizes code around classes and objects.", D, "600"),
    ("class (programming)", "クラス", "名詞", "The Car class defines the properties and methods every car object shares.", D, "500"),
    ("object (instance)", "オブジェクト・インスタンス", "名詞", "Each object created from the class has its own set of values.", D, "550"),
    ("constructor", "コンストラクタ", "名詞", "The constructor runs automatically when a new object is created.", D, "650"),
    ("destructor", "デストラクタ", "名詞", "The destructor releases resources when an object is destroyed.", D, "750"),
    ("method (programming)", "メソッド", "名詞", "Calling the save method writes the object's data to disk.", D, "500"),
    ("attribute (programming)", "属性・フィールド", "名詞", "The name attribute stores each user's display name.", D, "550"),
    ("interface (programming)", "インターフェース", "名詞", "Any class that implements the interface must provide a draw method.", D, "700"),
    ("abstract class", "抽象クラス", "名詞", "An abstract class cannot be instantiated directly; it must be subclassed.", D, "800"),
    ("operator overloading", "演算子オーバーロード", "名詞", "Operator overloading lets the + symbol add two custom objects together.", D, "850"),
    # --- 関数型・型システム ---
    ("generics", "ジェネリクス", "名詞", "Generics let a single function work with any data type safely.", D, "800"),
    ("template (programming)", "テンプレート", "名詞", "The template generates a specialized version of the function for each type used.", D, "850"),
    ("lambda expression", "ラムダ式", "名詞", "A lambda expression is a short, unnamed function written inline.", D, "700"),
    ("closure (programming)", "クロージャ", "名詞", "The closure remembers the variable from its enclosing function even after it returns.", D, "800"),
    ("higher-order function", "高階関数", "名詞", "A higher-order function takes another function as an argument.", D, "800"),
    ("recursion", "再帰", "名詞", "Recursion solves the problem by having the function call itself.", D, "700"),
    ("iterator", "イテレータ", "名詞", "The iterator returns one element of the collection at a time.", D, "700"),
    ("type annotation", "型注釈", "名詞", "The type annotation tells the compiler that the variable must be a number.", D, "700"),
    ("type inference", "型推論", "名詞", "Type inference lets the compiler guess the type without an explicit annotation.", D, "750"),
    ("duck typing", "ダックタイピング", "名詞", "Duck typing cares only whether an object has the right methods, not its declared type.", D, "850"),
    # --- 例外処理・実行環境 ---
    ("exception handling", "例外処理", "名詞", "Exception handling lets the program recover gracefully from an error.", D, "650"),
    ("try-catch block", "try-catch文", "名詞", "The try-catch block catches the error instead of letting the program crash.", D, "650"),
    ("checked exception", "検査例外", "名詞", "A checked exception must be declared or handled at compile time.", D, "850"),
    ("interpreter", "インタプリタ", "名詞", "An interpreter executes the source code line by line without a separate compile step.", D, "650"),
    ("virtual machine (software)", "仮想マシン", "名詞", "The Java Virtual Machine lets the same bytecode run on any operating system.", D, "750"),
    ("runtime environment", "実行環境", "名詞", "The app failed to start because the runtime environment was the wrong version.", D, "700"),
    ("package manager", "パッケージマネージャ", "名詞", "The package manager installs the library and all of its dependencies.", D, "600"),
    ("dependency (software)", "依存関係", "名詞", "Updating one dependency accidentally broke a different part of the app.", D, "600"),
    ("syntax (programming)", "構文", "名詞", "Every language has its own syntax for writing an if statement.", D, "550"),
    ("syntax error", "構文エラー", "名詞", "A missing closing bracket caused a syntax error.", D, "450"),
    ("keyword (programming)", "予約語・キーワード", "名詞", "You cannot use a reserved keyword like \"class\" as a variable name.", D, "500"),
    # --- Python ---
    ("indentation-based syntax", "インデントによる構文", "名詞", "Python uses indentation-based syntax instead of curly braces to mark blocks.", D, "700"),
    ("list comprehension", "リスト内包表記", "名詞", "The list comprehension builds a new list in a single readable line.", D, "800"),
    ("decorator (Python)", "デコレータ", "名詞", "The decorator adds logging to a function without changing its code.", D, "800"),
    ("virtual environment (Python)", "仮想環境", "名詞", "A virtual environment keeps this project's packages separate from others.", D, "650"),
    ("Global Interpreter Lock (GIL)", "グローバルインタプリタロック（GIL）", "名詞", "The Global Interpreter Lock limits Python to running one thread at a time.", D, "900"),
    # --- Java / TypeScript / JavaScript ---
    ("Java Virtual Machine (JVM)", "Java仮想マシン（JVM）", "名詞", "The Java Virtual Machine runs the same compiled bytecode on Windows, macOS, or Linux.", D, "750"),
    ("annotation (Java)", "アノテーション", "名詞", "The @Override annotation tells the compiler that this method replaces one from the parent class.", D, "850"),
    ("callback function", "コールバック関数", "名詞", "The callback function runs automatically once the file finishes loading.", D, "700"),
    ("promise (JavaScript)", "プロミス", "名詞", "A promise represents a value that will be available at some point in the future.", D, "750"),
    ("async/await", "async/await構文", "名詞", "Using async/await makes asynchronous code read almost like ordinary, synchronous code.", D, "800"),
    ("event loop", "イベントループ", "名詞", "JavaScript's event loop lets a single thread handle many tasks without blocking.", D, "850"),
    ("Document Object Model (DOM)", "文書オブジェクトモデル（DOM）", "名詞", "The script changes the page by modifying the Document Object Model.", D, "700"),
    ("prototype (JavaScript)", "プロトタイプ", "名詞", "Every JavaScript object inherits properties through its prototype.", D, "850"),
    # --- Go ---
    ("goroutine", "ゴルーチン", "名詞", "A goroutine lets the program run a function concurrently with very little overhead.", D, "900"),
    ("channel (Go)", "チャネル", "名詞", "Two goroutines can communicate safely by sending values through a channel.", D, "900"),
    ("defer statement", "defer文", "名詞", "The defer statement schedules a function to run right before the surrounding function returns.", D, "900"),
    # --- COBOL / レガシー・業務システム ---
    ("mainframe", "メインフレーム", "名詞", "The bank's core transactions still run on a mainframe written in COBOL.", D, "700"),
    ("batch processing", "バッチ処理", "名詞", "Batch processing runs a large set of jobs overnight instead of one at a time.", D, "700"),
    ("legacy system", "レガシーシステム", "名詞", "The legacy system has been running unchanged for over twenty years.", D, "700"),
    # --- HTML / マークアップ ---
    ("markup language", "マークアップ言語", "名詞", "HTML is a markup language that describes the structure of a web page.", D, "600"),
    ("tag (HTML)", "タグ", "名詞", "Every opening tag in HTML needs a matching closing tag.", D, "450"),
    ("semantic HTML", "セマンティックHTML", "名詞", "Semantic HTML uses tags like <article> to describe the meaning of content, not just its look.", D, "750"),
    # --- VBA / BASIC ---
    ("subroutine", "サブルーチン", "名詞", "The macro calls a subroutine to format every cell in the column.", D, "650"),
    ("userform", "ユーザーフォーム", "名詞", "The VBA userform lets users enter data through a small pop-up window.", D, "800"),
    ("line number (BASIC)", "行番号", "名詞", "Early BASIC programs used a line number before every single statement.", D, "600"),
    ("GOTO statement", "GOTO文", "名詞", "A GOTO statement jumps directly to another line, skipping the normal flow.", D, "700"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
