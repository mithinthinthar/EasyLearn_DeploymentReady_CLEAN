import json
import math
import heapq
from typing import Any, Dict, List, Optional
import numpy as np
from scipy.interpolate import CubicSpline
import sympy as sp
from langchain_core.tools import tool
import heapq

# =========================================================
# HELPERS
# =========================================================

def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _clean_expr(expr: Any) -> str:
    return str(expr).replace("^", "**")


def _to_sympy(value: Any):
    return sp.sympify(_clean_expr(value))


def _result(value: Any) -> Dict[str, Any]:
    value = sp.simplify(value)
    output = {
        "exact": str(value),
        "latex": sp.latex(value)
    }

    try:
        output["decimal"] = float(sp.N(value))
    except Exception:
        pass

    return output


def _matrix_to_latex(matrix: sp.Matrix) -> str:
    rows = []
    for row in matrix.tolist():
        rows.append(" & ".join(sp.latex(sp.simplify(x)) for x in row))
    return "\\begin{pmatrix} " + " \\\\ ".join(rows) + " \\end{pmatrix}"


def _point(p):
    if isinstance(p, dict):
        return float(p["x"]), float(p["y"])
    return float(p[0]), float(p[1])


def _parse_relation(equation: str, local_dict: dict):
    equation = _clean_expr(equation)

    if "<=" in equation:
        left, right = equation.split("<=", 1)
        return sp.Le(sp.sympify(left, locals=local_dict), sp.sympify(right, locals=local_dict))

    if ">=" in equation:
        left, right = equation.split(">=", 1)
        return sp.Ge(sp.sympify(left, locals=local_dict), sp.sympify(right, locals=local_dict))

    if "<" in equation:
        left, right = equation.split("<", 1)
        return sp.Lt(sp.sympify(left, locals=local_dict), sp.sympify(right, locals=local_dict))

    if ">" in equation:
        left, right = equation.split(">", 1)
        return sp.Gt(sp.sympify(left, locals=local_dict), sp.sympify(right, locals=local_dict))

    if "=" in equation:
        left, right = equation.split("=", 1)
        return sp.Eq(sp.sympify(left, locals=local_dict), sp.sympify(right, locals=local_dict))

    return sp.sympify(equation, locals=local_dict)


# =========================================================
# 1. GENERAL CALCULATION TOOL
# =========================================================

@tool
def calculate_expression(expression: str) -> str:
    """
    Calculate or simplify a mathematical expression.
    Use this for arithmetic, percentages, standard form, indices, fractions, roots, and direct substitution.
    Example: "3/5 + 2/7", "2.5*10**4", "sqrt(81)", "15/100 * 240"
    """
    try:
        value = _to_sympy(expression)
        return _json({
            "input": expression,
            "result": _result(value)
        })
    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 2. ALGEBRA TOOL
# =========================================================

@tool
def algebra_tool(operation: str, expression: str, variable: str = "") -> str:
    """
    Perform algebra operations.
    operation: simplify | expand | factor | cancel | collect
    Example:
    operation="factor", expression="x**2 + 5*x + 6"
    operation="expand", expression="(x+2)*(x+3)"
    """
    try:
        expr = _to_sympy(expression)

        if operation == "simplify":
            ans = sp.simplify(expr)
        elif operation == "expand":
            ans = sp.expand(expr)
        elif operation == "factor":
            ans = sp.factor(expr)
        elif operation == "cancel":
            ans = sp.cancel(expr)
        elif operation == "collect":
            if not variable:
                return _json({"error": "variable is required for collect"})
            ans = sp.collect(expr, sp.Symbol(variable))
        else:
            return _json({"error": f"Unsupported algebra operation: {operation}"})

        return _json({
            "operation": operation,
            "input": expression,
            "result": _result(ans)
        })
    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 3. EQUATION / INEQUALITY SOLVER
# =========================================================

@tool
def solve_equations_tool(equations: List[str], variables: List[str]) -> str:
    """
    Solve equations or inequalities.
    Use this for linear equations, simultaneous equations, quadratic equations, and linear inequalities.
    Examples:
    equations=["2*x + 3 = 7"], variables=["x"]
    equations=["x + y = 10", "2*x - y = 5"], variables=["x", "y"]
    equations=["2*x + 3 <= 9"], variables=["x"]
    """
    try:
        symbols = [sp.Symbol(v) for v in variables]
        local_dict = {v: sp.Symbol(v) for v in variables}

        relations = [_parse_relation(eq, local_dict) for eq in equations]

        has_inequality = any(
            isinstance(r, (sp.StrictLessThan, sp.StrictGreaterThan, sp.LessThan, sp.GreaterThan))
            for r in relations
        )

        if has_inequality:
            ans = sp.reduce_inequalities(relations, symbols)
            return _json({
                "type": "inequality",
                "input": equations,
                "variables": variables,
                "result": str(ans),
                "latex": sp.latex(ans)
            })

        ans = sp.solve(relations, symbols, dict=True)

        cleaned = []
        for sol in ans:
            cleaned.append({
                str(k): {
                    "exact": str(sp.simplify(v)),
                    "latex": sp.latex(sp.simplify(v)),
                    "decimal": float(sp.N(v)) if v.is_number else str(sp.N(v))
                }
                for k, v in sol.items()
            })

        return _json({
            "type": "equation",
            "input": equations,
            "variables": variables,
            "solutions": cleaned
        })
    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 4. MATRIX TOOL
# =========================================================

