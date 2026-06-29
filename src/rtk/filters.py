import re
from collections import defaultdict

# Constants mirroring Rust / JS parity
RAW_CAP = 10 * 1024 * 1024       # 10 MiB
MIN_COMPRESS_SIZE = 500          # bytes
DETECT_WINDOW = 1024             # peek window

GIT_DIFF_HUNK_MAX_LINES = 100
GIT_DIFF_CONTEXT_KEEP = 3
DEDUP_LINE_MAX = 2000

GREP_PER_FILE_MAX = 10
FIND_PER_DIR_MAX = 10
FIND_TOTAL_DIR_MAX = 20
STATUS_MAX_FILES = 10
STATUS_MAX_UNTRACKED = 10

LS_EXT_SUMMARY_TOP = 5
LS_NOISE_DIRS = [
    "node_modules", ".git", "target", "__pycache__",
    ".next", "dist", "build", ".cache", ".turbo",
    ".vercel", ".pytest_cache", ".mypy_cache", ".tox",
    ".venv", "venv", "env", "coverage", ".nyc_output",
    ".DS_Store", "Thumbs.db", ".idea", ".vscode", ".vs",
    "*.egg-info", ".eggs"
]

TREE_MAX_LINES = 200
SEARCH_LIST_PER_DIR_MAX = 10
SEARCH_LIST_TOTAL_DIR_MAX = 20

SMART_TRUNCATE_HEAD = 120
SMART_TRUNCATE_TAIL = 60
SMART_TRUNCATE_MIN_LINES = 250

READ_NUMBERED_MIN_HIT_RATIO = 0.7

# --- 1. git-diff filter ---
def git_diff(diff_text, max_lines=500):
    result = []
    current_file = ""
    added = 0
    removed = 0
    in_hunk = False
    hunk_shown = 0
    hunk_skipped = 0
    was_truncated = False

    lines = diff_text.split("\n")
    for line in lines:
        if line.startswith("diff --git"):
            if hunk_skipped > 0:
                result.append(f"  ... ({hunk_skipped} lines truncated)")
                was_truncated = True
                hunk_skipped = 0
            if current_file and (added > 0 or removed > 0):
                result.append(f"  +{added} -{removed}")
            
            parts = line.split(" b/")
            current_file = parts[1] if len(parts) > 1 else "unknown"
            result.append(f"\n{current_file}")
            added = 0
            removed = 0
            in_hunk = False
            hunk_shown = 0
        elif line.startswith("@@"):
            if hunk_skipped > 0:
                result.append(f"  ... ({hunk_skipped} lines truncated)")
                was_truncated = True
                hunk_skipped = 0
            in_hunk = True
            hunk_shown = 0
            result.append(f"  {line}")
        elif in_hunk:
            if line.startswith("+") and not line.startswith("+++"):
                added += 1
                if hunk_shown < GIT_DIFF_HUNK_MAX_LINES:
                    result.append(f"  {line}")
                    hunk_shown += 1
                else:
                    hunk_skipped += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed += 1
                if hunk_shown < GIT_DIFF_HUNK_MAX_LINES:
                    result.append(f"  {line}")
                    hunk_shown += 1
                else:
                    hunk_skipped += 1
            elif hunk_shown < GIT_DIFF_HUNK_MAX_LINES and not line.startswith("\\"):
                if hunk_shown > 0:
                    result.append(f"  {line}")
                    hunk_shown += 1
        
        if len(result) >= max_lines:
            result.append("\n... (more changes truncated)")
            was_truncated = True
            break

    if hunk_skipped > 0:
        result.append(f"  ... ({hunk_skipped} lines truncated)")
        was_truncated = True

    if current_file and (added > 0 or removed > 0):
        result.append(f"  +{added} -{removed}")

    if was_truncated:
        result.append("[full diff: rtk git diff --no-compact]")

    return "\n".join(result)

