---
name: caveman-compress
description: >
  Ultra-compresses a text or memory file while preserving code, URLs, technical
  terms, and structure. Use on "compress this file", "compress my notes",
  "shrink this document", or when given a file path to condense.
argument-hint: "[filepath]"
---
Compress the given file. Preserve all technical substance. Only fluff gone.

## When to use
User says "compress this", "compress <file>", "shrink", "make terse", or passes a file path with `/caveman-compress`.

## Rules
**Preserve exactly:** code blocks, inline code, URLs, file paths, commands, technical terms, proper nouns, dates/versions/numbers, environment variables, markdown headings, bullet hierarchy, numbered lists, tables, YAML frontmatter.
**Compress:** filler phrases, hedging, redundant explanations, repeated adjectives, long-winded examples, pleasantries, meta-commentary.
**Structure:** Keep the original heading hierarchy. Drop sections that add no information.
**Format:** Output the compressed version. Original: backup as `<filename>.original.md` if writing to disk.

## Output
The compressed content. Nothing else. If the file is already dense, say "Already minimal — no compression needed."

## Boundaries
Never compress source/config files (.py, .js, .ts, .json, .yaml, .toml, .env, .lock, .css, .html, .xml, .sql, .sh) unless explicitly told to. Natural language files only (.md, .txt).
