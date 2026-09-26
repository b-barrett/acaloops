#!/usr/bin/env python3
"""Generate 12x, 16x, and 20x Acaloops elevation-profile SVGs.

Run from repo root: python3 scripts/generate_elevation_profile.py
Input:  assets/route/Morning_Trail_Run.gpx
Output: assets/images/elevation-profile-{12x,16x,20x}.svg
"""

from pathlib import Path
import html
from bisect import bisect_left
import math
import xml.etree.ElementTree as ET


# =========================================================
# 1. CONFIGURATION — FUTURE BEN: START HERE
# =========================================================
# For normal updates, this is the part you're likely to touch.

ROOT = Path(__file__).resolve().parents[1]
GPX_PATH = ROOT / "assets" / "route" / "Morning_Trail_Run.gpx"
OUTPUT_DIR = ROOT / "assets" / "images"

CREAM = "#f4f1e8"
GREEN = "#142219"
MUTED = "#465248"
GRID = "#c9c7be"
SEGMENT_COLOR = "#BA8E23"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"

SVG_WIDTH = 1200
LEFT_MARGIN = 108

Y_AXIS_TITLE_X = 32
X_AXIS_TITLE_GAP = 68

RIGHT_MARGIN = 32
TOP_MARGIN = 32
BOTTOM_MARGIN = 84
GAIN_SECTION_HEIGHT = 175

MIN_ELEVATION_FT = 100
MAX_ELEVATION_FT = 800
ELEVATION_TICK_FT = 100
VERTICAL_EXAGGERATIONS = (20, 24, 28)

# Appearance: adjust these without hunting through SVG markup.
TICK_FONT_SIZE = 24

AXIS_TITLE_FONT_SIZE = 24
PROFILE_LINE_WIDTH = 4
GRID_LINE_WIDTH = 1
AXIS_LINE_WIDTH = 1.5
X_TICK_INTERVAL = 1       # Whole miles between distance labels.
MARKER_OFFSET = 26        # Pixels below each highlighted segment.
MARKER_RADIUS = 13
SEGMENT_LABEL_SIZE = 20
SEGMENT_LABEL_GAP = 8

# Segment name and approximate start/end miles.
# Adjust the distances here if the highlighted climbs need fine-tuning.
SEGMENTS = [
    {"name": "Suburban Escape", "label_lines": ["SUBURBAN", "ESCAPE"], "start": 0.47, "end": 0.96},
    {"name": "Sousa to Summit", "label_lines": ["SOUSA TO", "SUMMIT"], "start": 3.95, "end": 4.90},
    {"name": "Short and Steep", "label_lines": ["SHORT", "AND", "STEEP"], "start": 5.80, "end": 6.00},
    {"name": "Oh No, Not Yet", "label_lines": ["OH NO,", "NOT YET"], "start": 6.665, "end": 7.065},
]

M_TO_MI = 0.000621371
M_TO_FT = 3.28084
FEET_PER_MILE = 5280.0


# =========================================================
# 2. READ GPX + CALCULATE ROUTE DATA
# =========================================================

def read_gpx(path):
    """Return track points as (latitude, longitude, elevation_m)."""
    root = ET.parse(path).getroot()
    points = []

    for trkpt in root.findall(".//{*}trkpt"):
        ele = trkpt.find("{*}ele")
        if ele is not None and ele.text is not None:
            points.append((float(trkpt.attrib["lat"]),
                           float(trkpt.attrib["lon"]),
                           float(ele.text)))

    if len(points) < 2:
        raise ValueError("GPX must contain at least two track points with elevation data.")
    return points


