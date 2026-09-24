
import os
import json
import re
import math
from fractions import Fraction
from json_repair import repair_json
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from parser.parser_common import extract_json_object, strip_code_fences
from solving.format_json import AgentOutputProcessor
from solving.utils import prepare_solver_payload
from solving.math_tools import calculate_expression, solve_equations_tool, coordinate_geometry_tool, transformation_tool
from solving.config import aclient, openai_client
from itertools import permutations

def is_bm_language(language):
    code = str(language or "english").lower().strip()
    return code in ["bm", "ms", "malay", "bahasa_melayu", "bahasa melayu"]


def get_language_label(language):
    return "Bahasa Melayu" if is_bm_language(language) else "English"


def t_lang(language, en, bm):
    return bm if is_bm_language(language) else en

def parse_gemma_json_output(text):
    raw = str(text or "").strip()

    print("RAW GEMMA RESPONSE:")
    print(repr(raw[:2000]))

    raw = re.sub(
        r"<thought>.*?</thought>\s*",
        "",
        raw,
        flags=re.DOTALL | re.IGNORECASE
    )

    raw = strip_code_fences(raw)

    try:
        raw = extract_json_object(raw)
    except Exception:
        pass

    raw = re.sub(r",\s*}", "}", raw)
    raw = re.sub(r",\s*]", "]", raw)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = repair_json(raw, return_objects=True)

    # Sometimes model returns a JSON string that contains JSON
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except json.JSONDecodeError:
            parsed = repair_json(parsed, return_objects=True)

    if not isinstance(parsed, dict):
        raise ValueError(f"Gemma output is not a JSON object. Parsed type: {type(parsed)}")

    return parsed

def shape_dimensions(vertices):
    if not vertices:
        return None

    xs = [coord[0] for coord in vertices.values()]
    ys = [coord[1] for coord in vertices.values()]

    width = max(xs) - min(xs)
    height = max(ys) - min(ys)

    if width <= 0 or height <= 0:
        return None

    return {
        "width": width,
        "height": height,
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
    }


def dimension_ratios_mismatch(dim1, dim2, tolerance=0.04):
    width_ratio = min(dim1["width"], dim2["width"]) / max(dim1["width"], dim2["width"])
    height_ratio = min(dim1["height"], dim2["height"]) / max(dim1["height"], dim2["height"])

    return abs(width_ratio - height_ratio) > tolerance, width_ratio, height_ratio


def boundary_points(vertices):
    """
    Points on the outer boundary are most likely to be misread
    when Gemma rounds half-grid coordinates.
    """
    if not vertices:
        return []

    xs = [coord[0] for coord in vertices.values()]
    ys = [coord[1] for coord in vertices.values()]

    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    labels = []

    for label, coord in vertices.items():
        x, y = coord

        if x in [min_x, max_x] or y in [min_y, max_y]:
            labels.append(label)

    return labels

def get_all_vertices_by_label(diagram_facts):
    """
    Flatten all shape vertices into:
    {
      "P": {"role": "object", "coord": [8, 5]},
      "A": {"role": "image", "coord": [-3, 3]}
    }
    """
    label_to_info = {}

    for shape in diagram_facts.get("shapes", []):
        role = str(shape.get("role_guess", "unknown")).lower()
        vertices = shape.get("vertices") or {}

        if not isinstance(vertices, dict):
            continue

        for label, coord in vertices.items():
            label_to_info[str(label)] = {
                "role": role,
                "coord": coord
            }

    return label_to_info


def get_shape_vertices(shape):
    vertices = shape.get("vertices") or {}

    if not isinstance(vertices, dict):
        return {}

    clean = {}

    for label, coord in vertices.items():
        if (
            isinstance(coord, list)
            and len(coord) == 2
            and isinstance(coord[0], (int, float))
            and isinstance(coord[1], (int, float))
        ):
            clean[str(label)] = [float(coord[0]), float(coord[1])]

    return clean


def shape_width(vertices):
    if not vertices:
        return None

    xs = [coord[0] for coord in vertices.values()]
    return max(xs) - min(xs)


def all_vertices_are_integers(vertices):
    if not vertices:
        return False

    for coord in vertices.values():
        x, y = coord
        if not float(x).is_integer() or not float(y).is_integer():
            return False

    return True


def ratio_close_to_common_spm_value(ratio, tolerance=0.04):
    """
    Common SPM scale ratios are usually simple:
    1/2, 2/3, 3/2, 2, etc.
    If Gemma gives a weird ratio like 3/5, it may have rounded half-grid points.
    """
    common_ratios = [
        1 / 3,
        1 / 2,
        2 / 3,
        3 / 4,
        1,
        4 / 3,
        3 / 2,
        2,
        3,
    ]

    return any(abs(ratio - common) <= tolerance for common in common_ratios)

def validate_transformation_coordinates(diagram_facts):
    """
    Decide whether Gemma's coordinates are reliable enough.

    Checks:
    1. Gemma ambiguous_points.
    2. Low confidence.
    3. Width ratio and height ratio mismatch.
    """
    uncertain_points = set()
    suggested_coordinates = {}
    reasons = []

    shapes = diagram_facts.get("shapes") or []
    ambiguous_points = diagram_facts.get("ambiguous_points") or []

    # 1. Use Gemma ambiguous points directly.
    for item in ambiguous_points:
        if isinstance(item, str):
            uncertain_points.add(item)

    clean_shapes = []

    # 2. Store coordinates and check confidence.
    for shape in shapes:
        vertices = get_shape_vertices(shape)
        shape_label = shape.get("shape_label", "")

        try:
            confidence = float(shape.get("confidence", 1.0))
        except Exception:
            confidence = 1.0

        if confidence < 0.75:
            uncertain_points.update(vertices.keys())
            reasons.append(f"Low confidence for shape {shape_label}.")

        for label, coord in vertices.items():
            suggested_coordinates[label] = f"({coord[0]:g}, {coord[1]:g})"

        dimensions = shape_dimensions(vertices)

        if vertices and dimensions:
            clean_shapes.append({
                "shape_label": shape_label,
                "vertices": vertices,
                "dimensions": dimensions,
            })

    try:
        overall_confidence = float(diagram_facts.get("overall_confidence", 1.0))
    except Exception:
        overall_confidence = 1.0

    if overall_confidence < 0.75:
        for item in clean_shapes:
            uncertain_points.update(item["vertices"].keys())
        reasons.append("Overall diagram coordinate confidence is low.")

    # 3. Critical check: width ratio and height ratio must match.
    if len(clean_shapes) >= 2:
        dim1 = clean_shapes[0]["dimensions"]
        dim2 = clean_shapes[1]["dimensions"]

        mismatch, width_ratio, height_ratio = dimension_ratios_mismatch(dim1, dim2)

        if mismatch:
            # IMPORTANT:
            # If Gemma's shape ratio is suspicious, do NOT ask only boundary points.
            # Ask all vertices from both shapes because interior/turning points like R or C
            # may also be wrongly rounded.
            uncertain_points.update(clean_shapes[0]["vertices"].keys())
            uncertain_points.update(clean_shapes[1]["vertices"].keys())

            reasons.append(
                f"The extracted width ratio ({width_ratio:.4g}) and height ratio ({height_ratio:.4g}) do not match. "
                "Please confirm all vertices because some coordinates may have been rounded or misread from the graph."
            )

    if uncertain_points:
        return {
            "needs_user_coordinates": True,
            "uncertain_points": sorted(uncertain_points),
            "suggested_coordinates": suggested_coordinates,
            "reason": " ".join(reasons) or "Some coordinates are unclear from the graph."
        }

    return {
        "needs_user_coordinates": False,
        "uncertain_points": [],
        "suggested_coordinates": suggested_coordinates,
        "reason": ""
    }

def build_coordinate_input_from_uncertain_points(validation, diagram_facts):
    """
    Convert uncertain point labels into the frontend format:
    {
      object_points: [],
      image_points: [],
      other_required_points: [],
      suggested_coordinates: {}
    }
    """
    label_to_info = get_all_vertices_by_label(diagram_facts)

    object_points = []
    image_points = []
    other_required_points = []
    suggested_coordinates = {}

    for label in validation.get("uncertain_points", []):
        info = label_to_info.get(label, {})
        role = info.get("role", "unknown")
        coord = info.get("coord", "")

        if role == "object":
            object_points.append(label)
        elif role == "image":
            image_points.append(label)
        else:
            other_required_points.append(label)

        if isinstance(coord, list) and len(coord) == 2:
            suggested_coordinates[label] = f"({coord[0]}, {coord[1]})"
        else:
            suggested_coordinates[label] = ""

    return {
        "object_points": object_points,
        "image_points": image_points,
        "other_required_points": other_required_points,
        "suggested_coordinates": suggested_coordinates
    }


def merge_confirmed_coordinates(diagram_facts, confirmed_coordinates):
    """
    Override Gemma coordinates with user-confirmed coordinates.

    confirmed_coordinates format:
    {
      "P": {"x": 7.5, "y": 5},
      "Q": {"x": 4.5, "y": 5}
    }
    """
    if not confirmed_coordinates:
        return diagram_facts

    for shape in diagram_facts.get("shapes", []):
        vertices = shape.get("vertices") or {}

        for label, coord in confirmed_coordinates.items():
            if label not in vertices:
                continue

            if isinstance(coord, dict):
                x = coord.get("x")
                y = coord.get("y")
            elif isinstance(coord, list) and len(coord) == 2:
                x, y = coord
            else:
                continue

            try:
                vertices[label] = [float(x), float(y)]
            except Exception:
                continue

        shape["vertices"] = vertices

    diagram_facts["confirmed_coordinates_used"] = confirmed_coordinates
    diagram_facts["source"] = "gemma_with_user_confirmed_overrides"

    return diagram_facts


# ============================================================
# Deterministic SPM Transformation Engine
# ============================================================
EPS = 1e-6


def approx_equal(a, b, tol=EPS):
    return abs(float(a) - float(b)) <= tol


def clean_float(value):
    value = float(value)
    if abs(value) < EPS:
        return 0.0
    return value


def point_close(p1, p2, tol=EPS):
    return approx_equal(p1[0], p2[0], tol) and approx_equal(p1[1], p2[1], tol)


def shape_close(points_a, points_b, tol=EPS):
    if len(points_a) != len(points_b):
        return False

    for (_, p1), (_, p2) in zip(points_a, points_b):
        if not point_close(p1, p2, tol):
            return False

    return True


def format_number(value):
    value = clean_float(value)

    if float(value).is_integer():
        return str(int(value))

    frac = Fraction(value).limit_denominator(12)
    if abs(float(frac) - value) < 1e-6:
        if frac.denominator == 1:
            return str(frac.numerator)
        return f"\\frac{{{frac.numerator}}}{{{frac.denominator}}}"

    return str(round(value, 4))


