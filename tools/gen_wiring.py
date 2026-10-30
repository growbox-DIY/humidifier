# gen_wiring.py - draws docs/wiring.png (run on a computer, needs Pillow):
#   python3 tools/gen_wiring.py
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "wiring.png")
FONT = "/System/Library/Fonts/SFNS.ttf"

W, H = 1800, 1130
K = 2  # drawn at 2x, scaled down for smooth lines

BG = "#011515"
CARD = "#041C1B"
EDGE = "#123333"
TEXT = "#F2F5F4"
DIM = "#8FA3A0"
GREEN = "#00E95A"
CYAN = "#20DCE8"
BLUE = "#78BFFF"
YELLOW = "#FFD21C"
RED = "#FF6070"
GREY = "#7A8C8A"

img = Image.new("RGB", (W * K, H * K), BG)
d = ImageDraw.Draw(img)
_fonts = {}


def font(size, weight="Regular"):
    key = (size, weight)

    if key not in _fonts:
        f = ImageFont.truetype(FONT, size * K)
        f.set_variation_by_name(weight)
        _fonts[key] = f

    return _fonts[key]


def s(*v):
    return [x * K for x in v]


def text(x, y, t, size=20, weight="Regular", fill=TEXT, anchor="la"):
    d.text(s(x, y), t, font=font(size, weight), fill=fill, anchor=anchor)


def card(x0, y0, x1, y1, title, sub=None, right=False, accent=EDGE):
    d.rounded_rectangle(s(x0, y0, x1, y1), radius=22 * K, fill=CARD, outline=accent, width=2 * K)
    tx, anchor = (x1 - 22, "ra") if right else (x0 + 22, "la")
    text(tx, y0 + 20, title, 25, "Bold", anchor=anchor)

    if sub:
        text(tx, y0 + 54, sub, 15, fill=DIM, anchor=anchor)


def wire(points, color, width=4):
    d.line([c * K for p in points for c in p], fill=color, width=width * K, joint="curve")


def pin(x, y, color):
    r = 8
    d.ellipse(s(x - r, y - r, x + r, y + r), fill=CARD, outline=color, width=3 * K)


def dot(x, y, color):
    r = 7
    d.ellipse(s(x - r, y - r, x + r, y + r), fill=color)


def badge(x, y, label, color):
    w = font(15, "Semibold").getlength(label) / K + 20
    d.rounded_rectangle(s(x, y, x + w, y + 26), radius=13 * K, outline=color, width=2 * K)
    text(x + w / 2, y + 13, label, 15, "Semibold", color, anchor="mm")
    return w


def resistor(cx, cy, label, vertical=False):
    if vertical:
        box = (cx - 11, cy - 32, cx + 11, cy + 32)
        text(cx + 20, cy, label, 16, "Semibold", TEXT, anchor="lm")
    else:
        box = (cx - 32, cy - 11, cx + 32, cy + 11)
        text(cx, cy - 22, label, 16, "Semibold", TEXT, anchor="md")

    d.rounded_rectangle(s(*box), radius=5 * K, fill=CARD, outline=TEXT, width=3 * K)


# header
text(60, 44, "GrowBox humidifier wiring", 46, "Bold")
text(60, 104, "ESP32-C3 SuperMini · NPN driver · HW-307 relay · LM2596", 25, "Medium", CYAN)
text(60, 142, "Logical diagram, pin names as printed on the modules. The relay goes in series "
     "with the float switch; nothing is switched on 230 V.", 17, fill=DIM)

# --- cards ---
# humidifier main board
card(60, 210, 380, 600, "Humidifier", "ultrasonic · its own main board")
text(358, 310, "+28 V (CN1)", 19, "Semibold", RED, anchor="rm")
text(358, 370, "GND (CN1)", 19, "Semibold", GREY, anchor="rm")
text(82, 430, "float switch,", 16, fill=DIM)
text(82, 452, "middle wire cut here:", 16, fill=DIM)
text(160, 560, "board", 17, "Semibold", BLUE, anchor="mb")
text(290, 560, "float", 17, "Semibold", BLUE, anchor="mb")

# LM2596
card(490, 210, 790, 430, "LM2596", "step-down, set to 5.0 V")
text(512, 310, "IN+", 19, "Semibold", RED, anchor="lm")
text(512, 370, "IN−", 19, "Semibold", GREY, anchor="lm")
text(768, 310, "OUT+", 19, "Semibold", YELLOW, anchor="rm")
text(768, 370, "OUT−", 19, "Semibold", GREY, anchor="rm")

# ESP32-C3 SuperMini
d.rounded_rectangle(s(1005, 196, 1075, 214), radius=6 * K, fill="#0E2A28", outline=EDGE, width=2 * K)
card(920, 210, 1160, 560, "ESP32-C3", "SuperMini · MicroPython", accent=GREEN)
text(942, 310, "5V", 20, "Semibold", YELLOW, anchor="lm")
text(942, 370, "GND", 20, "Semibold", GREY, anchor="lm")
text(1138, 480, "GPIO 4", 21, "Bold", CYAN, anchor="rm")
text(942, 510, "LED GPIO 8 (on board)", 15, fill=DIM, anchor="lm")

