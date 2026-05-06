#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from shutil import copy2
from xml.sax.saxutils import escape

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
TAB_DIR = ROOT / "outputs" / "standardized_tables"
OUT_DIR = ROOT / "outputs" / "standardized_figures"
SITE_DIR = ROOT / "site" / "assets" / "figures"

MODELS = [
    "Model 1 baseline (climate controls)",
    "Model 2 (add bachelors)",
    "Model 2 (add housing value)",
    "Model 4 interactions (centered)",
    "Model 5C clustered SEs by county",
    "Model 7 (infrastructure controls, outcome-safe)",
    "Model 8 add demand proxy",
    "Model 9 + pv control (most controlled)",
]

TERMS = [
    "log_median_household_income",
    "pct_black",
    "pct_hispanic",
    "poverty_rate",
    "cdd65_2023",
    "hdd65_2023",
]

TERM_LABELS = {
    "log_median_household_income": "Log median income",
    "pct_black": "% Black",
    "pct_hispanic": "% Hispanic",
    "poverty_rate": "Poverty rate",
    "cdd65_2023": "Cooling degree days",
    "hdd65_2023": "Heating degree days",
}

TERM_COLORS = {
    "log_median_household_income": "#1D4ED8",
    "pct_black": "#7C3AED",
    "pct_hispanic": "#C2410C",
    "poverty_rate": "#B45309",
    "cdd65_2023": "#DC2626",
    "hdd65_2023": "#2563EB",
}

PAPER_BG = "#F8F5EF"
PANEL_BG = "#FFFDF8"
GRID = "#D9D4C7"
TEXT = "#1F2933"
MUTED = "#52606D"

PANEL_TICKS = {
    "log_median_household_income": [0.0, 0.2, 0.4],
    "pct_black": [-0.2, -0.1, 0.0],
    "pct_hispanic": [-0.3, -0.2, -0.1, 0.0],
    "poverty_rate": [-0.1, 0.0, 0.1],
    "cdd65_2023": [-0.2, -0.1, 0.0, 0.1, 0.2],
    "hdd65_2023": [0.0, 0.1, 0.2],
}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates: list[str] = []
    if bold:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
                "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Georgia.ttf",
                "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
                "/Library/Fonts/Arial.ttf",
            ]
        )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def wrap_label(text: str) -> str:
    replacements = [
        (" baseline ", " baseline\n"),
        (" bachelors", "\nbachelors"),
        (" housing value", "\nhousing value"),
        (" interactions ", " interactions\n"),
        (" clustered ", " clustered\n"),
        (" infrastructure ", " infrastructure\n"),
        (" demand proxy", "\ndemand proxy"),
        (" pv control", "\npv control"),
    ]
    padded = f" {text} "
    for old, new in replacements:
        if old in padded:
            return text.replace(old.strip(), new.strip(), 1)
    midpoint = len(text) // 2
    split_idx = text.rfind(" ", 0, midpoint)
    if split_idx == -1:
        split_idx = text.find(" ", midpoint)
    if split_idx == -1:
        return text
    return text[:split_idx] + "\n" + text[split_idx + 1 :]


def load_data() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for model in MODELS:
        path = TAB_DIR / f"y_storage | {model}.csv"
        df = pd.read_csv(path).rename(
            columns={
                "Unnamed: 0": "term",
                "Coef.": "coef",
                "P>|z|": "pval",
                "[0.025": "conf_low",
                "0.975]": "conf_high",
            }
        )
        df["model"] = model
        df["model_order"] = MODELS.index(model)
        frames.append(df[["term", "coef", "pval", "conf_low", "conf_high", "model", "model_order"]])
    out = pd.concat(frames, ignore_index=True)
    out = out[out["term"].isin(TERMS)].copy()
    out["term_label"] = out["term"].map(TERM_LABELS)
    return out


def panel_ranges(df: pd.DataFrame) -> dict[str, tuple[float, float]]:
    ranges: dict[str, tuple[float, float]] = {}
    for term in TERMS:
        s = df[df["term"] == term]
        tick_min = min(PANEL_TICKS[term])
        tick_max = max(PANEL_TICKS[term])
        ymin = min(float(s["conf_low"].min()), tick_min)
        ymax = max(float(s["conf_high"].max()), tick_max)
        spread = ymax - ymin
        pad = max(0.015, spread * 0.10)
        ymin -= pad
        ymax += pad
        ranges[term] = (ymin, ymax)
    return ranges