def display_fraction(value):
    value = float(value)
    frac = Fraction(value).limit_denominator(12)

    if abs(float(frac) - value) < 1e-6:
        if frac.denominator == 1:
            return str(frac.numerator)
        return f"\\frac{{{frac.numerator}}}{{{frac.denominator}}}"

    return str(round(value, 4))


def format_point(point):
    return f"({format_number(point[0])}, {format_number(point[1])})"


def format_line_y_x_c(c):
    c = clean_float(c)
    if approx_equal(c, 0):
        return "y = x"
    if c > 0:
        return f"y = x + {format_number(c)}"
    return f"y = x - {format_number(abs(c))}"


def format_line_y_neg_x_c(c):
    c = clean_float(c)
    if approx_equal(c, 0):
        return "y = -x"
    if c > 0:
        return f"y = -x + {format_number(c)}"
    return f"y = -x - {format_number(abs(c))}"


def normalise_angle(angle):
    angle = int(angle) % 360
    if angle == 270:
        return -90
    return angle


def get_ordered_shape_points(shape):
    """
    Return ordered labelled points from a shape JSON object.
    Example: [("P", [7.5, 5.0]), ("Q", [4.5, 5.0])]
    """
    if not isinstance(shape, dict):
        return []

    vertices = shape.get("vertices") or {}
    labels = shape.get("vertex_labels") or list(vertices.keys())
    ordered = []

    for label in labels:
        coord = vertices.get(label)
        if (
            isinstance(coord, list)
            and len(coord) == 2
            and isinstance(coord[0], (int, float))
            and isinstance(coord[1], (int, float))
        ):
            ordered.append((str(label), [float(coord[0]), float(coord[1])]))

    return ordered


def extract_object_and_image_shapes(diagram_facts):
    object_shape = None
    image_shape = None
    shapes = diagram_facts.get("shapes") or []

    for shape in shapes:
        role = str(shape.get("role_guess", "")).lower()
        if role == "object":
            object_shape = shape
        elif role == "image":
            image_shape = shape

    if object_shape is None and len(shapes) >= 1:
        object_shape = shapes[0]

    if image_shape is None and len(shapes) >= 2:
        image_shape = shapes[1]

    return object_shape, image_shape


def is_unlabelled_shape_question(diagram_facts):
    input_mode = str(diagram_facts.get("input_mode", "")).lower()
    if "unlabelled" in input_mode:
        return True

    # Whole-shape labels like K/L often use generated labels K1, K2...
    for shape in diagram_facts.get("shapes", []):
        shape_label = str(shape.get("shape_label", ""))
        labels = shape.get("vertex_labels") or []
        if shape_label and labels and all(str(label).startswith(shape_label) for label in labels):
            return True

    return False


def rotate_list(items, shift):
    return items[shift:] + items[:shift]

def generate_image_point_order_variants(image_points, allow_reorder=False):
    """
    For labelled shapes like ABCD, preserve the given order.
    For whole-shape labels like P, Q, R with generated P1/P2/P3 labels,
    try all possible point correspondences because users may enter vertices
    in a different order.
    """
    if not allow_reorder:
        return [image_points]

    n = len(image_points)

    # Safe for SPM polygons: 4! = 24, 5! = 120, 6! = 720
    if n <= 6:
        return [list(p) for p in permutations(image_points)]

    return [image_points]
def shape_uses_generated_labels(shape):
    shape_label = str(shape.get("shape_label", "")).strip()
    labels = shape.get("vertex_labels") or []

    if not shape_label or not labels:
        return False

    return all(str(label).startswith(shape_label) for label in labels)
def transformation_preference_score(result):
    """
    Lower score = better SPM-style answer.
    Used when unlabelled shapes allow more than one valid mapping.
    """

    kind = result.get("kind")
    params = result.get("params", {})

    if kind == "reflection_vertical":
        line_x = float(params.get("line_x", 999))
        score = 0

        # y-axis reflection is very common and should be preferred.
        if approx_equal(line_x, 0):
            score -= 20

        if float(line_x).is_integer():
            score -= 5

        return score

    if kind == "reflection_horizontal":
        line_y = float(params.get("line_y", 999))
        score = 2

        if approx_equal(line_y, 0):
            score -= 15

        if float(line_y).is_integer():
            score -= 5

        return score

    if kind == "reflection_y_equals_x":
        c = float(params.get("c", 0))
        score = 6

        if approx_equal(c, 0):
            score -= 5

        return score

    if kind == "reflection_y_equals_negative_x":
        c = float(params.get("c", 0))
        score = 7

        if approx_equal(c, 0):
            score -= 5

        return score

    if kind == "translation":
        return 12

    if kind == "rotation":
        centre = params.get("centre", [999, 999])
        angle = int(params.get("angle", 0)) % 360

        score = 20

        # Prefer 90° rotations over strange 180° alternatives
        # created only because of vertex reordering.
        if angle in [90, 270]:
            score -= 6
        elif angle == 180:
            score += 4

        # Integer centre is better than half-grid centre.
        if (
            isinstance(centre, list)
            and len(centre) == 2
            and float(centre[0]).is_integer()
            and float(centre[1]).is_integer()
        ):
            score -= 5
        else:
            score += 5

        return score

    if kind == "enlargement":
        return 30

    return 99


def detect_single_transformation_with_reorder(object_shape, image_shape):
    object_points = get_ordered_shape_points(object_shape)
    image_points = get_ordered_shape_points(image_shape)

    allow_reorder = (
        shape_uses_generated_labels(object_shape)
        or shape_uses_generated_labels(image_shape)
    )

    candidates = []

    for image_variant in generate_image_point_order_variants(
        image_points,
        allow_reorder=allow_reorder
    ):
        result = detect_single_transformation(object_points, image_variant)

        if result and result.get("solved"):
            result = dict(result)
            result["image_order_used"] = [
                label for label, _point in image_variant
            ]
            result["preference_score"] = transformation_preference_score(result)
            candidates.append(result)

    if candidates:
        candidates.sort(key=lambda item: item.get("preference_score", 999))

        print("🔎 VALID TRANSFORMATION CANDIDATES:")
        for item in candidates[:10]:
            print(
                item.get("kind"),
                item.get("params"),
                "score=",
                item.get("preference_score"),
                "order=",
                item.get("image_order_used")
            )

        return candidates[0]

    return {
        "solved": False,
        "type": "single",
        "reason": "No supported single transformation matched all vertices under any valid point order."
    }
# ============================================================
# Primitive transformation application
# ============================================================

def apply_translation_to_point(point, vector):
    return [point[0] + vector[0], point[1] + vector[1]]


def apply_reflection_vertical_to_point(point, line_x):
    x, y = point
    return [2 * line_x - x, y]


def apply_reflection_horizontal_to_point(point, line_y):
    x, y = point
    return [x, 2 * line_y - y]


def apply_reflection_y_equals_x_to_point(point, c=0):
    # Reflection in y = x + c: (x, y) -> (y - c, x + c)
    x, y = point
    return [y - c, x + c]


def apply_reflection_y_equals_negative_x_to_point(point, c=0):
    # Reflection in y = -x + c, or x + y = c: (x, y) -> (c - y, c - x)
    x, y = point
    return [c - y, c - x]


def apply_rotation_to_point(point, centre, angle_degrees):
    x, y = point
    cx, cy = centre
    angle = int(angle_degrees) % 360

    dx = x - cx
    dy = y - cy

    if angle == 90:
        return [cx - dy, cy + dx]
    if angle == 180:
        return [cx - dx, cy - dy]
    if angle == 270:
        return [cx + dy, cy - dx]

    raise ValueError(f"Unsupported SPM rotation angle: {angle_degrees}")


def apply_enlargement_to_point(point, centre, scale):
    x, y = point
    cx, cy = centre
    return [cx + scale * (x - cx), cy + scale * (y - cy)]


def apply_transform_to_shape(shape_points, transform):
    kind = transform["kind"]
    params = transform["params"]
    transformed = []

    for label, point in shape_points:
        if kind == "translation":
            new_point = apply_translation_to_point(point, params["vector"])
        elif kind == "reflection_vertical":
            new_point = apply_reflection_vertical_to_point(point, params["line_x"])
        elif kind == "reflection_horizontal":
            new_point = apply_reflection_horizontal_to_point(point, params["line_y"])
        elif kind == "reflection_y_equals_x":
            new_point = apply_reflection_y_equals_x_to_point(point, params.get("c", 0))
        elif kind == "reflection_y_equals_negative_x":
            new_point = apply_reflection_y_equals_negative_x_to_point(point, params.get("c", 0))
        elif kind == "rotation":
            new_point = apply_rotation_to_point(point, params["centre"], params["angle"])
        elif kind == "enlargement":
            new_point = apply_enlargement_to_point(point, params["centre"], params["scale"])
        else:
            raise ValueError(f"Unsupported transform kind: {kind}")

        transformed.append((label, [clean_float(new_point[0]), clean_float(new_point[1])]))

    return transformed


# ============================================================
# Primitive transformation detection
# ============================================================

def detect_translation(object_points, image_points):
    if len(object_points) != len(image_points) or not object_points:
        return None

    vector = [
        image_points[0][1][0] - object_points[0][1][0],
        image_points[0][1][1] - object_points[0][1][1],
    ]

    transformed = apply_transform_to_shape(
        object_points,
        {"kind": "translation", "params": {"vector": vector}}
    )

    if not shape_close(transformed, image_points):
        return None

    return {
        "solved": True,
        "type": "single",
        "kind": "translation",
        "params": {"vector": [clean_float(vector[0]), clean_float(vector[1])]},
    }


def detect_reflection_vertical(object_points, image_points):
    if len(object_points) != len(image_points) or not object_points:
        return None

    line_candidates = []

    for (_, p), (_, q) in zip(object_points, image_points):
        if not approx_equal(p[1], q[1]):
            return None
        line_candidates.append((p[0] + q[0]) / 2)

    if max(line_candidates) - min(line_candidates) > EPS:
        return None

    line_x = clean_float(line_candidates[0])

    return {
        "solved": True,
        "type": "single",
        "kind": "reflection_vertical",
        "params": {"line_x": line_x},
    }


def detect_reflection_horizontal(object_points, image_points):
    if len(object_points) != len(image_points) or not object_points:
        return None

    line_candidates = []

    for (_, p), (_, q) in zip(object_points, image_points):
        if not approx_equal(p[0], q[0]):
            return None
        line_candidates.append((p[1] + q[1]) / 2)

    if max(line_candidates) - min(line_candidates) > EPS:
        return None

    line_y = clean_float(line_candidates[0])

    return {
        "solved": True,
        "type": "single",
        "kind": "reflection_horizontal",
        "params": {"line_y": line_y},
    }


