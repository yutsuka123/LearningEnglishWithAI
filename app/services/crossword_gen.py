"""クロスワードパズルのグリッド生成(2026-09-03・ゲーム機能第一弾)。

外部依存なし・貪欲法+複数試行のシンプルなアルゴリズム。「小規模(10語
程度)」という前提なので、バックトラッキングを伴う本格的な制約ソルバー
は使わない(games.pyの計画ドキュメント参照)。

手順:
  1. 候補語を長さ降順にソート(シャッフル後の安定ソートなので、同じ
     長さの語同士の順序だけが試行ごとに変わる)。
  2. 最長語をグリッド中央付近に横向きで配置。
  3. 残りの語は、既に配置済みの語との交差点を探して配置する
     (交差できない語は保留し、他の語が置かれた後に再挑戦)。交差候補が
     複数見つかった場合は、**交差数(=既に配置済みの文字と重なるマス数)
     が最大になる配置を優先する**(2026-09-03ユーザー指示「クロス数が
     少なすぎる、平均2箇所ほしい、最低1箇所・最大制限なし」への対応)。
  4. これを3回試し、最も多く配置できたパターンを採用する。
  5. 配置結果の外接矩形でグリッドを切り詰め、標準的なクロスワード式の
     採番(左上から走査し、続く方向にマスがある語の先頭に採番)を行う。

方向は「ヨコ(across)」「タテ(down)」の2方向(2026-09-03: 一度ナナメ
(diagonal)も試したが「ややこしくなる」とのユーザー判断で撤回済み)。
方向は (dr, dc) の単位ベクトルとして扱い、「隣接直交方向」は90度回転
(-dc, dr)で求めるため、両方向とも同じロジックで扱える。

呼び出し側(app/routers/games.py)は、返り値の clues が入力語数より
少ない場合(配置しきれなかった語がある場合)を考慮すること。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

MAX_GRID = 34


def grid_size_for(word_count: int) -> int:
    """語数に応じたグリッド上限を返す(2026-09-03ユーザー指示「語数の
    上限を50まで」への対応)。語数が多いほど配置スペースが必要になる
    (固定20だと50語では28/50語しか置けないことを実測確認済み)。
    小規模(10語程度)では従来通り20を使う。"""
    return max(20, min(MAX_GRID, word_count + 10))

# 方向 -> 単位ベクトル(行方向, 列方向)。
DIRECTIONS: dict[str, tuple[int, int]] = {
    "across": (0, 1),
    "down": (1, 0),
}


@dataclass
class Clue:
    number: int
    direction: str  # 'across' | 'down'
    row: int
    col: int
    length: int
    word_id: int
    english: str


@dataclass
class Puzzle:
    rows: int
    cols: int
    cells: set[tuple[int, int]]  # 文字が入るマスの座標(0始まり)
    clues: list[Clue] = field(default_factory=list)


@dataclass
class _Placement:
    word_id: int
    english: str
    row: int
    col: int
    direction: str


def _cells_for(
    word: str, row: int, col: int, direction: str,
) -> list[tuple[int, int]]:
    dr, dc = DIRECTIONS[direction]
    return [(row + dr * i, col + dc * i) for i in range(len(word))]


def _crossing_count(word: str, row: int, col: int, direction: str,
                     grid: dict[tuple[int, int], str]) -> int:
    """この配置が既存の文字と重なるマス数(=交差数)。呼び出し前に
    _can_placeで整合性(重なるマスは必ず同じ文字)を確認しておくこと。"""
    return sum(1 for cell in _cells_for(word, row, col, direction)
               if cell in grid)


def _can_place(
    word: str, row: int, col: int, direction: str,
    grid: dict[tuple[int, int], str], max_grid: int,
    boundary: set[tuple[int, int]] = frozenset(),
) -> bool:
    """``boundary``: 既存の各語の直前・直後マス(before/after)の集合
    (2026-09-03発覚のバグ対策)。単語Aの前後マスが空であることは配置
    時に確認していたが、後から別の語Bがちょうどそのマスへ(Aとは無関係
    に)乗ってしまうケースを防げておらず、密なパズル(語数が多い場合)で
    「実際には繋がっていないのに読み上げると連続して見える」語や、
    採番ロジックが語の先頭マスを拾えずクラッシュする不具合につながって
    いた。新しい語を置くときも、既存語のboundaryに重ならないことを
    確認する。"""
    dr, dc = DIRECTIONS[direction]
    cells = _cells_for(word, row, col, direction)
    for r, c in cells:
        if r < 0 or c < 0 or r >= max_grid or c >= max_grid:
            return False
        if (r, c) in boundary:
            return False

    # 開始直前・終了直後のマスが空(または盤外)であること
    # (単語同士が意図せず前後で結合するのを防ぐ)。
    before = (row - dr, col - dc)
    after = (row + dr * len(word), col + dc * len(word))
    if before in grid or after in grid:
        return False

    # 直交方向(90度回転したベクトル)の隣接マス。ヨコなら上下、タテなら
    # 左右が相当する。
    perp = (-dc, dr)
    has_intersection = False
    for i, (r, c) in enumerate(cells):
        existing = grid.get((r, c))
        if existing is not None:
            if existing != word[i]:
                return False
            has_intersection = True
            continue
        # 交差点以外のマスは、直交方向の両隣も空であること
        # (意図しない語の併走・接触を防ぐ)。
        for sign in (1, -1):
            nr, nc = r + perp[0] * sign, c + perp[1] * sign
            if (nr, nc) in grid:
                return False
    return has_intersection


def _boundary_for(placements: list[_Placement]) -> set[tuple[int, int]]:
    """配置済みの各語の直前・直後マスの集合(_can_placeのboundary引数用)。"""
    b: set[tuple[int, int]] = set()
    for p in placements:
        dr, dc = DIRECTIONS[p.direction]
        b.add((p.row - dr, p.col - dc))
        b.add((p.row + dr * len(p.english), p.col + dc * len(p.english)))
    return b


def _try_place_via_intersection(
    word_id: int, word: str, grid: dict[tuple[int, int], str], max_grid: int,
    boundary: set[tuple[int, int]] = frozenset(),
) -> _Placement | None:
    """交差数が最大になる配置を探して返す(見つからなければNone)。
    交差数が同点の場合は、先頭文字/末尾文字での交差を優先する
    (2026-09-03ユーザー指示「先頭文字・末尾文字の50%以上はクロスして
    ほしい」への対応。本物のクロスワードは語の端で交差することが多い
    ため)。"""
    best: _Placement | None = None
    best_score = (-1, -1)
    for (r, c), letter in list(grid.items()):
        for i, ch in enumerate(word):
            if ch != letter:
                continue
            for direction, (dr, dc) in DIRECTIONS.items():
                row, col = r - dr * i, c - dc * i
                if not _can_place(
                        word, row, col, direction, grid, max_grid, boundary):
                    continue
                crossings = _crossing_count(word, row, col, direction, grid)
                edge_bonus = 1 if i in (0, len(word) - 1) else 0
                score = (crossings, edge_bonus)
                if score > best_score:
                    best_score = score
                    best = _Placement(word_id, word, row, col, direction)
    return best


def _run_attempt(
    candidates: list[tuple[int, str]], max_grid: int,
    target_count: int | None = None,
) -> list[_Placement]:
    if not candidates:
        return []
    shuffled = candidates[:]
    random.shuffle(shuffled)
    if target_count is not None:
        # 候補が目標語数より多い場合、試行ごとに異なる部分集合で組み方を
        # 試す(2026-09-03ユーザー指示「平均2以上、できれば3以上」への
        # 対応。単語の組み合わせ次第で交差しやすさが変わるため、順序
        # だけでなく採用する語の組み合わせ自体も試行間で変える方が
        # 平均交差数が伸びることを実測確認済み)。
        shuffled = shuffled[:target_count]
    ordered = sorted(shuffled, key=lambda wc: -len(wc[1]))

    grid: dict[tuple[int, int], str] = {}
    boundary: set[tuple[int, int]] = set()
    placements: list[_Placement] = []

    first_id, first_word = ordered[0]
    start_col = max((max_grid - len(first_word)) // 2, 0)
    start_row = max_grid // 2
    for i, ch in enumerate(first_word):
        grid[(start_row, start_col + i)] = ch
    first_placement = _Placement(
        first_id, first_word, start_row, start_col, "across")
    placements.append(first_placement)
    boundary |= _boundary_for([first_placement])

    pending = list(ordered[1:])
    while pending:
        # 2026-09-05ユーザー指示「平均3以上に増やしたい」への対応:
        # 従来は先頭から順に「置ける語を見つけたら即置く」方式だった
        # ため、置く順序次第で本来もっと交差できた語が先に(交差数の
        # 少ない位置に)置かれてしまうことがあった。ここでは毎回
        # pending全員の最善配置を評価し、**その時点で最も交差数が
        # 多い語を優先して置く**(best-first挿入)方式に変更。交差の
        # 多い語ほど早く確定させることで、後続の語がその交差点を
        # 目当てに配置しやすくなり、全体の平均交差数が伸びる
        # (小規模パズル前提なのでO(残語数^2)でも計算コストは軽い)。
        best_idx: int | None = None
        best_placement: _Placement | None = None
        best_score = (-1, -1)
        for idx, (word_id, word) in enumerate(pending):
            placement = _try_place_via_intersection(
                word_id, word, grid, max_grid, boundary)
            if placement is None:
                continue
            crossings = _crossing_count(
                placement.english, placement.row, placement.col,
                placement.direction, grid)
            score = (crossings, len(word))
            if score > best_score:
                best_score = score
                best_idx = idx
                best_placement = placement
        if best_placement is None:
            break  # 誰も配置できない語だけが残った

        word_id, word = pending.pop(best_idx)
        cells_here = _cells_for(
            word, best_placement.row, best_placement.col,
            best_placement.direction)
        dr, dc = DIRECTIONS[best_placement.direction]
        for r, c in cells_here:
            idx = ((r - best_placement.row) // dr if dr
                   else (c - best_placement.col) // dc)
            grid[(r, c)] = word[idx]
        boundary |= _boundary_for([best_placement])
        placements.append(best_placement)

    return _refine(placements, max_grid)


def _refine(
    placements: list[_Placement], max_grid: int, rounds: int = 4,
) -> list[_Placement]:
    """各語を1つずつ「他の語は固定したまま最善の位置に置き直せないか」を
    試す局所探索(2026-09-03ユーザー指示「最低1平均2以上、できれば平均
    3以上」への対応)。1回の貪欲配置(_run_attempt)は「先に置かれた語との
    交差」しか考慮できないため、後から置かれた語がより良い交差点を
    持っていても最初の一巡では見つからないことがある。全語を固定した
    グリッドを基準に、語を1つだけ抜いて再探索することで、既に確定した
    他の語との新たな交差点(見落とし)を拾えるようにする。件数が少ない
    小規模パズル前提なので計算コストは軽い。"""
    if len(placements) < 2:
        return placements
    result = list(placements)
    for _ in range(rounds):
        improved = False
        for idx in range(len(result)):
            target = result[idx]
            grid: dict[tuple[int, int], str] = {}
            others = [other for j, other in enumerate(result) if j != idx]
            for other in others:
                for (r, c), ch in zip(
                    _cells_for(other.english, other.row, other.col,
                               other.direction),
                    other.english,
                ):
                    grid[(r, c)] = ch
            boundary = _boundary_for(others)
            current_score = _crossing_count(
                target.english, target.row, target.col, target.direction,
                grid)
            candidate = _try_place_via_intersection(
                target.word_id, target.english, grid, max_grid, boundary)
            if candidate is None:
                continue
            candidate_score = _crossing_count(
                candidate.english, candidate.row, candidate.col,
                candidate.direction, grid)
            if candidate_score > current_score:
                result[idx] = candidate
                improved = True
        if not improved:
            break
    return result


def _bbox_area(placements: list[_Placement]) -> int:
    """配置全体の外接矩形の面積(2026-09-05ユーザー要望「一般的なクロス
    ワードの配置に近づける・無理のない範囲で」への対応)。generate()の
    試行選択で、配置数・交差数が同点のときのタイブレークに使う
    (同じ結果を保ったまま、より密集した=よくあるクロスワードらしい
    配置を優先できる)。"""
    if not placements:
        return 0
    all_cells = [
        cell for p in placements
        for cell in _cells_for(p.english, p.row, p.col, p.direction)
    ]
    rows = [r for r, _ in all_cells]
    cols = [c for _, c in all_cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _total_crossings(placements: list[_Placement]) -> int:
    """配置全体の交差マス総数(=各語のcrossing数の合計)。小規模(10語
    程度)前提なので、O(語数^2)の単純な総当たりで十分。"""
    spans = [
        (p, set(_cells_for(p.english, p.row, p.col, p.direction)))
        for p in placements
    ]
    total = 0
    for i, (_, cells_i) in enumerate(spans):
        for j, (_, cells_j) in enumerate(spans):
            if i != j:
                total += len(cells_i & cells_j)
    return total


def generate(
    candidates: list[tuple[int, str]], attempts: int = 15,
    max_grid: int = MAX_GRID, target_count: int | None = None,
    compact: bool = False,
) -> Puzzle | None:
    """candidates: [(word_id, english), ...]（英大文字小文字は問わないが
    内部ではそのまま比較に使うので、呼び出し側で大文字化しておくこと）。
    配置できる語が1つも無ければ None を返す。

    ``target_count``: 指定すると、candidatesがそれより多い場合に**試行
    ごとに異なる部分集合**を採用語数分だけランダムに選んで配置を試す
    (2026-09-03ユーザー指示「平均2以上、できれば3以上」対応。呼び出し側
    (games.py)が実際に必要な語数より多い候補を渡すことで、単語の組み
    合わせ自体も探索対象になり、順序だけを変える場合より平均交差数が
    伸びることを実測確認済み)。省略時は全candidatesをそのまま使う
    (従来通りの挙動)。

    複数回試行し、**配置できた語数を最優先**、同数なら**総交差マス数が
    多い方**を採用する(2026-09-03ユーザー指示「クロス数が少なすぎる、
    平均2箇所ほしい、最低1箇所・最大制限なし」への対応。件数が少ない
    小規模パズルなので試行を増やしても計算コストは軽い)。配置数・交差数
    まで同点の場合は、外接矩形の面積が小さい方(より密集した、一般的な
    クロスワードに近い配置)を採用する(2026-09-05ユーザー要望)。

    ``compact=True``(2026-09-05ユーザー要望「選択できるだけ面積減らして
    クロスを多くするモード」)のときは、面積の小ささを交差数より優先
    する(配置数最優先は変えず、2番目の判定基準を入れ替えるだけ)。
    既定(False)は従来通り交差数優先の「普通モード」。"""
    best: list[_Placement] = []
    best_key = (-1, -1, float("-inf"))
    for _ in range(attempts):
        result = _run_attempt(candidates, max_grid, target_count)
        crossings = _total_crossings(result)
        area = _bbox_area(result)
        key = ((len(result), -area, crossings) if compact
               else (len(result), crossings, -area))
        if key > best_key:
            best_key = key
            best = result
    if not best:
        return None

    all_cells = [
        cell for p in best
        for cell in _cells_for(p.english, p.row, p.col, p.direction)
    ]
    rows = [p.row for p in best] + [r for r, _ in all_cells]
    cols = [p.col for p in best] + [c for _, c in all_cells]
    min_row, min_col = min(rows), min(cols)
    max_row, max_col = max(rows), max(cols)

    cells: set[tuple[int, int]] = set()
    shifted: list[_Placement] = []
    for p in best:
        nr, nc = p.row - min_row, p.col - min_col
        shifted.append(_Placement(p.word_id, p.english, nr, nc, p.direction))
        for r, c in _cells_for(p.english, nr, nc, p.direction):
            cells.add((r, c))

    grid_rows = max_row - min_row + 1
    grid_cols = max_col - min_col + 1

    # 採番はcellsからの推測(隣接マスの有無)ではなく、実際の配置一覧
    # (shifted)から直接「語の開始マス」を求める(2026-09-03発覚:
    # 語数が多く密なパズルでは、無関係な2語がたまたま隣接するマスを
    # 持つことがあり、隣接判定だけでは語の開始マスを取りこぼして
    # KeyErrorになる不具合があった。_can_place/_boundary_forの修正で
    # この隣接自体は防げるが、採番は常に確実な方法にしておく)。
    starts: dict[tuple[int, int], set[str]] = {}
    for p in shifted:
        starts.setdefault((p.row, p.col), set()).add(p.direction)

    numbering: dict[tuple[int, int], int] = {}
    counter = 1
    for r in range(grid_rows):
        for c in range(grid_cols):
            if (r, c) in starts:
                numbering[(r, c)] = counter
                counter += 1

    clues = [
        Clue(
            number=numbering[(p.row, p.col)],
            direction=p.direction,
            row=p.row,
            col=p.col,
            length=len(p.english),
            word_id=p.word_id,
            english=p.english,
        )
        for p in shifted
    ]
    clues.sort(key=lambda cl: (cl.number, cl.direction))

    return Puzzle(rows=grid_rows, cols=grid_cols, cells=cells, clues=clues)