def compute_layout() -> dict[str, float]:
    width = 3609
    height = 3433
    margin_left = 940
    margin_right = 170
    margin_top = 390
    margin_bottom = 520
    panel_gap = 78
    usable_h = height - margin_top - margin_bottom - panel_gap * (len(TERMS) - 1)
    panel_h = usable_h / len(TERMS)
    plot_w = width - margin_left - margin_right
    return {
        "width": width,
        "height": height,
        "margin_left": margin_left,
        "margin_right": margin_right,
        "margin_top": margin_top,
        "margin_bottom": margin_bottom,
        "panel_gap": panel_gap,
        "panel_h": panel_h,
        "plot_w": plot_w,
    }


def x_positions(layout: dict[str, float]) -> dict[int, float]:
    plot_w = layout["plot_w"]
    x0 = layout["margin_left"]
    return {i: x0 + (i / (len(MODELS) - 1)) * plot_w for i in range(len(MODELS))}


def y_map(value: float, ymin: float, ymax: float, top: float, panel_h: float) -> float:
    return top + (ymax - value) / (ymax - ymin) * panel_h


def fmt_tick(value: float) -> str:
    return f"{value:.1f}"


def build_svg(df: pd.DataFrame, svg_path: Path) -> None:
    layout = compute_layout()
    xs = x_positions(layout)
    ranges = panel_ranges(df)

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{layout["width"]}" height="{layout["height"]}" viewBox="0 0 {layout["width"]} {layout["height"]}">',
        f'<rect width="100%" height="100%" fill="{PAPER_BG}"/>',
        f'<text x="{layout["width"]/2:.1f}" y="46" text-anchor="middle" font-family="Georgia, serif" font-size="28" font-weight="700" fill="{TEXT}">Coefficient stability across specifications: Storage</text>',
        f'<text x="{layout["width"]/2:.1f}" y="76" text-anchor="middle" font-family="Georgia, serif" font-size="16" fill="{MUTED}">Filled markers indicate p &lt; 0.05; hollow markers indicate p ≥ 0.05.</text>',
    ]

    for idx, term in enumerate(TERMS):
        top = layout["margin_top"] + idx * (layout["panel_h"] + layout["panel_gap"])
        bottom = top + layout["panel_h"]
        ymin, ymax = ranges[term]
        color = TERM_COLORS[term]
        sub = df[df["term"] == term].sort_values("model_order")

        lines.append(
            f'<rect x="{layout["margin_left"]:.1f}" y="{top:.1f}" width="{layout["plot_w"]:.1f}" height="{layout["panel_h"]:.1f}" fill="{PANEL_BG}"/>'
        )

        for tick in PANEL_TICKS[term]:
            y = y_map(tick, ymin, ymax, top, layout["panel_h"])
            lines.append(
                f'<line x1="{layout["margin_left"]:.1f}" y1="{y:.1f}" x2="{layout["margin_left"] + layout["plot_w"]:.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1" opacity="0.55"/>'
            )
            lines.append(
                f'<text x="{layout["margin_left"] - 26:.1f}" y="{y + 10:.1f}" text-anchor="end" font-family="Georgia, serif" font-size="36" fill="{TEXT}">{fmt_tick(tick)}</text>'
            )

        if ymin < 0 < ymax:
            zero_y = y_map(0.0, ymin, ymax, top, layout["panel_h"])
            lines.append(
                f'<line x1="{layout["margin_left"]:.1f}" y1="{zero_y:.1f}" x2="{layout["margin_left"] + layout["plot_w"]:.1f}" y2="{zero_y:.1f}" stroke="{MUTED}" stroke-width="1.2" stroke-dasharray="5 4"/>'
            )

        band_points: list[str] = []
        for _, row in sub.iterrows():
            x = xs[int(row["model_order"])]
            y = y_map(float(row["conf_high"]), ymin, ymax, top, layout["panel_h"])
            band_points.append(f"{x:.1f},{y:.1f}")
        for _, row in sub.iloc[::-1].iterrows():
            x = xs[int(row["model_order"])]
            y = y_map(float(row["conf_low"]), ymin, ymax, top, layout["panel_h"])
            band_points.append(f"{x:.1f},{y:.1f}")
        lines.append(
            f'<polygon points="{" ".join(band_points)}" fill="{color}" fill-opacity="0.15" stroke="none"/>'
        )

        coef_points = []
        for _, row in sub.iterrows():
            x = xs[int(row["model_order"])]
            y = y_map(float(row["coef"]), ymin, ymax, top, layout["panel_h"])
            coef_points.append(f"{x:.1f},{y:.1f}")
        lines.append(
            f'<polyline points="{" ".join(coef_points)}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        )

        for _, row in sub.iterrows():
            x = xs[int(row["model_order"])]
            y = y_map(float(row["coef"]), ymin, ymax, top, layout["panel_h"])
            fill = color if float(row["pval"]) < 0.05 else PANEL_BG
            stroke_width = 1.2 if float(row["pval"]) < 0.05 else 2.0
            lines.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="{fill}" stroke="{color}" stroke-width="{stroke_width}"/>'
            )

        lines.append(
            f'<text x="{layout["margin_left"] - 360:.1f}" y="{top + layout["panel_h"]/2 + 14:.1f}" text-anchor="middle" font-family="Georgia, serif" font-size="56" fill="{TEXT}">{escape(TERM_LABELS[term])}</text>'
        )

    axis_y = layout["height"] - layout["margin_bottom"] + 18
    for order, x in xs.items():
        lines.append(
            f'<line x1="{x:.1f}" y1="{layout["margin_top"] + (len(TERMS) - 1) * (layout["panel_h"] + layout["panel_gap"]) + layout["panel_h"]:.1f}" x2="{x:.1f}" y2="{axis_y - 2:.1f}" stroke="{TEXT}" stroke-width="2"/>'
        )
        label_parts = wrap_label(MODELS[order]).split("\n")
        label_y = axis_y + 28
        tspans = "".join(
            [
                f'<tspan x="{x:.1f}" dy="{0 if i == 0 else 16}">{escape(part)}</tspan>'
                for i, part in enumerate(label_parts)
            ]
        )
        lines.append(
            f'<text x="{x:.1f}" y="{label_y:.1f}" text-anchor="end" transform="rotate(-28 {x:.1f},{label_y:.1f})" font-family="Georgia, serif" font-size="44" fill="{TEXT}">{tspans}</text>'
        )

    lines.append(
        f'<text x="{layout["width"]/2:.1f}" y="{layout["height"] - 46:.1f}" text-anchor="middle" font-family="Georgia, serif" font-size="54" fill="{TEXT}">Specification</text>'
    )
    lines.append("</svg>")
    svg_path.write_text("\n".join(lines), encoding="utf-8")