# NPN driver
card(1200, 360, 1450, 600, "NPN driver", "BC547")

# HW-307 relay
card(1490, 210, 1750, 600, "HW-307 relay", "JQC3F-05VDC · 5 V coil", right=True)
text(1512, 310, "DC+", 19, "Semibold", YELLOW, anchor="lm")
text(1512, 430, "IN", 19, "Semibold", GREEN, anchor="lm")
text(1530, 578, "DC−", 17, "Semibold", GREY, anchor="mb")
text(1620, 578, "COM", 17, "Semibold", BLUE, anchor="mb")
text(1710, 578, "NO", 17, "Semibold", BLUE, anchor="mb")
text(1728, 480, "NC unused", 15, fill=DIM, anchor="rm")
text(1728, 502, "IN low = on", 15, fill=DIM, anchor="rm")

# --- wires ---
# +28 V and GND from the humidifier into the LM2596
wire([(380, 310), (490, 310)], RED)
wire([(380, 370), (490, 370)], GREY)

# 5 V: LM2596 -> ESP, and over the top to the relay
wire([(790, 310), (920, 310)], YELLOW)
wire([(850, 310), (850, 180), (1470, 180), (1470, 310), (1490, 310)], YELLOW)
dot(850, 310, YELLOW)

# GND: LM2596 -> ESP, and a bus under the driver to the relay
wire([(790, 370), (920, 370)], GREY)
wire([(870, 370), (870, 640), (1530, 640), (1530, 600)], GREY)
dot(870, 370, GREY)

# GPIO 4 -> 1k -> base; 10k base-GND; emitter GND; collector -> IN
bx, by = 1365, 480  # transistor centre
wire([(1160, 480), (bx - 10, 480)], CYAN)
resistor(1235, 480, "1 kΩ")
dot(1295, 480, CYAN)
wire([(1295, 480), (1295, 640)], GREY)
resistor(1295, 560, "10 kΩ", vertical=True)
dot(1295, 640, GREY)

d.ellipse(s(bx - 28, by - 28, bx + 28, by + 28), outline=TEXT, width=3 * K)
d.line(s(bx - 10, by - 18, bx - 10, by + 18), fill=TEXT, width=4 * K)
d.line(s(bx - 10, by - 7, bx + 12, by - 24), fill=TEXT, width=3 * K)
d.line(s(bx - 10, by + 7, bx + 12, by + 24), fill=TEXT, width=3 * K)
d.polygon(s(bx + 13, by + 25, bx + 1, by + 23, bx + 8, by + 13), fill=TEXT)
text(bx - 34, by - 8, "B", 14, "Semibold", DIM, anchor="rb")
text(bx + 22, by - 40, "C", 14, "Semibold", DIM, anchor="lm")
text(bx + 22, by + 40, "E", 14, "Semibold", DIM, anchor="lm")
wire([(bx + 12, by - 24), (bx + 12, 430), (1490, 430)], GREEN)
wire([(bx + 12, by + 24), (bx + 12, 640)], GREY)
dot(bx + 12, 640, GREY)

# relay contacts in series with the float switch middle wire
wire([(1620, 600), (1620, 720), (290, 720), (290, 600)], BLUE)
wire([(1710, 600), (1710, 770), (160, 770), (160, 600)], BLUE)
text(960, 712, "float switch middle wire ↔ COM", 16, "Semibold", BLUE, anchor="mb")
text(960, 762, "board sensor input ↔ NO", 16, "Semibold", BLUE, anchor="mb")

# pins on top of the wires
for x, y, c in [(380, 310, RED), (380, 370, GREY), (490, 310, RED), (490, 370, GREY),
                (790, 310, YELLOW), (790, 370, GREY), (920, 310, YELLOW), (920, 370, GREY),
                (1160, 480, CYAN), (1490, 310, YELLOW), (1490, 430, GREEN),
                (1530, 600, GREY), (1620, 600, BLUE), (1710, 600, BLUE),
                (160, 600, BLUE), (290, 600, BLUE)]:
    pin(x, y, c)

# --- notes ---
notes = [
    "GPIO 4 high → BC547 conducts → IN pulled to GND → relay on, COM–NO closed, the humidifier runs.",
    "At boot and reset GPIO 4 is an input and the 10 kΩ keeps the transistor off, so the relay stays off.",
    "Relay open = the humidifier sees “no water” and stops. The float switch still protects it from running dry.",
    "Set the LM2596 to 5.0 V before connecting the ESP. It is fed from the humidifier's CN1 (+28 V). All grounds are common.",
    "No wire to the main controller: the on/off state comes over ESP-NOW. On-board LED lit = link up.",
]
y = 850
for n in notes:
    d.ellipse(s(62, y + 7, 72, y + 17), fill=GREEN)
    text(86, y, n, 18)
    y += 44

img.resize((W, H), Image.LANCZOS).save(OUT)
print(OUT)
