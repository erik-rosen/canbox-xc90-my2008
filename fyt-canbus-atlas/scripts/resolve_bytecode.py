"""Exact profile -> parser mapping: interpret HandlerCanbus.getCallbackCanbusById(int) bytecode.

jadx mangles this method from case 452 on (switch fall-through), so instead of trusting the Java,
step through the Dalvik instructions for each id. The method only shifts/masks the id, switches
on it, compares registers with constants and returns `new Callback_X()`. Anything else is an
error, so a wrong mapping can't pass silently.
"""
import sys
import sqlite3
from androguard.misc import AnalyzeAPK
from androguard.core.dex import DEX

APK = sys.argv[1] if len(sys.argv) > 1 else "canbus.apk"
CLS = sys.argv[2] if len(sys.argv) > 2 else "Lcom/syu/module/canbus/HandlerCanbus;"
METH = sys.argv[3] if len(sys.argv) > 3 else "getCallbackCanbusById"
OUT = sys.argv[4] if len(sys.argv) > 4 else "resolved-bytecode.tsv"


def load_method():
    from androguard.core.apk import APK as A
    a = A(APK)
    for dexbytes in a.get_all_dex():
        d = DEX(dexbytes)
        for c in d.get_classes():
            if c.get_name() == CLS:
                for m in c.get_methods():
                    if m.get_name() == METH and "(I)" in m.get_descriptor():
                        return m
    raise SystemExit("method not found")


def build(m):
    code = m.get_code()
    ins = []
    off = 0
    for i in code.get_bc().get_instructions():
        ins.append((off, i))
        off += i.get_length()
    by_off = {o: k for k, (o, _) in enumerate(ins)}
    payload = {o: i for o, i in ins}
    return ins, by_off, payload, code.get_registers_size(), code.get_ins_size()


def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def run(prog, ident):
    ins, by_off, payload, nregs, nins = prog
    r = [0] * nregs
    r[nregs - nins] = ident                      # static method: the only argument is in the last register
    k = 0
    pending_new = None
    for _ in range(100000):
        off, i = ins[k]
        name = i.get_name()
        ops = i.get_operands()
        nxt = k + 1
        def reg(n): return r[ops[n][1]]
        def lit(n): return ops[n][1]
        if name in ("move", "move/from16", "move/16"):
            r[ops[0][1]] = reg(1)
        elif name.startswith("const-string") or name.startswith("const-class"):
            r[ops[0][1]] = ("str", None)          # only used for the log line
        elif name.startswith("const"):
            v = lit(1)
            if name == "const/high16":
                v = v << 16 if abs(v) < 0x10000 else v
            r[ops[0][1]] = s32(v)
        elif name in ("and-int/lit16", "and-int/lit8"):
            r[ops[0][1]] = s32(reg(1) & lit(2))
        elif name in ("shr-int/lit8", "ushr-int/lit8"):
            v = reg(1) & 0xFFFFFFFF if name.startswith("u") else reg(1)
            r[ops[0][1]] = s32(v >> lit(2))
        elif name == "and-int/2addr":
            r[ops[0][1]] = s32(reg(0) & reg(1))
        elif name == "and-int":
            r[ops[0][1]] = s32(reg(1) & reg(2))
        elif name in ("sput", "sput-object", "sget", "sget-object"):
            pass                                  # DataCanbus.sCanbusId / carId bookkeeping
        elif name in ("packed-switch", "sparse-switch"):
            target = off + ops[1][1] * 2
            p = payload[target]
            v = reg(0)
            jump = None
            if name == "packed-switch":
                first = p.get_keys()[0] if hasattr(p, "get_keys") else p.first_key
                targets = p.get_targets()
                idx = v - first
                if 0 <= idx < len(targets):
                    jump = off + targets[idx] * 2
            else:
                for key, t in zip(p.get_keys(), p.get_targets()):
                    if key == v:
                        jump = off + t * 2
            if jump is not None:
                nxt = by_off[jump]
        elif name.startswith("if-"):
            cond = name[3:]
            if cond.endswith("z"):
                a, b, t = reg(0), 0, ops[1][1]
                cond = cond[:-1]
            else:
                a, b, t = reg(0), reg(1), ops[2][1]
            ok = {"eq": a == b, "ne": a != b, "lt": a < b, "ge": a >= b, "gt": a > b, "le": a <= b}[cond]
            if ok:
                nxt = by_off[off + t * 2]
        elif name.startswith("goto"):
            nxt = by_off[off + ops[0][1] * 2]
        elif name == "new-instance":
            pending_new = ops[1][2] if len(ops[1]) > 2 else str(ops[1])
            r[ops[0][1]] = ("obj", pending_new) if "StringBuilder" not in pending_new else ("str", None)
        elif name.startswith("invoke-"):
            pass                                  # constructors, StringBuilder and Log.e for the log line
        elif name.startswith("move-result"):
            r[ops[0][1]] = ("str", None)
        elif name == "return-object":
            v = reg(0)
            if isinstance(v, tuple) and v[0] == "obj":
                return v[1]
            return "null" if v == 0 else f"?{v}"
        elif name == "nop":
            pass
        else:
            raise RuntimeError(f"unhandled {name} at {off:#x}")
        k = nxt
    raise RuntimeError("no return")


def main():
    m = load_method()
    prog = build(m)
    ids = [r[0] for r in sqlite3.connect("pu/assets/canbus.db").execute(
        "select distinct id_value from canbus_canbox where id_value > 0")]
    with open(OUT, "w") as f:
        for i in ids:
            try:
                cls = run(prog, i)
            except Exception as ex:
                cls = f"ERROR {ex}"
            cls = cls.lstrip("L").rstrip(";")
            f.write(f"{i}\t{cls}\n")
    print("done", len(ids))


if __name__ == "__main__":
    main()
