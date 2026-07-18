"""
ADPS 双轴矩阵图片水印工具 · v4 (2026-07-18)
==========================================
v4 相对 v3 三个改动:
1. 深底图上不再用白面板 (突兀), 改成半透明 navy 面板 + gold 描边, 与图融合
2. ADPS wordmark 与副标题之间加更多呼吸空间 (line_gap 4→10)
3. 增加 lang 参数: "en" 只显示 "by Jia Huang"; "zh" 只显示 "by 黄佳"; "both" 双语 (旧行为)

用法:
    python3 add_watermark.py <input.png> <output.png> [--position tr|br|tl|bl] [--lang en|zh|both]

或从其它脚本导入:
    from add_watermark import add_watermark
    add_watermark("in.png", "out.png", position="tr", lang="en")
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

NAVY = (15, 58, 95)
GOLD = (196, 145, 54)
INK_LIGHT = (248, 250, 252)
INK_DARK = (15, 23, 42)
INK_MUTED = (100, 116, 139)
MUTED_LIGHT = (199, 212, 232)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
FONT_PATH = next((c for c in FONT_CANDIDATES if Path(c).exists()), None)
if FONT_PATH is None:
    raise SystemExit("No CJK font found. Install fonts-noto-cjk or fonts-wqy-microhei.")


def _f(size):
    return ImageFont.truetype(FONT_PATH, size)


def detect_bg_color(img: Image.Image):
    W, H = img.size
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    corners = [(0, 0), (W - 10, 0), (0, H - 10), (W - 10, H - 10)]
    r_sum, g_sum, b_sum, cnt = 0, 0, 0, 0
    for cx, cy in corners:
        crop = img.crop((cx, cy, cx + 10, cy + 10))
        for px in crop.getdata():
            r_sum += px[0]; g_sum += px[1]; b_sum += px[2]; cnt += 1
    r, g, b = r_sum // cnt, g_sum // cnt, b_sum // cnt
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return (r, g, b), luminance < 128


def build_watermark_tile(is_dark_bg: bool, scale: float = 1.0, lang: str = "both", bg_rgb=None):
    """
    构建紧凑水印 tile(RGBA)。
    lang: "en" → "by Jia Huang" · "zh" → "by 黄佳" · "both" → "by Jia Huang · 黄佳"
    """
    icon = int(52 * scale)
    pad_x = int(16 * scale)
    pad_y = int(14 * scale)
    text_gap_x = int(12 * scale)
    line_gap_title = int(10 * scale)  # ADPS → subtitle (v3 是 4, 呼吸不够)
    line_gap_sub = int(6 * scale)     # subtitle → by

    f_adps = _f(int(26 * scale))
    f_sub = _f(int(11 * scale))
    f_by = _f(int(13 * scale))

    if lang == "en":
        by_text = "by Jia Huang"
    elif lang == "zh":
        by_text = "by 黄佳"
    else:
        by_text = "by Jia Huang · 黄佳"

    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    adps_box = d.textbbox((0, 0), "ADPS", font=f_adps)
    adps_w, adps_h = adps_box[2] - adps_box[0], adps_box[3] - adps_box[1]
    sub_box = d.textbbox((0, 0), "Agent Design Patterns Society", font=f_sub)
    sub_w, sub_h = sub_box[2] - sub_box[0], sub_box[3] - sub_box[1]
    by_box = d.textbbox((0, 0), by_text, font=f_by)
    by_w, by_h = by_box[2] - by_box[0], by_box[3] - by_box[1]

    text_col_w = max(adps_w, sub_w, by_w)
    inner_w = icon + text_gap_x + text_col_w
    inner_h = max(icon, adps_h + line_gap_title + sub_h + line_gap_sub + by_h)

    W = inner_w + pad_x * 2
    H = inner_h + pad_y * 2

    if is_dark_bg:
        # v4: 与底图融合的半透明 navy 面板 + gold 边框, 不再是刺眼白块
        if bg_rgb is not None:
            r, g, b = bg_rgb
            # 面板色 = 底色再暗一点 + 轻微 navy tint, 保持一致性
            panel_r = max(0, min(255, int(r * 0.6 + NAVY[0] * 0.4)))
            panel_g = max(0, min(255, int(g * 0.6 + NAVY[1] * 0.4)))
            panel_b = max(0, min(255, int(b * 0.6 + NAVY[2] * 0.4)))
            bg_fill = (panel_r, panel_g, panel_b, 215)
        else:
            bg_fill = (15, 40, 70, 215)
        border_color = GOLD
        border_w = max(1, int(1.5 * scale))
        text_color_primary = INK_LIGHT
        text_color_sub = MUTED_LIGHT
        text_color_by = GOLD
    else:
        bg_fill = (255, 255, 255, 232)
        border_color = NAVY
        border_w = max(1, int(1 * scale))
        text_color_primary = NAVY
        text_color_sub = INK_MUTED
        text_color_by = INK_DARK

    tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)

    radius = int(10 * scale)
    td.rounded_rectangle(
        [(0, 0), (W - 1, H - 1)],
        radius=radius,
        fill=bg_fill,
        outline=border_color,
        width=border_w,
    )

    icon_x = pad_x
    icon_y = (H - icon) // 2

    td.rounded_rectangle(
        [(icon_x, icon_y), (icon_x + icon, icon_y + icon)],
        radius=int(6 * scale),
        fill=NAVY,
    )

    dot_r = max(1, int(0.9 * scale))
    dot_spacing = int(6 * scale)
    dot_start = int(6.5 * scale)
    dot_fill = (INK_LIGHT[0], INK_LIGHT[1], INK_LIGHT[2], 107)
    for row in range(7):
        for col in range(6):
            cx = icon_x + dot_start + col * dot_spacing
            cy = icon_y + dot_start + row * dot_spacing
            if cx <= icon_x + icon - 3 and cy <= icon_y + icon - 3:
                td.ellipse(
                    [(cx - dot_r, cy - dot_r), (cx + dot_r, cy + dot_r)],
                    fill=dot_fill,
                )

    def _s(v):
        return int(v * (icon / 64.0))
    gold_w = max(2, int(2.8 * scale))
    a_left = (icon_x + _s(13), icon_y + _s(49))
    a_top = (icon_x + _s(31.5), icon_y + _s(13))
    a_right = (icon_x + _s(50), icon_y + _s(49))
    a_cross_l = (icon_x + _s(21.5), icon_y + _s(34.5))
    a_cross_r = (icon_x + _s(41.5), icon_y + _s(34.5))
    td.line([a_left, a_top], fill=GOLD, width=gold_w)
    td.line([a_top, a_right], fill=GOLD, width=gold_w)
    td.line([a_cross_l, a_cross_r], fill=GOLD, width=gold_w)

    sq = max(2, int(2.8 * scale))
    for cx, cy in [a_left, a_top, a_right]:
        td.rectangle(
            [(cx - sq // 2, cy - sq // 2), (cx + sq // 2, cy + sq // 2)],
            fill=INK_LIGHT,
        )

    text_x = icon_x + icon + text_gap_x
    total_text_h = adps_h + line_gap_title + sub_h + line_gap_sub + by_h
    text_y = (H - total_text_h) // 2

    td.text((text_x, text_y), "ADPS", font=f_adps, fill=text_color_primary)
    td.text(
        (text_x, text_y + adps_h + line_gap_title),
        "Agent Design Patterns Society",
        font=f_sub,
        fill=text_color_sub,
    )
    td.text(
        (text_x, text_y + adps_h + line_gap_title + sub_h + line_gap_sub),
        by_text,
        font=f_by,
        fill=text_color_by,
    )

    return tile


def add_watermark(src_path: str, dst_path: str, position: str = "tr", lang: str = "both"):
    """
    在源图指定角落空白处叠加水印。不改变画布尺寸。
    position: 'tr' 右上角(默认) · 'br' 右下角 · 'tl' 左上角 · 'bl' 左下角
    lang: 'en' 只英文署名 · 'zh' 只中文署名 · 'both' 双语(默认)
    """
    src = Image.open(src_path).convert("RGBA")
    W, H = src.size

    bg_rgb, is_dark = detect_bg_color(src)

    if W >= 2200:
        scale = 1.5
    elif W >= 1600:
        scale = 1.2
    elif W >= 1200:
        scale = 1.0
    elif W >= 900:
        scale = 0.85
    else:
        scale = 0.7

    tile = build_watermark_tile(is_dark, scale=scale, lang=lang, bg_rgb=bg_rgb)
    tw, th = tile.size

    margin = int(28 * scale)
    positions = {
        "tr": (W - tw - margin, margin),
        "br": (W - tw - margin, H - th - margin),
        "tl": (margin, margin),
        "bl": (margin, H - th - margin),
    }
    px, py = positions.get(position, positions["tr"])

    out = src.copy()
    out.paste(tile, (px, py), tile)

    out.save(dst_path, "PNG", optimize=True)
    print(f"Watermarked: {dst_path} ({W}x{H}, tile={tw}x{th}, pos={position}, lang={lang}, bg={'dark' if is_dark else 'light'}, scale={scale})")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 add_watermark.py <input.png> <output.png> [--position tr|br|tl|bl] [--lang en|zh|both]")
        sys.exit(1)
    pos = "tr"
    lang = "both"
    for i, arg in enumerate(sys.argv):
        if arg == "--position" and i + 1 < len(sys.argv):
            pos = sys.argv[i + 1]
        if arg == "--lang" and i + 1 < len(sys.argv):
            lang = sys.argv[i + 1]
    add_watermark(sys.argv[1], sys.argv[2], position=pos, lang=lang)
