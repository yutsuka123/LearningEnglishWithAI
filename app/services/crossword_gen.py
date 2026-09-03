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

MAX_GRID = 20

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
) -> bool:
    dr, dc = DIRECTIONS[direction]
    cells = _cells_for(word, row, col, direction)
    for r, c in cells:
        if r < 0 or c < 0 or r >= max_grid or c >= max_grid:
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


def _try_place_via_intersection(
    word_id: int, word: str, grid: dict[tuple[int, int], str], max_grid: int,
) -> _Placement | None:
    """交差数が最大になる配置を探して返す(見つからなければNone)。"""
    best: _Placement | None = None
    best_score = -1
    for (r, c), letter in list(grid.items()):
        for i, ch in enumerate(word):
            if ch != letter:
                continue
            for direction, (dr, dc) in DIRECTIONS.items():
                row, col = r - dr * i, c - dc * i
                if not _can_place(word, row, col, direction, grid, max_grid):
                    continue
                score = _crossing_count(word, row, col, direction, grid)
                if score > best_score:
                    best_score = score
                    best = _Placement(word_id, word, row, col, direction)
    return best


def _run_attempt(
    candidates: list[tuple[int, str]], max_grid: int,
) -> list[_Placement]:
    if not candidates:
        return []
    shuffled = candidates[:]
    random.shuffle(shuffled)
    ordered = sorted(shuffled, key=lambda wc: -len(wc[1]))

    grid: dict[tuple[int, int], str] = {}
    placements: list[_Placement] = []

    first_id, first_word = ordered[0]
    start_col = max((max_grid - len(first_word)) // 2, 0)
    start_row = max_grid // 2
    for i, ch in enumerate(first_word):
        grid[(start_row, start_col + i)] = ch
    placements.append(
        _Placement(first_id, first_word, start_row, start_col, "across"))

    pending = list(ordered[1:])
    while pending:
        placed_this_round = False
        still_pending: list[tuple[int, str]] = []
        for word_id, word in pending:
            placement = _try_place_via_intersection(
                word_id, word, grid, max_grid)
            if placement is None:
                still_pending.append((word_id, word))
                continue
            cells_here = _cells_for(
                word, placement.row, placement.col, placement.direction)
            dr, dc = DIRECTIONS[placement.direction]
            for r, c in cells_here:
                idx = ((r - placement.row) // dr if dr
                       else (c - placement.col) // dc)
                grid[(r, c)] = word[idx]
            placements.append(placement)
            placed_this_round = True
        pending = still_pending
        if not placed_this_round:
            break  # これ以上配置できる語がない

    return placements


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
    max_grid: int = MAX_GRID,
) -> Puzzle | None:
    """candidates: [(word_id, english), ...]（英大文字小文字は問わないが
    内部ではそのまま比較に使うので、呼び出し側で大文字化しておくこと）。
    配置できる語が1つも無ければ None を返す。

    複数回試行し、**配置できた語数を最優先**、同数なら**総交差マス数が
    多い方**を採用する(2026-09-03ユーザー指示「クロス数が少なすぎる、
    平均2箇所ほしい、最低1箇所・最大制限なし」への対応。件数が少ない
    小規模パズルなので試行を増やしても計算コストは軽い)。"""
    best: list[_Placement] = []
    best_key = (-1, -1)
    for _ in range(attempts):
        result = _run_attempt(candidates, max_grid)
        key = (len(result), _total_crossings(result))
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

    numbering: dict[tuple[int, int], int] = {}
    counter = 1
    for r in range(grid_rows):
        for c in range(grid_cols):
            if (r, c) not in cells:
                continue
            starts_across = (c == 0 or (r, c - 1) not in cells) and (
                c + 1 < grid_cols and (r, c + 1) in cells)
            starts_down = (r == 0 or (r - 1, c) not in cells) and (
                r + 1 < grid_rows and (r + 1, c) in cells)
            if starts_across or starts_down:
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
