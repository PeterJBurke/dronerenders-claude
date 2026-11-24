#!/usr/bin/env python3
"""Rebuild fc/assets/pin-data.js from the StackF765 design generators.

Reads the pin tables straight out of the design sources (no pin names are typed in here):
  gen/upper.py  J1_ROWS (3x12 header), SVC (service cable)
  gen/lower.py  J2_ROWS / J2_LABELS (3x9 solder holes), B2B_COLS (board-to-board), PAD_X (power pads)

Usage: tools/make-pin-data.py [/path/to/stackf765-checkout]   (default /root/fcclaude)
"""
import ast, hashlib, json, pathlib, sys

src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/root/fcclaude")
out = pathlib.Path(__file__).resolve().parent.parent / "fc/assets/pin-data.js"


def literals(path, names):
    found = {}
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in names:
            # constant expressions only (lists are built with * and + in the source); no names, no builtins
            found[node.targets[0].id] = eval(compile(ast.Expression(node.value), str(path), "eval"), {"__builtins__": {}})
    missing = set(names) - set(found)
    if missing:
        raise SystemExit(f"{path}: missing {sorted(missing)}")
    return found


up = literals(src / "gen/upper.py", ["J1_ROWS", "SVC"])
lo = literals(src / "gen/lower.py", ["J2_ROWS", "J2_LABELS", "B2B_COLS", "PAD_X"])

UARTS = [1, 2, 3, 4, 6, 7, 8]          # ArduPilot SERIAL1-7, from docs/pinout.md


def describe(net):
    if net == "GND": return "Ground / common return"
    if net == "+5V": return "5 V from the battery regulator (off on USB power)"
    if net == "+5V_SYS": return "5 V that is also live on USB power"
    if net == "+5V_PI": return "Separate 5 V / 3 A regulator for a companion computer"
    if net == "+3V3": return "3.3 V rail"
    if net[:2] in ("TX", "RX") and net[2:].isdigit():
        n = int(net[2:])
        return f"UART {n} {'transmit' if net[:2] == 'TX' else 'receive'}, 3.3 V logic (ArduPilot SERIAL{UARTS.index(n) + 1})"
    if net[0] == "M" and net[1:].isdigit(): return f"Motor or servo output {net[1:]} (PWM, OneShot, DShot)"
    return {
        "SDA": "I2C data for an external compass etc. (3.3 V, 2.2 k pull-up fitted)",
        "SCL": "I2C clock for an external compass etc. (3.3 V, 2.2 k pull-up fitted)",
        "CAM_IN": "Analog video in from the camera",
        "VTX_OUT": "Analog video out to the transmitter, with OSD",
        "LED_STRIP": "Addressable LED data (ArduPilot output 7)",
        "VBAT_SENSE": "Battery voltage divider output to the flight controller",
        "CURR_SENSE": "Current-sense amplifier output to the flight controller",
        "VBUS": "USB 5 V from the service board",
        "USB_DM": "USB D-",
        "USB_DP": "USB D+",
        "BUZ_OUT": "Buzzer drive (5 V pulses)",
        "BOOT0": "Boot button (bootloader select)",
    }[net]


def sig(label, net):
    return label if label.replace("G", "GND") == net or label == net.lstrip("+") else f"{label} · {net}"


groups = []
ROWNOTE = {"A": "inner, highest pins", "B": "middle", "C": "front edge, lowest pins"}
rows = []
for row in "CBA":
    for i, (label, net) in enumerate(up["J1_ROWS"][row]):
        rows.append({"pin": f"{row}{i + 1}", "net": sig(label, net), "function": describe(net)})
groups.append({"board": "UpperLogic", "ref": "J1", "title": "Upper · J1 · 3×12 header",
               "note": "Right-angle 0.1 inch header; all contacts face the front edge. Seen from above with the header "
                       "pointing away from you, column 1 is on the left. Row A: " + ROWNOTE["A"] + ". Row B: " + ROWNOTE["B"] +
                       ". Row C: " + ROWNOTE["C"] + ". Pins marked 5V are powered only from the battery; pins marked 4V5 "
                       "are also powered from USB.", "rows": rows})