# --- 2. git-status filter ---
def git_status(status_text):
    lines = status_text.split("\n")
    if not lines or (len(lines) == 1 and not lines[0].strip()):
        return "Clean working tree"

    branch = ""
    staged_files = []
    modified_files = []
    untracked_files = []
    staged = 0
    modified = 0
    untracked = 0
    conflicts = 0

    for raw in lines:
        if not raw.strip():
            continue

        long_branch = re.match(r"^On branch (\S+)", raw)
        if long_branch:
            branch = long_branch.group(1)
            continue

        if raw.startswith("##"):
            branch = re.sub(r"^##\s*", "", raw)
            continue

        if len(raw) >= 3 and re.match(r"^[ MADRCU?!][ MADRCU?!] ", raw):
            x = raw[0]
            y = raw[1]
            file = raw[3:]

            if raw[0:2] == "??":
                untracked += 1
                untracked_files.append(file)
                continue

            if x in "MADRC":
                staged += 1
                staged_files.append(file)
            elif x == "U":
                conflicts += 1

            if y in "MD":
                modified += 1
                modified_files.append(file)
            continue

        long_match = re.match(r"^\s*(modified|new file|deleted|renamed|both modified):\s+(.+)$", raw)
        if long_match:
            kind = long_match.group(1)
            path = long_match.group(2).strip()
            if kind == "both modified":
                conflicts += 1
            elif kind in ("modified", "deleted"):
                modified += 1
                modified_files.append(path)
            elif kind in ("new file", "renamed"):
                staged += 1
                staged_files.append(path)
            continue

    out = []
    if branch:
        out.append(f"* {branch}")

    if staged > 0:
        out.append(f"+ Staged: {staged} files")
        for f in staged_files[:STATUS_MAX_FILES]:
            out.append(f"   {f}")
        if len(staged_files) > STATUS_MAX_FILES:
            out.append(f"   ... +{len(staged_files) - STATUS_MAX_FILES} more")

    if modified > 0:
        out.append(f"~ Modified: {modified} files")
        for f in modified_files[:STATUS_MAX_FILES]:
            out.append(f"   {f}")
        if len(modified_files) > STATUS_MAX_FILES:
            out.append(f"   ... +{len(modified_files) - STATUS_MAX_FILES} more")

    if untracked > 0:
        out.append(f"? Untracked: {untracked} files")
        for f in untracked_files[:STATUS_MAX_UNTRACKED]:
            out.append(f"   {f}")
        if len(untracked_files) > STATUS_MAX_UNTRACKED:
            out.append(f"   ... +{len(untracked_files) - STATUS_MAX_UNTRACKED} more")

    if conflicts > 0:
        out.append(f"conflicts: {conflicts} files")

    if staged == 0 and modified == 0 and untracked == 0 and conflicts == 0:
        out.append("clean — nothing to commit")

    return "\n".join(out)

# --- 3. ls filter ---
LS_DATE_RE = re.compile(r"\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+(\d{4}|\d{2}:\d{2})\s+")

def human_size(bytes_val):
    if bytes_val >= 1048576:
        return f"{bytes_val / 1048576:.1f}M"
    if bytes_val >= 1024:
        return f"{bytes_val / 1024:.1f}K"
    return f"{bytes_val}B"

def parse_ls_line(line):
    m = LS_DATE_RE.search(line)
    if not m:
        return None
    name = line[m.end():]
    before_date = line[:m.start()]
    before_parts = [p for p in before_date.split() if p]
    if len(before_parts) < 4:
        return None

    perms = before_parts[0]
    file_type = perms[0]

    size = 0
    for part in reversed(before_parts):
        try:
            size = int(part)
            break
        except ValueError:
            continue
    return {"file_type": file_type, "size": size, "name": name}

def ls_compact(input_text):
    dirs = []
    files = []
    by_ext = defaultdict(int)

    for line in input_text.split("\n"):
        if line.startswith("total ") or not line:
            continue
        parsed = parse_ls_line(line)
        if not parsed:
            continue
        if parsed["name"] in (".", ".."):
            continue
        if parsed["name"] in LS_NOISE_DIRS:
            continue

        if parsed["file_type"] == "d":
            dirs.append(parsed["name"])
        elif parsed["file_type"] in ("-", "l"):
            dot = parsed["name"].rfind(".")
            ext = parsed["name"][dot:] if dot > 0 else "no ext"
            by_ext[ext] += 1
            files.append((parsed["name"], human_size(parsed["size"])))

    if not dirs and not files:
        return input_text

    out = []
    for d in dirs:
        out.append(f"{d}/")
    for name, size in files:
        out.append(f"{name}  {size}")

    summary = f"\nSummary: {len(files)} files, {len(dirs)} dirs"
    if by_ext:
        ext_sorted = sorted(by_ext.items(), key=lambda x: x[1], reverse=True)
        parts = [f"{c} {e}" for e, c in ext_sorted[:LS_EXT_SUMMARY_TOP]]
        summary += f" ({', '.join(parts)}"
        if len(ext_sorted) > LS_EXT_SUMMARY_TOP:
            summary += f", +{len(ext_sorted) - LS_EXT_SUMMARY_TOP} more"
        summary += ")"
    out.append(summary)
    return "\n".join(out)

