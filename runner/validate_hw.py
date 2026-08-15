#!/usr/bin/env python3
"""Grade a hardware+software project answer (hw_projects category).

Usage:
  python3 runner/validate_hw.py <item-id> <answer-file>

The answer must contain fenced artifacts as specified by the prompt:
JSON blocks tagged with an "artifact" key ("bom"/"wiring" or
"parts"/"storage_plan"), a python code block, and a markdown instructions
block. Prints a per-check breakdown and `HW_SCORE: <points>/10`.
Stdlib-only. Importable: score_answer(item_id, answer) -> (points, notes).
"""
import json
import os
import re
import subprocess
import sys
import tempfile

MAX_POINTS = 10


def extract_blocks(answer):
    blocks = re.findall(r"```([^\n`]*)\n(.*?)```", answer, re.S)
    out = {"json": {}, "python": None, "markdown": None}
    for lang, body in blocks:
        lang = lang.strip().lower()
        if lang in ("json", "") :
            try:
                obj = json.loads(body)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(obj, dict) and "artifact" in obj:
                out["json"][obj["artifact"]] = obj
        elif lang in ("python", "py"):
            out["python"] = body
        elif lang in ("markdown", "md"):
            out["markdown"] = body
    return out


def _norm(s):
    return re.sub(r"[^a-z0-9.+-]+", "", str(s).lower())


def check_bom(bom, required_categories):
    """1 pt for a well-formed BOM, 1 pt for covering all required categories."""
    notes, pts = [], 0.0
    comps = (bom or {}).get("components")
    if isinstance(comps, list) and comps and all(
            isinstance(c, dict) and c.get("ref") and c.get("part") and c.get("category")
            for c in comps):
        pts += 1
        cats = {_norm(c["category"]) for c in comps}
        missing = [c for c in required_categories if _norm(c) not in cats]
        if not missing:
            pts += 1
        else:
            notes.append(f"BOM missing categories: {missing}")
    else:
        notes.append("BOM absent or malformed (need components[] with ref/part/category)")
    return pts, notes


def _ref_cats(bom):
    m = {}
    for c in (bom or {}).get("components", []) or []:
        if isinstance(c, dict) and c.get("ref"):
            m[_norm(c["ref"])] = _norm(c.get("category", ""))
    return m


def check_wiring(wiring, bom, rules, forbidden=()):
    """Each rule = (description, cat_a, pin_regex_a, cat_b, pin_regex_b).
    Points scaled to 3 by fraction of rules satisfied; forbidden rules subtract."""
    notes = []
    conns = (wiring or {}).get("connections")
    if not isinstance(conns, list) or not conns:
        return 0.0, ["wiring netlist absent or malformed"]
    refcat = _ref_cats(bom)
    edges = []
    for c in conns:
        if not isinstance(c, dict):
            continue
        a, b = str(c.get("from", "")), str(c.get("to", ""))
        for x, y in ((a, b), (b, a)):
            ref, _, pin = x.partition(".")
            r2, _, p2 = y.partition(".")
            edges.append((refcat.get(_norm(ref), _norm(ref)), _norm(pin),
                          refcat.get(_norm(r2), _norm(r2)), _norm(p2)))

    def satisfied(cat_a, pat_a, cat_b, pat_b):
        for ca, pa, cb, pb in edges:
            if ca == cat_a and re.search(pat_a, pa) and cb == cat_b and re.search(pat_b, pb):
                return True
        return False

    hit = 0
    for desc, ca, pa, cb, pb in rules:
        if satisfied(ca, pa, cb, pb):
            hit += 1
        else:
            notes.append(f"wiring rule not satisfied: {desc}")
    pts = 3.0 * hit / len(rules)
    for desc, ca, pa, cb, pb in forbidden:
        if satisfied(ca, pa, cb, pb):
            pts = max(0.0, pts - 1.0)
            notes.append(f"forbidden connection present: {desc}")
    return round(pts, 2), notes