rows = []
for row in "ABC":
    for i, (label, net) in enumerate(lo["J2_ROWS"][row]):
        fn = "Flight-controller 5 V rail" if net == "+5V" else describe(net)
        rows.append({"pin": f"{row}{i + 1}", "net": sig(label, net), "function": fn})
ncol = len(lo["J2_LABELS"])
groups.append({"board": "LowerPower", "ref": "J2", "title": f"Lower · J2 · 3×{ncol} solder holes",
               "note": "Solder holes on the 0.1 inch grid; no header is fitted, so nothing tall sits under the Upper "
                       "board's header pins. Solder one 3-wire servo / ESC lead per column: signal / 5 V / ground from "
                       "the inner hole to the board edge. Seen from above with the front edge away from you, column 1 is "
                       "on the left. Row A (inner, signal): " + " ".join(lo["J2_LABELS"]) + ". Row B (middle): 5 V, "
                       "or PI5V in the two PI5V columns. Row C (nearest the edge): all GND.", "rows": rows})
pads = sorted(lo["PAD_X"], key=lambda k: lo["PAD_X"][k])
PADFN = {"BAT+": "Battery positive", "BAT-": "Battery negative", "ESC+": "ESC positive", "ESC-": "ESC negative"}
groups.append({"board": "LowerPower", "ref": "POWER", "title": "Lower · Power solder pads",
               "note": "Rear edge, seen from above: " + "  ".join(pads) + ". 2S–3S LiPo, 50 A continuous.",
               "rows": [{"pin": p, "net": p, "function": PADFN[p]} for p in pads]})
SVCLABEL = {"USB_DM": "D-", "USB_DP": "D+", "BUZ_OUT": "BUZ", "BOOT0": "BOOT"}
groups.append({"board": "UpperLogic", "ref": "J5", "title": "Service cable · Upper J5 ↔ Service J2",
               "note": "JST-SH 1.0 mm, six pins, 100 mm cable wired pin 1 to pin 1. Same pin order on both ends. The order is "
                       "reversal-safe: a cable wired 6-to-1 by mistake does no damage.",
               "rows": [{"pin": str(p), "net": sig(SVCLABEL.get(n, n), n), "function": describe(n)} for p, n in sorted(up["SVC"].items())]})
rows = []
for c, (top, bottom) in enumerate(lo["B2B_COLS"]):
    rows.append({"pin": str(2 * c + 1), "net": top, "function": describe(top)})
    rows.append({"pin": str(2 * c + 2), "net": bottom, "function": describe(bottom)})
groups.append({"board": "UpperLogic", "ref": "J3", "title": "Between boards · Upper J3 ↔ Lower J1",
               "note": "20 contacts, 2×10 at 1.27 mm pitch: Samtec FTSH-110-04-L-DV header on the Upper board mates with SFMC-110-02-L-D socket on the Lower; same-number contacts mate. Not an external connector.", "rows": rows})

data = {
    "metadata": {
        "board": "StackF765", "revision": "B", "processor": "STM32F765VIT6", "ardupilot_board_name": "StackF765",
        "status": "Design verified by rule checks; no hardware built yet.",
        "sources": {f"gen/{n}.py": hashlib.sha256((src / f"gen/{n}.py").read_bytes()).hexdigest() for n in ("upper", "lower")},
        "repository": "https://github.com/PeterJBurke/stackf765",
        "group_count": len(groups), "row_count": sum(len(g["rows"]) for g in groups),
    },
    "intro": "Seven UARTs (1, 2, 3, 4, 6, 7, 8). TX and RX are named from the flight controller’s side. Match the "
             "silkscreen labels; screen direction changes when the board is rotated.",
    "scope": "Includes the external headers, power pads, service cable and interboard contacts. Service board is separate "
             "from the main stack. Power ratings and assembly fit are design values: design verified by rule checks; no hardware built yet.",
    "groups": groups,
}
out.write_text("window.FC_PIN_DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
print(out, data["metadata"]["group_count"], "groups", data["metadata"]["row_count"], "rows")
