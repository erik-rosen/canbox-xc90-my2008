"""Byte-level spec of every FYT canbus decoder (com.syu.ms, classes extending j0.ft).

For each decoder: every `kt.w0(code, value)` (and the rarer A0/v0/x0/z0 writers) with the
conditions it sits under (frame command byte, sub-id, other byte tests) and the value expression,
rewritten in frame terms: B[0] is the command byte the decoder switches on (bArr[i2]), B[1] the
length, B[2]... the data. Frames go to V2(byte[] bArr, int i2, int i3); helper methods called with
bArr (and an offset) inherit the call site's conditions.

This is a text-level reading of jadx output, not a full Java parser, so each write carries a
'confidence': 'ok' when every byte reference in it resolved to a frame offset, else 'partial'.
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
MS = os.path.join(ROOT, "../dudu/ms-src/sources")
WRITERS = r"kt\.(w0|A0|v0|x0|z0)"


def methods(src):
    """name -> (params, body lines) for every method in the top-level class (inner classes skipped)."""
    out = {}
    lines = src.splitlines()
    i = 0
    depth = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"\s{4}(?:public |private |protected )?(?:static )?(?:final )?(?:synchronized )?[\w\[\]<>.]+ (\w+)\(([^)]*)\)(?: throws [\w., ]+)? \{\s*$", line)
        if m and depth == 1:
            name, params = m.group(1), m.group(2)
            body, d = [], 1
            i += 1
            while i < len(lines) and d > 0:
                d += lines[i].count("{") - lines[i].count("}")
                if d > 0:
                    body.append(lines[i])
                i += 1
            out.setdefault(name, []).append((params, body))
            continue
        depth += line.count("{") - line.count("}")
        i += 1
    return out


class Ctx:
    def __init__(self, arr, off):
        self.arr, self.off = arr, off              # frame array and base-offset parameter names
        self.byte = {}                             # local -> frame index (value of bArr[off + k])
        self.idx = {}                              # local -> k (index variable = off + k)
        self.alias = {}                            # local -> expression text (in B[] terms)

    def frame_ref(self, text):
        """Rewrite bArr[i2 + k], bArr[iN], bArr[i2] and known locals into B[k]; count unresolved."""
        unresolved = 0
        def arr_sub(m):
            nonlocal unresolved
            inner = m.group(1).strip()
            if inner == self.off:
                return "B[0]"
            mm = re.fullmatch(re.escape(self.off) + r"\s*\+\s*(\d+)", inner)
            if mm:
                return f"B[{mm.group(1)}]"
            if inner in self.idx:
                return f"B[{self.idx[inner]}]"
            mm = re.fullmatch(r"(\w+)\s*\+\s*(\d+)", inner)
            if mm and mm.group(1) in self.idx:
                return f"B[{self.idx[mm.group(1)] + int(mm.group(2))}]"
            unresolved += 1
            return f"B[?{inner}]"
        t = re.sub(re.escape(self.arr) + r"\[([^\]]+)\]", arr_sub, text)
        def var_sub(m):
            v = m.group(0)
            if v in self.byte:
                return self.byte[v]
            if v in self.alias:
                return f"({self.alias[v]})"
            return v
        t = re.sub(r"\b[bi]\d+\b", var_sub, t)
        return t, unresolved


def analyse_method(body, arr, off, ctx, inherited, calls_out, writes_out, cls):
    """Walk one method body, tracking if/switch conditions by brace depth."""
    stack = []                                     # (depth, condition text)
    depth = 0
    switch_var = {}
    for raw in body:
        line = raw.strip()
        # local definitions
        m = re.match(r"(?:final )?(?:byte|int|short|char|long) (\w+) = (.+);$", line)
        if m:
            var, expr = m.group(1), m.group(2)
            mm = re.fullmatch(re.escape(off) + r"\s*\+\s*(\d+)", expr)
            if mm:
                ctx.idx[var] = int(mm.group(1))
            else:
                t, _ = ctx.frame_ref(expr)
                if "B[" in t:
                    ctx.byte[var] = t if re.fullmatch(r"B\[\d+\]", t) else f"({t})"
        # conditions
        closes = line.count("}") if line.startswith("}") else 0
        for _ in range(closes):
            depth -= 1
            while stack and stack[-1][0] > depth:
                stack.pop()
        m = re.match(r"(?:\}\s*else\s+)?if \((.+)\) \{$", line)
        if m:
            cond, _ = ctx.frame_ref(m.group(1))
            if line.startswith("}"):
                stack.append((depth + 1, f"else-if {cond}"))
            else:
                stack.append((depth + 1, cond))
        elif re.match(r"\}?\s*else \{$", line):
            stack.append((depth + 1, "else"))
        m = re.match(r"switch \((.+)\) \{$", line)
        if m:
            sw, _ = ctx.frame_ref(m.group(1))
            switch_var[depth + 1] = sw
        m = re.match(r"case (-?\d+):$", line)
        if m:
            sv = switch_var.get(depth, "switch")
            # replace a previous case at this depth
            # a case stays in force until the next case at this depth, or the switch closes
            if stack and stack[-1][0] == depth and stack[-1][1].startswith("case:"):
                stack.pop()
            stack.append((depth, f"case:{sv} == {m.group(1)}"))
        depth += line.count("{") - (line.count("}") - closes)
        conds = inherited + [c[5:] if c.startswith("case:") else c for _, c in stack]
        # writes
        for wm in re.finditer(WRITERS + r"\((\d+),\s*(.+?)\);", line):
            writer, code, val = wm.group(1), int(wm.group(2)), wm.group(3)
            v, unresolved = ctx.frame_ref(val)
            writes_out.append({"code": code, "writer": writer, "value": v, "when": conds,
                               "confidence": "ok" if unresolved == 0 else "partial"})
        # helper calls that pass the frame on
        for cm in re.finditer(r"\b(?:this\.)?(\w+)\(" + re.escape(arr) + r"(?:,\s*([^,)]+))?", line):
            name, second = cm.group(1), cm.group(2)
            base = 0
            if second:
                s = second.strip()
                mm = re.fullmatch(re.escape(off) + r"\s*\+\s*(\d+)", s)
                if mm:
                    base = int(mm.group(1))
                elif s in ctx.idx:
                    base = ctx.idx[s]
                elif s == off:
                    base = 0
                else:
                    base = None
            calls_out.append((name, base, list(conds)))


def analyse_class(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    ms = methods(src)
    if "V2" not in ms:
        return None
    writes, seen = [], set()
    queue = []
    for params, body in ms["V2"]:
        p = [x.split()[-1] for x in params.split(",")]
        if len(p) >= 2 and "byte[]" in params:
            queue.append(("V2", params, body, p[0], p[1], 0, []))
    while queue:
        name, params, body, arr, off, base, inherited = queue.pop()
        key = (name, base, tuple(inherited))
        if key in seen or len(seen) > 400:
            continue
        seen.add(key)
        ctx = Ctx(arr, off)
        calls = []
        local = []
        analyse_method(body, arr, off, ctx, inherited, calls, local, path)
        for w in local:
            if base:
                w["value"] = re.sub(r"B\[(\d+)\]", lambda m: f"B[{int(m.group(1)) + base}]", w["value"])
                w["when"] = [re.sub(r"B\[(\d+)\]", lambda m: f"B[{int(m.group(1)) + base}]", c) for c in w["when"]]
            if base is None:
                w["confidence"] = "partial"
            writes.append(w)
        for cname, cbase, cconds in calls:
            if cname in ms and cname != name:
                for p2, b2 in ms[cname]:
                    ps = [x.split()[-1] for x in p2.split(",") if x.strip()]
                    if not ps or "byte[]" not in p2:
                        continue
                    arr2 = ps[0]
                    off2 = ps[1] if len(ps) > 1 else "__no_offset__"
                    nb = None if cbase is None or base is None else base + cbase
                    queue.append((cname, p2, b2, arr2, off2, nb, cconds))
    return writes


def frame_of(w):
    """(command, sub) from a write's conditions, when it has them."""
    cmd = sub = None
    pos = None
    for c in w["when"]:
        c2 = re.sub(r"[()]", "", c.replace("else-if ", "")).replace(" & 255", "")
        if "||" in c2 or "!=" in c2:
            continue
        for m in re.finditer(r"B\[(\d+)\] == (-?\d+)", c2):
            k, v = int(m.group(1)), int(m.group(2)) & 0xFF
            if cmd is None and k in (0, 1):
                cmd, pos = v, k
            elif cmd is not None and sub is None and k == pos + 2:
                sub = v
    return cmd, sub, pos


def main():
    resolved = [l.rstrip("\n").split("\t") for l in open(os.path.join(ROOT, "resolved-ms.tsv"))]
    classes = sorted({c for _, c in resolved})
    spec = {}
    for c in classes:
        path = os.path.join(MS, c + ".java")
        if not os.path.exists(path):
            spec[c] = {"error": "no source"}
            continue
        w = analyse_class(path)
        if w is None:
            spec[c] = {"error": "no V2"}
            continue
        for x in w:
            x["frame"] = frame_of(x)
        spec[c] = {"writes": w}
    json.dump(spec, open(os.path.join(ROOT, "spec-ms.json"), "w"), indent=0)
    n = sum(len(v.get("writes", [])) for v in spec.values())
    ok = sum(1 for v in spec.values() for x in v.get("writes", []) if x["confidence"] == "ok")
    framed = sum(1 for v in spec.values() for x in v.get("writes", []) if x["frame"][0] is not None)
    print(f"{len(classes)} decoders, {n} writes, {ok} fully resolved, {framed} with a command byte;"
          f" errors: {collections.Counter(v.get('error') for v in spec.values() if 'error' in v)}")


if __name__ == "__main__":
    main()