@tool
def matrix_tool(
    operation: str,
    matrix_a: List[List[Any]],
    matrix_b: Optional[List[List[Any]]] = None,
    scalar: Optional[Any] = None
) -> str:
    """
    Perform matrix operations.
    operation: add | subtract | multiply | determinant | inverse | transpose | scalar_multiply
    * NOTE ON ALGEBRA: You CAN pass unknown variables into the matrices, but they MUST BE STRINGS WRAPPED IN QUOTES! 
      CORRECT: matrix_b=[["-1", "3"], ["m", "1"]]
      FATAL ERROR: matrix_b=[[-1, 3], [m, 1]] (This will crash)
    """
    try:
        A = sp.Matrix(matrix_a)

        if operation == "determinant":
            ans = A.det()
            return _json({"operation": operation, "result": _result(ans)})

        if operation == "inverse":
            ans = A.inv()
            return _json({
                "operation": operation,
                "result": ans.tolist(),
                "latex": _matrix_to_latex(ans)
            })

        if operation == "transpose":
            ans = A.T
            return _json({
                "operation": operation,
                "result": ans.tolist(),
                "latex": _matrix_to_latex(ans)
            })

        if operation == "scalar_multiply":
            if scalar is None:
                return _json({"error": "scalar is required"})
            ans = _to_sympy(scalar) * A
            return _json({
                "operation": operation,
                "result": ans.tolist(),
                "latex": _matrix_to_latex(ans)
            })

        if matrix_b is None:
            return _json({"error": "matrix_b is required for this operation"})

        B = sp.Matrix(matrix_b)

        if operation == "add":
            ans = A + B
        elif operation == "subtract":
            ans = A - B
        elif operation == "multiply":
            ans = A * B
        else:
            return _json({"error": f"Unsupported matrix operation: {operation}"})

        return _json({
            "operation": operation,
            "result": ans.tolist(),
            "latex": _matrix_to_latex(ans)
        })
    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 5. COORDINATE GEOMETRY TOOL
# =========================================================

@tool
def coordinate_geometry_tool(
    operation: str,
    point_a: Optional[Any] = None,
    point_b: Optional[Any] = None,
    point: Optional[Any] = None,
    gradient: Optional[Any] = None
) -> str:
    """
    Coordinate geometry calculations.
    operation: distance | midpoint | gradient | line_equation_two_points | line_equation_point_gradient
    Points can be [x, y] or {"x": x, "y": y}.
    """
    try:
        x = sp.Symbol("x")
        y = sp.Symbol("y")

        if operation in ["distance", "midpoint", "gradient", "line_equation_two_points"]:
            if point_a is None or point_b is None:
                return _json({"error": "point_a and point_b are required"})

            x1, y1 = _point(point_a)
            x2, y2 = _point(point_b)

            if operation == "distance":
                ans = sp.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                return _json({"operation": operation, "result": _result(ans)})

            if operation == "midpoint":
                ans = [(x1 + x2) / 2, (y1 + y2) / 2]
                return _json({"operation": operation, "result": ans})

            if operation == "gradient":
                if x2 == x1:
                    return _json({"operation": operation, "result": "undefined"})
                ans = (y2 - y1) / (x2 - x1)
                return _json({"operation": operation, "result": _result(ans)})

            if operation == "line_equation_two_points":
                if x2 == x1:
                    equation = sp.Eq(x, x1)
                else:
                    m = sp.Rational(str((y2 - y1) / (x2 - x1)))
                    equation = sp.Eq(y - y1, m * (x - x1))

                simplified = sp.solve(equation, y)[0] if equation.lhs != x else equation
                return _json({
                    "operation": operation,
                    "equation": str(equation),
                    "latex": sp.latex(equation),
                    "simplified": str(simplified)
                })

        if operation == "line_equation_point_gradient":
            if point is None or gradient is None:
                return _json({"error": "point and gradient are required"})

            x1, y1 = _point(point)
            m = _to_sympy(gradient)
            equation = sp.Eq(y - y1, m * (x - x1))
            simplified = sp.Eq(y, sp.solve(equation, y)[0])

            return _json({
                "operation": operation,
                "equation": str(simplified),
                "latex": sp.latex(simplified)
            })

        return _json({"error": f"Unsupported coordinate operation: {operation}"})

    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 6. TRANSFORMATION TOOL
# =========================================================

@tool
def transformation_tool(
    operation: str,
    points: Dict[str, Any],
    vector: Optional[Any] = None,
    line: str = "",
    center: Optional[Any] = None,
    angle_degrees: Optional[float] = None,
    scale_factor: Optional[float] = None
) -> str:
    """
    Apply transformations to coordinate points.
    operation: translation | reflection | rotation | enlargement
    points (CRITICAL REQUIRED FIELD): You MUST pass the dictionary of coordinates to transform. Example: {"P": [-1, 5], "Q": [-5, 7]}. The tool will crash if you forget this!
    reflection line: x-axis | y-axis | y=x | y=-x | x=number | y=number
    """
    try:
        transformed = {}

        for label, p in points.items():
            px, py = _point(p)

            if operation == "translation":
                if vector is None:
                    return _json({"error": "vector is required"})
                dx, dy = _point(vector)
                nx, ny = px + dx, py + dy

            elif operation == "reflection":
                if line == "x-axis":
                    nx, ny = px, -py
                elif line == "y-axis":
                    nx, ny = -px, py
                elif line == "y=x":
                    nx, ny = py, px
                elif line == "y=-x":
                    nx, ny = -py, -px
                elif line.startswith("x="):
                    a = float(line.split("=")[1])
                    nx, ny = 2 * a - px, py
                elif line.startswith("y="):
                    b = float(line.split("=")[1])
                    nx, ny = px, 2 * b - py
                else:
                    return _json({"error": "Unsupported reflection line"})

            elif operation == "rotation":
                if center is None or angle_degrees is None:
                    return _json({"error": "center and angle_degrees are required"})
                cx, cy = _point(center)
                theta = math.radians(angle_degrees)

                tx, ty = px - cx, py - cy
                nx = cx + tx * math.cos(theta) - ty * math.sin(theta)
                ny = cy + tx * math.sin(theta) + ty * math.cos(theta)

            elif operation == "enlargement":
                if center is None or scale_factor is None:
                    return _json({"error": "center and scale_factor are required"})
                cx, cy = _point(center)
                nx = cx + scale_factor * (px - cx)
                ny = cy + scale_factor * (py - cy)

            else:
                return _json({"error": f"Unsupported transformation: {operation}"})

            transformed[label + "'"] = [
                round(nx, 6),
                round(ny, 6)
            ]

        return _json({
            "operation": operation,
            "transformed_points": transformed
        })
    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 7. GEOMETRY & MENSURATION TOOL
# =========================================================

