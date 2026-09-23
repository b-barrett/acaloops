#!/usr/bin/env python3
"""Generate 12x, 16x, and 20x Acaloops elevation-profile SVGs.

Run from repo root: python3 scripts/generate_elevation_profile.py
Input:  assets/route/acaloop.gpx
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
GPX_PATH = ROOT / "assets" / "route" / "acaloop.gpx"
OUTPUT_DIR = ROOT / "assets" / "images"

CREAM = "#f4f1e8"
GREEN = "#142219"
MUTED = "#465248"
GRID = "#c9c7be"
SEGMENT_COLOR = "#BA8E23"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"

SVG_WIDTH = 1200
LEFT_MARGIN = 72
RIGHT_MARGIN = 32
TOP_MARGIN = 32
BOTTOM_MARGIN = 56

MIN_ELEVATION_FT = 100
MAX_ELEVATION_FT = 800
ELEVATION_TICK_FT = 100
VERTICAL_EXAGGERATIONS = (12, 16, 20)

# Appearance: adjust these without hunting through SVG markup.
TICK_FONT_SIZE = 18
AXIS_TITLE_FONT_SIZE = 18
PROFILE_LINE_WIDTH = 4
GRID_LINE_WIDTH = 1
AXIS_LINE_WIDTH = 1.5
X_TICK_INTERVAL = 1       # Whole miles between distance labels.
MARKER_OFFSET = 26        # Pixels below each highlighted segment.
MARKER_RADIUS = 13
SEGMENT_LABEL_SIZE = 16
SEGMENT_LABEL_GAP = 8

# Segment name and approximate start/end miles.
# Adjust the distances here if the highlighted climbs need fine-tuning.
SEGMENTS = [
    {"name": "Suburban Escape", "start": 0.20, "end": 1.065},
    {"name": "Sousa to Summit", "start": 3.95, "end": 4.90},
    {"name": "Short and Steep", "start": 5.80, "end": 6.00},
    {"name": "Oh No, Not Yet", "start": 6.65, "end": 7.075},
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


# =========================================================
# 3. CHART GEOMETRY
# =========================================================

def height_for_exaggeration(distance_mi, exaggeration):
    """Calculate SVG height for the requested vertical exaggeration."""
    plot_w = SVG_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    horizontal_ft = distance_mi * FEET_PER_MILE
    elevation_ft = MAX_ELEVATION_FT - MIN_ELEVATION_FT
    plot_h = exaggeration * elevation_ft * plot_w / horizontal_ft
    return round(TOP_MARGIN + plot_h + BOTTOM_MARGIN)


def actual_exaggeration(distance_mi, height):
    """Actual exaggeration after height is rounded to a whole pixel."""
    plot_w = SVG_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    plot_h = height - TOP_MARGIN - BOTTOM_MARGIN
    horizontal_px_per_ft = plot_w / (distance_mi * FEET_PER_MILE)
    vertical_px_per_ft = plot_h / (MAX_ELEVATION_FT - MIN_ELEVATION_FT)
    return vertical_px_per_ft / horizontal_px_per_ft


# =========================================================
# 4. BUILD SVG
# =========================================================

def make_svg(miles, feet, height):
    """Build one elevation-profile SVG."""
    plot_w = SVG_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    plot_h = height - TOP_MARGIN - BOTTOM_MARGIN
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
        name, start, finish = segment["name"], segment["start"], segment["end"]
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
        # The third and fourth climbs are close together: label #3 on the left.
        label_left = number == 3
        label_x = mx + (-1 if label_left else 1) * (MARKER_RADIUS + SEGMENT_LABEL_GAP)
        label_anchor = "end" if label_left else "start"
        lines += [
            f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="{MARKER_RADIUS}" fill="{SEGMENT_COLOR}"/>',
            f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-family="{FONT}" font-size="14" font-weight="700" fill="{CREAM}">{number}</text>',
            f'<text x="{label_x:.1f}" y="{my:.1f}" text-anchor="{label_anchor}" '
            f'dominant-baseline="central" font-family="{FONT}" font-size="{SEGMENT_LABEL_SIZE}" '
            f'font-weight="600" fill="{GREEN}">{html.escape(name)}</text>',
        ]

    # Distance axis and labels.
    lines.append(f'<line x1="{LEFT_MARGIN}" y1="{baseline:.1f}" x2="{SVG_WIDTH-RIGHT_MARGIN}" y2="{baseline:.1f}" stroke="{GREEN}" stroke-width="{AXIS_LINE_WIDTH}"/>')
    for tick in x_ticks:
        xx = x(tick)
        label = f"{tick:g}" if isinstance(tick, int) else f"{tick:.1f}"
        lines += [
            f'<line x1="{xx:.1f}" y1="{baseline:.1f}" x2="{xx:.1f}" y2="{baseline+7:.1f}" stroke="{GREEN}" stroke-width="{AXIS_LINE_WIDTH}"/>',
            f'<text x="{xx:.1f}" y="{baseline+28:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{TICK_FONT_SIZE}" fill="{MUTED}">{html.escape(label)}</text>',
        ]

    # Axis titles and start/finish dots.
    lines += [
        f'<text x="{LEFT_MARGIN + plot_w/2:.1f}" y="{height-8}" text-anchor="middle" font-family="{FONT}" font-size="{AXIS_TITLE_FONT_SIZE}" font-weight="700" letter-spacing="1.5" fill="{MUTED}">MILES</text>',
        f'<text x="18" y="{TOP_MARGIN + plot_h/2:.1f}" text-anchor="middle" transform="rotate(-90 18 {TOP_MARGIN + plot_h/2:.1f})" font-family="{FONT}" font-size="{AXIS_TITLE_FONT_SIZE}" font-weight="700" letter-spacing="1.5" fill="{MUTED}">ELEVATION (FT)</text>',
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