def detect_reflection_y_equals_x(object_points, image_points):
    """
    Detect reflection in y = x + c. Includes y = x when c = 0.
    """
    if len(object_points) != len(image_points) or not object_points:
        return None

    c_values = []

    for (_, p), (_, q) in zip(object_points, image_points):
        x, y = p
        xp, yp = q
        c1 = yp - x
        c2 = y - xp

        if not approx_equal(c1, c2):
            return None
        c_values.append(c1)

    if max(c_values) - min(c_values) > EPS:
        return None

    c = clean_float(c_values[0])

    return {
        "solved": True,
        "type": "single",
        "kind": "reflection_y_equals_x",
        "params": {"c": c},
    }


def detect_reflection_y_equals_negative_x(object_points, image_points):
    """
    Detect reflection in y = -x + c. Includes y = -x when c = 0.
    """
    if len(object_points) != len(image_points) or not object_points:
        return None

    c_values = []

    for (_, p), (_, q) in zip(object_points, image_points):
        x, y = p
        xp, yp = q
        c1 = xp + y
        c2 = yp + x

        if not approx_equal(c1, c2):
            return None
        c_values.append(c1)

    if max(c_values) - min(c_values) > EPS:
        return None

    c = clean_float(c_values[0])

    return {
        "solved": True,
        "type": "single",
        "kind": "reflection_y_equals_negative_x",
        "params": {"c": c},
    }


def solve_2x2(a, b, c, d, e, f):
    det = a * d - b * c
    if abs(det) < EPS:
        return None

    x = (e * d - b * f) / det
    y = (a * f - e * c) / det
    return [clean_float(x), clean_float(y)]


def detect_rotation(object_points, image_points):
    if len(object_points) != len(image_points) or len(object_points) < 2:
        return None

    for angle in [90, 180, 270]:
        centres = []

        for (_, p), (_, q) in zip(object_points, image_points):
            x, y = p
            xp, yp = q

            if angle == 90:
                # q = (cx - (y-cy), cy + (x-cx))
                # xp = cx + cy - y ; yp = cy + x - cx
                centre = solve_2x2(1, 1, -1, 1, xp + y, yp - x)
            elif angle == 180:
                # centre is midpoint of p and q
                centre = [(x + xp) / 2, (y + yp) / 2]
            else:  # 270
                # xp = cx + y - cy ; yp = cy - x + cx
                centre = solve_2x2(1, -1, 1, 1, xp - y, yp + x)

            if centre is None:
                centres = []
                break

            centres.append([clean_float(centre[0]), clean_float(centre[1])])

        if not centres:
            continue

        first = centres[0]
        if not all(point_close(centre, first) for centre in centres):
            continue

        transform = {
            "kind": "rotation",
            "params": {"centre": first, "angle": angle}
        }
        transformed = apply_transform_to_shape(object_points, transform)

        if shape_close(transformed, image_points):
            return {
                "solved": True,
                "type": "single",
                "kind": "rotation",
                "params": {"centre": first, "angle": angle},
            }

    return None


def detect_enlargement(object_points, image_points):
    if len(object_points) != len(image_points) or len(object_points) < 2:
        return None

    scale_candidates = []

    for i in range(len(object_points)):
        for j in range(i + 1, len(object_points)):
            p1 = object_points[i][1]
            p2 = object_points[j][1]
            q1 = image_points[i][1]
            q2 = image_points[j][1]

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            qdx = q2[0] - q1[0]
            qdy = q2[1] - q1[1]

            if abs(dx) > EPS:
                scale_candidates.append(qdx / dx)
            if abs(dy) > EPS:
                scale_candidates.append(qdy / dy)

    if not scale_candidates:
        return None

    scale = scale_candidates[0]

    for candidate in scale_candidates:
        if not approx_equal(candidate, scale):
            return None

    if approx_equal(scale, 1):
        return None

    centres = []

    for (_, p), (_, q) in zip(object_points, image_points):
        cx = (q[0] - scale * p[0]) / (1 - scale)
        cy = (q[1] - scale * p[1]) / (1 - scale)
        centres.append([clean_float(cx), clean_float(cy)])

    first_centre = centres[0]

    if not all(point_close(centre, first_centre) for centre in centres):
        return None

    transform = {
        "kind": "enlargement",
        "params": {"centre": first_centre, "scale": clean_float(scale)}
    }
    transformed = apply_transform_to_shape(object_points, transform)

    if not shape_close(transformed, image_points):
        return None

    centre_label = find_label_for_point(object_points + image_points, first_centre)

    return {
        "solved": True,
        "type": "single",
        "kind": "enlargement",
        "params": {
            "centre": first_centre,
            "centre_label": centre_label,
            "scale": clean_float(scale),
        },
    }


def detect_single_transformation(object_points, image_points):
    detectors = [
        detect_translation,
        detect_reflection_vertical,
        detect_reflection_horizontal,
        detect_reflection_y_equals_x,
        detect_reflection_y_equals_negative_x,
        detect_rotation,
        detect_enlargement,
    ]

    for detector in detectors:
        result = detector(object_points, image_points)
        if result:
            result["solved"] = True
            result["type"] = "single"
            return result

    return {
        "solved": False,
        "type": "single",
        "reason": "No supported single transformation matched all vertices."
    }


# ============================================================
# Candidate generation for combined transformations
# ============================================================

def find_label_for_point(labelled_points, target_point):
    for label, point in labelled_points:
        if point_close(point, target_point):
            return label
    return None


def get_candidate_centres(object_points, image_points):
    centres = []

    for label, point in object_points + image_points:
        centres.append({"label": label, "point": point, "source": "vertex"})

    centres.append({"label": "O", "point": [0.0, 0.0], "source": "origin"})

    for (label_a, point_a), (label_b, point_b) in zip(object_points, image_points):
        midpoint = [(point_a[0] + point_b[0]) / 2, (point_a[1] + point_b[1]) / 2]
        centres.append({"label": f"midpoint_{label_a}{label_b}", "point": midpoint, "source": "midpoint"})

    unique = []
    seen = set()
    for centre in centres:
        key = (round(centre["point"][0], 6), round(centre["point"][1], 6))
        if key not in seen:
            unique.append(centre)
            seen.add(key)

    return unique


def common_scale_factors():
    return [
        Fraction(1, 3), Fraction(1, 2), Fraction(2, 3), Fraction(3, 4),
        Fraction(4, 3), Fraction(3, 2), Fraction(2, 1), Fraction(3, 1),
        Fraction(-1, 1), Fraction(-1, 2), Fraction(-2, 3), Fraction(-3, 2), Fraction(-2, 1),
    ]


def generate_grid_line_values(object_points, image_points):
    all_points = [point for _label, point in object_points + image_points]
    xs = [point[0] for point in all_points]
    ys = [point[1] for point in all_points]

    min_x = math.floor(min(xs)) - 3
    max_x = math.ceil(max(xs)) + 3
    min_y = math.floor(min(ys)) - 3
    max_y = math.ceil(max(ys)) + 3

    x_lines = []
    y_lines = []

    current = min_x
    while current <= max_x:
        x_lines.append(float(current))
        x_lines.append(float(current) + 0.5)
        current += 1

    current = min_y
    while current <= max_y:
        y_lines.append(float(current))
        y_lines.append(float(current) + 0.5)
        current += 1

    return sorted(set(x_lines)), sorted(set(y_lines))


def generate_diagonal_c_values(object_points, image_points):
    c_pos = set()
    c_neg = set()

    for _label, point in object_points + image_points:
        x, y = point
        c_pos.add(round(y - x, 6))
        c_neg.add(round(x + y, 6))

    return sorted(c_pos), sorted(c_neg)


def make_transform(kind, params):
    return {"kind": kind, "params": params}


def generate_first_transform_candidates(object_points, image_points):
    candidates = []
    centres = get_candidate_centres(object_points, image_points)

    # Enlargements
    for centre_item in centres:
        centre = centre_item["point"]
        centre_label = centre_item["label"]

        for scale_frac in common_scale_factors():
            scale = float(scale_frac)
            if approx_equal(scale, 1):
                continue
            candidates.append(make_transform("enlargement", {
                "centre": centre,
                "centre_label": centre_label,
                "scale": scale,
            }))

    # Reflections in grid lines
    x_lines, y_lines = generate_grid_line_values(object_points, image_points)

    for line_x in x_lines:
        candidates.append(make_transform("reflection_vertical", {"line_x": line_x}))

    for line_y in y_lines:
        candidates.append(make_transform("reflection_horizontal", {"line_y": line_y}))

    # Diagonal reflections y = x + c and y = -x + c
    c_pos, c_neg = generate_diagonal_c_values(object_points, image_points)

    for c in c_pos:
        candidates.append(make_transform("reflection_y_equals_x", {"c": c}))

    for c in c_neg:
        candidates.append(make_transform("reflection_y_equals_negative_x", {"c": c}))

    # Rotations
    for centre_item in centres:
        centre = centre_item["point"]
        centre_label = centre_item["label"]
        for angle in [90, 180, 270]:
            candidates.append(make_transform("rotation", {
                "centre": centre,
                "centre_label": centre_label,
                "angle": angle,
            }))

    # Translations using corresponding vectors
    for (_label_a, p), (_label_b, q) in zip(object_points, image_points):
        candidates.append(make_transform("translation", {"vector": [q[0] - p[0], q[1] - p[1]]}))

    return candidates


def transform_complexity_score(transform):
    kind = transform.get("kind")
    params = transform.get("params", {})
    score = 0

    if kind == "translation":
        score += 4
    elif kind in ["reflection_vertical", "reflection_horizontal"]:
        score += 1
        line_value = params.get("line_x", params.get("line_y", 0))
        if not float(line_value).is_integer():
            score += 1
    elif kind in ["reflection_y_equals_x", "reflection_y_equals_negative_x"]:
        score += 3
        if approx_equal(params.get("c", 0), 0):
            score -= 1
    elif kind == "rotation":
        score += 3
        if str(params.get("centre_label", "")).startswith("midpoint"):
            score += 2
    elif kind == "enlargement":
        score += 1
        if str(params.get("centre_label", "")).startswith("midpoint"):
            score += 3
        if abs(float(params.get("scale", 1))) in [0.5, 2 / 3, 1.5, 2.0]:
            score -= 1

    return score


def combined_result_score(first_transform, second_transform):
    score = transform_complexity_score(first_transform) + transform_complexity_score(second_transform)
    kinds = {first_transform.get("kind"), second_transform.get("kind")}

    if "enlargement" in kinds and any(kind.startswith("reflection") for kind in kinds):
        score -= 3

    return score