@tool
def geometry_mensuration_tool(shape: str, operation: str, values: Optional[Dict[str, Any]] = None) -> str:
    """
    Calculate area, perimeter, volume, or surface area.
    operation: area | perimeter | volume | surface_area | curved_surface_area | radius_from_volume
    shape examples: rectangle, square, triangle, trapezium, trapezium_prism, circle, cuboid, cube, cylinder, cone, sphere, hemisphere, prism
    
    CRITICAL PRISM RULE: For a 'prism', you MUST provide 'cross_section_area' and 'length' (e.g., {"cross_section_area": 252, "length": 10}). 
    If the base is a trapezium or triangle, calculate the area of that 2D shape FIRST using this tool, then call the prism volume.

    values examples:
    {"length": 5, "width": 3}
    {"parallel_a": 16, "parallel_b": 26, "height": 12}
    {"radius": 7} OR {"diameter": 14}
    """
    try:
        pi = sp.pi
        v = {k: _to_sympy(val) for k, val in values.items()}

        ans = None

        if shape == "rectangle":
            if operation == "area":
                ans = v["length"] * v["width"]
            elif operation == "perimeter":
                ans = 2 * (v["length"] + v["width"])

        elif shape == "square":
            if operation == "area":
                ans = v["side"] ** 2
            elif operation == "perimeter":
                ans = 4 * v["side"]

        elif shape == "triangle":
            if operation == "area":
                if "base" in v and "height" in v:
                    ans = sp.Rational(1, 2) * v["base"] * v["height"]
                elif all(k in v for k in ["a", "b", "c"]):
                    s = (v["a"] + v["b"] + v["c"]) / 2
                    ans = sp.sqrt(s * (s - v["a"]) * (s - v["b"]) * (s - v["c"]))

        elif shape == "trapezium":
            if operation == "area":
                required = ["parallel_a", "parallel_b", "height"]
                missing = [key for key in required if key not in v]
                if missing:
                    return _json({
                        "error": f"Missing values for trapezium area: {missing}. Required: parallel_a, parallel_b, height."
                    })

                ans = sp.Rational(1, 2) * (v["parallel_a"] + v["parallel_b"]) * v["height"]

        elif shape == "trapezium_prism":
            if operation == "volume":
                required = ["parallel_a", "parallel_b", "height", "length"]
                missing = [key for key in required if key not in v]

                if missing:
                    return _json({
                        "error": f"Missing values for trapezium_prism volume: {missing}. Required: parallel_a, parallel_b, height, length."
                    })

                cross_section_area = sp.Rational(1, 2) * (
                    v["parallel_a"] + v["parallel_b"]
                ) * v["height"]

                ans = cross_section_area * v["length"]

        elif shape == "circle":
            r = v.get("radius", v.get("diameter", 0) / 2)
            if operation == "area":
                ans = pi * r ** 2
            elif operation in ["circumference", "perimeter"]:
                ans = 2 * pi * r

        elif shape == "cuboid":
            l, w, h = v["length"], v["width"], v["height"]
            if operation == "volume":
                ans = l * w * h
            elif operation == "surface_area":
                ans = 2 * (l * w + l * h + w * h)

        elif shape == "cube":
            s = v["side"]
            if operation == "volume":
                ans = s ** 3
            elif operation == "surface_area":
                ans = 6 * s ** 2

        elif shape == "cylinder":
            r, h = v["radius"], v["height"]
            if operation == "volume":
                ans = pi * r ** 2 * h
            elif operation == "surface_area":
                ans = 2 * pi * r ** 2 + 2 * pi * r * h

        elif shape == "cone":
            r, h = v["radius"], v["height"]
            if operation == "volume":
                ans = sp.Rational(1, 3) * pi * r ** 2 * h
            elif operation == "surface_area":
                slant = v.get("slant_height", sp.sqrt(r ** 2 + h ** 2))
                ans = pi * r ** 2 + pi * r * slant

        elif shape == "sphere":
            pi_value = v.get("pi", pi)

            if operation == "volume":
                r = v["radius"]
                ans = sp.Rational(4, 3) * pi_value * r ** 3

            elif operation == "radius_from_volume":
                ans = sp.real_root((3 * v["volume"]) / (4 * pi_value), 3)

            elif operation == "surface_area":
                r = v["radius"]
                ans = 4 * pi_value * r ** 2

        elif shape == "prism":
            # If the LLM passes the raw cross section area directly
            if "cross_section_area" in v:
                if operation == "volume":
                    ans = v["cross_section_area"] * v.get("length", v.get("height", 0))
            else:
                 return _json({
                    "error": "Missing 'cross_section_area'. Calculate the 2D area first (e.g., triangle or trapezium), then pass it here."
                })
        elif shape == "hemisphere":
            pi_value = v.get("pi", pi)
            r = v.get("radius", v.get("diameter", 0) / 2)

            if operation == "volume":
                ans = sp.Rational(2, 3) * pi_value * r ** 3

            elif operation == "radius_from_volume":
                ans = sp.real_root((3 * v["volume"]) / (2 * pi_value), 3)

            elif operation == "surface_area":
                ans = 3 * pi_value * r ** 2

            elif operation == "curved_surface_area":
                ans = 2 * pi_value * r ** 2
        if ans is None:
            return _json({"error": f"Unsupported shape/operation: {shape}/{operation}"})

        return _json({
            "shape": shape,
            "operation": operation,
            "result": _result(ans)
        })

    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 8. TRIGONOMETRY TOOL
# =========================================================