# --- 4. grep filter ---
def grep_compact(input_text):
    by_file = defaultdict(list)
    total = 0

    for line in input_text.split("\n"):
        first = line.find(":")
        if first == -1:
            continue
        second = line.find(":", first + 1)
        if second == -1:
            continue
        file = line[:first]
        line_num_str = line[first + 1:second]
        content = line[second + 1:]

        if not line_num_str.isdigit():
            continue
        total += 1
        by_file[file].append((line_num_str, content))

    if total == 0:
        return input_text

    files = sorted(by_file.keys())
    out = [f"{total} matches in {len(files)}F:\n"]

    for file in files:
        matches = by_file[file]
        out.append(f"[file] {file} ({len(matches)}):")
        show = matches[:GREP_PER_FILE_MAX]
        for line_num, content in show:
            out.append(f"  {line_num.rjust(4)}: {content.strip()}")
        if len(matches) > GREP_PER_FILE_MAX:
            out.append(f"  +{len(matches) - GREP_PER_FILE_MAX}")
        out.append("")

    return "\n".join(out).strip()

# --- 5. find filter ---
def find_compact(input_text):
    lines = [l for l in input_text.split("\n") if l.strip()]
    if not lines:
        return input_text

    by_dir = defaultdict(list)
    for path in lines:
        last_slash = path.rfind("/")
        if last_slash == -1:
            directory = "."
            basename = path
        else:
            directory = path[:last_slash] or "/"
            basename = path[last_slash + 1:]
        by_dir[directory].append(basename)

    dirs = sorted(by_dir.keys())
    out = [f"{len(lines)} files in {len(dirs)} dirs:\n"]

    for directory in dirs[:FIND_TOTAL_DIR_MAX]:
        files = by_dir[directory]
        out.append(f"{directory}/  ({len(files)})")
        show_files = files[:FIND_PER_DIR_MAX]
        for f in show_files:
            out.append(f"  {f}")
        if len(files) > FIND_PER_DIR_MAX:
            out.append(f"  +{len(files) - FIND_PER_DIR_MAX}")

    if len(dirs) > FIND_TOTAL_DIR_MAX:
        out.append(f"\n+{len(dirs) - FIND_TOTAL_DIR_MAX} more dirs")

    return "\n".join(out)

# --- 6. tree filter ---
def tree_compact(input_text):
    lines = input_text.split("\n")
    if not lines:
        return input_text

    filtered = []
    for line in lines:
        if "director" in line and "file" in line:
            continue
        if not line.strip() and not filtered:
            continue
        filtered.append(line)

    while filtered and not filtered[-1].strip():
        filtered.pop()

    if len(filtered) > TREE_MAX_LINES:
        cut = len(filtered) - TREE_MAX_LINES
        return "\n".join(filtered[:TREE_MAX_LINES]) + f"\n... +{cut} more lines"

    return "\n".join(filtered)

# --- 7. dedup-log filter ---
def dedup_log(input_text):
    lines = input_text.split("\n")
    out = []
    prev = None
    run_count = 0
    blank_streak = 0

    def flush_run():
        if prev is not None and run_count > 1:
            out.append(f"  ... ({run_count - 1} duplicate lines)")

    for line in lines:
        if not line.strip():
            if blank_streak < 1:
                out.append(line)
            blank_streak += 1
            flush_run()
            prev = None
            run_count = 0
            continue

        blank_streak = 0
        if line == prev:
            run_count += 1
            continue

        flush_run()
        out.append(line)
        prev = line
        run_count = 1

        if len(out) >= DEDUP_LINE_MAX:
            out.append(f"... (truncated at {DEDUP_LINE_MAX} lines)")
            return "\n".join(out)

    flush_run()
    return "\n".join(out)

# --- 8. smart-truncate filter ---
def smart_truncate(input_text):
    lines = input_text.split("\n")
    if len(lines) < SMART_TRUNCATE_MIN_LINES:
        return input_text

    head = lines[:SMART_TRUNCATE_HEAD]
    tail = lines[-SMART_TRUNCATE_TAIL:]
    cut = len(lines) - len(head) - len(tail)
    return "\n".join(head + [f"... +{cut} lines truncated"] + tail)

# --- 9. read-numbered filter ---
def read_numbered(input_text):
    lines = input_text.split("\n")
    if len(lines) < SMART_TRUNCATE_MIN_LINES:
        return input_text

    head = lines[:SMART_TRUNCATE_HEAD]
    tail = lines[-SMART_TRUNCATE_TAIL:]
    cut = len(lines) - len(head) - len(tail)
    return "\n".join(head + [f"... +{cut} lines truncated (file continues)"] + tail)