def detect_combined_transformation(object_points, image_points):
    """
    Search all two-step combinations from supported SPM transformations.
    object --first_transform--> intermediate --second_transform--> image
    """
    candidates = generate_first_transform_candidates(object_points, image_points)
    matches = []

    for first_transform in candidates:
        intermediate_points = apply_transform_to_shape(object_points, first_transform)
        second = detect_single_transformation(intermediate_points, image_points)

        if second and second.get("solved"):
            matches.append({
                "solved": True,
                "type": "combined",
                "first": first_transform,
                "second": second,
                "intermediate_points": intermediate_points,
                "score": combined_result_score(first_transform, second),
            })

    if not matches:
        return {
            "solved": False,
            "type": "combined",
            "reason": "No supported two-step transformation matched all vertices."
        }

    matches.sort(key=lambda item: item["score"])
    best = matches[0]
    best["alternatives_count"] = len(matches) - 1
    return best



def extract_combined_labels(interpreted=None, rag_data=None):
    """
    For combined transformation MN, N is first and M is second.
    Returns (first_label, second_label). Defaults to (N, M) for your current screenshot style.
    """
    text = json.dumps(interpreted or {}, ensure_ascii=False) + "\n" + str(rag_data or "")

    patterns = [
        r"combined transformations?\s+([A-Z]{2})",
        r"gabungan\s+([A-Z]{2})",
        r"transformation\s+([A-Z]{2})",
        r"transformations?\s+([A-Z]{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            code = match.group(1).upper()
            return code[1], code[0]

    # fallback used by common SPM wording: describe N and M
    return "N", "M"

def find_shape_by_label(diagram_facts, target_label):
    """
    Finds a shape from diagram_facts by shape_label.
    Example target_label: "P", "Q", "R", "PQRSTU", "ABCDEF"
    """
    if not target_label:
        return None

    target = str(target_label).strip().upper()

    for shape in diagram_facts.get("shapes", []):
        label = str(shape.get("shape_label", "")).strip().upper()

        if label == target:
            return shape

    return None


def text_says_combined_transformation(interpreted=None, rag_data=None, diagram_facts=None):
    """
    Decides whether the question expects a combined transformation.

    This prevents the engine from wrongly preferring a 2-step answer
    when the question is actually asking for one transformation only.
    """
    text_parts = []

    if interpreted:
        text_parts.append(str(interpreted))

    if rag_data:
        text_parts.append(str(rag_data))

    if diagram_facts:
        text_parts.append(str(diagram_facts.get("question_text", "")))
        text_parts.append(str(diagram_facts.get("reason", "")))

    text = " ".join(text_parts).lower()

    combined_keywords = [
        "combined transformation",
        "combined transformations",
        "gabungan transformasi",
        "gabungan penjelmaan",
        "transformasi gabungan",
        "penjelmaan gabungan",
        "under the combined transformation",
        "di bawah gabungan",
    ]

    return any(keyword in text for keyword in combined_keywords)


def solve_transformation_pair(
    object_shape,
    image_shape,
    prefer_combined=False,
    allow_combined=True
):
    """
    Solves one pair:
    object_shape -> image_shape

    Returns either:
    - single transformation result
    - combined transformation result
    - failed result
    """
    object_points = get_ordered_shape_points(object_shape)
    image_points = get_ordered_shape_points(image_shape)

    object_label = object_shape.get("shape_label", "object")
    image_label = image_shape.get("shape_label", "image")

    if len(object_points) != len(image_points):
        return {
            "solved": False,
            "reason": (
                f"Shape {object_label} has {len(object_points)} vertices but "
                f"shape {image_label} has {len(image_points)} vertices."
            ),
            "object_shape_label": object_label,
            "image_shape_label": image_label,
            "object_points": object_points,
            "image_points": image_points,
        }

    if len(object_points) < 2:
        return {
            "solved": False,
            "reason": f"Not enough vertices to solve {object_label} -> {image_label}.",
            "object_shape_label": object_label,
            "image_shape_label": image_label,
            "object_points": object_points,
            "image_points": image_points,
        }

    single_result = detect_single_transformation_with_reorder(
        object_shape,
        image_shape
    )

    combined_result = {
        "solved": False,
        "reason": "Combined transformation not checked."
    }

    if allow_combined:
        combined_result = detect_combined_transformation(object_points, image_points)

    # If the question clearly asks for combined transformation, prefer combined.
    if prefer_combined and combined_result.get("solved"):
        combined_result["object_shape_label"] = object_label
        combined_result["image_shape_label"] = image_label
        combined_result["object_points"] = object_points
        combined_result["image_points"] = image_points
        return combined_result

    # For ordinary pair questions like P -> Q under X, prefer single transformation.
    if single_result.get("solved"):
        single_result["object_shape_label"] = object_label
        single_result["image_shape_label"] = image_label
        single_result["object_points"] = object_points
        single_result["image_points"] = image_points
        return single_result

    # If no single transformation works, accept combined if it works.
    if combined_result.get("solved"):
        combined_result["object_shape_label"] = object_label
        combined_result["image_shape_label"] = image_label
        combined_result["object_points"] = object_points
        combined_result["image_points"] = image_points
        return combined_result

    return {
        "solved": False,
        "reason": (
            f"No supported single or combined transformation matched "
            f"{object_label} -> {image_label} exactly."
        ),
        "object_shape_label": object_label,
        "image_shape_label": image_label,
        "object_points": object_points,
        "image_points": image_points,
        "single_attempt": single_result,
        "combined_attempt": combined_result,
    }

def solve_combined_using_named_intermediate(diagram_facts):
    """
    Solves official SPM combined transformation when an intermediate shape is given.

    Example:
    PQRS --L--> ABCD --K--> EFGH

    This prevents the engine from choosing another mathematically valid
    2-step transformation that skips the labelled intermediate shape.
    """

    task_info = diagram_facts.get("combined_task") or {}

    if task_info.get("task_type") != "combined":
        return None

    object_label = task_info.get("object_shape")
    intermediate_label = task_info.get("intermediate_shape")
    image_label = task_info.get("image_shape")

    if not object_label or not intermediate_label or not image_label:
        return None

    object_shape = find_shape_by_label(diagram_facts, object_label)
    intermediate_shape = find_shape_by_label(diagram_facts, intermediate_label)
    image_shape = find_shape_by_label(diagram_facts, image_label)

    if not object_shape or not intermediate_shape or not image_shape:
        return {
            "solved": False,
            "type": "combined",
            "reason": (
                f"Could not find object/intermediate/image shapes: "
                f"{object_label}, {intermediate_label}, {image_label}."
            )
        }

    first_result = solve_transformation_pair(
        object_shape=object_shape,
        image_shape=intermediate_shape,
        prefer_combined=False,
        allow_combined=False
    )

    if not first_result.get("solved"):
        return {
            "solved": False,
            "type": "combined",
            "reason": (
                f"Could not verify first transformation "
                f"{object_label} -> {intermediate_label}."
            ),
            "first_attempt": first_result
        }

    second_result = solve_transformation_pair(
        object_shape=intermediate_shape,
        image_shape=image_shape,
        prefer_combined=False,
        allow_combined=False
    )

    if not second_result.get("solved"):
        return {
            "solved": False,
            "type": "combined",
            "reason": (
                f"Could not verify second transformation "
                f"{intermediate_label} -> {image_label}."
            ),
            "first": first_result,
            "second_attempt": second_result
        }

    first_result["transformation_label"] = task_info.get("first_transform_label", "")
    second_result["transformation_label"] = task_info.get("second_transform_label", "")

    return {
        "solved": True,
        "type": "combined",
        "first": first_result,
        "second": second_result,
        "object_shape_label": object_label,
        "intermediate_shape_label": intermediate_label,
        "image_shape_label": image_label,
        "object_points": get_ordered_shape_points(object_shape),
        "intermediate_points": get_ordered_shape_points(intermediate_shape),
        "image_points": get_ordered_shape_points(image_shape),
        "reason": (
            "Combined transformation was verified using the named intermediate shape."
        )
    }

def interpreted_question_asks_for_area(interpreted):
    """
    Returns True only if the actual extracted question asks for area/luas.
    This prevents the engine from adding a fake part (b) just because
    the RAG text or question number contains a number.
    """

    text_parts = []

    if isinstance(interpreted, dict):
        text_parts.append(str(interpreted.get("instructions_en", "")))
        text_parts.append(str(interpreted.get("instructions_ms", "")))
        text_parts.append(str(interpreted.get("introductory_instructions_en", "")))
        text_parts.append(str(interpreted.get("introductory_instructions_ms", "")))
        text_parts.append(str(interpreted.get("target", "")))

        subparts = interpreted.get("subpart_classification") or {}
        if isinstance(subparts, dict):
            for info in subparts.values():
                if isinstance(info, dict):
                    text_parts.append(str(info.get("instruction_en", "")))
                    text_parts.append(str(info.get("instruction_ms", "")))

    text = " ".join(text_parts).lower()

    area_keywords = [
        "area",
        "luas"
    ]

    action_keywords = [
        "calculate",
        "find",
        "determine",
        "hitung",
        "tentukan",
        "cari"
    ]

    return (
        any(keyword in text for keyword in area_keywords)
        and any(keyword in text for keyword in action_keywords)
    )

def solve_transformation_deterministically(diagram_facts, interpreted=None, rag_data=None):
    """
    Main deterministic transformation solver.

    Supports two modes:

    MODE 1: Multi-pair question
    Example:
        Q is the image of P under X.
        R is the image of Q under Y.

    diagram_facts should contain:
        "transformation_pairs": [
            {"object_shape": "P", "image_shape": "Q", "transformation_label": "X"},
            {"object_shape": "Q", "image_shape": "R", "transformation_label": "Y"}
        ]

    MODE 2: Ordinary object -> image question
    Example:
        ABCDEF is the image of PQRSTU under combined transformation MN.

    Uses object/image roles or falls back to first two shapes.

    Guarantee:
    - Returns solved=True only when every corresponding vertex maps exactly.
    - If no exact verified match is found, returns solved=False.
    """

    if not isinstance(diagram_facts, dict):
        return {
            "solved": False,
            "reason": "diagram_facts is not a dictionary."
        }

    prefer_combined = text_says_combined_transformation(
        interpreted=interpreted,
        rag_data=rag_data,
        diagram_facts=diagram_facts
    )
    named_intermediate_result = solve_combined_using_named_intermediate(diagram_facts)

    if named_intermediate_result is not None:
        return named_intermediate_result
    # ============================================================
    # MODE 1: Multi-pair transformation question
    # Example: P -> Q under X, Q -> R under Y
    # ============================================================

    transformation_pairs = diagram_facts.get("transformation_pairs") or []

    if transformation_pairs:
        pair_results = []

        for pair in transformation_pairs:
            object_label = (
                pair.get("object_shape")
                or pair.get("object")
                or pair.get("from")
                or pair.get("preimage")
            )

            image_label = (
                pair.get("image_shape")
                or pair.get("image")
                or pair.get("to")
                or pair.get("postimage")
            )

            transformation_label = (
                pair.get("transformation_label")
                or pair.get("label")
                or pair.get("transformation")
                or ""
            )

            object_shape = find_shape_by_label(diagram_facts, object_label)
            image_shape = find_shape_by_label(diagram_facts, image_label)

            if object_shape is None or image_shape is None:
                return {
                    "solved": False,
                    "type": "multi_pair",
                    "reason": (
                        f"Could not find shape pair {object_label} -> {image_label} "
                        f"for transformation {transformation_label}."
                    ),
                    "transformation_pairs": transformation_pairs
                }

            # For multi-pair SPM questions, each X/Y is usually a single transformation.
            # But allow combined fallback if no single transformation matches.
            result = solve_transformation_pair(
                object_shape=object_shape,
                image_shape=image_shape,
                prefer_combined=False,
                allow_combined=True
            )

            if not result.get("solved"):
                return {
                    "solved": False,
                    "type": "multi_pair",
                    "reason": (
                        f"Could not verify transformation {transformation_label}: "
                        f"{object_label} -> {image_label}."
                    ),
                    "failed_pair": {
                        "object_shape": object_label,
                        "image_shape": image_label,
                        "transformation_label": transformation_label,
                    },
                    "failed_result": result,
                    "partial_results": pair_results
                }

            result["transformation_label"] = transformation_label
            result["pair"] = {
                "object_shape": object_label,
                "image_shape": image_label,
                "transformation_label": transformation_label,
            }

            pair_results.append(result)

        return {
            "solved": True,
            "type": "multi_pair",
            "pairs": pair_results,
            "reason": "All transformation pairs were verified exactly."
        }

    # ============================================================
    # MODE 2: Single object -> image or combined object -> image
    # ============================================================

    object_shape, image_shape = extract_object_and_image_shapes(diagram_facts)

    if not object_shape or not image_shape:
        return {
            "solved": False,
            "reason": "Could not identify object and image shapes."
        }

    result = solve_transformation_pair(
        object_shape=object_shape,
        image_shape=image_shape,
        prefer_combined=prefer_combined,
        allow_combined=True
    )

    if result.get("solved"):
        single_task = diagram_facts.get("single_task") or {}

        if single_task.get("task_type") == "single":
            result["transformation_label"] = single_task.get("transformation_label", "")
            result["single_task"] = single_task

        return result

    return {
        "solved": False,
        "reason": result.get(
            "reason",
            "No supported single or combined transformation matched exactly."
        ),
        "attempt": result
    }


# ============================================================
# Engine output builder
# ============================================================
def transform_description(transform, language="english"):
    kind = transform.get("kind")
    params = transform.get("params", {})

    if kind == "translation":
        vector = params["vector"]
        return t_lang(
            language,
            f"Translation by vector \\(\\begin{{pmatrix}}{format_number(vector[0])}\\\\{format_number(vector[1])}\\end{{pmatrix}}\\)",
            f"Translasi oleh vektor \\(\\begin{{pmatrix}}{format_number(vector[0])}\\\\{format_number(vector[1])}\\end{{pmatrix}}\\)"
        )

    if kind == "reflection_vertical":
        line_x = params["line_x"]

        if approx_equal(line_x, 0):
            return t_lang(
                language,
                "Reflection in the y-axis \\((x = 0)\\)",
                "Pantulan pada paksi-y \\((x = 0)\\)"
            )

        return t_lang(
            language,
            f"Reflection in the line \\(x = {format_number(line_x)}\\)",
            f"Pantulan pada garis \\(x = {format_number(line_x)}\\)"
        )

    if kind == "reflection_horizontal":
        line_y = params["line_y"]

        if approx_equal(line_y, 0):
            return t_lang(
                language,
                "Reflection in the x-axis \\((y = 0)\\)",
                "Pantulan pada paksi-x \\((y = 0)\\)"
            )

        return t_lang(
            language,
            f"Reflection in the line \\(y = {format_number(line_y)}\\)",
            f"Pantulan pada garis \\(y = {format_number(line_y)}\\)"
        )

    if kind == "reflection_y_equals_x":
        line = format_line_y_x_c(params.get("c", 0))
        return t_lang(
            language,
            f"Reflection in the line \\({line}\\)",
            f"Pantulan pada garis \\({line}\\)"
        )

    if kind == "reflection_y_equals_negative_x":
        line = format_line_y_neg_x_c(params.get("c", 0))
        return t_lang(
            language,
            f"Reflection in the line \\({line}\\)",
            f"Pantulan pada garis \\({line}\\)"
        )

    if kind == "rotation":
        angle = int(params["angle"]) % 360
        centre = params["centre"]
        centre_label = params.get("centre_label")
        centre_text = (
            f"{centre_label}{format_point(centre)}"
            if centre_label and not str(centre_label).startswith("midpoint")
            else format_point(centre)
        )

        if angle == 90:
            direction_en = "90° anticlockwise"
            direction_bm = "90° lawan arah jam"
        elif angle == 270:
            direction_en = "90° clockwise"
            direction_bm = "90° ikut arah jam"
        else:
            direction_en = "180°"
            direction_bm = "180°"

        return t_lang(
            language,
            f"Rotation {direction_en} about centre \\({centre_text}\\)",
            f"Putaran {direction_bm} pada pusat \\({centre_text}\\)"
        )

    if kind == "enlargement":
        centre = params["centre"]
        centre_label = params.get("centre_label")
        centre_text = (
            f"{centre_label}{format_point(centre)}"
            if centre_label and not str(centre_label).startswith("midpoint")
            else format_point(centre)
        )

        return t_lang(
            language,
            f"Enlargement, centre \\({centre_text}\\), scale factor \\({display_fraction(params['scale'])}\\)",
            f"Pembesaran, pusat \\({centre_text}\\), faktor skala \\({display_fraction(params['scale'])}\\)"
        )

    return kind or "Transformation"

def transform_math(transform):
    kind = transform.get("kind")
    params = transform.get("params", {})

    if kind == "translation":
        vector = params["vector"]
        return f"\\begin{{pmatrix}}{format_number(vector[0])}\\\\{format_number(vector[1])}\\end{{pmatrix}}"

    if kind == "reflection_vertical":
        return f"x = {format_number(params['line_x'])}"

    if kind == "reflection_horizontal":
        return f"y = {format_number(params['line_y'])}"

    if kind == "reflection_y_equals_x":
        return format_line_y_x_c(params.get("c", 0))

    if kind == "reflection_y_equals_negative_x":
        return format_line_y_neg_x_c(params.get("c", 0))

    if kind == "rotation":
        angle = int(params["angle"]) % 360
        centre = params["centre"]
        if angle == 90:
            direction = "90^{\\circ}\\ anticlockwise"
        elif angle == 270:
            direction = "90^{\\circ}\\ clockwise"
        else:
            direction = "180^{\\circ}"
        return f"{direction},\\ centre={format_point(centre)}"

    if kind == "enlargement":
        return f"k = {display_fraction(params['scale'])},\\ centre={format_point(params['centre'])}"

    return ""


def get_enlargement_scale_from_engine_result(engine_result):
    if engine_result.get("type") == "single" and engine_result.get("kind") == "enlargement":
        return engine_result["params"]["scale"]

    if engine_result.get("type") == "combined":
        for key in ["first", "second"]:
            transform = engine_result.get(key) or {}
            if transform.get("kind") == "enlargement":
                return transform["params"]["scale"]

    return None


def extract_given_area(text):
    raw = str(text or "")
    patterns = [
        r"area[^0-9]{0,80}(\d+(?:\.\d+)?)",
        r"luas[^0-9]{0,80}(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:unit|cm|m)\s*(?:\^?2|²)",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))

    return None