@tool
def trigonometry_tool(operation: str, values: Dict[str, Any]) -> str:
    """
    Trigonometry calculations.
    operation: trig_value | find_side | find_angle | sine_rule_side | cosine_rule_side | cosine_rule_angle
    Angles are in degrees.
    """
    try:
        v = {k: _to_sympy(val) for k, val in values.items()}

        if operation == "trig_value":
            angle = float(v["angle_degrees"])
            trig = values.get("trig", "sin")
            rad = math.radians(angle)

            if trig == "sin":
                ans = math.sin(rad)
            elif trig == "cos":
                ans = math.cos(rad)
            elif trig == "tan":
                ans = math.tan(rad)
            else:
                return _json({"error": "trig must be sin, cos, or tan"})

            return _json({"operation": operation, "result": ans})

        if operation == "find_side":
            trig = values["trig"]
            angle = math.radians(float(v["angle_degrees"]))
            known_side = float(v["known_side"])

            if trig == "sin_opposite":
                ans = known_side * math.sin(angle)
            elif trig == "cos_adjacent":
                ans = known_side * math.cos(angle)
            elif trig == "tan_opposite":
                ans = known_side * math.tan(angle)
            else:
                return _json({"error": "Unsupported find_side trig type"})

            return _json({"operation": operation, "result": ans})

        if operation == "find_angle":
            trig = values["trig"]
            ratio = float(v["ratio"])

            if trig == "sin":
                ans = math.degrees(math.asin(ratio))
            elif trig == "cos":
                ans = math.degrees(math.acos(ratio))
            elif trig == "tan":
                ans = math.degrees(math.atan(ratio))
            else:
                return _json({"error": "trig must be sin, cos, or tan"})

            return _json({"operation": operation, "angle_degrees": ans})

        if operation == "cosine_rule_side":
            a, b, C = float(v["a"]), float(v["b"]), math.radians(float(v["included_angle_degrees"]))
            ans = math.sqrt(a ** 2 + b ** 2 - 2 * a * b * math.cos(C))
            return _json({"operation": operation, "result": ans})

        if operation == "cosine_rule_angle":
            a, b, c = float(v["a"]), float(v["b"]), float(v["c"])
            ans = math.degrees(math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b)))
            return _json({"operation": operation, "angle_degrees": ans})

        return _json({"error": f"Unsupported trigonometry operation: {operation}"})

    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 9. STATISTICS TOOL
# =========================================================

