"""Optional tree-sitter AST for Infinite Wiki — tighter symbol ranges.

Install (optional):
  pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript

If packages are missing, callers fall back to regex/indent heuristics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

_PARSERS: Dict[str, Any] = {}
_STATUS: Optional[Dict[str, Any]] = None


def treesitter_status() -> Dict[str, Any]:
    global _STATUS
    if _STATUS is not None:
        return dict(_STATUS)
    info: Dict[str, Any] = {
        "available": False,
        "core": False,
        "languages": {},
        "install": "pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript",
    }
    try:
        import tree_sitter  # noqa: F401

        info["core"] = True
    except Exception as e:
        info["error"] = f"tree_sitter: {e}"
        _STATUS = info
        return dict(info)

    for key, mod_name, attr in (
        ("python", "tree_sitter_python", "language"),
        ("javascript", "tree_sitter_javascript", "language"),
        ("typescript", "tree_sitter_typescript", "language_typescript"),
        ("tsx", "tree_sitter_typescript", "language_tsx"),
    ):
        try:
            mod = __import__(mod_name)
            fn = getattr(mod, attr, None)
            if callable(fn):
                info["languages"][key] = True
            else:
                info["languages"][key] = False
        except Exception:
            info["languages"][key] = False

    info["available"] = info["core"] and any(info["languages"].values())
    _STATUS = info
    return dict(info)


def _parser_for(lang: str):
    lang = (lang or "").lower()
    if lang in ("js", "jsx"):
        lang = "javascript"
    if lang in ("ts",):
        lang = "typescript"
    if lang in _PARSERS:
        return _PARSERS[lang]
    st = treesitter_status()
    if not st.get("core") or not st.get("languages", {}).get(lang):
        return None
    try:
        from tree_sitter import Language, Parser

        if lang == "python":
            import tree_sitter_python as tsp

            language = Language(tsp.language())
        elif lang == "javascript":
            import tree_sitter_javascript as tsjs

            language = Language(tsjs.language())
        elif lang == "typescript":
            import tree_sitter_typescript as tsts

            language = Language(tsts.language_typescript())
        elif lang == "tsx":
            import tree_sitter_typescript as tsts

            language = Language(tsts.language_tsx())
        else:
            return None
        parser = Parser(language)
        _PARSERS[lang] = parser
        return parser
    except TypeError:
        # Older tree-sitter API: Parser() then set_language
        try:
            from tree_sitter import Language, Parser

            if lang == "python":
                import tree_sitter_python as tsp

                language = Language(tsp.language())
            elif lang == "javascript":
                import tree_sitter_javascript as tsjs

                language = Language(tsjs.language())
            elif lang == "typescript":
                import tree_sitter_typescript as tsts

                language = Language(tsts.language_typescript())
            else:
                return None
            parser = Parser()
            parser.set_language(language)
            _PARSERS[lang] = parser
            return parser
        except Exception:
            return None
    except Exception:
        return None


def _node_text(source: bytes, node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _child_by_field(node, name: str):
    try:
        return node.child_by_field_name(name)
    except Exception:
        return None


def profile_with_treesitter(
    text: str, language: str
) -> Optional[Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]]:
    """Return (sections, symbols, deps) or None if tree-sitter unavailable/fails."""
    lang = (language or "").lower()
    if lang in ("js", "jsx"):
        lang = "javascript"
    if lang == "ts":
        lang = "typescript"
    parser = _parser_for(lang if lang != "tsx" else "tsx")
    if parser is None and lang == "typescript":
        parser = _parser_for("javascript")  # soft fallback
    if parser is None:
        return None

    source = text.encode("utf-8")
    try:
        tree = parser.parse(source)
    except Exception:
        return None
    root = tree.root_node
    symbols: List[Dict[str, Any]] = []
    deps: List[str] = []

    def add_sym(name: str, kind: str, node) -> None:
        if not name:
            return
        symbols.append(
            {
                "name": name,
                "kind": kind,
                "line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "engine": "tree-sitter",
            }
        )

    def walk(node) -> None:
        t = node.type
        if lang == "python":
            if t in ("function_definition", "async_function_definition", "class_definition"):
                name_node = _child_by_field(node, "name")
                if name_node:
                    kind = "class" if t == "class_definition" else "function"
                    add_sym(_node_text(source, name_node), kind, node)
            if t == "import_statement":
                for ch in node.children:
                    if ch.type in ("dotted_name", "aliased_import", "relative_import", "name"):
                        deps.append(_node_text(source, ch).split(" as ")[0].strip())
            if t == "import_from_statement":
                mod = _child_by_field(node, "module_name")
                if mod:
                    deps.append(_node_text(source, mod))
        elif lang in ("javascript", "typescript", "tsx"):
            if t in (
                "function_declaration",
                "generator_function_declaration",
                "class_declaration",
                "method_definition",
            ):
                name_node = _child_by_field(node, "name")
                if name_node:
                    kind = "class" if "class" in t else "function"
                    add_sym(_node_text(source, name_node), kind, node)
            if t == "lexical_declaration":
                # const foo = () => {}
                for ch in node.children:
                    if ch.type == "variable_declarator":
                        name_node = _child_by_field(ch, "name")
                        val = _child_by_field(ch, "value")
                        if name_node and val is not None and val.type in (
                            "arrow_function",
                            "function",
                            "function_expression",
                        ):
                            add_sym(_node_text(source, name_node), "function", ch)
            if t == "import_statement":
                # grab string source
                for ch in node.children:
                    if ch.type == "string":
                        deps.append(_node_text(source, ch).strip("'\""))
            if t == "call_expression":
                # require('x')
                fn = _child_by_field(node, "function")
                if fn and _node_text(source, fn) == "require":
                    args = _child_by_field(node, "arguments")
                    if args and args.child_count:
                        for ch in args.children:
                            if ch.type == "string":
                                deps.append(_node_text(source, ch).strip("'\""))
        for ch in node.children:
            walk(ch)

    walk(root)

    # de-dupe symbols by name+line
    seen = set()
    uniq = []
    for s in symbols:
        key = (s["name"], s["line"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(s)
    symbols = uniq[:200]

    sections = [
        {
            "name": s["name"],
            "kind": s["kind"],
            "start": s["line"],
            "end": s["end_line"],
            "engine": "tree-sitter",
        }
        for s in symbols
        if s.get("kind") in ("class", "function")
    ][:40]
    if not sections and symbols:
        sections = [
            {
                "name": s["name"],
                "kind": s["kind"],
                "start": s["line"],
                "end": s["end_line"],
                "engine": "tree-sitter",
            }
            for s in symbols[:20]
        ]
    if not sections:
        nlines = text.count("\n") + (1 if text else 0)
        sections = [{"name": "body", "kind": "file", "start": 1, "end": max(1, nlines), "engine": "tree-sitter"}]

    dep_clean = sorted({d for d in deps if d and not d.startswith(".") or d.startswith(".")})[:80]
    # keep relative and absolute deps
    dep_clean = sorted({d.strip() for d in deps if d})[:80]
    return sections, symbols, dep_clean
