from pathlib import Path
import math

OBJ_FILE = "flyer.obj"
OUT_FILE = "model.html"

SCALE = 100.0


def sub(a, b):
    return (
        a[0] - b[0],
        a[1] - b[1],
        a[2] - b[2],
    )


def dot(a, b):
    return (
        a[0] * b[0]
        + a[1] * b[1]
        + a[2] * b[2]
    )


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length(v):
    return math.sqrt(dot(v, v))


def normalize(v):
    l = length(v)

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

            vertices.append(
                (
                    float(x),
                    float(y),
                    float(z),
                )
            )

        elif line.startswith("f "):
            face = []

            for token in line.split()[1:]:
                face.append(
                    int(token.split("/")[0]) - 1
                )

            if len(face) >= 3:
                faces.append(face)

    return vertices, faces


def build_basis(points):
    p0 = points[0]

    ux = normalize(
        sub(points[1], p0)
    )

    nz = normalize(
        cross(
            sub(points[1], p0),
            sub(points[2], p0),
        )
    )

    vy = cross(nz, ux)

    return p0, ux, vy, nz


def project(points, origin, ux, vy):
    result = []

    for p in points:
        d = sub(p, origin)

        result.append(
            (
                dot(d, ux) * SCALE,
                dot(d, vy) * SCALE,
            )
        )

    return result


def matrix3d(origin, ux, vy, nz):
    ox = origin[0] * SCALE
    oy = -origin[1] * SCALE
    oz = origin[2] * SCALE

    return ",".join(
        f"{v:.12g}"
        for v in (
            ux[0], -ux[1], ux[2], 0,
            vy[0], -vy[1], vy[2], 0,
            nz[0], -nz[1], nz[2], 0,
            ox, oy, oz, 1,
        )
    )


def build_face(points3d, idx):
    origin, ux, vy, nz = build_basis(points3d)

    local = project(
        points3d,
        origin,
        ux,
        vy,
    )

    min_x = min(x for x, _ in local)
    max_x = max(x for x, _ in local)

    min_y = min(y for _, y in local)
    max_y = max(y for _, y in local)

    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)

    clip_points = [
        (
            x - min_x,
            y - min_y,
        )
        for x, y in local
    ]

    corrected_origin = (
        origin[0]
        + ux[0] * (min_x / SCALE)
        + vy[0] * (min_y / SCALE),

        origin[1]
        + ux[1] * (min_x / SCALE)
        + vy[1] * (min_y / SCALE),

        origin[2]
        + ux[2] * (min_x / SCALE)
        + vy[2] * (min_y / SCALE),
    )

    clip = ",".join(
        f"{x:.6f}px {y:.6f}px"
        for x, y in clip_points
    )

    cls = f"f{idx}"

    css = (
        f".{cls}{{"
        f"width:{width:.6f}px;"
        f"height:{height:.6f}px;"
        f"clip-path:polygon({clip});"
        f"transform:matrix3d("
        f"{matrix3d(corrected_origin, ux, vy, nz)}"
        f");"
        f"}}\n"
    )

    html = f'<svg class="{cls}"></svg>\n'

    return css, html


def build_output(vertices, faces):
    css = [
        ".obj{position:relative;\n"
        "transform-style:preserve-3d;\n"
        "translate: 140px 140px;\n"
        "scale: 20%;\n"
        "transform: rotate3d(1, 0, 0, -40deg);\n"
        "}\n\n",

        ".obj>svg{\n"
        "position:absolute;\n"
        "left:0;\n"
        "top:0;\n"
        "transform-origin:0 0;\n"
        "transform-style:preserve-3d;\n"
        f"background:black;\n"
        "overflow:visible;\n"
        "}\n",
        ".obj>svg:is(:nth-child(17),:nth-child(18),:nth-child(48),:nth-child(49),:nth-child(59)) {\n"
        "background:#06d8 !important;\n"        
        "}",
    ]

    body = []

    for i, face in enumerate(faces):
        points = [vertices[j] for j in face]

        rule, element = build_face(
            points,
            i
        )

        css.append(rule)
        body.append(element)

    return (
        "<style>"
        + "".join(css)
        + "</style>"
        + '<div class="obj">\n'
        + "".join(body)
        + "\n</div>"
    )


def main():
    text = Path(OBJ_FILE).read_text(
        encoding="utf-8"
    )

    vertices, faces = parse_obj(text)

    output = build_output(
        vertices,
        faces
    )

    Path(OUT_FILE).write_text(
        output,
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()