@tool
def statistics_tool(
    operation: str,
    data: Optional[List[Any]] = None,
    frequencies: Optional[List[Any]] = None,
    class_midpoints: Optional[List[Any]] = None,
    intervals: Optional[List[List[float]]] = None
) -> str:
    """
    Statistics calculations.
    operation: mean | median | mode | range | variance | standard_deviation | grouped_mean
    Use data for raw data.
    Use class_midpoints + frequencies for grouped data.
    For frequency_distribution, provide 'data' and 'intervals' (e.g., [[1,5], [6,10]]).
    """
    try:
        if operation == "grouped_mean":
            if class_midpoints is None or frequencies is None:
                return _json({"error": "class_midpoints and frequencies are required"})

            mids = [float(x) for x in class_midpoints]
            freq = [float(x) for x in frequencies]
            ans = sum(m * f for m, f in zip(mids, freq)) / sum(freq)

            return _json({"operation": operation, "result": ans})

        if operation == "ogive_interpolation":
            if data is None or frequencies is None:
                return _json({"error": "data (coordinates) and frequencies (Y targets) are required"})
            try:
                # Sort points by Y to create an inverse spline (Input Y, output X)
                points = sorted(data, key=lambda p: p[1])
                y_vals = np.array([p[1] for p in points])
                x_vals = np.array([p[0] for p in points])
                
                # Build the mathematical curve
                inv_spline = CubicSpline(y_vals, x_vals)
                
                results = []
                for y_target in frequencies: 
                    x_interp = float(inv_spline(y_target))
                    x_rounded = round(x_interp * 2) / 2
                    results.append(x_rounded)
                    
                return _json({"operation": "ogive_interpolation", "interpolated_x_values": results})
            except Exception as e:
                return _json({"error": f"Interpolation failed: {str(e)}"})

        if data is None:
            return _json({"error": "data is required"})

        nums = [float(x) for x in data]
        nums_sorted = sorted(nums)

        if operation == "frequency_distribution":
            if data is None or intervals is None:
                return _json({"error": "data and intervals are required for frequency_distribution"})
            
            nums = [float(x) for x in data]
            counts = [0] * len(intervals)
            
            for num in nums:
                for i, (low, high) in enumerate(intervals):
                    if low <= num <= high:
                        counts[i] += 1
                        break
            
            return _json({
                "operation": operation,
                "intervals": intervals,
                "frequencies": counts
            })
        if operation == "mean":
            ans = sum(nums) / len(nums)

        elif operation == "median":
            n = len(nums_sorted)
            mid = n // 2
            ans = nums_sorted[mid] if n % 2 == 1 else (nums_sorted[mid - 1] + nums_sorted[mid]) / 2

        elif operation == "mode":
            counts = {}
            for x in nums:
                counts[x] = counts.get(x, 0) + 1
            max_count = max(counts.values())
            ans = [k for k, c in counts.items() if c == max_count]

        elif operation == "range":
            ans = max(nums) - min(nums)

        elif operation == "variance":
            mean = sum(nums) / len(nums)
            ans = sum((x - mean) ** 2 for x in nums) / len(nums)

        elif operation == "standard_deviation":
            mean = sum(nums) / len(nums)
            variance = sum((x - mean) ** 2 for x in nums) / len(nums)
            ans = math.sqrt(variance)
        elif operation == "quartiles":
            n = len(nums_sorted)
            
            # Helper to find median of a slice
            def get_median(arr):
                m = len(arr)
                if m == 0: return 0
                return arr[m//2] if m % 2 == 1 else (arr[m//2 - 1] + arr[m//2]) / 2

            mid_idx = n // 2
            
            if n % 2 == 0:
                lower_half = nums_sorted[:mid_idx]
                upper_half = nums_sorted[mid_idx:]
            else:
                lower_half = nums_sorted[:mid_idx]
                upper_half = nums_sorted[mid_idx+1:]
                
            q1 = get_median(lower_half)
            q2 = get_median(nums_sorted) # Q2 is the median
            q3 = get_median(upper_half)
            iqr = q3 - q1

            return _json({
                "operation": operation,
                "q1": q1,
                "q2_median": q2,
                "q3": q3,
                "interquartile_range": iqr
            })
    
        else:
            return _json({"error": f"Unsupported statistics operation: {operation}"})

        return _json({"operation": operation, "result": ans})

    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 10. PROBABILITY TOOL
# =========================================================

@tool
def probability_tool(operation: str, values: Dict[str, Any]) -> str:
    """
    Probability calculations.
    operation: simple | complement | and_independent | or_inclusion_exclusion | conditional
    Examples:
    simple: {"favourable": 3, "total": 10}
    complement: {"p_a": 0.3}
    and_independent: {"p_a": 0.5, "p_b": 0.2}
    or_inclusion_exclusion: {"p_a": 0.5, "p_b": 0.4, "p_a_intersect_b": 0.2}
    conditional: {"p_a_intersect_b": 0.2, "p_b": 0.5}
    """
    try:
        v = {k: _to_sympy(val) for k, val in values.items()}

        if operation == "simple":
            ans = v["favourable"] / v["total"]

        elif operation == "complement":
            ans = 1 - v["p_a"]

        elif operation == "and_independent":
            ans = v["p_a"] * v["p_b"]

        elif operation == "or_inclusion_exclusion":
            ans = v["p_a"] + v["p_b"] - v["p_a_intersect_b"]

        elif operation == "conditional":
            ans = v["p_a_intersect_b"] / v["p_b"]

        else:
            return _json({"error": f"Unsupported probability operation: {operation}"})

        return _json({
            "operation": operation,
            "result": _result(ans)
        })

    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 11. FINANCIAL MATHEMATICS TOOL
# =========================================================

@tool
def financial_math_tool(operation: str, values: Dict[str, Any]) -> str:
    """
    Financial mathematics calculations.
    operation: simple_interest | compound_interest | depreciation | discount | percentage_change | hire_purchase_total | monthly_payment | shared_dividend | roi_percentage
    """
    try:
        v = {k: _to_sympy(val) for k, val in values.items()}

        if operation == "simple_interest":
            ans = v["principal"] * v["rate_percent"] / 100 * v["time_years"]

        elif operation == "compound_interest":
            ans = v["principal"] * (1 + v["rate_percent"] / 100) ** v["time_years"]

        elif operation == "depreciation":
            ans = v["original_value"] * (1 - v["rate_percent"] / 100) ** v["time_years"]

        elif operation == "discount":
            ans = v["original_price"] * (1 - v["discount_percent"] / 100)

        elif operation == "percentage_change":
            ans = (v["new_value"] - v["old_value"]) / v["old_value"] * 100

        elif operation == "hire_purchase_total":
            ans = v["deposit"] + v["monthly_payment"] * v["months"]

        elif operation == "monthly_payment":
            ans = (v["total_price"] - v["deposit"]) / v["months"]
        elif operation == "share_dividend":
            ans = (v["rate_percent"] / 100) * v["price_per_share"] * v["units"]

        elif operation == "roi_percentage":
            # Requires total_return (dividends + capital gain) and total_investment
            ans = (v["total_return"] / v["total_investment"]) * 100
        else:
            return _json({"error": f"Unsupported financial operation: {operation}"})

        return _json({
            "operation": operation,
            "result": _result(ans)
        })

    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# 12. MOTION / GRAPH OF MOTION TOOL
# =========================================================

@tool
def motion_graph_tool(operation: str, values: Dict[str, Any]) -> str:
    """
    Motion and graph calculations.
    CRITICAL: You MUST always provide BOTH 'operation' AND the 'values' dictionary!
    
    operation: speed | distance | time | acceleration | gradient | area_under_speed_time_graph
    
    Examples of required 'values' formatting:
    - gradient: values={"y2": 10, "y1": 2, "x2": 5, "x1": 1}
    - acceleration: values={"final_speed": 20, "initial_speed": 0, "time": 5}
    - area_under_speed_time_graph: values={"segments": [[t1, v1, t2, v2], [t2, v2, t3, v3]]}
    """
    try:
        v = {k: _to_sympy(val) for k, val in values.items() if k != "segments"}

        if operation == "speed":
            ans = v["distance"] / v["time"]

        elif operation == "distance":
            ans = v["speed"] * v["time"]

        elif operation == "time":
            ans = v["distance"] / v["speed"]

        elif operation == "acceleration":
            ans = (v["final_speed"] - v["initial_speed"]) / v["time"]

        elif operation == "gradient":
            ans = (v["y2"] - v["y1"]) / (v["x2"] - v["x1"])

        elif operation == "area_under_speed_time_graph":
            total = 0
            for segment in values["segments"]:
                t1, s1, t2, s2 = [float(x) for x in segment]
                total += 0.5 * (s1 + s2) * (t2 - t1)
            ans = total

        else:
            return _json({"error": f"Unsupported motion operation: {operation}"})

        return _json({
            "operation": operation,
            "result": _result(ans)
        })

    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# OPTIONAL 13. SEQUENCES TOOL
# =========================================================

@tool
def sequence_tool(operation: str, values: Dict[str, Any]) -> str:
    """
    Sequence calculations.
    operation: arithmetic_nth | arithmetic_sum | geometric_nth | geometric_sum
    """
    try:
        v = {k: _to_sympy(val) for k, val in values.items()}

        if operation == "arithmetic_nth":
            ans = v["a"] + (v["n"] - 1) * v["d"]

        elif operation == "arithmetic_sum":
            ans = v["n"] / 2 * (2 * v["a"] + (v["n"] - 1) * v["d"])

        elif operation == "geometric_nth":
            ans = v["a"] * v["r"] ** (v["n"] - 1)

        elif operation == "geometric_sum":
            ans = v["a"] * (v["r"] ** v["n"] - 1) / (v["r"] - 1)

        else:
            return _json({"error": f"Unsupported sequence operation: {operation}"})

        return _json({
            "operation": operation,
            "result": _result(ans)
        })

    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# OPTIONAL 14. SETS TOOL
# =========================================================

@tool
def sets_logic_tool(operation: str, values: Dict[str, Any]) -> str:
    """
    Set calculations.
    operation: union_count | intersection_count | complement_count | difference_count
    """
    try:
        v = {k: _to_sympy(val) for k, val in values.items()}

        if operation == "union_count":
            ans = v["n_a"] + v["n_b"] - v["n_a_intersect_b"]

        elif operation == "intersection_count":
            ans = v["n_a"] + v["n_b"] - v["n_a_union_b"]

        elif operation == "complement_count":
            ans = v["universal"] - v["set_count"]

        elif operation == "difference_count":
            ans = v["n_a"] - v["n_a_intersect_b"]

        else:
            return _json({"error": f"Unsupported sets operation: {operation}"})

        return _json({
            "operation": operation,
            "result": _result(ans)
        })

    except Exception as e:
        return _json({"error": str(e)})


# =========================================================
# OPTIONAL 15. GRAPH THEORY TOOL
# =========================================================

@tool
def graph_theory_tool(operation: str, values: Dict[str, Any]) -> str:
    """
    Graph theory calculations.
    operation: degree_count | shortest_path
    For shortest_path:
    values = {
      "edges": [["A", "B", 5], ["B", "C", 2]],
      "start": "A",
      "end": "C"
    }
    """
    try:
        if operation == "degree_count":
            edges = values["edges"]
            degree = {}

            for edge in edges:
                a, b = edge[0], edge[1]
                degree[a] = degree.get(a, 0) + 1
                degree[b] = degree.get(b, 0) + 1

            return _json({
                "operation": operation,
                "degree": degree
            })

        if operation == "shortest_path":
            edges = values["edges"]
            start = values["start"]
            end = values["end"]

            graph = {}
            for a, b, w in edges:
                graph.setdefault(a, []).append((b, float(w)))
                graph.setdefault(b, []).append((a, float(w)))

            pq = [(0, start, [])]
            visited = set()

            while pq:
                cost, node, path = heapq.heappop(pq)

                if node in visited:
                    continue

                visited.add(node)
                path = path + [node]

                if node == end:
                    return _json({
                        "operation": operation,
                        "distance": cost,
                        "path": path
                    })

                for neighbour, weight in graph.get(node, []):
                    if neighbour not in visited:
                        heapq.heappush(pq, (cost + weight, neighbour, path))

            return _json({"error": "No path found"})

        return _json({"error": f"Unsupported graph theory operation: {operation}"})

    except Exception as e:
        return _json({"error": str(e)})

# =========================================================
# 16. TAXATION TOOL
# =========================================================
@tool
def taxation_tool(operation: str, values: Optional[Dict[str, Any]] = None) -> str:
    """
    SPM Taxation calculations.

    Always provide:
    - operation
    - values

    Supported operations:

    1. chargeable_income
       values = {
         "total_income": number,
         "exemptions": number, optional, default 0
         "reliefs": number, optional, default 0
       }

    2. chargeable_income_components / joint_chargeable_income
       Use this for joint assessment or complex relief calculations.
       The tool will calculate total income, total reliefs, exemptions,
       rebates, and chargeable income from components.

       values = {
         "incomes": [
           {"name": "husband income", "amount": 120000},
           {"name": "wife income", "amount": 40000}
         ],
         "reliefs": [
           {"name": "individual relief", "amount": 9000},
           {"name": "lifestyle", "amounts": [4000, 2000], "limit": 2500},
           {"name": "life insurance", "amounts": [3000, 1000], "limit": 7000},
           {"name": "medical insurance", "amounts": [2000, 1500], "limit": 3000}
         ],
         "exemptions": [
           {"name": "donation", "amounts": [200, 200]}
         ],
         "rebates": [
           {"name": "zakat", "amount": 1800}
         ]
       }

    3. income_tax
       values = {
         "base_tax": number,
         "next_amount": number,
         "next_rate_percent": number,
         "rebates": number, optional, default 0
       }

    4. property_assessment_tax
       values = {
         "annual_value": number,
         "rate_percent": number
       }

    5. quit_rent
       values = {
         "area": number,
         "rate_per_area": number
       }

    6. road_tax
       values = {
         "base_rate": number,
         "engine_cc": number,
         "base_cc_limit": number,
         "rate_per_cc": number
       }
    """

    if values is None:
        return _json({
            "error": "Missing required 'values' dictionary.",
            "example": {
                "operation": "chargeable_income_components",
                "values": {
                    "incomes": [
                        {"name": "husband income", "amount": 120000},
                        {"name": "wife income", "amount": 40000}
                    ],
                    "reliefs": [
                        {"name": "individual relief", "amount": 9000},
                        {"name": "lifestyle", "amounts": [4000, 2000], "limit": 2500},
                        {"name": "life insurance", "amounts": [3000, 1000], "limit": 7000},
                        {"name": "medical insurance", "amounts": [2000, 1500], "limit": 3000}
                    ],
                    "exemptions": [
                        {"name": "donation", "amounts": [200, 200]}
                    ],
                    "rebates": [
                        {"name": "zakat", "amount": 1800}
                    ]
                }
            }
        })

    try:
        def to_num(value, default=0):
            if value is None or value == "":
                return default

            if isinstance(value, (int, float)):
                return float(value)

            cleaned = (
                str(value)
                .replace("RM", "")
                .replace("rm", "")
                .replace(",", "")
                .replace(" ", "")
                .strip()
            )

            if cleaned == "":
                return default

            return float(cleaned)

        def as_items(value):
            if value is None:
                return []
            if isinstance(value, list):
                return value
            return [value]

        def calculate_component(item):
            """
            Supports:
            {"name": "medical", "amount": 3000, "limit": 3000}
            {"name": "medical", "amounts": [2000, 1500], "limit": 3000}
            3000
            """

            if isinstance(item, dict):
                name = item.get("name", "")

                if "amounts" in item and isinstance(item["amounts"], list):
                    raw_amount = sum(to_num(x) for x in item["amounts"])
                else:
                    raw_amount = to_num(item.get("amount", 0))

                limit = item.get("limit", None)

                if limit is not None:
                    limit_value = to_num(limit)
                    claimable = min(raw_amount, limit_value)
                else:
                    limit_value = None
                    claimable = raw_amount

                return {
                    "name": name,
                    "raw_amount": round(raw_amount, 2),
                    "limit": limit_value,
                    "claimable": round(claimable, 2)
                }

            raw_amount = to_num(item)

            return {
                "name": "",
                "raw_amount": round(raw_amount, 2),
                "limit": None,
                "claimable": round(raw_amount, 2)
            }

        # =====================================================
        # COMPONENT-BASED CHARGEABLE INCOME
        # Best for joint assessment.
        # =====================================================
        if operation in ["chargeable_income_components", "joint_chargeable_income"]:
            income_items = as_items(
                values.get("incomes", values.get("income_items", []))
            )
            relief_items = as_items(
                values.get("reliefs", values.get("relief_items", []))
            )
            exemption_items = as_items(
                values.get("exemptions", values.get("exemption_items", []))
            )
            rebate_items = as_items(
                values.get("rebates", values.get("rebate_items", []))
            )

            income_audit = [calculate_component(item) for item in income_items]
            relief_audit = [calculate_component(item) for item in relief_items]
            exemption_audit = [calculate_component(item) for item in exemption_items]
            rebate_audit = [calculate_component(item) for item in rebate_items]

            total_income = sum(item["claimable"] for item in income_audit)
            total_reliefs = sum(item["claimable"] for item in relief_audit)
            total_exemptions = sum(item["claimable"] for item in exemption_audit)
            total_rebates = sum(item["claimable"] for item in rebate_audit)

            chargeable_income = total_income - total_reliefs - total_exemptions

            return _json({
                "operation": operation,
                "total_income": round(total_income, 2),
                "total_reliefs": round(total_reliefs, 2),
                "total_exemptions": round(total_exemptions, 2),
                "total_rebates": round(total_rebates, 2),
                "chargeable_income": round(chargeable_income, 2),
                "formula": "chargeable_income = total_income - total_reliefs - total_exemptions",
                "income_audit": income_audit,
                "relief_audit": relief_audit,
                "exemption_audit": exemption_audit,
                "rebate_audit": rebate_audit
            })

        # =====================================================
        # OLD SIMPLE OPERATIONS
        # Keep these for backward compatibility.
        # =====================================================
        v = {k: to_num(val) for k, val in values.items()}

        if operation == "chargeable_income":
            ans = v["total_income"] - v.get("exemptions", 0) - v.get("reliefs", 0)

            return _json({
                "operation": operation,
                "total_income": round(v["total_income"], 2),
                "reliefs": round(v.get("reliefs", 0), 2),
                "exemptions": round(v.get("exemptions", 0), 2),
                "result": round(ans, 2),
                "formula": "chargeable_income = total_income - reliefs - exemptions"
            })
        elif operation == "electricity_service_tax":
            total_usage_kwh = v["total_usage_kwh"]
            threshold_kwh = v.get("threshold_kwh", 600)
            service_tax_rate_percent = v["service_tax_rate_percent"]

            # Option 1: taxable amount is already calculated from tariff table
            if "taxable_excess_amount" in v:
                taxable_excess_amount = v["taxable_excess_amount"]
            else:
                excess_kwh = max(0, total_usage_kwh - threshold_kwh)
                excess_rate = v["excess_rate"]
                taxable_excess_amount = excess_kwh * excess_rate

            service_tax = taxable_excess_amount * service_tax_rate_percent / 100

            return _json({
                "operation": operation,
                "total_usage_kwh": round(total_usage_kwh, 2),
                "threshold_kwh": round(threshold_kwh, 2),
                "taxable_excess_amount": round(taxable_excess_amount, 2),
                "service_tax_rate_percent": round(service_tax_rate_percent, 2),
                "result": round(service_tax, 2),
                "formula": "service_tax = taxable_excess_amount × service_tax_rate_percent / 100"
            })
        elif operation == "income_tax":
            base_tax = v.get("base_tax", 0)
            next_amount = v.get("next_amount", 0)
            rate = v.get("next_rate_percent", 0) / 100
            rebates = v.get("rebates", 0)

            calculated_tax = base_tax + (next_amount * rate)
            ans = max(0, calculated_tax - rebates)

            return _json({
                "operation": operation,
                "base_tax": round(base_tax, 2),
                "next_amount": round(next_amount, 2),
                "next_rate_percent": round(v.get("next_rate_percent", 0), 2),
                "rebates": round(rebates, 2),
                "calculated_tax_before_rebate": round(calculated_tax, 2),
                "result": round(ans, 2)
            })

        elif operation == "property_assessment_tax":
            ans = v["annual_value"] * (v["rate_percent"] / 100)

            return _json({
                "operation": operation,
                "annual_value": round(v["annual_value"], 2),
                "rate_percent": round(v["rate_percent"], 2),
                "result": round(ans, 2)
            })

        elif operation == "quit_rent":
            ans = v["area"] * v["rate_per_area"]

            return _json({
                "operation": operation,
                "area": round(v["area"], 2),
                "rate_per_area": round(v["rate_per_area"], 2),
                "result": round(ans, 2)
            })

        elif operation == "road_tax":
            base = v["base_rate"]
            extra_cc = max(0, v["engine_cc"] - v["base_cc_limit"])
            ans = base + (extra_cc * v["rate_per_cc"])

            return _json({
                "operation": operation,
                "base_rate": round(base, 2),
                "engine_cc": round(v["engine_cc"], 2),
                "base_cc_limit": round(v["base_cc_limit"], 2),
                "extra_cc": round(extra_cc, 2),
                "rate_per_cc": round(v["rate_per_cc"], 2),
                "result": round(ans, 2)
            })

        else:
            return _json({
                "error": f"Unsupported taxation operation: {operation}",
                "supported_operations": [
                    "chargeable_income",
                    "chargeable_income_components",
                    "joint_chargeable_income",
                    "income_tax",
                    "property_assessment_tax",
                    "quit_rent",
                    "road_tax"
                ]
            })

    except Exception as e:
        return _json({
            "error": str(e),
            "operation": operation,
            "values": values
        })
@tool
def graph_theory_tool(operation: str, edges: list, start: str, end: str):
    """
    Solves weighted undirected graph path problems.

    operation:
    - shortest_path
    - longest_simple_path
    - min_hamiltonian_path
    - max_hamiltonian_path

    edges format:
    [
      ["A", "B", 800],
      ["A", "C", 700]
    ]
    """

    # Build graph
    graph = {}
    vertices = set()

    for u, v, w in edges:
        w = float(w)
        vertices.add(u)
        vertices.add(v)
        graph.setdefault(u, []).append((v, w))
        graph.setdefault(v, []).append((u, w))

    vertices = sorted(vertices)

    def path_weight(path):
        total = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            found = False
            for nxt, w in graph.get(u, []):
                if nxt == v:
                    total += w
                    found = True
                    break
            if not found:
                return None
        return total

    def all_simple_paths(current, target, visited, path):
        if current == target:
            return [path[:]]

        results = []
        for nxt, _w in graph.get(current, []):
            if nxt not in visited:
                visited.add(nxt)
                path.append(nxt)
                results.extend(all_simple_paths(nxt, target, visited, path))
                path.pop()
                visited.remove(nxt)

        return results

    if operation == "shortest_path":
        pq = [(0, start, [start])]
        visited_best = {}

        while pq:
            dist, node, path = heapq.heappop(pq)

            if node == end:
                return {
                    "operation": operation,
                    "path": path,
                    "distance": dist
                }

            if node in visited_best and visited_best[node] <= dist:
                continue

            visited_best[node] = dist

            for nxt, w in graph.get(node, []):
                heapq.heappush(pq, (dist + w, nxt, path + [nxt]))

        return {"error": "No path found"}

    simple_paths = all_simple_paths(start, end, {start}, [start])

    weighted_paths = []
    for path in simple_paths:
        total = path_weight(path)
        if total is not None:
            weighted_paths.append({
                "path": path,
                "distance": total
            })

    if operation == "longest_simple_path":
        best = max(weighted_paths, key=lambda x: x["distance"])
        return {
            "operation": operation,
            "path": best["path"],
            "distance": best["distance"],
            "tested_paths": weighted_paths
        }

    hamiltonian_paths = [
        item for item in weighted_paths
        if len(item["path"]) == len(vertices)
    ]

    if not hamiltonian_paths:
        return {"error": "No Hamiltonian path found"}

    if operation == "min_hamiltonian_path":
        best = min(hamiltonian_paths, key=lambda x: x["distance"])
        return {
            "operation": operation,
            "path": best["path"],
            "distance": best["distance"],
            "tested_paths": hamiltonian_paths
        }

    if operation == "max_hamiltonian_path":
        best = max(hamiltonian_paths, key=lambda x: x["distance"])
        return {
            "operation": operation,
            "path": best["path"],
            "distance": best["distance"],
            "tested_paths": hamiltonian_paths
        }

    return {"error": f"Unknown operation: {operation}"}
@tool
def insurance_tool(operation: str, values: Optional[Dict[str, Any]] = None) -> str:
    """
    Insurance calculation tool for SPM Mathematics.

    Always call with:
    insurance_tool(
      operation="property_partial_loss",
      values={
        "insurable_value": 2400000,
        "coinsurance_percent": 75,
        "deductible": 20000,
        "loss": 500000,
        "compensation": 430000,
        "solve_for": "insured_amount"
      }
    )
    """

    if values is None:
        return _json({
            "error": "Missing required 'values' dictionary.",
            "expected_format": {
                "operation": "property_partial_loss",
                "values": {
                    "insurable_value": 2400000,
                    "coinsurance_percent": 75,
                    "deductible": 20000,
                    "loss": 500000,
                    "compensation": 430000,
                    "solve_for": "insured_amount"
                }
            }
        })

    def get_num(key, default=None):
        value = values.get(key, default)
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "").replace("RM", "").strip())

    if operation == "property_required_amount":
        insurable_value = get_num("insurable_value")
        coinsurance_percent = get_num("coinsurance_percent")

        if insurable_value is None or coinsurance_percent is None:
            return _json({
                "error": "property_required_amount requires insurable_value and coinsurance_percent."
            })

        required_amount = insurable_value * coinsurance_percent / 100

        return _json({
            "operation": operation,
            "required_amount": required_amount,
            "formula": "Required Amount = coinsurance_percent × insurable_value"
        })

    if operation == "property_partial_loss":
        insurable_value = get_num("insurable_value")
        coinsurance_percent = get_num("coinsurance_percent")
        deductible = get_num("deductible", 0)
        required_amount = get_num("required_amount")

        if required_amount is None:
            if insurable_value is None or coinsurance_percent is None:
                return _json({
                    "error": "Provide either required_amount, or both insurable_value and coinsurance_percent."
                })
            required_amount = insurable_value * coinsurance_percent / 100

        insured_amount = get_num("insured_amount")
        loss = get_num("loss")
        compensation = get_num("compensation")
        solve_for = str(values.get("solve_for") or "").strip().lower()

        result = {
            "operation": operation,
            "required_amount": required_amount,
            "deductible": deductible,
            "formula": "Compensation = (insured_amount / required_amount) × loss - deductible"
        }

        if solve_for == "compensation":
            if insured_amount is None or loss is None:
                return _json({
                    "error": "To solve compensation, provide insured_amount and loss."
                })

            compensation = (insured_amount / required_amount) * loss - deductible
            result["compensation"] = compensation
            return _json(result)

        if solve_for == "loss":
            if compensation is None or insured_amount is None:
                return _json({
                    "error": "To solve loss, provide compensation and insured_amount."
                })

            loss = (compensation + deductible) * required_amount / insured_amount
            result["loss"] = loss
            result["verification_compensation"] = (
                (insured_amount / required_amount) * loss - deductible
            )
            return _json(result)

        if solve_for == "insured_amount":
            if compensation is None or loss is None:
                return _json({
                    "error": "To solve insured_amount, provide compensation and loss."
                })

            insured_amount = (compensation + deductible) * required_amount / loss
            result["insured_amount"] = insured_amount
            result["verification_compensation"] = (
                (insured_amount / required_amount) * loss - deductible
            )
            return _json(result)

        return _json({
            "error": "For property_partial_loss, solve_for must be compensation, loss, or insured_amount."
        })

    return _json({"error": f"Unsupported insurance operation: {operation}"})