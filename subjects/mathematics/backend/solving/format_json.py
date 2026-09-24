from datetime import date, datetime
from decimal import Decimal
import json
import re

class AgentOutputProcessor:
    """
    A unified pipeline to clean, parse, and format LLM JSON outputs.
    Replaces safe_parse_json, make_json_safe, and normalize_solution_display.
    """
    
    @staticmethod
    def process(raw_text: str) -> dict:
        # 1. Clean Markdown & Extract JSON String
        text = re.sub(r"```json", "", raw_text)
        text = re.sub(r"```", "", text)
        text = re.sub(r"</?[^>]+>", "", text)
        text = text.strip()

        start = text.find("{") if text.find("{") != -1 else text.find("[")
        if start == -1:
            raise ValueError("No JSON found in response")
        text = text[start:]
        text = re.sub(r',\s*([\]}])', r'\1', text)
        # 2. The LaTeX JSON Sanitizer (The Silver Bullet)
        # Fixes \div, \frac, \times etc. before the JSON parser crashes
        text = text.replace("\\\\", "\\")   # Temporarily unescape everything
        text = text.replace("\\", "\\\\")   # Re-escape perfectly for LaTeX
        text = text.replace('\\\\"', '\\"') # Restore valid JSON quotes
        text = text.replace('\\\\n', '\\n') # Restore valid JSON newlines

        # 3. Parse JSON
        try:
            parsed_json, _ = json.JSONDecoder(strict=False).raw_decode(text)
        except json.JSONDecodeError:
            # Fallback for trailing commas
            end = max(text.rfind("}"), text.rfind("]"))
            if end != -1:
                clean_text = re.sub(r",\s*}", "}", text[:end + 1])
                clean_text = re.sub(r",\s*]", "]", clean_text)
                parsed_json = json.loads(clean_text, strict=False)
            else:
                raise ValueError("Could not parse JSON")

        # 4. Normalize Math & Make Data Types Safe
        return AgentOutputProcessor._walk_and_format(parsed_json)

    @staticmethod
    def _walk_and_format(data):
        """Recursively formats math strings and sanitizes data types."""
        # Handle Data Types (make_json_safe logic)
        if isinstance(data, Decimal):
            return float(data)
        if isinstance(data, (datetime, date)):
            return data.isoformat()

        # Handle Dictionaries (normalize_solution_display logic)
        if isinstance(data, dict):
            if "text" in data and "math" in data:
                text_val = str(data.get("text") or "").strip()
                math_val = str(data.get("math") or "").strip()

                if math_val:
                    # Move prose math into text
                    if AgentOutputProcessor._looks_like_sentence(math_val):
                        data["text"] = f"{text_val} {math_val}".strip()
                        data["math"] = ""
                    else:
                        data["math"] = AgentOutputProcessor._format_math(math_val)
                else:
                    data["math"] = ""
            
            return {str(k): AgentOutputProcessor._walk_and_format(v) for k, v in data.items()}

        # Handle Lists
        if isinstance(data, (list, tuple)):
            return [AgentOutputProcessor._walk_and_format(item) for item in data]

        return data

    @staticmethod
    def _looks_like_sentence(text: str) -> bool:
        """Detects if LLM put a prose explanation inside the math field."""
        # 1. Strip out English words safely wrapped inside LaTeX \text{} blocks
        clean_text = re.sub(r"\\text\{[^}]+\}", "", text)
        clean_text = re.sub(r"\\[a-zA-Z]+", "", clean_text)
        word_tokens = re.findall(r"\b[a-zA-Z]{3,}\b", clean_text)
        
        # 2. Expanded whitelist to ignore LaTeX layout commands
        allowed_math = {
            "sin", "cos", "tan", "log", "ln", "min", "max", "sum", "mean", "mode", "median",
            "cm", "km", "unit", "units", "true", "false", "valid", "sound", "not",
            "begin", "end", "pmatrix", "bmatrix", "vmatrix", "matrix", "aligned", "array", "cases",
            "frac", "sqrt", "left", "right", "times", "div", "cdot", "leq", "geq", "neq", "quad", "qquad",
            "theta", "pi", "alpha", "beta", "gamma"
        }
        
        meaningful_words = [w.lower() for w in word_tokens if w.lower() not in allowed_math]
        
        return len(meaningful_words) >= 4

    @staticmethod
    def _format_math(math_text: str) -> str:
        """Aligns equations and fixes percent signs."""
        math_text = re.sub(r"(?<!\\)%", r"\\%", math_text)
        
        if "\\begin{aligned}" in math_text or "\\begin{array}" in math_text:
            return math_text

        math_text = math_text.replace("\\n", "\n")
        lines = [line.strip() for line in math_text.splitlines() if line.strip()]

        if len(lines) <= 1:
            # Enforce alignment even on single lines if there's an equals sign
            if lines and "=" in lines[0] and "&=" not in lines[0]:
                lines[0] = lines[0].replace("=", "&=", 1)
                return "\\begin{aligned} " + lines[0] + " \\end{aligned}"
            return lines[0] if lines else ""

        formatted_lines = []
        for i, line in enumerate(lines):
            if "=" in line and "&=" not in line:
                line = line.replace("=", "&=", 1)
            formatted_lines.append(line if i == 0 else "\\Rightarrow " + line)

        return "\\begin{aligned} " + " \\\\ ".join(formatted_lines) + " \\end{aligned}"