# --- 10. search-list filter ---
def search_list(input_text):
    lines = input_text.split("\n")
    if not lines:
        return input_text

    header = lines[0] or ""
    rest = lines[1:]

    paths = []
    for raw in rest:
        t = raw.strip()
        if not t.startswith("- "):
            continue
        paths.append(t[2:])

    if not paths:
        return input_text

    by_dir = defaultdict(list)
    for p in paths:
        slash = p.rfind("/")
        directory = "." if slash == -1 else (p[:slash] or "/")
        name = p if slash == -1 else p[slash + 1:]
        by_dir[directory].append(name)

    dirs = sorted(by_dir.keys())
    out = [f"{header}\n{len(paths)} files in {len(dirs)} dirs:\n"]

    for directory in dirs[:SEARCH_LIST_TOTAL_DIR_MAX]:
        names = by_dir[directory]
        out.append(f"{directory}/ ({len(names)}):")
        for n in names[:SEARCH_LIST_PER_DIR_MAX]:
            out.append(f"  {n}")
        if len(names) > SEARCH_LIST_PER_DIR_MAX:
            out.append(f"  +{len(names) - SEARCH_LIST_PER_DIR_MAX}")
        out.append("")

    if len(dirs) > SEARCH_LIST_TOTAL_DIR_MAX:
        out.append(f"+{len(dirs) - SEARCH_LIST_TOTAL_DIR_MAX} more dirs")

    return "\n".join(out).strip()

# --- 11. build-output filter ---
RE_CARGO_ERR_CONT = re.compile(r"^\s*(-->|\||\d+\s*\||=)")

def build_output(input_text):
    lines = input_text.split("\n")
    if not lines:
        return input_text

    errors = []
    warnings = []
    deprecations = []
    summary = []
    compiling_count = 0
    downloading_count = 0
    in_cargo_error = False

    for line in lines:
        trimmed = line.strip()

        if in_cargo_error:
            if not trimmed:
                in_cargo_error = False
                continue
            if RE_CARGO_ERR_CONT.match(line):
                errors.append(line)
                continue
            in_cargo_error = False

        if not trimmed:
            continue

        if re.match(r"^npm (ERR!|error)", trimmed, re.I) or re.match(r"^yarn error", trimmed, re.I):
            errors.append(line)
            continue

        if re.match(r"^npm warn deprecated", trimmed, re.I):
            deprecations.append(line)
            continue
        if re.match(r"^npm warn", trimmed, re.I) or re.match(r"^yarn warn", trimmed, re.I):
            warnings.append(line)
            continue

        if re.match(r"^error(\[|:)", trimmed, re.I) or trimmed.startswith("error -->"):
            errors.append(line)
            in_cargo_error = True
            continue

        if re.match(r"^warning(\[|:)", trimmed, re.I) or trimmed.startswith("warning -->"):
            warnings.append(line)
            in_cargo_error = True
            continue

        if re.match(r"^ERROR:", trimmed, re.I):
            errors.append(line)
            continue

        if re.match(r"^\[ERROR\]", trimmed, re.I) or re.match(r"^BUILD FAILED", trimmed, re.I):
            errors.append(line)
            continue

        if re.match(r"^\[WARNING\]", trimmed, re.I):
            warnings.append(line)
            continue

        if re.match(r"^\s*Compiling\s+\S+", trimmed, re.I):
            compiling_count += 1
            continue
        if re.match(r"^\s*Downloading\s+\S+", trimmed, re.I) or re.match(r"^Fetching\s+", trimmed, re.I):
            downloading_count += 1
            continue

        if (
            re.match(r"^(added|removed|changed|audited|installed)\s+\d+\s+package", trimmed, re.I) or
            re.match(r"^\s*Finished\s+", trimmed, re.I) or
            re.match(r"^BUILD SUCCESS", trimmed, re.I) or
            re.match(r"^\d+\s+(vulnerabilities|packages?|warnings?|errors?)", trimmed, re.I) or
            re.match(r"^Successfully (installed|built)", trimmed, re.I) or
            re.match(r"^To address .* issues", trimmed, re.I) or
            re.match(r"^Run `npm (audit|fund)`", trimmed, re.I) or
            "packages are looking for funding" in trimmed
        ):
            summary.append(line)
            continue

    out = []
    keep_dep = deprecations[:3]
    for d in keep_dep:
        out.append(d)
    if len(deprecations) > 3:
        out.append(f"... +{len(deprecations) - 3} more deprecated packages")

    if compiling_count > 0:
        out.append(f"Compiled {compiling_count} packages")
    if downloading_count > 0:
        out.append(f"Downloaded {downloading_count} packages")

    for e in errors:
        out.append(e)

    keep_warnings = warnings[:5]
    for w in keep_warnings:
        out.append(w)
    if len(warnings) > 5:
        out.append(f"... +{len(warnings) - 5} more warnings")

    if summary:
        out.extend(summary)

    res = "\n".join(out).strip()
    return res if res else input_text
