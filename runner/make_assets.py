"""Deterministically generate the image/audio assets used by the visual and
other-modalities prompts. Requires: matplotlib, pillow."""
import math
import os
import struct
import wave

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
os.makedirs(ASSETS, exist_ok=True)


def shapes_png():
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    # 7 circles
    for (x, y, c) in [(1.5, 8.5, "blue"), (4, 7, "green"), (2, 4.5, "orange"),
                      (5.5, 2, "blue"), (8, 4.5, "purple"), (6.5, 5.5, "green"),
                      (3.5, 1.5, "gray")]:
        ax.add_patch(Circle((x, y), 0.6, color=c))
    # 2 squares
    ax.add_patch(Rectangle((6.8, 1.0), 1.2, 1.2, color="brown"))
    ax.add_patch(Rectangle((0.8, 6.0), 1.2, 1.2, color="teal"))
    # red triangle in top-right corner
    ax.add_patch(Polygon([(8.4, 8.4), (9.6, 8.4), (9.0, 9.6)], color="red"))
    fig.savefig(os.path.join(ASSETS, "shapes.png"), dpi=100, bbox_inches="tight")
    plt.close(fig)


def chart_png():
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    revenue = [62, 57, 74, 91, 83, 68]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(months, revenue, color="#4C72B0")
    ax.bar_label(bars)
    ax.set_ylabel("Revenue ($k)")
    ax.set_title("Monthly Revenue 2025")
    fig.savefig(os.path.join(ASSETS, "chart.png"), dpi=100, bbox_inches="tight")
    plt.close(fig)


def ocr_png():
    img = Image.new("RGB", (640, 160), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
    d.text((20, 30), "Gate B7 boarding 18:42", fill="black", font=font)
    d.text((20, 90), "Flight QX-118, seat 23F", fill="black", font=font)
    img.save(os.path.join(ASSETS, "ocr.png"))


def flowchart_png():
    fig, ax = plt.subplots(figsize=(5, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")

    def box(x, y, text):
        ax.add_patch(Rectangle((x - 2, y - 0.7), 4, 1.4, fill=False))
        ax.text(x, y, text, ha="center", va="center", fontsize=11)

    def arrow(x1, y1, x2, y2, label=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->"))
        if label:
            ax.text((x1 + x2) / 2 + 0.5, (y1 + y2) / 2, label, fontsize=10)

    box(5, 13, "START: x = 3")
    box(5, 10.5, "x = x * 2")
    box(5, 8, "x = x + 1")
    box(5, 5.5, "x < 10 ?")
    box(5, 3, "print(x)")
    arrow(5, 12.3, 5, 11.2)
    arrow(5, 9.8, 5, 8.7)
    arrow(5, 7.3, 5, 6.2)
    arrow(5, 4.8, 5, 3.7, "no")
    # loop back on yes
    ax.annotate("", xy=(7, 10.5), xytext=(7, 5.5),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.3"))
    ax.text(8.1, 8, "yes", fontsize=10)
    fig.savefig(os.path.join(ASSETS, "flowchart.png"), dpi=100, bbox_inches="tight")
    plt.close(fig)


def beeps_wav():
    rate = 16000
    frames = []
    for _ in range(5):
        for i in range(int(rate * 0.2)):  # 200ms 880Hz beep
            frames.append(int(12000 * math.sin(2 * math.pi * 880 * i / rate)))
        frames.extend([0] * int(rate * 0.3))  # 300ms silence
    with wave.open(os.path.join(ASSETS, "beeps.wav"), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", f) for f in frames))


if __name__ == "__main__":
    shapes_png()
    chart_png()
    ocr_png()
    flowchart_png()
    beeps_wav()
    print("assets written to", os.path.abspath(ASSETS))
