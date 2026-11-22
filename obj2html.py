from pathlib import Path
import math

OBJ_FILE = "flyer.obj"
HTML_FILE = "model.html"

SCALE = 100.0
FACE_CLASS_PREFIX = "f"


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
    return math.sqrt(vdot(v, v))


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
            face = []

            for token in line.split()[1:]:
                face.append(
                    int(token.split("/")[0]) - 1
                )

            if len(face) >= 3:
                faces.append(face)

    return vertices, faces


def build_frame(points):
    p0 = points[0]
    p1 = points[1]
    p2 = points[2]

    ux = vnorm(
        vsub(p1, p0)
    )

    nz = vnorm(
        vcross(
            vsub(p1, p0),
            vsub(p2, p0)
        )
    )

    vy = vcross(nz, ux)

    return p0, ux, vy, nz


def project(points, origin, ux, vy):
    result = []

    for p in points:
        d = vsub(p, origin)

        result.append((
            vdot(d, ux) * SCALE,
            vdot(d, vy) * SCALE
        ))

    return result


def matrix3d(origin, ux, vy, nz):
    ox = origin[0] * SCALE
    oy = -origin[1] * SCALE
    oz = origin[2] * SCALE

    values = [
        ux[0], -ux[1], ux[2], 0,
        vy[0], -vy[1], vy[2], 0,
        nz[0], -nz[1], nz[2], 0,
        ox, oy, oz, 1
    ]

    return ",".join(
        f"{v:.12g}"
        for v in values
    )


def is_y_symmetric(points, eps=1e-5):
    pts = [
        (round(x, 5), round(y, 5))
        for x, y in points
    ]

    s = set(pts)

    for x, y in pts:
        if (-x, y) not in s:
            return False

    return True


def make_face(points3d, index):
    origin, ux, vy, nz = build_frame(points3d)

    pts = project(
        points3d,
        origin,
        ux,
        vy
    )

    symmetric = is_y_symmetric(pts)

    if symmetric:
        max_x = max(abs(x) for x, _ in pts) or 1
        min_y = min(y for _, y in pts)
        max_y = max(y for _, y in pts)

        local = [
            (
                x / max_x * 50 + 50,
                (y - min_y) / max(max_y - min_y, 1e-9) * 100
            )
            for x, y in pts
        ]

        width = 2*max_x
        height = max(max_y - min_y, 1)

    else:
        min_x = min(x for x, _ in pts)
        max_x = max(x for x, _ in pts)

        min_y = min(y for _, y in pts)
        max_y = max(y for _, y in pts)

        width = max(max_x - min_x, 1)
        height = max(max_y - min_y, 1)

        local = [
            (
                (x - min_x) / width * 100,
                (y - min_y) / height * 100
            )
            for x, y in pts
        ]

    clip = ",".join(
        f"{x:.4f}% {y:.4f}%"
        for x, y in local
    )

    cls = f"{FACE_CLASS_PREFIX}{index}"

    css = (
        f".{cls}{{"
        f"width:{width:.6f}px;"
        f"height:{height:.6f}px;"
        f"clip-path:polygon({clip});"
        f"transform:matrix3d({matrix3d(origin, ux, vy, nz)});"
        f"}}"
    )

    html = f'<svg class="{cls}"></svg>'

    return css, html


def build_html(vertices, faces):
    css_rules = [
        ".obj{position:relative;"
        "transform-style:preserve-3d;"
        "translate: 200px 100px;"
        "scale: 20%;"
        "transform: rotate3d(1, 0, 0, -40deg);"
        "}",
        ".obj>svg{"
        "position:absolute;"
        "left:0;"
        "top:0;"
        "overflow:visible;"
        "transform-origin:0 0;"
        "background:currentColor;"
        "}",
        ".obj>svg:is(:nth-child(16),:nth-child(17),:nth-child(47),:nth-child(48),:nth-child(58)) {"
        "background:#06d8 !important;"        
        "}",
    ]

    elements = []

    for i, face in enumerate(faces):
        points3d = [
            vertices[idx]
            for idx in face
        ]

        css, html = make_face(
            points3d,
            i
        )

        css_rules.append(css)
        elements.append(html)

    return (
        "<style>"
        + "".join(css_rules)
        + "</style>"
        + '<div class="obj">'
        + "".join(elements)
        + "</div>"
    )


def main():
    vertices, faces = parse_obj(
        Path(OBJ_FILE).read_text(
            encoding="utf-8"
        )
    )

    html = build_html(
        vertices,
        faces
    )

    Path(HTML_FILE).write_text(
        html,
        encoding="utf-8"
    )

    print(f"saved {HTML_FILE}")


if __name__ == "__main__":
    main()