def get_combined_answer_subpart_labels(interpreted, engine_result=None):
    """
    Decide which subpart labels should be used for a combined transformation answer.

    Important:
    If one subpart says "Describe transformations X and Y", both engine steps
    belong to the SAME subpart, usually "a".
    """

    if not isinstance(interpreted, dict):
        return "a", "a"

    subparts = interpreted.get("subpart_classification") or {}

    if not isinstance(subparts, dict):
        return "a", "a"

    first_label = ""
    second_label = ""

    if isinstance(engine_result, dict) and engine_result.get("type") == "combined":
        first_label = (
            engine_result.get("first", {}).get("transformation_label", "")
            or ""
        )
        second_label = (
            engine_result.get("second", {}).get("transformation_label", "")
            or ""
        )

    first_label = str(first_label).lower()
    second_label = str(second_label).lower()

    # Case like:
    # a: Describe the transformations of X and Y in detail.
    for key, info in subparts.items():
        if not isinstance(info, dict):
            continue

        text = (
            str(info.get("instruction_en", "")) + " " +
            str(info.get("instruction_ms", ""))
        ).lower()

        if first_label and second_label:
            if first_label in text and second_label in text:
                return key, key

        if "transformations of x and y" in text or "transformasi x dan y" in text:
            return key, key

    # Normal cases with explicit split labels.
    keys = list(subparts.keys())

    if "i" in keys and "ii" in keys:
        return "i", "ii"

    if "a(i)" in keys and "a(ii)" in keys:
        return "a(i)", "a(ii)"

    # If part a exists and no explicit a(i)/a(ii), keep both under a.
    if "a" in keys:
        return "a", "a"

    return keys[0], keys[0] if keys else ("a", "a")

def get_engine_transform_labels(engine_result, diagram_facts=None, interpreted=None, rag_data=None):
    """
    Use labels already attached to the verified engine result.

    Priority:
    1. engine_result first/second transformation_label
    2. diagram_facts combined_task first/second labels
    3. fallback text extraction only if both are missing
    """

    first_label = ""
    second_label = ""

    if isinstance(engine_result, dict):
        first_label = str(
            engine_result.get("first", {}).get("transformation_label", "") or ""
        ).strip()

        second_label = str(
            engine_result.get("second", {}).get("transformation_label", "") or ""
        ).strip()

    if (not first_label or not second_label) and isinstance(diagram_facts, dict):
        task_info = diagram_facts.get("combined_task") or {}

        first_label = first_label or str(
            task_info.get("first_transform_label", "") or ""
        ).strip()

        second_label = second_label or str(
            task_info.get("second_transform_label", "") or ""
        ).strip()

    if not first_label or not second_label:
        fallback_first, fallback_second = extract_combined_labels(interpreted, rag_data)
        first_label = first_label or fallback_first
        second_label = second_label or fallback_second

    return first_label, second_label