def run_code(code, harness):
    """3 pts scaled by passing asserts. Harness = list of (expr, expected)."""
    if not code:
        return 0.0, ["python code block absent"]
    lines = [
        "import json, sys",
        code,
        "passed = 0",
        "total = 0",
        "results = []",
    ]
    for expr, expected in harness:
        lines += [
            "total += 1",
            "try:",
            f"    ok = ({expr}) == ({expected!r})",
            "except Exception:",
            "    ok = False",
            "passed += ok",
            f"results.append(({expr!r}, ok))",
        ]
    lines += ["print('HWTEST', json.dumps({'passed': passed, 'total': total, "
              "'failed': [r[0] for r in results if not r[1]]}))"]
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "sol.py")
        with open(path, "w") as f:
            f.write("\n".join(lines))
        try:
            p = subprocess.run([sys.executable, path], capture_output=True,
                               text=True, timeout=20)
        except subprocess.TimeoutExpired:
            return 0.0, ["code timed out"]
    m = re.search(r"HWTEST (\{.*\})", p.stdout)
    if not m:
        return 0.0, [f"code failed to run: {(p.stderr or p.stdout)[-300:]}"]
    r = json.loads(m.group(1))
    notes = [f"code tests failed: {r['failed']}"] if r["failed"] else []
    return round(3.0 * r["passed"] / r["total"], 2), notes


def check_docs(md, required_topics):
    """2 pts scaled by checklist coverage. Each topic = (name, regex)."""
    if not md:
        return 0.0, ["markdown instructions block absent"]
    notes, hit = [], 0
    for name, pat in required_topics:
        if re.search(pat, md, re.I):
            hit += 1
        else:
            notes.append(f"instructions missing topic: {name}")
    return round(2.0 * hit / len(required_topics), 2), notes


# ---------------------------------------------------------------- items

def grade_waterer(blocks):
    total, notes = 0.0, []
    bom = blocks["json"].get("bom")
    p, n = check_bom(bom, ["microcontroller", "sensor", "relay", "pump", "power"])
    total += p; notes += n
    rules = [
        ("sensor analog out -> MCU analog/ADC pin", "sensor", r"aout|a0$|sig|analog|out",
         "microcontroller", r"^a\d|adc|gpio3[2-9]|analog"),
        ("sensor VCC -> MCU 3V3/5V", "sensor", r"vcc|vin|\+|pwr",
         "microcontroller", r"3v3|3\.3|5v|vcc"),
        ("sensor GND -> GND", "sensor", r"gnd|-", "microcontroller", r"gnd"),
        ("relay IN -> MCU GPIO/digital pin", "relay", r"in|sig|s$|ctl|gate",
         "microcontroller", r"gpio|^d\d|dig|io\d|^a?\d+$"),
        ("pump through relay switched contact (COM/NO)", "pump", r".*",
         "relay", r"com|no$|nc$|out|drain"),
        ("pump/relay return to power", "pump", r"-|gnd|neg", "power", r"-|gnd|neg"),
    ]
    forbidden = [
        ("sensor analog out tied to a power rail", "sensor", r"aout|a0$|sig|analog",
         "power", r".*"),
    ]
    p, n = check_wiring(blocks["json"].get("wiring"), bom, rules, forbidden)
    total += p; notes += n
    harness = [
        ("control(25.0, False, 0.0)", True),
        ("control(35.0, True, 10.0)", True),
        ("control(45.0, True, 10.0)", False),
        ("control(35.0, False, 0.0)", False),
        ("control(50.0, False, 0.0)", False),
        ("control(10.0, True, 120.0)", False),
        ("control(10.0, True, 500.0)", False),
        ("control(29.9, False, 0.0)", True),
    ]
    p, n = run_code(blocks["python"], harness)
    total += p; notes += n
    topics = [
        ("parts list", r"part|component|bom|material"),
        ("wiring/assembly", r"wir|connect|assembl"),
        ("flashing firmware", r"flash|upload|sketch|firmware|program"),
        ("calibration", r"calibrat"),
        ("testing", r"test"),
        ("safety", r"safety|caution|warning"),
    ]
    p, n = check_docs(blocks["markdown"], topics)
    total += p; notes += n
    return total, notes


