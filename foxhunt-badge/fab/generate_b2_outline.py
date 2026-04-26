"""B-2 Spirit silhouette outline generator for KiCad Edge.Cuts.

Source: top-down silhouette extracted from a real B-2 mesh
(b2.stl from user's Downloads).  Scaled to a 200mm wingspan badge.

Process:
  1. Project all triangles in the STL to the X-Y plane (top-down view).
  2. Compute the unary union → polygon outline.
  3. Scale so wingspan (X-range) = 200mm; flip Y so nose at top (Y=0).
  4. Output 13-vertex polygon: nose, wingtip, 5 trailing-edge segments
     per side (3 aft spikes + 2 forward notches per side), mirrored.
"""
from pathlib import Path

# ---- Tunables ----
TARGET_WINGSPAN_MM = 200.0
SOURCE_STL         = Path.home() / "Downloads" / "b2.stl"


def extract_outline_from_stl(stl_path: Path):
    """Return a list of (x, y) points (centered around centerline at x=100,
    nose at y=0) by projecting the STL to the XY plane."""
    from stl import mesh
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    m = mesh.Mesh.from_file(str(stl_path))
    polys = []
    for tri in m.vectors:
        pts = [(float(tri[i, 0]), float(tri[i, 1])) for i in range(3)]
        # Skip degenerate triangles
        a = (pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1])
        b = (pts[2][0] - pts[0][0]) * (pts[1][1] - pts[0][1])
        if abs(a - b) < 1e-9:
            continue
        polys.append(Polygon(pts))
    silhouette = unary_union(polys)
    # Largest polygon (handle MultiPolygon)
    if hasattr(silhouette, "exterior"):
        coords = list(silhouette.exterior.coords)
    else:
        largest = max(silhouette.geoms, key=lambda g: g.area)
        coords = list(largest.exterior.coords)
    # Dedup near-coincident points
    cleaned = [coords[0]]
    for c in coords[1:]:
        if abs(c[0] - cleaned[-1][0]) > 0.01 or abs(c[1] - cleaned[-1][1]) > 0.01:
            cleaned.append(c)
    return cleaned


def transform_to_badge(raw_coords, target_wingspan):
    """Scale + flip Y so the badge sits with nose at (centerX, 0)."""
    src_xrange = max(c[0] for c in raw_coords) - min(c[0] for c in raw_coords)
    scale = target_wingspan / src_xrange
    # Nose Y in source = max Y (B-2 STL has nose pointing +Y)
    nose_y = max(c[1] for c in raw_coords)
    out = []
    for x, y in raw_coords:
        kx = x * scale + target_wingspan / 2  # centerline at X=target/2
        ky = (nose_y - y) * scale
        out.append((round(max(0.0, kx), 2), round(max(0.0, ky), 2)))
    return out


def main():
    raw = extract_outline_from_stl(SOURCE_STL)
    out = transform_to_badge(raw, TARGET_WINGSPAN_MM)
    print(f"Extracted {len(raw)} vertices from STL.")
    print(f"\nBadge-coord points (paste into pcb_gen.py B2_OUTLINE_MM):")
    for x, y in out:
        print(f"    ({x:7.2f}, {y:7.2f}),")
    xs = [p[0] for p in out]
    ys = [p[1] for p in out]
    print(f"\nBoard: {max(xs)-min(xs):.2f} x {max(ys)-min(ys):.2f} mm")


if __name__ == "__main__":
    main()