def get_single_answer_subpart_label(interpreted, engine_result=None, diagram_facts=None):
    """
    Find the actual subpart label for a single transformation answer.

    Example:
    (i) congruence
    (ii) describe transformation Q

    The engine answer should go to (ii), not hardcoded (a).
    """

    if not isinstance(interpreted, dict):
        return "a"

    subparts = interpreted.get("subpart_classification") or {}

    if not isinstance(subparts, dict):
        return "a"

    transform_label = ""

    if isinstance(engine_result, dict):
        transform_label = str(engine_result.get("transformation_label", "") or "").strip()

    if not transform_label and isinstance(diagram_facts, dict):
        single_task = diagram_facts.get("single_task") or {}
        transform_label = str(single_task.get("transformation_label", "") or "").strip()

    transform_label_lower = transform_label.lower()

    for key, info in subparts.items():
        if not isinstance(info, dict):
            continue

        text = (
            str(info.get("instruction_en", "")) + " " +
            str(info.get("instruction_ms", ""))
        ).lower()

        # Strong match: "transformation Q" / "transformasi Q"
        if transform_label_lower:
            if f"transformation {transform_label_lower}" in text:
                return key

            if f"transformasi {transform_label_lower}" in text:
                return key

            if f"penjelmaan {transform_label_lower}" in text:
                return key

        # Generic fallback for single transformation subpart
        if (
            "describe" in text
            and ("transformation" in text or "transformasi" in text or "penjelmaan" in text)
        ):
            return key

        if (
            "huraikan" in text
            and ("transformasi" in text or "penjelmaan" in text)
        ):
            return key

    # Common case: (i) congruence, (ii) transformation
    if "ii" in subparts:
        return "ii"

    if "b(ii)" in subparts:
        return "b(ii)"

    if "a(ii)" in subparts:
        return "a(ii)"

    if "a" in subparts:
        return "a"

    keys = list(subparts.keys())
    return keys[0] if keys else "a"

def build_engine_solution_json(engine_result, diagram_facts, interpreted=None, rag_data=None, language = "english"):
    object_coords = [f"{label}{format_point(point)}" for label, point in engine_result.get("object_points", [])]
    image_coords = [f"{label}{format_point(point)}" for label, point in engine_result.get("image_points", [])]
    intermediate_coords = [f"{label}'{format_point(point)}" for label, point in engine_result.get("intermediate_points", [])]
    if engine_result.get("type") == "multi_pair":
        steps = []
        final_answers = {}
        visual_pairs = []

        for pair_result in engine_result.get("pairs", []):
            transform_label = (
                pair_result.get("transformation_label")
                or pair_result.get("pair", {}).get("transformation_label")
                or ""
            )

            object_label = pair_result.get("object_shape_label", "object")
            image_label = pair_result.get("image_shape_label", "image")

            answer_text = transform_description(pair_result, language)

            object_coords_for_pair = [
                f"{label}{format_point(point)}"
                for label, point in pair_result.get("object_points", [])
            ]

            image_coords_for_pair = [
                f"{label}{format_point(point)}"
                for label, point in pair_result.get("image_points", [])
            ]

            visual_pairs.append({
                "transformation_label": transform_label,
                "object_shape": object_label,
                "image_shape": image_label,
                "object_coordinates": object_coords_for_pair,
                "image_coordinates": image_coords_for_pair,
                "answer": answer_text,
            })

            steps.append({
                "subpart": "a",
                "step": f"Describe transformation {transform_label}",
                "text": (
                    f"Transformation \\({transform_label}\\) maps shape "
                    f"\\({object_label}\\) to shape \\({image_label}\\). "
                    f"Therefore, transformation \\({transform_label}\\) is {answer_text}."
                ),
                "math": f"{transform_label}: {transform_math(pair_result)}",
            })

            final_answers[transform_label] = answer_text

        return {
            "rag_usage_audit": {
                "rag_strength": "engine",
                "used_rag": bool(rag_data),
                "reusable_method_found": "Solved using deterministic multi-pair transformation engine.",
                "special_condition_found": "Each transformation pair was verified separately using user-confirmed coordinates.",
                "values_copied_from_rag": False,
            },
            "visual_mapping": {
                "pairs": visual_pairs,
            },
            "calculation_scratchpad": [
                "The question contains multiple transformation pairs.",
                "Each pair was solved separately using the deterministic transformation engine.",
                "All transformed vertices were checked against the corresponding image shape.",
            ],
            "question_text": "Transformation question solved using verified coordinate facts.",
            "steps": steps,
            "final_answers": final_answers,
            "engine_verified": True,
        }
    if engine_result.get("type") == "single":
        answer_text = transform_description(engine_result, language)

        subpart_label = get_single_answer_subpart_label(
            interpreted=interpreted,
            engine_result=engine_result,
            diagram_facts=diagram_facts
        )

        transform_label = (
            engine_result.get("transformation_label")
            or (diagram_facts.get("single_task") or {}).get("transformation_label")
            or ""
        )

        step_title = (
            t_lang(language, f"Describe transformation {transform_label}", f"Huraikan transformasi {transform_label}")
            if transform_label
            else t_lang(language, "Identify transformation", "Kenal pasti transformasi")
        )

        text = (
            t_lang(
                language,
                f"Transformation \\({transform_label}\\) is {answer_text}.",
                f"Transformasi \\({transform_label}\\) ialah {answer_text}."
            )
            if transform_label
            else t_lang(
                language,
                f"The transformation is {answer_text}.",
                f"Transformasi tersebut ialah {answer_text}."
            )
        )

        math = (
            f"{transform_label}: {transform_math(engine_result)}"
            if transform_label
            else transform_math(engine_result)
        )

        return {
            "rag_usage_audit": {
                "rag_strength": "engine",
                "used_rag": bool(rag_data),
                "reusable_method_found": "Solved using deterministic coordinate transformation engine.",
                "special_condition_found": "All corresponding vertices were verified exactly.",
                "values_copied_from_rag": False,
            },
            "visual_mapping": {
                "object_coordinates": object_coords,
                "intermediate_coordinates": [],
                "image_coordinates": image_coords,
            },
            "calculation_scratchpad": [
                "A single supported SPM transformation maps every object vertex to its matching image vertex.",
                answer_text,
            ],
            "question_text": "Transformation question solved using verified coordinate facts.",
            "steps": [
                {
                    "subpart": subpart_label,
                    "step": step_title,
                    "text": text,
                    "math": math,
                }
            ],
            "final_answers": {
                subpart_label: answer_text,
            },
            "engine_verified": True,
        }

    if engine_result.get("type") == "combined":
        first = engine_result["first"]
        second = engine_result["second"]
        first_label, second_label = get_engine_transform_labels(
            engine_result=engine_result,
            diagram_facts=diagram_facts,
            interpreted=interpreted,
            rag_data=rag_data
        )

        first_text = transform_description(first, language)
        second_text = transform_description(second, language)
        first_subpart, second_subpart = get_combined_answer_subpart_labels(
            interpreted,
            engine_result
        )
        steps = [
            {
                "subpart": first_subpart,
                "step": t_lang(language, f"Describe transformation {first_label}", f"Huraikan transformasi {first_label}"),
                "text": t_lang(
                    language,
                    f"Transformation \\({first_label}\\) is {first_text}.",
                    f"Transformasi \\({first_label}\\) ialah {first_text}."
                ),
                "math": f"{first_label}: {transform_math(first)}",
            },
            {
                "subpart": second_subpart,
                "step": t_lang(language, f"Describe transformation {second_label}", f"Huraikan transformasi {second_label}"),
                "text": t_lang(
                    language,
                    f"Transformation \\({second_label}\\) is {second_text}.",
                    f"Transformasi \\({second_label}\\) ialah {second_text}."
                ),
                "math": f"{second_label}: {transform_math(second)}",
            },
        ]

        if first_subpart == second_subpart:
            final_answers = {
                first_subpart: (
                    f"{first_label}: {first_text}\n"
                    f"{second_label}: {second_text}"
                )
            }
        else:
            final_answers = {
                first_subpart: first_text,
                second_subpart: second_text,
            }

        scale = get_enlargement_scale_from_engine_result(engine_result)
        full_text = json.dumps(interpreted or {}, ensure_ascii=False) + "\n" + str(rag_data or "")
        given_area = extract_given_area(full_text)

        if scale and given_area and interpreted_question_asks_for_area(interpreted):
            original_area = given_area / (float(scale) ** 2)
            steps.extend([
                {
                    "subpart": "b",
                    "step": "Use area scale factor",
                    "text": f"The enlargement scale factor is \\({display_fraction(scale)}\\), so the area scale factor is \\(({display_fraction(scale)})^2\\).",
                    "math": f"{format_number(given_area)} = \\left({display_fraction(scale)}\\right)^2 \\times A",
                },
                {
                    "subpart": "b",
                    "step": "Find the original area",
                    "text": "Rearrange to find the area of the object.",
                    "math": f"A = {format_number(given_area)} \\div \\left({display_fraction(scale)}\\right)^2 = {format_number(original_area)}",
                },
            ])
            final_answers["b"] = format_number(original_area)

        return {
            "rag_usage_audit": {
                "rag_strength": "engine",
                "used_rag": bool(rag_data),
                "reusable_method_found": "Solved using deterministic combined-transformation engine.",
                "special_condition_found": f"For combined transformation, {first_label} is performed first, followed by {second_label}.",
                "values_copied_from_rag": False,
            },
            "visual_mapping": {
                "object_coordinates": object_coords,
                "intermediate_coordinates": intermediate_coords,
                "image_coordinates": image_coords,
            },
            "calculation_scratchpad": [
                f"First transformation: {first_text}",
                f"Second transformation: {second_text}",
                "Every transformed vertex was checked against the image coordinates.",
            ],
            "question_text": "Combined transformation question solved using verified coordinate facts.",
            "steps": steps,
            "final_answers": final_answers,
            "engine_verified": True,
        }

    return {
        "solved": False,
        "reason": engine_result.get("reason", "Engine could not solve."),
        "engine_verified": False,
    }

def get_answered_subparts(solution_json):
    answered = set()

    for step in solution_json.get("steps", []) or []:
        subpart = str(step.get("subpart", "")).strip()
        if subpart:
            answered.add(subpart)

    return answered


def get_remaining_subparts(interpreted, answered_subparts):
    subparts = interpreted.get("subpart_classification") or {}

    if not isinstance(subparts, dict):
        return {}

    remaining = {}

    for label, info in subparts.items():
        if label not in answered_subparts:
            remaining[label] = info

    return remaining

