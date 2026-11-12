r"""Inside inline code spans, "\|" renders literally (a visible backslash), while a plain "|" inside
backticks already stays in its table cell with Python-Markdown. Replace "\|" by "|" in code spans
(fenced blocks untouched). Usage: python3 research/fix_code_pipes.py FILE..."""
import re, sys
CODE = re.compile(r"(`+)(.+?)\1")
for path in sys.argv[1:]:
    out, fence, n = [], False, 0
    for line in open(path, encoding="utf-8").read().split("\n"):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
        elif not fence and "\\|" in line:
            def fix(m):
                global n
                n += m.group(2).count("\\|")
                return m.group(1) + m.group(2).replace("\\|", "|") + m.group(1)
            line = CODE.sub(fix, line)
        out.append(line)
    open(path, "w", encoding="utf-8").write("\n".join(out))
    print(f"{path}: {n} fixed")
