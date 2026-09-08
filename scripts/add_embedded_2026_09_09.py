# ruff: noqa: E501
"""組み込み（ソフト）・組み込み（エレキ）新ドメイン(2026-09-09・authored by Claude)。ユーザー提起「組み込み（ソフト）組み込み（エレキ）...SPI I2C データシートを読むにあたり必要な用語を網羅する」。既存の組み込み開発(70語)/電気電子(91語)/半導体(96語)/ソフトウェア工学(253語)と重複しないよう 各エージェントが既存語を確認済み。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_embedded_2026_09_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("ISR", "割り込みが発生した際にCPUがメイン処理を中断し、その要因に対応するために呼び出す短い関数。処理を終えると元の実行位置に復帰する。割り込みサービスルーチン(ISR)。", "名詞", "Keep the ISR as short as possible—just clear the interrupt flag and set a semaphore for the handler task.", "組み込み（ソフト）", "780"),
    ("device driver", "特定のハードウェア(センサー、通信インタフェース、ストレージなど)を制御するために書かれたソフトウェアで、アプリケーションやOSからのハードウェアに依存しない要求を、実際のレジスタ操作や信号のやり取りに変換する層。デバイスドライバ。", "名詞", "The SPI flash device driver exposes simple read() and write() functions so the application never touches the controller registers directly.", "組み込み（ソフト）", "760"),
    ("toolchain", "ソースコードを書いてから実機で動くバイナリを得るまでに使う、コンパイラ・アセンブラ・リンカ・デバッガなどの一式のツール群。ターゲットのCPUアーキテクチャ向けにクロスコンパイルする一連のツールを指すことが多い。ツールチェーン。", "名詞", "Make sure the ARM GCC toolchain is on your PATH before running the build script.", "組み込み（ソフト）", "740"),
    ("bare-metal programming", "OSを介さず、CPU上で直接ソフトウェアを実行するプログラミング方式。割り込みベクタの設定やペリフェラルの初期化などをすべて自前のコードで行う。ベアメタルプログラミング。", "名詞", "The bootloader itself is bare-metal code that runs before any RTOS is initialized.", "組み込み（ソフト）", "800"),
    ("memory-mapped I/O", "CPUのアドレス空間の一部にペリフェラル(タイマー、UART、GPIOなど)のレジスタを割り当て、通常のメモリ読み書き命令でハードウェアを操作できるようにする方式。組み込みソフトウェアの多くはこの方式でハードウェアにアクセスする。メモリマップドI/O。", "名詞", "Because the GPIO controller uses memory-mapped I/O, setting a pin high is just a single store instruction to its ODR register.", "組み込み（ソフト）", "830"),
    ("DMA", "CPUを介さずに、周辺機器とメモリの間、あるいはメモリ同士でデータを転送する専用のハードウェア機構。転送中もCPUは別の処理を続けられるため、大量データの入出力を高速かつ低負荷に行える。ダイレクトメモリアクセス(DMA)。", "名詞", "Using DMA to transfer ADC samples into the buffer frees the CPU to run the control loop without being interrupted for every sample.", "組み込み（ソフト）", "800"),
    ("polling", "割り込みを使わず、ソフトウェアが一定間隔でハードウェアの状態(フラグやレジスタの値)を繰り返し確認し、変化があれば処理する方式。ポーリング。", "名詞", "The simplest UART driver just polls the RXNE flag in a tight loop until a byte arrives.", "組み込み（ソフト）", "720"),
    ("interrupt-driven I/O", "ハードウェアの状態変化を、ソフトウェアが定期的に確認する(ポーリングする)のではなく、割り込みという形でCPUに通知させ、そのタイミングでのみ処理を行う方式。割り込み駆動I/O。", "名詞", "Switching the sensor driver from polling to interrupt-driven I/O cut average power consumption by more than half.", "組み込み（ソフト）", "800"),
    ("hard real-time system", "定められた締め切り(デッドライン)を一度でも守れないと、システムの故障や事故につながるなど致命的な結果を招くとみなされるリアルタイムシステム。エアバッグの展開制御などが典型例。ハードリアルタイムシステム。", "名詞", "An airbag controller is a hard real-time system: missing its deadline by even a few milliseconds is unacceptable.", "組み込み（ソフト）", "850"),
    ("soft real-time system", "デッドラインを多少超過しても、性能の劣化にとどまり致命的な問題にはならないリアルタイムシステム。動画のフレーム落ちなどが典型例。ソフトリアルタイムシステム。", "名詞", "A video streaming pipeline is typically a soft real-time system—an occasional dropped frame degrades quality but doesn't crash anything.", "組み込み（ソフト）", "830"),
    ("critical section", "複数の割り込みやタスクから同時にアクセスされると不整合が起きうる、共有資源(変数やハードウェアレジスタなど)を操作するコードの区間。実行中は割り込みを禁止したりミューテックスで保護したりして、他から割り込まれないようにする必要がある。クリティカルセクション。", "名詞", "Disable interrupts before entering the critical section that updates the shared buffer index.", "組み込み（ソフト）", "820"),
    ("reentrant function", "複数のタスクや割り込みから同時に、あるいは実行途中で再び呼び出されても、共有状態を壊さず正しく動作する関数。内部でグローバル変数や静的変数を保護なしに使わないことが条件となる。リエントラント関数(再入可能関数)。", "名詞", "Because the logging function uses a static buffer without locking, it is not a reentrant function and must never be called from an ISR.", "組み込み（ソフト）", "870"),
    ("atomic operation", "実行の途中で他の割り込みやタスクによって中断されることがなく、一つの不可分な処理として完了することが保証された操作。共有変数への読み書きを安全に行うための基本要素となる。アトミック操作。", "名詞", "On this 8-bit MCU, incrementing a 32-bit counter is not an atomic operation, so it must be protected from the ISR that also updates it.", "組み込み（ソフト）", "850"),
    ("priority inheritance", "低優先度のタスクが共有資源(ミューテックスなど)を保持しているために高優先度のタスクが待たされている間、そのタスクの優先度を一時的に高優先度タスクと同じ水準まで引き上げる仕組み。優先度逆転を緩和するために使われる。優先度継承。", "名詞", "Turning on priority inheritance for the shared mutex resolved the intermittent watchdog resets caused by priority inversion.", "組み込み（ソフト）", "900"),
    ("preemptive scheduling", "実行中のタスクよりも優先度の高いタスクが実行可能になった時点で、OSやスケジューラが強制的に実行中のタスクを中断し、優先度の高いタスクに切り替える方式。RTOSで一般的なスケジューリング方式。プリエンプティブスケジューリング。", "名詞", "With preemptive scheduling, a high-priority sensor task interrupts the lower-priority display task the instant new data arrives.", "組み込み（ソフト）", "830"),
    ("cooperative scheduling", "実行中のタスクが自ら処理を終える、あるいは明示的にCPUを手放す(yieldする)まで、他のタスクに切り替わらないスケジューリング方式。強制的な中断がないため排他制御は簡単になるが、一つのタスクが長く処理を占有すると他のタスクの応答が遅れる。協調的スケジューリング。", "名詞", "The original super-loop firmware used cooperative scheduling: each task function had to return quickly so the next one could run.", "組み込み（ソフト）", "830"),
    ("idle task", "RTOSにおいて、他に実行可能なタスクが一つもないときにスケジューラが実行する、最低優先度の特殊なタスク。CPUを省電力モードへ移行させたり、統計情報を集めたりする処理を行うことが多い。アイドルタスク。", "名詞", "The idle task puts the microcontroller into sleep mode whenever no other task has work to do, cutting average power draw.", "組み込み（ソフト）", "800"),
    ("system tick", "RTOSが時間を管理するために、ハードウェアタイマーによって一定周期で発生させる割り込み。この周期を基準にタスクの遅延(delay)やタイムアウト、スケジューリングの判断が行われる。システムティック。", "名詞", "With a 1 ms system tick, calling vTaskDelay(100) blocks the task for roughly 100 milliseconds.", "組み込み（ソフト）", "800"),
    ("software reset", "電源電圧の異常(ブラウンアウト)や外部リセット端子ではなく、ソフトウェア自身がレジスタへの書き込みなどによって意図的にCPUを再起動させること。ソフトウェアリセット。", "名詞", "After applying the firmware update, the bootloader triggers a software reset to jump into the new image.", "組み込み（ソフト）", "760"),
    ("hard fault", "不正なメモリアクセスやゼロ除算、不正な命令の実行など、CPUが処理を継続できない致命的なエラーが発生した際に呼び出される例外ハンドラ、またはその状態。多くのARM Cortex-Mマイコンで使われる用語。ハードフォールト。", "名詞", "Dereferencing a null pointer inside the sensor driver triggered a hard fault and reset the board.", "組み込み（ソフト）", "870"),
    ("checksum", "データの誤りを検出するために、送信・保存するデータから単純な加算などによって算出する短い値。受信側や読み出し側で同じ計算をして値が一致するかを確かめることで、伝送や記憶中の破損を検出する。チェックサム。", "名詞", "The bootloader verifies the firmware image's checksum before jumping to it, refusing to boot a corrupted binary.", "組み込み（ソフト）", "720"),
    ("CRC", "データに多項式除算に基づく演算を施して得られる検査値を付加し、伝送や記憶の過程で生じた誤りを高い確率で検出する手法。単純なチェックサムより誤り検出能力が高く、通信プロトコルやフラッシュメモリの整合性確認に広く使われる。巡回冗長検査(CRC)。", "名詞", "Each CAN frame ends with a CRC field so a receiving node can detect bit errors introduced by electrical noise.", "組み込み（ソフト）", "850"),
    ("firmware image", "マイコンのフラッシュメモリに書き込むために生成された、ファームウェア全体を含む一つのバイナリファイル。ブートローダやOTA更新の仕組みは、この単位でイメージを検証・書き込み・切り替えする。ファームウェアイメージ。", "名詞", "The build process signs the firmware image with a private key so the bootloader can verify its authenticity before flashing it.", "組み込み（ソフト）", "800"),
    ("dual-bank update", "フラッシュメモリを二つの領域(バンク)に分け、一方で現在のファームウェアを実行させたまま、もう一方に新しいファームウェアを書き込み、検証が済んでから起動先を切り替える更新方式。更新中に電源が落ちても現行バンクが無事なため、ファームウェアを起動不能な状態(文鎮化)にしにくい。デュアルバンク更新(A/B更新)。", "名詞", "The OTA client writes the new firmware to the inactive bank, so a power loss mid-update still leaves the device bootable from the old bank.", "組み込み（ソフト）", "880"),
    ("wear leveling", "フラッシュメモリの特定の物理セルだけに書き換えが集中して劣化・故障するのを防ぐため、書き込み先の物理アドレスを分散させる制御手法。フラッシュストレージのコントローラやファイルシステムが行う。ウェアレベリング。", "名詞", "Without wear leveling, a log file that's rewritten every second would burn out the same flash sector within days.", "組み込み（ソフト）", "850"),
    ("MISRA C", "主に自動車業界で発展した、C言語で安全性・信頼性の高い組み込みソフトウェアを書くためのコーディングガイドライン集。未定義動作につながりやすい書き方や誤りを誘発しやすい構文を制限するルールを定めており、静的解析ツールによる準拠チェックとあわせて使われることが多い。MISRA C。", "名詞", "The static analyzer flagged three MISRA C violations, including an implicit conversion that could silently truncate a value.", "組み込み（ソフト）", "850"),
    ("read-modify-write", "レジスタや変数の現在の値を読み出し、必要なビットだけを変更したうえで元のアドレスに書き戻すという、ハードウェアレジスタ操作の基本パターン。この一連の操作が途中で割り込みなどにより中断されると、他の変更が失われる競合状態を招きうる。リードモディファイライト。", "名詞", "Setting a single bit in the control register with `REG |= (1 << 3)` compiles into a read-modify-write sequence of three instructions.", "組み込み（ソフト）", "850"),
    ("bitmask", "特定のビット位置だけを取り出したり、セット・クリアしたりするために用意された、対象のビット位置が1になっている定数値。レジスタの特定フィールドを操作する際にAND・OR・XOR演算と組み合わせて使う。ビットマスク。", "名詞", "Applying the bitmask 0x0F with a bitwise AND extracts only the lower four bits of the status register.", "組み込み（ソフト）", "760"),
    ("low-power mode", "消費電力を抑えるため、CPUのクロックを止めたり周辺回路への電源供給を切ったりして機能の一部・全部を停止させる、マイコンがソフトウェアから遷移できる動作モードの総称。スリープ、スタンバイ、ディープスリープなど複数段階が用意されていることが多い。低消費電力モード。", "名詞", "The firmware enters a low-power mode between sensor readings and wakes up on the next timer interrupt.", "組み込み（ソフト）", "780"),
    ("in-application programming", "起動中のファームウェアが、専用の書き込み器を使わずに自分自身でフラッシュメモリの一部(自分のプログラム領域を含む)を書き換え、新しいファームウェアに更新する仕組み。OTA更新やブートローダ経由のアップデートを実現する基盤となる。インアプリケーションプログラミング(IAP)。", "名詞", "The bootloader uses in-application programming to write the downloaded firmware image into the flash sectors normally occupied by the application.", "組み込み（ソフト）", "870"),
    ("non-blocking code", "I/O処理や待ち時間の発生する操作の完了を、その場で止まって待つのではなく、すぐに制御を返して他の処理を続けられるように書かれたコード。完了はポーリングやコールバック、割り込みなどで別途確認する。ノンブロッキングコード。", "名詞", "Rewriting the sensor read as non-blocking code let the main loop keep servicing the UART while waiting for the conversion to finish.", "組み込み（ソフト）", "800"),
    ("super loop", "RTOSを使わず、初期化処理のあとmain関数の中に置かれた終わらないwhileループの中で、各機能の処理を順番に(あるいは経過時間を見ながら)呼び出していく、最も基本的な組み込みソフトウェアのアーキテクチャ。スーパーループ。", "名詞", "The original prototype ran as a simple super loop, calling readSensors(), updateControl(), and sendTelemetry() once per iteration.", "組み込み（ソフト）", "780"),
    ("finite state machine", "システムの振る舞いを、あらかじめ定義された有限個の「状態」と、入力やイベントに応じた状態間の「遷移」の組み合わせとして表現するソフトウェア設計手法。ボタン操作やプロトコルの解析など、条件分岐が複雑になりがちな制御ロジックを整理するために組み込みソフトウェアで広く使われる。有限状態機械(FSM)。", "名詞", "The button driver is implemented as a finite state machine with states for IDLE, DEBOUNCING, PRESSED, and LONG_PRESS.", "組み込み（ソフト）", "800"),
    ("circular buffer", "固定長の配列を、末尾の次を先頭に折り返すように扱うことで、リング状に連続してデータを読み書きできるようにしたデータ構造。UARTの受信バッファやDMA転送先など、生成と消費の速度が異なるデータの受け渡しに組み込みソフトウェアで広く使われる。循環バッファ(リングバッファ)。", "名詞", "The UART ISR pushes each received byte into a circular buffer, and the main loop pops bytes out of it whenever it's ready.", "組み込み（ソフト）", "780"),
    ("double buffering", "表示や送信に使うデータを二つのバッファに分けて用意し、一方を実際の出力に使っている間にもう一方へ次のデータを書き込み、準備ができた時点で使用するバッファを切り替える手法。出力中のデータが書き換え途中の不完全な状態になることを防ぐ。ダブルバッファリング。", "名詞", "Without double buffering, the DMA could start transmitting the display buffer while the drawing routine is still halfway through updating it.", "組み込み（ソフト）", "800"),
    ("lookup table", "実行時に計算するのではなく、あらかじめ計算しておいた結果を配列として持っておき、インデックスを指定して値を取り出すことで処理を高速化する手法。三角関数の値やセンサーの補正値、CRC計算の中間値などに使われる。ルックアップテーブル(LUT)。", "名詞", "Instead of computing sine on every control loop iteration, the firmware reads the value from a precomputed lookup table.", "組み込み（ソフト）", "750"),
    ("fixed-point arithmetic", "浮動小数点数を使わず、整数の値に固定の桁位置(スケール)を仮定して小数を表現し、加減乗除を整数演算だけで行う計算方式。FPUを持たない、あるいは浮動小数点演算が遅いマイコンで、速度や消費電力を優先する場合に使われる。固定小数点演算。", "名詞", "The audio filter was rewritten using 16-bit fixed-point arithmetic to run in real time on a Cortex-M0 without an FPU.", "組み込み（ソフト）", "850"),
    ("register access", "ソフトウェアがポインタや専用の構造体を介して、ペリフェラルの制御・状態レジスタを直接読み書きすること。値の読み取りだけでなく、特定ビットの変更にはビットマスクを使ったread-modify-writeが伴うことが多い。レジスタアクセス。", "名詞", "The vendor's header file wraps raw register access in named structs, so `GPIOA->ODR |= (1 << 5)` is more readable than a bare hexadecimal address.", "組み込み（ソフト）", "830"),
    ("spinlock", "資源を確保できるまでループで確認し続ける(ビジーウェイトする)ことで排他制御を行うロック機構。スレッドを休止させるオーバーヘッドを避けられるため、ロック保持時間が非常に短い場合や、マルチコアの組み込みチップでコア間の排他制御に使われる。スピンロック。", "名詞", "The dual-core microcontroller uses a hardware spinlock so Core 0 and Core 1 can safely take turns accessing the shared peripheral.", "組み込み（ソフト）", "870"),
    ("memory pool", "あらかじめ固定サイズのブロックをいくつか用意しておき、動的なメモリが必要になった際にmalloc/freeの代わりにそこから貸し出し・返却する仕組み。実行時間が予測しにくいヒープの断片化を避けられるため、リアルタイム性が求められる組み込みソフトウェアで好まれる。メモリプール。", "名詞", "Instead of calling malloc() for every incoming packet, the driver allocates buffers from a fixed-size memory pool created at startup.", "組み込み（ソフト）", "850"),
    ("datasheet", "半導体部品やICについて、電気的特性・ピン配置・タイミング仕様・パッケージ情報などをメーカーが公式にまとめた技術資料。データシート。", "名詞", "Before soldering the chip onto the board, always check the pin assignments in the datasheet.", "組み込み（エレキ）", "780"),
    ("pinout", "ICやコネクタの各ピン(端子)にどの信号が割り当てられているかを示した図や一覧。ピン配置図・ピン配列。", "名詞", "Refer to the pinout diagram to identify which pin is VCC and which is ground.", "組み込み（エレキ）", "800"),
    ("absolute maximum ratings", "半導体部品が破壊されずに耐えられる、電圧・電流・温度などの絶対的な限界値を示した規定。瞬間的でも超えると素子が損傷する可能性がある値であり、通常動作を保証する値ではない。絶対最大定格。", "名詞", "Exceeding the absolute maximum ratings for even a few nanoseconds can permanently damage the device.", "組み込み（エレキ）", "900"),
    ("electrical characteristics", "データシート中で、電源電圧・入出力電流・しきい値電圧などのICの電気的な性能値を、条件ごとの最小・標準・最大値として一覧にした表。電気的特性(表)。", "名詞", "According to the electrical characteristics table, the typical input leakage current is only 1 μA.", "組み込み（エレキ）", "900"),
    ("recommended operating conditions", "メーカーが、規定された性能や信頼性を発揮できると保証する、電源電圧・動作温度などの推奨される使用範囲。推奨動作条件。", "名詞", "The recommended operating conditions specify an ambient temperature range of -40°C to +85°C.", "組み込み（エレキ）", "850"),
    ("functional block diagram", "ICの内部構成を、実際の回路図ではなくCPUコアやレジスタ、周辺回路などを機能単位のブロックとその接続関係で簡略に示した図。機能ブロック図。", "名詞", "The functional block diagram shows how the ADC, timer, and communication peripherals share the internal bus.", "組み込み（エレキ）", "830"),
    ("truth table", "論理回路やロジックICについて、入力信号のすべての組み合わせに対する出力を一覧にした表。真理値表。", "名詞", "According to the truth table, the output goes high only when both inputs A and B are low.", "組み込み（エレキ）", "800"),
    ("typical application circuit", "データシート中で、そのICを実際に使う際の標準的な周辺回路(電源のパスコンや発振子、プルアップ抵抗など)を示した参考回路図。標準応用回路・代表的応用回路。", "名詞", "The typical application circuit shows a 0.1 μF decoupling capacitor placed close to each power pin.", "組み込み（エレキ）", "850"),
    ("timing diagram", "信号の立ち上がり・立ち下がりのタイミングや、複数信号間の時間的な関係(セットアップ時間・ホールド時間など)を波形図で示した図。タイミング図・タイミングチャート。", "名詞", "The timing diagram shows that data must be stable for at least 10 ns before the clock edge.", "組み込み（エレキ）", "850"),
    ("setup time", "フリップフロップやレジスタにデータを正しく取り込むために、クロックの有効エッジが来る前にデータ信号が安定していなければならない最小時間。セットアップ時間。", "名詞", "If the setup time is violated, the flip-flop may output a metastable, unpredictable value.", "組み込み（エレキ）", "900"),
    ("hold time", "フリップフロップやレジスタがデータを正しく取り込むために、クロックの有効エッジの後もデータ信号が安定した状態を保っていなければならない最小時間。ホールド時間。", "名詞", "The hold time requirement means the input data must not change until 2 ns after the clock edge.", "組み込み（エレキ）", "900"),
    ("propagation delay", "論理回路やICにおいて、入力信号が変化してから、それに対応して出力信号が変化するまでに生じる遅延時間。伝搬遅延(時間)。", "名詞", "The propagation delay from input to output is typically 12 ns at room temperature.", "組み込み（エレキ）", "880"),
    ("rise time", "信号がLowからHighへ遷移する際に、規定された下限(例えば最終値の10%)から上限(例えば90%)まで変化するのに要する時間。立ち上がり時間。", "名詞", "A slower rise time reduces electromagnetic interference but can violate setup-time margins at high clock speeds.", "組み込み（エレキ）", "870"),
    ("fall time", "信号がHighからLowへ遷移する際に、規定された上限(例えば最終値の90%)から下限(例えば10%)まで変化するのに要する時間。立ち下がり時間。", "名詞", "Rise time and fall time are usually measured between the 10% and 90% points of the output swing.", "組み込み（エレキ）", "870"),
    ("clock skew", "同じクロック信号が、配線の長さや負荷の違いなどにより、回路内の異なる箇所へわずかに異なるタイミングで到達してしまうずれ。クロックスキュー。", "名詞", "Excessive clock skew between two flip-flops can effectively eat into the available setup time margin.", "組み込み（エレキ）", "920"),
    ("jitter", "クロック信号などの周期的な信号において、本来あるべきタイミングからのわずかな周期的・非周期的なばらつき・揺らぎ。ジッター。", "名詞", "Excessive clock jitter can cause bit errors in high-speed serial communication links.", "組み込み（エレキ）", "900"),
    ("metastability", "フリップフロップにおいて、セットアップ時間やホールド時間の規定に違反した入力を受けたとき、出力がHighともLowとも定まらない中間的な電圧レベルにとどまり、その後どちらかの状態に落ち着くまでに不定な時間を要する現象。メタステーブル状態・準安定状態。", "名詞", "Metastability typically arises when an asynchronous signal is sampled without proper synchronization.", "組み込み（エレキ）", "950"),
    ("rising edge", "デジタル信号がLowからHighへ切り替わる瞬間。多くの同期回路はこの瞬間を基準にデータを取り込む。立ち上がりエッジ。", "名詞", "This flip-flop captures the D input on the rising edge of the clock.", "組み込み（エレキ）", "800"),
    ("falling edge", "デジタル信号がHighからLowへ切り替わる瞬間。立ち下がりエッジ。", "名詞", "Some devices sample data on the falling edge of the clock instead of the rising edge.", "組み込み（エレキ）", "800"),
    ("data bus", "CPUとメモリや周辺回路との間で、実際のデータ(命令やデータ値)をやり取りするための、複数の信号線をまとめた伝送路。データバス。", "名詞", "This microcontroller has an 8-bit data bus, so it transfers one byte per read or write cycle.", "組み込み（エレキ）", "800"),
    ("address bus", "CPUがメモリや周辺回路上のどの番地(アドレス)にアクセスするかを指定するための、複数の信号線をまとめた伝送路。アドレスバス。", "名詞", "A 16-bit address bus can directly address up to 65,536 memory locations.", "組み込み（エレキ）", "800"),
    ("control bus", "データバスやアドレスバスと組み合わせて、読み出し・書き込み・割り込みなどの制御信号をやり取りするための伝送路。制御バス。", "名詞", "The control bus carries signals such as read/write and chip-select that coordinate data transfers.", "組み込み（エレキ）", "820"),
    ("open-drain", "MOSFET出力段において、Highレベルを能動的に出力する回路を持たずLowへの引き込みのみを行い、Highにするには外部のプルアップ抵抗が必要な出力方式。オープンドレイン(出力)。", "形容詞", "I2C bus lines are typically driven by open-drain outputs and pulled high with external resistors.", "組み込み（エレキ）", "900"),
    ("open-collector", "バイポーラトランジスタ出力段において、Highレベルを能動的に出力する回路を持たずLowへの引き込みのみを行い、Highにするには外部のプルアップ抵抗が必要な出力方式。オープンコレクタ(出力)。", "形容詞", "The open-collector output can sink up to 20 mA when pulled low.", "組み込み（エレキ）", "900"),
    ("tri-state", "デジタル出力において、通常のHigh・Lowに加えて、出力段を電気的に切り離した高インピーダンス状態(Hi-Z)を持たせることができる出力形式。3ステート・トライステート(出力)。", "形容詞", "When the output-enable pin is high, the tri-state buffer places the bus in a high-impedance state.", "組み込み（エレキ）", "900"),
    ("active-low", "信号のピンや制御線について、電圧がLow(0V付近)のときにその機能が有効になる方式。データシートではピン名の上に上線(オーバーバー)を付けたり、末尾に「N」や「B」を付けたりして示されることが多い。アクティブロー(負論理)。", "形容詞", "The RESET pin is active-low, so the chip is held in reset while that pin is at 0 V.", "組み込み（エレキ）", "870"),
    ("pull-down resistor", "信号線に接続し、何も駆動されていない(浮いている)ときの電位を既定でLowレベルに保つための抵抗。プルダウン抵抗。", "名詞", "A pull-down resistor ensures the input pin reads low when the button is not pressed.", "組み込み（エレキ）", "830"),
    ("voltage rail", "回路基板上で、複数の回路ブロックへ共通の電圧を供給する電源ラインの通称。例えば3.3Vや1.2Vなど、特定の電圧値ごとに「〜Vレール」と呼ぶ。電源レール。", "名詞", "The board has separate 3.3 V and 1.8 V voltage rails for the MCU and the sensor, respectively.", "組み込み（エレキ）", "830"),
    ("decoupling capacitor", "ICの電源ピンとグラウンドの間に近接して配置し、電源電圧の瞬間的な変動やノイズを吸収して安定させるためのコンデンサ。デカップリングコンデンサ・パスコン。", "名詞", "Place a 0.1 μF decoupling capacitor as close as possible to each power pin of the IC.", "組み込み（エレキ）", "850"),
    ("bypass capacitor", "電源ラインに含まれる高周波ノイズを、コンデンサを通してグラウンドへ迂回(バイパス)させ、回路の他の部分への影響を減らすためのコンデンサ。バイパスコンデンサ。", "名詞", "A bypass capacitor is added at the power input to filter out high-frequency noise from the supply.", "組み込み（エレキ）", "850"),
    ("quiescent current", "回路が信号処理や負荷駆動などの実質的な動作をしていない、待機状態にあるときに消費する電流。無信号時電流・静止電流。", "名詞", "The regulator's quiescent current is only 5 μA, making it suitable for battery-powered designs.", "組み込み（エレキ）", "900"),
    ("supply current", "ICが電源から実際に引き込む電流。動作状態(通常動作時・待機時など)ごとに規定されることが多い。供給電流・消費電流。", "名詞", "The maximum supply current under full load is specified as 150 mA in the electrical characteristics table.", "組み込み（エレキ）", "850"),
    ("ESD protection", "人体や工具などから瞬間的に流れ込む静電気(静電放電)による素子破壊を防ぐために、ICの入出力ピンに組み込まれた保護回路、またはその保護対策全般。ESD保護。", "名詞", "The input pins include built-in ESD protection diodes rated to withstand 2 kV per the human body model.", "組み込み（エレキ）", "900"),
    ("footprint", "部品を基板に実装するために必要な、はんだパッドの配置・寸法など基板上の占有領域のパターン。部品フットプリント。", "名詞", "Make sure the PCB footprint matches the package's pin pitch before ordering the boards.", "組み込み（エレキ）", "830"),
    ("ball grid array", "パッケージの底面全体に格子状に並んだ、はんだボール状の端子で基板に実装するIC実装方式。多ピン化・小型化に適する。ボールグリッドアレイ(BGA)。", "名詞", "The high pin-count processor is only available in a ball grid array package.", "組み込み（エレキ）", "880"),
    ("surface-mount device", "基板に開けた穴に足を通すのではなく、基板表面のパッドに直接はんだ付けして実装する部品の総称。表面実装部品(SMD)。", "名詞", "Surface-mount devices are smaller and better suited to automated assembly than through-hole components.", "組み込み（エレキ）", "830"),
    ("sampling rate", "ADC(アナログ-デジタル変換器)が、アナログ信号を1秒間に何回デジタル値へ変換するかを表す値。サンプリング周波数・標本化周波数。", "名詞", "The on-chip ADC supports a maximum sampling rate of 1 MSPS (mega-samples per second).", "組み込み（エレキ）", "870"),
    ("resolution", "ADC(アナログ-デジタル変換器)やDAC(デジタル-アナログ変換器)が、アナログ値をどれだけ細かい段階(ビット数)で表現できるかを示す性能。分解能。", "名詞", "A 12-bit ADC has a resolution of 4096 discrete levels across its input voltage range.", "組み込み（エレキ）", "850"),
    ("ground bounce", "複数の出力が同時にスイッチングする際、パッケージやボンディングワイヤの寄生インダクタンスを通じて瞬間的に大きな電流が流れることで、チップ内部の基準となるグラウンド電位が一時的に変動する現象。グラウンドバウンス。", "名詞", "Ground bounce caused by simultaneous switching outputs can be mistaken for a logic-level glitch on other pins.", "組み込み（エレキ）", "930"),
    ("signal integrity", "信号が送信端から受信端まで伝わる過程で、波形の歪みやノイズの混入、反射などによって本来の情報が損なわれずに保たれているかという性質、およびそれを扱う設計分野。信号品質・シグナルインテグリティ。", "名詞", "At high clock frequencies, signal integrity issues such as reflections and crosstalk become significant design concerns.", "組み込み（エレキ）", "920"),
    ("noise margin", "デジタル論理回路において、出力の保証されるHigh/Lowレベルと、受信側が入力として認識するHigh/Lowのしきい値との間にある余裕(電圧差)。ノイズマージン。", "名詞", "A wider noise margin makes the circuit more tolerant of voltage drops and induced noise on the line.", "組み込み（エレキ）", "920"),
    ("logic level", "デジタル信号のHigh(論理1)およびLow(論理0)を、それぞれ何ボルトとして扱うかという電圧の基準。TTL・CMOS・LVTTLなど、規格によって異なる。論理レベル。", "名詞", "Connecting a 5 V logic level output directly to a 3.3 V-only input can damage the receiving chip.", "組み込み（エレキ）", "870"),
    ("TTL", "バイポーラトランジスタで構成された、5V系の代表的な論理回路方式。しきい値電圧の規定を含め、長年デジタル回路の論理レベルの基準として広く使われてきた。トランジスタ・トランジスタ・ロジック(TTL)。", "名詞", "This sensor module outputs a TTL-compatible signal that can be read directly by a 5 V microcontroller.", "組み込み（エレキ）", "850"),
    ("CMOS", "pチャネルとnチャネルのMOSFETを相補的に組み合わせて構成する、消費電力が小さい代表的な論理回路・半導体プロセス方式。信号のHigh/Lowを判定するしきい値電圧の規格としても使われる。相補型MOS(CMOS)。", "名詞", "The microcontroller's I/O pins can be configured for either CMOS or TTL input thresholds.", "組み込み（エレキ）", "870"),
    ("junction-to-ambient thermal resistance", "ICの内部で発生した熱が、半導体の接合部(ジャンクション)から周囲の空気(アンビエント)まで伝わる際の伝わりにくさを示す値。単位は℃/W。この値と消費電力から接合部温度を見積もることができる。接合部-周囲間熱抵抗(θJA)。", "名詞", "With a junction-to-ambient thermal resistance of 60°C/W, dissipating 0.5 W raises the junction temperature by 30°C above ambient.", "組み込み（エレキ）", "940"),
    ("bus contention", "共有されたバス上で、複数のデバイスが同時にHighとLowを出力しようとする(あるいは複数が同時に駆動しようとする)ことで生じる、信号の競合状態。過大な電流が流れ素子を損傷する原因にもなりうる。バス競合。", "名詞", "Enabling two devices' outputs on the same bus at the same time causes bus contention and can damage both drivers.", "組み込み（エレキ）", "900"),
    ("reference designator", "回路図や基板上で個々の部品を識別するために付けられる、部品種別を表すアルファベットと通し番号の組み合わせ(例: 抵抗のR1、コンデンサのC3、ICのU2など)。リファレンス指定子・部品番号。", "名詞", "The typical application circuit labels the decoupling capacitor as C1 using its reference designator.", "組み込み（エレキ）", "800"),
    ("input capacitance", "ICの入力ピンが持つ、寄生的な静電容量。信号源から見た負荷となり、立ち上がり・立ち下がり時間や高速動作時の信号品質に影響する。入力容量。", "名詞", "The 5 pF input capacitance of this pin adds a small RC delay when driven through a high-impedance source.", "組み込み（エレキ）", "900"),
    ("leakage current", "理想的にはゼロであるべき、オフ状態の入出力ピンやpn接合を通じてわずかに漏れ出す電流。入力リーク電流・出力リーク電流など。リーク電流・漏れ電流。", "名詞", "Input leakage current is specified as ±1 μA maximum when the pin is at either supply rail.", "組み込み（エレキ）", "900"),
    ("slew rate", "増幅器や出力段が、単位時間あたりに出力電圧をどれだけ速く変化させられるかを示す限界値。単位はV/µsなど。スルーレート。", "名詞", "The op-amp's slew rate of 0.5 V/μs limits how fast its output can follow a rapidly changing input.", "組み込み（エレキ）", "900"),
    ("power dissipation", "ICが動作中に電気エネルギーを消費し、それが熱として放出される量。絶対最大定格や熱設計の基準として規定される。消費電力(発熱量)。", "名詞", "The package can safely dissipate up to 1.5 W of power dissipation at 25°C ambient temperature.", "組み込み（エレキ）", "880"),
]


def main() -> None:
    with db() as conn:
        existing = set()
        for r in conn.execute("SELECT english FROM words").fetchall():
            existing.add(r["english"].lower())
        inserted = 0
        skipped = 0
        for english, japanese, pos, example, domain, level in WORDS:
            if english.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (english, japanese, pos, example, domain, level),
            )
            existing.add(english.lower())
            inserted += 1
        print("inserted=" + str(inserted) + " skipped=" + str(skipped))


if __name__ == "__main__":
    main()
