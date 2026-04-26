"""
Generate anim_frames.h -- a 60-frame, 128x64 monochrome animation
showing a B-2 silhouette flying across the screen with a sweeping
radar-style scan, then a foxhunt logo reveal.

Output layout: each frame is 1024 bytes (128x64 / 8), packed in the
SSD1306-friendly 'horizontal' bitmap order that Adafruit_GFX expects
for drawBitmap(): row-major, MSB-first per byte.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

W, H = 128, 64
N_FRAMES = 60
FPS = 20  # 3 seconds at 20fps


def b2_silhouette(scale=1.0):
    """Return a list of (x,y) points for a small B-2 flying-wing icon
    rendered at the given scale (relative to baseline 30px wingspan)."""
    span_px = 30 * scale
    chord_px = 16 * scale
    # Half outline, then mirror
    half = [
        (0, 0),
        (span_px * 0.25, chord_px * 0.18),
        (span_px * 0.50, chord_px * 0.42),
        (span_px * 0.50, chord_px * 0.95),  # wingtip
        (span_px * 0.36, chord_px * 1.00),  # peak
        (span_px * 0.24, chord_px * 0.70),  # valley
        (span_px * 0.12, chord_px * 1.00),  # peak
        (0, chord_px * 0.78),  # center notch
    ]
    full = list(half) + [(-x, y) for x, y in reversed(half[1:-1])]
    return full


def render_frame(idx: int) -> Image.Image:
    img = Image.new("1", (W, H), 0)  # black bg (off pixels)
    draw = ImageDraw.Draw(img)

    if idx < 30:
        # Phase 1: B-2 flies left-to-right with radar scan
        t = idx / 30.0
        cx = -20 + (W + 40) * t
        cy = 20 + 4 * math.sin(t * 6.28)

        # Radar sweep arc
        sweep_angle = -90 + t * 360
        for r in range(10, 40, 4):
            x0, y0 = W // 2 - r, H - r - 2
            x1, y1 = W // 2 + r, H - r - 2 + 2 * r
            draw.arc([x0, y0, x1, y1],
                     start=sweep_angle - 30, end=sweep_angle,
                     fill=1, width=1)

        # Aircraft silhouette
        pts = b2_silhouette(scale=1.1)
        translated = [(cx + x, cy + y) for x, y in pts]
        draw.polygon(translated, fill=1)

        # Tracking crosshair at aircraft center
        draw.line([(cx - 4, cy + 6), (cx + 4, cy + 6)], fill=1)
        draw.line([(cx, cy + 2), (cx, cy + 10)], fill=1)

    elif idx < 45:
        # Phase 2: Logo reveal - "FOXHUNT" wipes in
        t = (idx - 30) / 15.0
        # Bombs falling? scattered dots dropping
        for i in range(8):
            x = 16 + i * 14
            y_off = int(t * 60) - i * 3
            if 0 < y_off < 50:
                draw.ellipse([x - 1, y_off - 1, x + 1, y_off + 1], fill=1)
        # Title text wiping in from left
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 18)
        except (OSError, IOError):
            font = ImageFont.load_default()
        title = "FOXHUNT"
        wipe_x = int(t * 140) - 20
        bbox = draw.textbbox((0, 0), title, font=font)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        draw.text((tx, 24), title, fill=1, font=font)
        # Mask: black rectangle covering the un-wiped portion
        draw.rectangle([wipe_x, 0, W, H], fill=0)
        # Re-draw bomb trails on top of mask
        for i in range(8):
            x = 16 + i * 14
            y_off = int(t * 60) - i * 3
            if 0 < y_off < 50 and x < wipe_x:
                draw.ellipse([x - 1, y_off - 1, x + 1, y_off + 1], fill=1)

    else:
        # Phase 3: Final logo + tagline pulse
        t = (idx - 45) / 15.0
        try:
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 18)
            font_sm  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 9)
        except (OSError, IOError):
            font_big = ImageFont.load_default()
            font_sm = ImageFont.load_default()
        title = "FOXHUNT"
        bbox = draw.textbbox((0, 0), title, font=font_big)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, 12), title, fill=1, font=font_big)

        # Pulsing crosshair underline
        pulse = (math.sin(t * 6.28 * 2) + 1) / 2
        line_w = int(20 + 30 * pulse)
        draw.line([((W - line_w) // 2, 36), ((W + line_w) // 2, 36)],
                  fill=1, width=2)

        sub = "// 145.5 MHz //"
        bbox = draw.textbbox((0, 0), sub, font=font_sm)
        sw = bbox[2] - bbox[0]
        draw.text(((W - sw) // 2, 46), sub, fill=1, font=font_sm)

    return img


def img_to_bytes(img: Image.Image) -> bytes:
    """Convert 1-bit PIL image to row-major MSB-first byte array,
    matching Adafruit_GFX::drawBitmap() horizontal format."""
    pixels = img.load()
    out = bytearray()
    for y in range(H):
        for byte_x in range(W // 8):
            b = 0
            for bit in range(8):
                x = byte_x * 8 + bit
                if pixels[x, y]:
                    b |= (1 << (7 - bit))
            out.append(b)
    return bytes(out)


def emit_header(frames_bytes, path):
    lines = []
    lines.append("// anim_frames.h -- AUTO-GENERATED. Do not edit by hand.")
    lines.append("// Generated by fab/generate_anim.py -- 60 frames @ 20fps = 3.0s")
    lines.append("// Format: row-major, MSB-first per byte, 128x64 each = 1024 bytes/frame")
    lines.append("#pragma once")
    lines.append("#include <Arduino.h>")
    lines.append("")
    lines.append(f"#define ANIM_FRAME_COUNT {len(frames_bytes)}")
    lines.append(f"#define ANIM_FPS {FPS}")
    lines.append("")
    # Each frame as its own PROGMEM array, then a master pointer table
    for idx, fb in enumerate(frames_bytes):
        lines.append(f"static const uint8_t PROGMEM anim_frame_{idx:02d}[] = {{")
        for row_start in range(0, len(fb), 16):
            row = fb[row_start:row_start + 16]
            lines.append("    " + ", ".join(f"0x{b:02x}" for b in row) + ",")
        lines.append("};")
        lines.append("")
    lines.append("static const uint8_t* const PROGMEM anim_frames_table[] = {")
    for idx in range(len(frames_bytes)):
        lines.append(f"    anim_frame_{idx:02d},")
    lines.append("};")
    lines.append("")
    lines.append("static inline const uint8_t* anim_frame(uint32_t idx) {")
    lines.append("    return (const uint8_t*)pgm_read_ptr(&anim_frames_table[idx % ANIM_FRAME_COUNT]);")
    lines.append("}")
    Path(path).write_text("\n".join(lines))
    print(f"Wrote {path} ({sum(len(f) for f in frames_bytes)} bytes of frame data)")


def main():
    frames_bytes = []
    for i in range(N_FRAMES):
        img = render_frame(i)
        frames_bytes.append(img_to_bytes(img))
    out_path = Path(__file__).parent.parent / "firmware" / "src" / "anim_frames.h"
    emit_header(frames_bytes, out_path)

    # Also emit a preview montage
    montage = Image.new("1", (W * 10, H * 6), 0)
    for i in range(min(60, N_FRAMES)):
        col = i % 10
        row = i // 10
        f = render_frame(i)
        montage.paste(f, (col * W, row * H))
    preview_path = Path(__file__).parent / "anim_preview.png"
    montage.convert("L").save(preview_path)
    print(f"Wrote preview {preview_path}")


if __name__ == "__main__":
    main()