def interpret_transformation_diagram_with_gemma(image_base64, interpreted):
    """
    Uses Gemma/Gemini vision model only to extract diagram facts.
    It must not solve the question.
    """

    solver_payload = prepare_solver_payload(interpreted)

    system_prompt = r"""
    You are a diagram interpretation model for SPM Mathematics transformation questions.

    Your task is NOT to solve the question.

    Extract only the Cartesian plane information:
    - axis scale
    - visible shape labels
    - vertex labels
    - coordinates of vertices
    - whether vertices are labelled or unlabelled
    - ambiguous points

    Rules:
    - Do not identify the transformation type.
    - Do not calculate scale factor.
    - Do not calculate centre.
    - Do not solve the question.
    - If a whole shape is labelled K or L but vertices are not labelled, create ordered vertex names K1, K2, K3... in clockwise order.
    - Coordinates may be integers, decimals, or fractions.
    - Return valid JSON only.

    FOCUSED EXTRACTION RULE:
    - Extract only shapes directly mentioned in the transformation sentence.
    - If the question says "Q is the image of P under X" and "R is the image of Q under Y", extract only P, Q, and R.
    - Ignore other unlabelled or repeated shapes unless they are named in the question.
    - If a labelled point such as M is shown, extract it under "labelled_points".
    - Do not solve the transformation.
    - Do not explain your reasoning.
    - Return JSON only.

    COORDINATE CONFIDENCE MODE:
    - You are not asking the user directly.
    - Your job is to extract the best coordinates you can and identify uncertain points.
    - If a point may be on a half-grid position, add that point label to "ambiguous_points".
    - If you are unsure whether a point is 7.5 or 8, still output your best estimate, but add the point to "ambiguous_points".
    - Do not give confidence 1.0 if any point may be rounded or half-grid.

    DECIMAL / HALF-GRID COORDINATE RULE:
    - Do NOT force every vertex to be an integer coordinate.
    - Some vertices may lie halfway between two grid lines.
    - If a point is halfway between x = 7 and x = 8, output x = 7.5.
    - If a point is halfway between x = 4 and x = 5, output x = 4.5.
    - Use decimals such as 4.5, 7.5, -1.5 when needed.
    - Do NOT round 7.5 to 8 or 4.5 to 5.
    - Carefully compare each vertex position with nearby axis labels

    LEFT/RIGHT SHAPE CONSISTENCY RULE:
    - After extracting coordinates, check whether the relative side lengths of corresponding shapes are consistent.
    - If one shape is an enlargement/reduction of another, decimal coordinates may be required.
    - Do not snap a vertex to the nearest integer just because it is near a grid
      line.

    OUTPUT FORMAT RULES:
    - Return only one raw JSON object.
    - Do not wrap the JSON inside ```json.
    - Do not use Python dictionary syntax.
    - Do not use single quotes.
    - All property names and string values must use double quotes.
    - Do not return the JSON as a string.
    - Do not include explanation before or after the JSON.

    Required JSON:
    {
    "diagram_type": "cartesian_plane_transformations",
    "input_mode": "unlabelled_shape_vertices",
    "axis_scale": {
        "x_axis_step": 1,
        "y_axis_step": 1,
        "origin_visible": true
    },
    "transformation_pairs": [
        {
        "object_shape": "P",
        "image_shape": "Q",
        "transformation_label": "X"
        },
        {
        "object_shape": "Q",
        "image_shape": "R",
        "transformation_label": "Y"
        }
    ],
    "shapes": [
        {
        "shape_label": "P",
        "role_guess": "object",
        "vertex_labels": ["P1", "P2", "P3", "P4"],
        "vertices": {}
        },
        {
        "shape_label": "Q",
        "role_guess": "image_and_object",
        "vertex_labels": ["Q1", "Q2", "Q3", "Q4"],
        "vertices": {}
        },
        {
        "shape_label": "R",
        "role_guess": "image",
        "vertex_labels": ["R1", "R2", "R3", "R4"],
        "vertices": {}
        }
    ],
    "labelled_points": {
        "M": []
    },
    "ambiguous_points": [],
    "reason": ""
    }
    """

    user_prompt = f"""
    CURRENT QUESTION SUMMARY:
    {json.dumps(solver_payload, ensure_ascii=False, indent=2)}

    Extract the diagram facts only.
    """

    response = aclient.chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    text = response.choices[0].message.content.strip()

    return parse_gemma_json_output(text)
def request_transformation_coordinate_fields_with_llm_reader(image_base64, interpreted):
    """
    Uses LLM vision only to identify which coordinate fields the user must enter.
    It must NOT extract coordinate values and must NOT solve the question.
    """

    solver_payload = prepare_solver_payload(interpreted)

    system_prompt = r"""
You are a coordinate-field planner for SPM Mathematics transformation questions.

Your job is NOT to solve the question.
Your job is NOT to read or estimate exact coordinates.
Your job is ONLY to decide which coordinate fields the user must enter.

CRITICAL RULES:
- Do NOT calculate the transformation type.
- Do NOT calculate centre, scale factor, reflection line, rotation angle, or vector.
- Do NOT extract coordinate values from the image.
- Do NOT estimate coordinates.
- Do NOT solve the question.
- Identify only the relevant shapes and point labels needed for solving.

HOW TO IDENTIFY POINT LABELS:
1. If the shape has labelled vertices such as ABCD, EFGH, PQRS, ABCDEF, PQRSTU:
   - Use the individual letters as point labels.
   - Example: ABCD -> ["A", "B", "C", "D"].
   - Example: PQRSTU -> ["P", "Q", "R", "S", "T", "U"].

2. If a whole shape is labelled by one letter only, such as P, Q, R, K, L:
   - Create artificial vertex labels in clockwise order.
   - For quadrilateral P -> ["P1", "P2", "P3", "P4"].
   - For pentagon P -> ["P1", "P2", "P3", "P4", "P5"].
   - For hexagon P -> ["P1", "P2", "P3", "P4", "P5", "P6"].

3. Use the question wording to determine the number of sides:
   - quadrilateral / sisi empat -> 4
   - trapezium -> 4
   - pentagon / pentagon -> 5
   - hexagon / heksagon -> 6

CONGRUENCE + TRANSFORMATION RULE:
- If the question asks whether two shapes are congruent and also asks for a transformation between them,
  still output coordinate fields for both shapes.
- The congruence part will be solved later using the shape coordinates.
- If the question says "L is the image of K under transformation Q",
  then object_shape = "K", image_shape = "L", transformation_label = "Q".
- If the shapes are whole-shape labels only, such as K and L, create artificial vertex labels:
  K1, K2, K3, K4, K5, K6
  L1, L2, L3, L4, L5, L6
- For hexagon / heksagon, use 6 vertices.

TASK TYPES:
1. Single transformation:
   Example: "L is the image of K under transformation Q."
   Output task_type = "single".

2. Multi-pair transformation:
   Example: "Q is the image of P under transformation X while R is the image of Q under transformation Y."
   Output task_type = "multi_pair".
   transformation_pairs must contain:
   P -> Q under X
   Q -> R under Y

3. Combined transformation:
   Example: "ABCDEF is the image of PQRSTU under combined transformation MN."
   Output task_type = "combined".
   For combined transformation MN:
   - N is performed first.
   - M is performed second.
   Therefore:
   first_transform_label = "N"
   second_transform_label = "M"

   For KL:
   - L is performed first.
   - K is performed second.

   For JI:
   - I is performed first.
   - J is performed second.

IMPORTANT INTERMEDIATE SHAPE RULE:
- For combined transformation questions, if the diagram shows THREE labelled shapes and the question states:
  "final shape is the image of object shape under combined transformation KL/MN/JI",
  then the third labelled shape is usually the intermediate image.
- You MUST include this third shape in coordinate_input.shapes.
- Set its role_guess = "intermediate".
- Set task_info.intermediate_shape to that shape label.

Example:
"Diagram shows three trapeziums ABCD, EFGH and PQRS."
"EFGH is the image of PQRS under combined transformation KL."

Output:
object_shape = "PQRS"
intermediate_shape = "ABCD"
image_shape = "EFGH"

shapes must include:
PQRS, ABCD, EFGH
ROLE RULES:
- object_shape means the original shape.
- image_shape means the final image shape.
- intermediate_shape means a shape that appears between object and final image, if mentioned or visually labelled.
- In multi_pair, a middle shape can be both image and object, so use role_guess = "image_and_object".

Return raw JSON only.
Do not wrap in markdown.
Do not include explanation.

Required JSON:
{
  "needs_user_coordinates": true,
  "coordinate_input": {
    "mode": "all_vertices",
    "shapes": [
      {
        "shape_label": "",
        "point_labels": [],
        "role_guess": "object / image / image_and_object / intermediate / unknown"
      }
    ],
    "task_info": {
      "task_type": "single / combined / multi_pair / unknown",
      "object_shape": "",
      "image_shape": "",
      "intermediate_shape": "",
      "combined_code": "",
      "first_transform_label": "",
      "second_transform_label": "",
      "transformation_pairs": []
    },
    "suggested_coordinates": {}
  }
}
"""

    user_prompt = f"""
CURRENT QUESTION SUMMARY:
{json.dumps(solver_payload, ensure_ascii=False, indent=2)}

Look at the question image and identify only the coordinate fields needed for the user to fill in.

Do NOT extract coordinate values.
Do NOT solve the transformation.
"""

    response = openai_client.with_options(timeout=25).chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        temperature=0,
        max_tokens=1200,
        response_format={"type": "json_object"}
    )

    text = response.choices[0].message.content.strip()
    parsed = parse_gemma_json_output(text)

    coordinate_input = parsed.get("coordinate_input", {})

    if not coordinate_input.get("shapes"):
        coordinate_input = {
            "mode": "all_vertices",
            "shapes": [],
            "task_info": {
                "task_type": "unknown",
                "object_shape": "",
                "image_shape": "",
                "intermediate_shape": "",
                "combined_code": "",
                "first_transform_label": "",
                "second_transform_label": "",
                "transformation_pairs": []
            },
            "suggested_coordinates": {}
        }

    return {
        "needs_user_coordinates": True,
        "coordinate_input": coordinate_input
    }

def merge_engine_and_llm_solutions(engine_solution, remaining_solution):
    """
    Merge deterministic engine result with LLM result.
    Engine answers take priority.
    """

    if not isinstance(engine_solution, dict):
        return remaining_solution

    if not isinstance(remaining_solution, dict):
        return engine_solution

    merged = dict(engine_solution)

    engine_steps = merged.get("steps") or []
    llm_steps = remaining_solution.get("steps") or []

    engine_final = merged.get("final_answers") or {}
    llm_final = remaining_solution.get("final_answers") or {}

    merged["steps"] = engine_steps + llm_steps

    ordered_final = dict(engine_final)

    for key, value in llm_final.items():
        if key not in ordered_final:
            ordered_final[key] = value

    merged["final_answers"] = ordered_final
    merged["hybrid_solver_used"] = True

    return merged

