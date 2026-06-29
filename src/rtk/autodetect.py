import re
from . import filters

RE_GIT_DIFF = re.compile(r"^diff --git ", re.M)
RE_GIT_DIFF_HUNK = re.compile(r"^@@ ", re.M)
RE_GIT_STATUS = re.compile(r"^On branch |^nothing to commit|^Changes (not |to be )|^Untracked files:", re.M)
RE_PORCELAIN = re.compile(r"^[ MADRCU?!][ MADRCU?!] \S", re.M)
RE_BUILD_OUTPUT = re.compile(
    r"^(npm (warn|error|ERR!)|yarn (warn|error)|\s*Compiling\s+\S+|\s*Downloading\s+\S+|added \d+ package|\[ERROR\]|BUILD (SUCCESS|FAILED)|\s*Finished\s+|Successfully (installed|built)|ERROR:)",
    re.I | re.M
)
RE_TREE_GLYPH = re.compile(r"[├└]──|│  ")
RE_LS_ROW = re.compile(r"^[-dlbcps][rwx-]{9}", re.M)
RE_LS_TOTAL = re.compile(r"^total \d+$", re.M)
READ_NUMBERED_LINE_RE = re.compile(r"^\s*\d+\|")
SEARCH_LIST_HEADER_RE = re.compile(r"^Result of search in '[^']*' \(total (\d+) files?\):")

def is_grep_line(line):
    first = line.find(":")
    if first == -1:
        return False
    second = line.find(":", first + 1)
    if second == -1:
        return False
    lineno = line[first + 1:second]
    return lineno.isdigit()

def is_path_like(line):
    t = line.strip()
    if not t:
        return False
    if ":" in t:
        return False
    return t.startswith(".") or t.startswith("/") or "/" in t

def is_mostly_porcelain(head):
    lines = [l for l in head.split("\n") if l.strip()]
    if len(lines) < 3:
        return False
    hits = sum(1 for l in lines if RE_PORCELAIN.search(l))
    return (hits / len(lines)) >= 0.6

def is_line_numbered(lines):
    hits = 0
    non_empty = 0
    sample = lines[:100]
    for l in sample:
        if not l.strip():
            continue
        non_empty += 1
        if READ_NUMBERED_LINE_RE.match(l):
            hits += 1
    if non_empty < 5:
        return False
    return (hits / non_empty) >= filters.READ_NUMBERED_MIN_HIT_RATIO

def count_matches(text, pattern):
    return len(pattern.findall(text))

def auto_detect_filter(text):
    head = text[:filters.DETECT_WINDOW] if len(text) > filters.DETECT_WINDOW else text

    if RE_GIT_DIFF.search(head) or RE_GIT_DIFF_HUNK.search(head):
        return "git-diff", filters.git_diff
    if RE_GIT_STATUS.search(head):
        return "git-status", filters.git_status
    if RE_BUILD_OUTPUT.search(head):
        return "build-output", filters.build_output
    if is_mostly_porcelain(head):
        return "git-status", filters.git_status

    lines = head.split("\n")
    non_empty = [l for l in lines if l.strip()]

    # Grep rule
    first_5 = non_empty[:5]
    if any(is_grep_line(l) for l in first_5):
        return "grep", filters.grep_compact

    # Find rule
    if len(non_empty) >= 3 and all(is_path_like(l) for l in non_empty):
        return "find", filters.find_compact

    if RE_TREE_GLYPH.search(head):
        return "tree", filters.tree_compact

    if RE_LS_TOTAL.search(head) or count_matches(head, RE_LS_ROW) >= 3:
        return "ls", filters.ls_compact

    if SEARCH_LIST_HEADER_RE.search(head):
        return "search-list", filters.search_list

    if len(lines) >= filters.SMART_TRUNCATE_MIN_LINES and is_line_numbered(lines):
        return "read-numbered", filters.read_numbered

    if len(non_empty) >= 5:
        # Check if there are duplicates to justify dedup
        unique_lines = set(non_empty)
        if len(unique_lines) < len(non_empty):
            return "dedup-log", filters.dedup_log

    if len(lines) >= filters.SMART_TRUNCATE_MIN_LINES:
        return "smart-truncate", filters.smart_truncate

    return None, None