def grade_camera(blocks):
    total, notes = 0.0, []
    bom = blocks["json"].get("bom")
    p, n = check_bom(bom, ["sbc", "camera", "battery", "power", "button", "led", "storage"])
    total += p; notes += n
    rules = [
        ("battery -> power board battery input", "battery", r".*",
         "power", r"bat|in|jst|lipo"),
        ("power board 5V out -> SBC 5V", "power", r"5v|out|\+",
         "sbc", r"5v|vin|pwr"),
        ("power board GND -> SBC GND", "power", r"gnd|-", "sbc", r"gnd"),
        ("camera -> SBC CSI port", "camera", r".*", "sbc", r"csi|cam"),
        ("button -> SBC GPIO", "button", r".*", "sbc", r"gpio|pin\d|bcm"),
        ("button -> GND (pull-up)", "button", r".*", "sbc", r"gnd"),
        ("LED -> SBC GPIO", "led", r".*|anode|\+", "sbc", r"gpio|pin\d|bcm"),
        ("LED through resistor", "led", r".*", "resistor", r".*"),
    ]
    p, n = check_wiring(blocks["json"].get("wiring"), bom, rules)
    total += p; notes += n
    def he(call):  # tolerate tuple-vs-list in the returned pair
        return f"[list(x) if isinstance(x, tuple) else x for x in {call}]"
    harness = [
        (he("handle_event('boot', {'photo_count': 0})"),
         [["led_blink"], {"photo_count": 0}]),
        (he("handle_event('short_press', {'photo_count': 0})"),
         [["capture:photo_1.jpg", "led_flash"], {"photo_count": 1}]),
        (he("handle_event('short_press', {'photo_count': 7})"),
         [["capture:photo_8.jpg", "led_flash"], {"photo_count": 8}]),
        (he("handle_event('long_press', {'photo_count': 3})"),
         [["led_off", "shutdown"], {"photo_count": 3}]),
        (he("handle_event('noise', {'photo_count': 2})"),
         [[], {"photo_count": 2}]),
    ]
    p, n = run_code(blocks["python"], harness)
    total += p; notes += n
    topics = [
        ("parts list", r"part|component|bom|material"),
        ("assembly/wiring", r"assembl|wir|connect|solder"),
        ("OS/software setup", r"os |raspberry pi os|raspbian|software|install|setup|image"),
        ("usage", r"usage|using|take|photo|shutter"),
        ("safe shutdown", r"shut ?down|power off"),
        ("battery safety", r"batter"),
    ]
    p, n = check_docs(blocks["markdown"], topics)
    total += p; notes += n
    return total, notes