def build_png(df: pd.DataFrame, png_path: Path) -> None:
    layout = compute_layout()
    xs = x_positions(layout)
    ranges = panel_ranges(df)

    img = Image.new("RGB", (int(layout["width"]), int(layout["height"])), PAPER_BG)
    draw = ImageDraw.Draw(img, "RGBA")
    title_font = load_font(72, bold=True)
    subtitle_font = load_font(48)
    term_font = load_font(56)
    tick_font = load_font(36)
    axis_font = load_font(54)

    title = "Coefficient stability across specifications: Storage"
    tw, _ = text_bbox(draw, title, title_font)
    draw.text(((layout["width"] - tw) / 2, 40), title, font=title_font, fill=TEXT)

    subtitle = "Filled markers indicate p < 0.05; hollow markers indicate p ≥ 0.05."
    sw, _ = text_bbox(draw, subtitle, subtitle_font)
    draw.text(((layout["width"] - sw) / 2, 118), subtitle, font=subtitle_font, fill=MUTED)

    last_bottom = 0.0
    for idx, term in enumerate(TERMS):
        top = layout["margin_top"] + idx * (layout["panel_h"] + layout["panel_gap"])
        bottom = top + layout["panel_h"]
        last_bottom = bottom
        ymin, ymax = ranges[term]
        color = TERM_COLORS[term]
        sub = df[df["term"] == term].sort_values("model_order")

        draw.rectangle(
            [layout["margin_left"], top, layout["margin_left"] + layout["plot_w"], bottom],
            fill=PANEL_BG,
        )

        for tick in PANEL_TICKS[term]:
            y = y_map(tick, ymin, ymax, top, layout["panel_h"])
            draw.line(
                [(layout["margin_left"], y), (layout["margin_left"] + layout["plot_w"], y)],
                fill=GRID,
                width=3,
            )
            label = fmt_tick(tick)
            lw, lh = text_bbox(draw, label, tick_font)
            draw.text((layout["margin_left"] - lw - 26, y - lh / 2), label, font=tick_font, fill=TEXT)

        if ymin < 0 < ymax:
            zero_y = y_map(0.0, ymin, ymax, top, layout["panel_h"])
            x = layout["margin_left"]
            while x < layout["margin_left"] + layout["plot_w"]:
                draw.line([(x, zero_y), (min(x + 18, layout["margin_left"] + layout["plot_w"]), zero_y)], fill=MUTED, width=3)
                x += 32

        band = []
        for _, row in sub.iterrows():
            x = xs[int(row["model_order"])]
            y = y_map(float(row["conf_high"]), ymin, ymax, top, layout["panel_h"])
            band.append((x, y))
        for _, row in sub.iloc[::-1].iterrows():
            x = xs[int(row["model_order"])]
            y = y_map(float(row["conf_low"]), ymin, ymax, top, layout["panel_h"])
            band.append((x, y))
        draw.polygon(band, fill=tuple(int(color[i : i + 2], 16) for i in (1, 3, 5)) + (38,))

        line_points = []
        for _, row in sub.iterrows():
            x = xs[int(row["model_order"])]
            y = y_map(float(row["coef"]), ymin, ymax, top, layout["panel_h"])
            line_points.append((x, y))
        draw.line(line_points, fill=color, width=7)

        for _, row in sub.iterrows():
            x = xs[int(row["model_order"])]
            y = y_map(float(row["coef"]), ymin, ymax, top, layout["panel_h"])
            if float(row["pval"]) < 0.05:
                draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=color, outline=(255, 255, 255), width=4)
            else:
                draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=PANEL_BG, outline=color, width=6)

        label = TERM_LABELS[term]
        lw, lh = text_bbox(draw, label, term_font)
        draw.text((layout["margin_left"] - 360 - lw / 2, top + layout["panel_h"] / 2 - lh / 2), label, font=term_font, fill=TEXT)

    axis_y = layout["height"] - layout["margin_bottom"] + 18
    for order, x in xs.items():
        draw.line([(x, last_bottom), (x, axis_y - 2)], fill=TEXT, width=2)
        label = wrap_label(MODELS[order])
        label_img = Image.new("RGBA", (700, 240), (255, 255, 255, 0))
        label_draw = ImageDraw.Draw(label_img)
        bbox = label_draw.multiline_textbbox((0, 0), label, font=tick_font, spacing=6, align="right")
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = label_img.width - text_w - 20
        text_y = 8
        label_draw.multiline_text((text_x, text_y), label, font=tick_font, fill=TEXT, spacing=6, align="right")
        rotated = label_img.rotate(28, expand=True, resample=Image.Resampling.BICUBIC)
        anchor_x = rotated.width - 36
        paste_x = int(x - anchor_x)
        img.paste(rotated, (paste_x, int(axis_y + 10)), rotated)

    axis_label = "Specification"
    aw, _ = text_bbox(draw, axis_label, axis_font)
    draw.text(((layout["width"] - aw) / 2, layout["height"] - 70), axis_label, font=axis_font, fill=TEXT)

    png_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(png_path)


def sync_outputs(*paths: Path) -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        copy2(path, SITE_DIR / path.name)


def main() -> None:
    df = load_data()
    png_path = OUT_DIR / "y_storage_robustness.png"
    svg_path = OUT_DIR / "y_storage_robustness.svg"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_png(df, png_path)
    build_svg(df, svg_path)
    sync_outputs(png_path, svg_path)
    print(f"Saved {png_path.relative_to(ROOT)}")
    print(f"Saved {svg_path.relative_to(ROOT)}")
    print(f"Synced site copies to {SITE_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