def build_diagram_facts_from_coordinate_input(coordinate_input, confirmed_coordinates):
    shapes_template = coordinate_input.get("shapes", [])
    task_info = coordinate_input.get("task_info", {})

    shapes = []

    for shape in shapes_template:
        shape_label = shape.get("shape_label", "")
        point_labels = shape.get("point_labels", [])
        role_guess = shape.get("role_guess", "unknown")

        vertices = {}

        for point_label in point_labels:
            coord = confirmed_coordinates.get(point_label)

            if not coord:
                continue

            if isinstance(coord, dict):
                x = coord.get("x")
                y = coord.get("y")
            elif isinstance(coord, list) and len(coord) == 2:
                x, y = coord
            else:
                continue

            try:
                vertices[point_label] = [float(x), float(y)]
            except Exception:
                continue

        shapes.append({
            "shape_label": shape_label,
            "role_guess": role_guess,
            "vertex_labels": point_labels,
            "vertices": vertices,
            "confidence": 1.0
        })

    diagram_facts = {
        "diagram_type": "cartesian_plane_transformations",
        "input_mode": "manual_user_coordinates",
        "axis_scale": {
            "x_axis_step": 1,
            "y_axis_step": 1,
            "origin_visible": True
        },
        "shapes": shapes,
        "ambiguous_points": [],
        "confirmed_coordinates_used": confirmed_coordinates,
        "source": "manual_user_coordinates"
    }

    if task_info.get("task_type") == "single":
        diagram_facts["single_task"] = task_info

        object_shape = task_info.get("object_shape")
        image_shape = task_info.get("image_shape")

        for shape in diagram_facts["shapes"]:
            label = shape.get("shape_label")

            if label == object_shape:
                shape["role_guess"] = "object"
            elif label == image_shape:
                shape["role_guess"] = "image"
    if task_info.get("task_type") == "multi_pair":
        diagram_facts["transformation_pairs"] = task_info.get("transformation_pairs", [])

    if task_info.get("task_type") == "combined":
        diagram_facts["combined_task"] = task_info

        object_shape = task_info.get("object_shape")
        image_shape = task_info.get("image_shape")
        intermediate_shape = task_info.get("intermediate_shape")

        for shape in diagram_facts["shapes"]:
            label = shape.get("shape_label")

            if label == object_shape:
                shape["role_guess"] = "object"
            elif label == image_shape:
                shape["role_guess"] = "image"
            elif intermediate_shape and label == intermediate_shape:
                shape["role_guess"] = "intermediate"

    return diagram_facts
def solve_transformations(
    new_question_image_base64,
    interpreted,
    rag_data,
    confirmed_coordinates=None,
    coordinate_input=None,
    language="english"
):
    """Specialized solver for Transformations."""

    print("🦋 Transformation solver started.")

    # First call: ask user to fill coordinates.
    if not confirmed_coordinates:
        coordinate_request = request_transformation_coordinate_fields_with_llm_reader(
            new_question_image_base64,
            interpreted
        )

        return {
            "status": "needs_user_coordinates",
            "needs_user_coordinates": True,
            "result_type": "coordinate_confirmation",
            "question_text": "Transformation question needs exact coordinates",
            "reason": (
                "Please enter the coordinates for the required points. "
                "The AI will use them to solve the transformation exactly."
            ),
            "coordinate_input": coordinate_request.get("coordinate_input", {}),
            "pending_interpreted": interpreted,
            "steps": [],
            "final_answers": {}
        }

    # Second call: user already filled coordinates.
    if not coordinate_input:
        return {
            "status": "needs_user_coordinates",
            "needs_user_coordinates": True,
            "result_type": "coordinate_confirmation",
            "question_text": "Transformation coordinate structure missing",
            "reason": (
                "The coordinates were received, but coordinate_input was not sent back. "
                "Please make sure the frontend sends both confirmed_coordinates and coordinate_input."
            ),
            "coordinate_input": {},
            "pending_interpreted": interpreted,
            "steps": [],
            "final_answers": {}
        }

    print("✅ USER CONFIRMED COORDINATES RECEIVED:")
    print(json.dumps(confirmed_coordinates, ensure_ascii=False, indent=2))

    print("📌 COORDINATE INPUT STRUCTURE RECEIVED:")
    print(json.dumps(coordinate_input, ensure_ascii=False, indent=2))

    diagram_facts = build_diagram_facts_from_coordinate_input(
        coordinate_input=coordinate_input,
        confirmed_coordinates=confirmed_coordinates
    )

    print("📌 DIAGRAM FACTS BUILT FROM USER COORDINATES:")
    print(json.dumps(diagram_facts, ensure_ascii=False, indent=2))

    engine_result = solve_transformation_deterministically(
        diagram_facts,
        interpreted=interpreted,
        rag_data=rag_data
    )

    print("🧮 TRANSFORMATION ENGINE RESULT:")
    print(json.dumps(engine_result, ensure_ascii=False, indent=2, default=str))

    if engine_result.get("solved"):
        engine_solution = build_engine_solution_json(
            engine_result=engine_result,
            diagram_facts=diagram_facts,
            interpreted=interpreted,
            rag_data=rag_data,
            language=language
        )

        remaining_solution = solve_remaining_transformation_subparts_with_llm(
            image_base64=new_question_image_base64,
            interpreted=interpreted,
            rag_data=rag_data,
            diagram_facts=diagram_facts,
            engine_solution_json=engine_solution,
            language=language
        )

        return merge_engine_and_llm_solutions(
            engine_solution,
            remaining_solution
        )

    return {
        "status": "needs_user_coordinates",
        "needs_user_coordinates": True,
        "result_type": "coordinate_confirmation",
        "question_text": t_lang(
            language,
            "Transformation question needs exact coordinates",
            "Soalan transformasi memerlukan koordinat yang tepat"
        ),
        "reason": t_lang(
            language,
            "Please enter the coordinates for the required points. The AI will use them to solve the transformation exactly.",
            "Sila masukkan koordinat bagi titik yang diperlukan. AI akan menggunakan koordinat tersebut untuk menyelesaikan transformasi dengan tepat."
        ),
        "coordinate_input": coordinate_input,
        "pending_interpreted": interpreted,
        "steps": [],
        "final_answers": {},
        "engine_result": engine_result
    }

def solve_remaining_transformation_subparts_with_llm(
    image_base64,
    interpreted,
    rag_data,
    diagram_facts,
    engine_solution_json,
    language="english"
):
    language_label = get_language_label(language)

    language_rule = f"""
    RESPONSE LANGUAGE RULE:
    The selected response language is: {language_label}.

    If the selected response language is Bahasa Melayu:
    - Write all step titles, explanations, reasons, and final answer text in Bahasa Melayu.
    - Keep mathematical symbols, variables, coordinates, equations, and LaTeX unchanged.
    - Use SPM-style Malay terms where suitable.

    If the selected response language is English:
    - Write all step titles, explanations, reasons, and final answer text in English.
    - Keep mathematical symbols, variables, coordinates, equations, and LaTeX unchanged.
    """
    """
    Solves transformation subparts that are not handled by the deterministic engine.

    Examples:
    - congruence questions
    - point transformation questions
    - area questions
    - short justification questions

    It must not override engine-verified transformation answers.
    """

    system_prompt = language_rule + r"""
You are solving the remaining unsolved parts of an SPM Mathematics transformation question.

CRITICAL RULES:
- The deterministic engine has already solved the shape-to-shape transformation part.
- Do NOT change or override any engine-verified answer.
- Solve only the remaining subparts not already answered.
- You may solve:
  1. congruence questions
  2. point transformation questions
  3. area questions involving enlargement
  4. short justification questions

CONGRUENCE RULE:
- Two shapes are congruent if they have the same shape and same size.
- If one shape can be mapped to the other by reflection, rotation, or translation only, they are congruent.
- If enlargement with scale factor not equal to 1 is needed, they are not congruent.
- Give a short justification suitable for SPM.

COMBINED TRANSFORMATION ORDER:
- A combined transformation code is a sequence of capital letters.
- Always apply transformations from RIGHT to LEFT.
- For a two-letter code AB, apply B first, then A.
- For a three-letter code ABC, apply C first, then B, then A.
- Use ONLY the transformation letters that appear in that code.
- Do NOT apply any transformation letter that is not in the requested code.

TRANSFORMATION DEFINITION RULE:
- First, read the question and identify the definition of each transformation symbol.
- A symbol may represent:
  1. translation by a vector
  2. rotation with angle and centre
  3. reflection in a line
  4. enlargement with centre and scale factor
- Build the transformation meaning from the question text itself.
- Do not assume that a symbol always has the same meaning across questions.

POINT TRANSFORMATION RULE:
- If the question asks for the image of a point under a combined transformation:
  1. Start from the given point coordinate.
  2. Apply the rightmost transformation first.
  3. Continue leftwards until all letters in the code are applied.
  4. Show each intermediate coordinate.
- If the code contains only two letters, use exactly those two transformations.
- If a transformation symbol is defined in the question but is not inside the requested code, ignore it.

Return valid JSON only.

Required JSON:
{
  "steps": [
    {
      "subpart": "",
      "step": "",
      "text": "",
      "math": ""
    }
  ],
  "final_answers": {}
}
"""
    answered_subparts = get_answered_subparts(engine_solution_json)
    remaining_subparts = get_remaining_subparts(interpreted, answered_subparts)
    user_prompt = f"""
QUESTION DATA:
{json.dumps(interpreted or {}, ensure_ascii=False, indent=2)}

ONLY SOLVE THESE REMAINING SUBPARTS:
{json.dumps(remaining_subparts, ensure_ascii=False, indent=2)}

USER-CONFIRMED DIAGRAM FACTS:
{json.dumps(diagram_facts or {}, ensure_ascii=False, indent=2)}

ENGINE-VERIFIED SOLUTION:
{json.dumps(engine_solution_json or {}, ensure_ascii=False, indent=2, default=str)}

RAG CONTEXT:
{str(rag_data or "")}

Do NOT solve any subpart not listed in ONLY SOLVE THESE REMAINING SUBPARTS.
Do NOT describe transformations X and Y again.
Return JSON only.
"""

    response = openai_client.with_options(timeout=30).chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        temperature=0,
        max_tokens=1200,
        response_format={"type": "json_object"}
    )

    text = response.choices[0].message.content.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return repair_json(text, return_objects=True)
    