def grade_nas(blocks):
    total, notes = 0.0, []
    parts = blocks["json"].get("parts")
    checks = []
    if isinstance(parts, dict):
        g = lambda *ks: _dig(parts, *ks)
        checks = [
            ("cpu.socket == motherboard.socket",
             _norm(g("cpu", "socket")) == _norm(g("motherboard", "socket")) != ""),
            ("ram.type == motherboard.ram_type",
             _norm(g("ram", "type")) == _norm(g("motherboard", "ram_type")) != ""),
            ("mobo form factor fits case",
             _norm(g("motherboard", "form_factor")) in
             [_norm(x) for x in (g("case", "supported_form_factors") or [])]),
            ("case has >= 4 drive bays", _num(g("case", "drive_bays")) >= 4),
            ("data_drives.count >= 4", _num(g("data_drives", "count")) >= 4),
            ("enough SATA ports",
             _num(g("motherboard", "sata_ports")) >= _num(g("data_drives", "count")) +
             (1 if "sata" in _norm(g("boot_drive", "interface")) else 0)),
            ("psu >= 300W", _num(g("psu", "watts")) >= 300),
        ]
        hit = sum(1 for _, ok in checks if ok)
        notes += [f"parts check failed: {d}" for d, ok in checks if not ok]
        total += round(3.0 * hit / len(checks), 2)
    else:
        notes.append("parts artifact absent or malformed")

    plan = blocks["json"].get("storage_plan")
    if isinstance(plan, dict) and isinstance(parts, dict):
        lvl = _norm(plan.get("raid_level"))
        n_d = _num(plan.get("data_drives")) + _num(plan.get("parity_drives"))
        cap = _num(_dig(parts, "data_drives", "capacity_tb"))
        cnt = _num(_dig(parts, "data_drives", "count"))
        parity = {"raid5": 1, "raidz1": 1, "raid6": 2, "raidz2": 2}.get(lvl)
        if lvl == "raid10":
            expect = cnt / 2 * cap
            parity_ok = True
        elif parity is not None:
            expect = (cnt - parity) * cap
            parity_ok = _num(plan.get("parity_drives")) == parity
        else:
            expect, parity_ok = None, False
        pts = 0.0
        if expect is not None and parity_ok and n_d == cnt:
            pts += 1.0
        else:
            notes.append("storage plan raid level/parity/drive count inconsistent")
        if expect is not None and abs(_num(plan.get("usable_capacity_tb")) - expect) <= 0.01 * max(expect, 1):
            pts += 1.0
        else:
            notes.append(f"usable_capacity_tb wrong (expected {expect})")
        total += pts
    else:
        notes.append("storage_plan artifact absent or malformed")

    harness = [
        ("round(usable_capacity_tb(4, 4, 'raid5'), 6)", 12.0),
        ("round(usable_capacity_tb(4, 4, 'raidz1'), 6)", 12.0),
        ("round(usable_capacity_tb(8, 6, 'raid6'), 6)", 32.0),
        ("round(usable_capacity_tb(8, 6, 'raidz2'), 6)", 32.0),
        ("round(usable_capacity_tb(2, 4, 'raid10'), 6)", 4.0),
        ("round(usable_capacity_tb(3, 5, 'raid0'), 6)", 15.0),
        ("round(usable_capacity_tb(10, 2, 'raid1'), 6)", 10.0),
    ]
    p, n = run_code(blocks["python"], harness)
    total += p; notes += n
    topics = [
        ("parts list", r"part|component|bom"),
        ("assembly", r"assembl|build|install the|mount"),
        ("OS installation", r"truenas|openmediavault|unraid|omv|debian|os install|operating system"),
        ("RAID/pool setup", r"raid|pool|zfs|array|share"),
        ("backup strategy", r"backup|3-2-1|replication"),
        ("testing / failure simulation", r"test|scrub|smart|failure"),
        ("ESD safety", r"esd|static|ground(ing)? strap|anti-static"),
    ]
    p, n = check_docs(blocks["markdown"], topics)
    total += p; notes += n
    return total, notes


def _dig(d, *keys):
    for k in keys:
        d = d.get(k) if isinstance(d, dict) else None
    return d


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return -1.0


GRADERS = {
    "hw-01-garden-waterer": grade_waterer,
    "hw-02-portable-camera": grade_camera,
    "hw-03-nas-build": grade_nas,
}


def score_answer(item_id, answer):
    blocks = extract_blocks(answer)
    points, notes = GRADERS[item_id](blocks)
    return min(round(points, 2), MAX_POINTS), notes


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in GRADERS:
        print(f"usage: validate_hw.py <{'|'.join(GRADERS)}> <answer-file>")
        sys.exit(2)
    with open(sys.argv[2]) as f:
        answer = f.read()
    points, notes = score_answer(sys.argv[1], answer)
    for note in notes:
        print(f"[-] {note}")
    print(f"HW_SCORE: {points}/{MAX_POINTS}")


if __name__ == "__main__":
    main()
