from pathlib import Path
import math
import html


OBJ_FILE = "model.obj"
SVG_FILE = "model.svg"

SCALE = 100.0

FILL = "#64b4ff"
STROKE = "#222222"
STROKE_WIDTH = "1"


def vsub(a, b):
    return (
        a[0] - b[0],
        a[1] - b[1],
        a[2] - b[2],
    )


def vdot(a, b):
    return (
        a[0] * b[0] +
        a[1] * b[1] +
        a[2] * b[2]
    )


def vcross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vlen(v):
    return math.sqrt(
        v[0] * v[0] +
        v[1] * v[1] +
        v[2] * v[2]
    )


def vnorm(v):
    l = vlen(v)

    if l == 0:
        return (0.0, 0.0, 0.0)

    return (
        v[0] / l,
        v[1] / l,
        v[2] / l,
    )


def parse_obj(text):
    vertices = []
    faces = []

    for line in text.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("v "):
            _, x, y, z = line.split()[:4]

            vertices.append((
                float(x),
                float(y),
                float(z)
            ))

        elif line.startswith("f "):
            indices = []

            for token in line.split()[1:]:
                indices.append(
                    int(token.split("/")[0]) - 1
                )

            if len(indices) >= 3:
                faces.append(indices)

    return vertices, faces


def build_face_frame(points):
    p0 = points[0]
    p1 = points[1]
    p2 = points[2]

    u = vnorm(vsub(p1, p0))

    n = vnorm(
        vcross(
            vsub(p1, p0),
            vsub(p2, p0)
        )
    )

    v = vcross(n, u)

    return p0, u, v, n


def project_face(points, origin, u, v):
    result = []

    for p in points:
        d = vsub(p, origin)

        result.append((
            vdot(d, u) * SCALE,
            vdot(d, v) * SCALE
        ))

    return result


def css_matrix3d(origin, u, v, n):
    ox = origin[0] * SCALE
    oy = -origin[1] * SCALE
    oz = origin[2] * SCALE

    ux, uy, uz = u
    vx, vy, vz = v
    nx, ny, nz = n

    values = [
        ux, -uy, uz, 0,
        vx, -vy, vz, 0,
        nx, -ny, nz, 0,
        ox, oy, oz, 1
    ]

    return ",".join(
        f"{x:.12g}"
        for x in values
    )


def build_polygon(points3d):
    origin, u, v, n = build_face_frame(points3d)

    pts2d = project_face(
        points3d,
        origin,
        u,
        v
    )

    polygon = " ".join(
        f"{x:.6f},{y:.6f}"
        for x, y in pts2d
    )

    matrix = css_matrix3d(
        origin,
        u,
        v,
        n
    )

    return (
        f'<polygon '
        f'points="{html.escape(polygon)}" '
        f'fill="{FILL}" '
        f'stroke="{STROKE}" '
        f'stroke-width="{STROKE_WIDTH}" '
        f'style="transform-box:fill-box;'
        f'transform-origin:0 0;'
        f'transform:matrix3d({matrix});"'
        f' />'
    )


def obj_to_svg(vertices, faces):
    polygons = []

    for face in faces:
        points3d = [
            vertices[i]
            for i in face
        ]

        polygons.append(
            build_polygon(points3d)
        )

    svg = (
        '<svg '
        'xmlns="http://www.w3.org/2000/svg" '
        'style="overflow:visible;'
        'transform-style:preserve-3d;"'
        '>\n'
        + "\n".join(polygons) +
        '\n</svg>\n'
    )

    return svg


def main():
    obj_text = Path(OBJ_FILE).read_text(
        encoding="utf-8"
    )

    vertices, faces = parse_obj(obj_text)

    svg_text = obj_to_svg(
        vertices,
        faces
    )

    Path(SVG_FILE).write_text(
        svg_text,
        encoding="utf-8"
    )

    print(f"saved {SVG_FILE}")


if __name__ == "__main__":
    main()