# fontforge -script font_create.py

import fontforge
import os
import re

PIXEL_SIZE = 64
FONT_WIDTH = 8
FONT_HEIGHT = 16
GLYPH_WIDTH = PIXEL_SIZE * FONT_WIDTH
GLYPH_HEIGHT = PIXEL_SIZE * FONT_HEIGHT

font = fontforge.font()
font.encoding = "ISO8859-1"
font.em = GLYPH_HEIGHT
font.ascent = GLYPH_HEIGHT
font.descent = 0
font.fontname = "DarwinBitmap8x16"
font.familyname = "Darwin Bitmap 8x16"
font.fullname = "Darwin Bitmap 8x16 Pixel Font"
font.copyright = "Copyright (c) 2000 Ka-Ping Yee <ping@lfw.org>"

# Load bitmap
with open("iso_font.c", "r") as f:
    raw = f.read()

hex_bytes = re.findall(r"0x([0-9a-fA-F]{2})", raw)
bitmap_data = [int(h, 16) for h in hex_bytes]

# Compute left/right padding for each glyph
def compute_side_bearings(bitmap):
    col_bits = [0] * FONT_WIDTH
    for row in bitmap:
        for col in range(FONT_WIDTH):
            col_bits[col] |= (row >> (7 - col)) & 1

    left_pad = 0
    for b in col_bits:
        if b == 0:
            left_pad += 1
        else:
            break

    right_pad = 0
    for b in reversed(col_bits):
        if b == 0:
            right_pad += 1
        else:
            break

    return left_pad * PIXEL_SIZE, right_pad * PIXEL_SIZE

# Make SVG for each glyph
def make_svg(char_index, bitmap):
    svg = [
        '<?xml version="1.0" standalone="no"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{GLYPH_WIDTH}" height="{GLYPH_HEIGHT}" viewBox="0 0 {GLYPH_WIDTH} {GLYPH_HEIGHT}">'
    ]
    for y in range(FONT_HEIGHT):
        byte = bitmap[y]
        for x in range(FONT_WIDTH):
            if (byte >> (7 - x)) & 1:
                x_flipped = (FONT_WIDTH - 1 - x) * PIXEL_SIZE
                y_coord = y * PIXEL_SIZE
                svg.append(f'<rect x="{x_flipped}" y="{y_coord}" width="{PIXEL_SIZE}" height="{PIXEL_SIZE}" fill="#000" />')
    svg.append("</svg>")

    return "\n".join(svg)

# Glyph generation
os.makedirs("glyph_svgs", exist_ok=True)

for codepoint in range(256):
    print(f"Processing glyph {codepoint:03d}")

    offset = codepoint * FONT_HEIGHT
    bitmap = bitmap_data[offset:offset + FONT_HEIGHT]

    # Skip empty glyphs
    if all(b == 0x00 for b in bitmap):
        print("  Skipping empty glyph")
        continue

    # Compute bearings
    left_bearing, right_bearing = compute_side_bearings(bitmap)
    print(f"  Left bearing: {left_bearing}, Right bearing: {right_bearing}")

    # Write SVG
    svg_path = f"glyph_svgs/glyph_{codepoint}.svg"
    with open(svg_path, "w") as svg_file:
        svg_file.write(make_svg(codepoint, bitmap))

    glyph = font.createChar(codepoint)
    glyph.importOutlines(svg_path)
    glyph.width = GLYPH_WIDTH
    glyph.left_side_bearing = left_bearing
    glyph.right_side_bearing = right_bearing
    glyph.simplify()
    glyph.removeOverlap()
    glyph.round()

# Add space
space = font.createChar(0x20, "space")
space.width = GLYPH_WIDTH

# Finalize
font.selection.all()
font.autoHint()
font.autoInstr()
font.generate("darwinbitmap8x16.ttf")
print("Font generated: darwinbitmap8x16.ttf")