def haversine_m(lat1, lon1, lat2, lon2):
    """Distance between two GPS points, in meters."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def profile_data(points):
    """Return cumulative distance (mi), elevation (ft), and raw gain (ft)."""
    distances_m = [0.0]
    elevations_m = [points[0][2]]

    for prev, cur in zip(points, points[1:]):
        distances_m.append(distances_m[-1] + haversine_m(prev[0], prev[1], cur[0], cur[1]))
        elevations_m.append(cur[2])

    miles = [d * M_TO_MI for d in distances_m]
    feet = [e * M_TO_FT for e in elevations_m]
    raw_gain_ft = sum(max(0.0, b - a) for a, b in zip(feet, feet[1:]))
    return miles, feet, raw_gain_ft



def gain_by_mile(miles, feet):
    """Return raw elevation gain within each mile."""
    gains = []

    for mile in range(math.ceil(miles[-1])):
        finish = min(mile + 1, miles[-1])
        gain = sum(
            max(0.0, feet[i] - feet[i - 1])
            for i in range(1, len(miles))
            if miles[i] > mile and miles[i - 1] < finish
        )
        gains.append((mile, finish, gain))

    return gains


# =========================================================
# 3. CHART GEOMETRY
# =========================================================

def height_for_exaggeration(distance_mi, exaggeration):
    """Calculate SVG height for the requested vertical exaggeration."""
    plot_w = SVG_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    horizontal_ft = distance_mi * FEET_PER_MILE
    elevation_ft = MAX_ELEVATION_FT - MIN_ELEVATION_FT
    plot_h = exaggeration * elevation_ft * plot_w / horizontal_ft
    return round(TOP_MARGIN + plot_h + BOTTOM_MARGIN + GAIN_SECTION_HEIGHT)


def actual_exaggeration(distance_mi, height):
    """Actual exaggeration after height is rounded to a whole pixel."""
    plot_w = SVG_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    plot_h = height - TOP_MARGIN - BOTTOM_MARGIN - GAIN_SECTION_HEIGHT
    horizontal_px_per_ft = plot_w / (distance_mi * FEET_PER_MILE)
    vertical_px_per_ft = plot_h / (MAX_ELEVATION_FT - MIN_ELEVATION_FT)
    return vertical_px_per_ft / horizontal_px_per_ft


# =========================================================
# 4. BUILD SVG
# =========================================================

def make_svg(miles, feet, height):
    """Build one elevation-profile SVG."""
    plot_w = SVG_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    plot_h = height - TOP_MARGIN - BOTTOM_MARGIN - GAIN_SECTION_HEIGHT
    max_mi = miles[-1]
    baseline = TOP_MARGIN + plot_h

    def x(mi):
        return LEFT_MARGIN + (mi / max_mi) * plot_w

    def y(ft):
        return TOP_MARGIN + (MAX_ELEVATION_FT - ft) / (MAX_ELEVATION_FT - MIN_ELEVATION_FT) * plot_h

    coords = " ".join(f"{x(mi):.1f},{y(ft):.1f}" for mi, ft in zip(miles, feet))
    area = f"{LEFT_MARGIN:.1f},{baseline:.1f} {coords} {x(max_mi):.1f},{baseline:.1f}"

    x_ticks = list(range(0, int(max_mi) + 1, X_TICK_INTERVAL))
    if abs(max_mi - x_ticks[-1]) > 0.05:
        x_ticks.append(max_mi)
    y_ticks = range(MIN_ELEVATION_FT, MAX_ELEVATION_FT + 1, ELEVATION_TICK_FT)

    ve = actual_exaggeration(max_mi, height)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_WIDTH} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Acaloops elevation profile</title>',
        f'<desc id="desc">Elevation profile for the {max_mi:.1f}-mile Acaloops loop, displayed from {MIN_ELEVATION_FT} to {MAX_ELEVATION_FT} feet at approximately {ve:.1f}x vertical exaggeration.</desc>',
        f'<rect width="100%" height="100%" fill="{CREAM}"/>',
    ]

    # Elevation grid and labels.
    for tick in y_ticks:
        yy = y(tick)
        lines += [
            f'<line x1="{LEFT_MARGIN}" y1="{yy:.1f}" x2="{SVG_WIDTH-RIGHT_MARGIN}" y2="{yy:.1f}" stroke="{GRID}" stroke-width="{GRID_LINE_WIDTH}" opacity="0.7"/>',
            f'<text x="{LEFT_MARGIN-12}" y="{yy+4:.1f}" text-anchor="end" font-family="{FONT}" font-size="{TICK_FONT_SIZE}" fill="{MUTED}">{tick:,}</text>',
        ]

    # Draw the full route first; highlight the four climbs on top.
    lines += [
        f'<polygon points="{area}" fill="{GREEN}" opacity="0.10"/>',
        f'<polyline points="{coords}" fill="none" stroke="{GREEN}" stroke-width="{PROFILE_LINE_WIDTH}" stroke-linejoin="round" stroke-linecap="round"/>',
    ]

    # Nearest existing GPX points: no interpolation or extra geometry.
    def nearest_index(distance):
        i = bisect_left(miles, distance)
        if i == 0:
            return 0
        if i == len(miles):
            return len(miles) - 1
        return i if miles[i] - distance < distance - miles[i - 1] else i - 1

    for number, segment in enumerate(SEGMENTS, 1):
        name = segment["name"]
        label_lines = segment["label_lines"]
        start = segment["start"]
        finish = segment["end"]
        
        if start < 0 or finish > max_mi or finish <= start:
            raise ValueError(f"Segment {name!r} falls outside the route or has invalid bounds.")

        first, last = nearest_index(start), nearest_index(finish)
        highlighted = " ".join(
            f"{x(miles[i]):.1f},{y(feet[i]):.1f}"
            for i in range(first, last + 1)
        )
        lines.append(
            f'<polyline points="{highlighted}" fill="none" stroke="{SEGMENT_COLOR}" '
            f'stroke-width="{PROFILE_LINE_WIDTH}" stroke-linejoin="round" stroke-linecap="round"/>'
        )

        # Number and name just below the segment's starting point.
        mx, my = x(miles[first]), y(feet[first]) + MARKER_OFFSET

        label_x = mx + MARKER_RADIUS + SEGMENT_LABEL_GAP
        label_anchor = "start"

        lines += [
            f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="{MARKER_RADIUS}" fill="{SEGMENT_COLOR}"/>',
            f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-family="{FONT}" font-size="14" font-weight="700" fill="{CREAM}">{number}</text>',
        ]

        text_block = [
            f'<text x="{label_x:.1f}" y="{my:.1f}" '
            f'text-anchor="{label_anchor}" '
            f'font-family="{FONT}" font-size="{SEGMENT_LABEL_SIZE}" '
            f'font-weight="600" fill="{GREEN}">'
        ]

        for i, line in enumerate(label_lines):
            dy = 0 if i == 0 else SEGMENT_LABEL_SIZE + 2
            text_block.append(
                f'<tspan x="{label_x:.1f}" dy="{dy}">{html.escape(line)}</tspan>'
            )

        text_block.append('</text>')
        lines.append("".join(text_block))

    # Distance axis and labels.
    lines.append(f'<line x1="{LEFT_MARGIN}" y1="{baseline:.1f}" x2="{SVG_WIDTH-RIGHT_MARGIN}" y2="{baseline:.1f}" stroke="{GREEN}" stroke-width="{AXIS_LINE_WIDTH}"/>')
    for tick in x_ticks:
        xx = x(tick)
        label = f"{tick:g}" if isinstance(tick, int) else f"{tick:.1f}"
        lines += [
            f'<line x1="{xx:.1f}" y1="{baseline:.1f}" x2="{xx:.1f}" y2="{baseline+7:.1f}" stroke="{GREEN}" stroke-width="{AXIS_LINE_WIDTH}"/>',
            f'<text x="{xx:.1f}" y="{baseline+28:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{TICK_FONT_SIZE}" fill="{MUTED}">{html.escape(label)}</text>',
        ]

    # Gain by mile.
    mile_gains = gain_by_mile(miles, feet)
    max_gain = max(gain for _, _, gain in mile_gains)

    miles_title_y = baseline + X_AXIS_TITLE_GAP

    # Gain chart positioning.
    bar_group_offset = 15      # Moves bars, numbers, and gain title together.
    gain_title_gap = 40        # Space between bottom of bars and gain title.

    bar_top = miles_title_y + 34 + bar_group_offset
    bar_height = 60
    gain_title_y = bar_top + bar_height + gain_title_gap

    for start, finish, gain in mile_gains:
        bar_x = x(start) + 5
        bar_w = x(finish) - x(start) - 10
        bar_h = gain / max_gain * bar_height

        lines += [
            f'<rect x="{bar_x:.1f}" y="{bar_top + bar_height - bar_h:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="3" fill="{GREEN}" opacity="0.25"/>',
            f'<text x="{bar_x + bar_w/2:.1f}" y="{bar_top + bar_height - bar_h - 7:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{SEGMENT_LABEL_SIZE}" font-weight="700" fill="{GREEN}">{gain:.0f}</text>',
        ]

    # Axis titles and start/finish dots.
    lines += [
        f'<text x="{LEFT_MARGIN + plot_w/2:.1f}" y="{miles_title_y:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{AXIS_TITLE_FONT_SIZE}" font-weight="700" letter-spacing="1.5" fill="{MUTED}">MILES</text>',
        f'<text x="{LEFT_MARGIN + plot_w/2:.1f}" y="{gain_title_y:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{AXIS_TITLE_FONT_SIZE}" font-weight="700" letter-spacing="1.5" fill="{MUTED}">VERTICAL GAIN BY MILE (FT)</text>',
        f'<text x="{Y_AXIS_TITLE_X}" y="{TOP_MARGIN + plot_h/2:.1f}" text-anchor="middle" transform="rotate(-90 {Y_AXIS_TITLE_X} {TOP_MARGIN + plot_h/2:.1f})" font-family="{FONT}" font-size="{AXIS_TITLE_FONT_SIZE}" font-weight="700" letter-spacing="1.5" fill="{MUTED}">ELEVATION (FT)</text>',
    ]
    for mi, ft in ((miles[0], feet[0]), (miles[-1], feet[-1])):
        lines.append(f'<circle cx="{x(mi):.1f}" cy="{y(ft):.1f}" r="6" fill="{CREAM}" stroke="{GREEN}" stroke-width="3"/>')

    lines.append("</svg>")
    return "\n".join(lines)


# =========================================================
# 5. RUN IT
# =========================================================

def main():
    points = read_gpx(GPX_PATH)
    miles, feet, raw_gain_ft = profile_data(points)

    # Fixed axis is intentional: fail instead of silently clipping a future route.
    if min(feet) < MIN_ELEVATION_FT or max(feet) > MAX_ELEVATION_FT:
        raise ValueError(
            f"GPX elevation range {min(feet):.0f}-{max(feet):.0f} ft falls outside "
            f"the fixed {MIN_ELEVATION_FT}-{MAX_ELEVATION_FT} ft y-axis."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Reading:       {GPX_PATH.relative_to(ROOT)}")
    print(f"Track points:  {len(points):,}")
    print(f"Distance:      {miles[-1]:.2f} mi")
    print(f"Elevation:     {min(feet):,.0f}-{max(feet):,.0f} ft")
    print(f"Raw GPX gain:  {raw_gain_ft:,.0f} ft")
    print(f"Y-axis:        {MIN_ELEVATION_FT}-{MAX_ELEVATION_FT} ft by {ELEVATION_TICK_FT} ft\n")

    for exaggeration in VERTICAL_EXAGGERATIONS:
        height = height_for_exaggeration(miles[-1], exaggeration)
        output_path = OUTPUT_DIR / f"elevation-profile-{exaggeration}x.svg"
        output_path.write_text(make_svg(miles, feet, height), encoding="utf-8")
        print(f"Created:       {output_path.relative_to(ROOT)} ({SVG_WIDTH} x {height})")

    print("\nNote: raw GPX gain can differ from Strava/COROS because those platforms")
    print("smooth and correct elevation data differently.")


if __name__ == "__main__":
    main()
