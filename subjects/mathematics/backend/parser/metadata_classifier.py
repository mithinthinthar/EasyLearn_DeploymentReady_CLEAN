from collections import Counter, defaultdict
import re

CHAPTER_RULES = [
    # =========================
    # FORM 4
    # =========================

    {
        "form": "Form 4",
        "chapter": "Chapter 1: Quadratic Functions and Equations in One Variable",
        "strong_signals": [
        ["quadratic", "kuadratik"],
        ["quadratic equation", "persamaan kuadratik"],
        ["quadratic function", "fungsi kuadratik"],
        ["ax^2 + bx + c", "ax² + bx + c"],
        ["parabola", "parabola"],
        ["axis of symmetry", "paksi simetri"]
        ],
        "signals": [
            ["x^2", "x²"],
            ["root", "roots", "punca"],
            ["factorisation", "factorization", "pemfaktoran"],
            ["graphical method", "kaedah graf"],
            ["y-intercept", "pintasan-y"]
        ]
    },
    {
        "form": "Form 4",
        "chapter": "Chapter 2: Number Bases",
        "strong_signals": [
        ["number base", "asas nombor"],
        ["base two", "base 2", "asas dua"],
        ["base eight", "base 8", "asas lapan"],
        ["base ten", "base 10", "asas sepuluh"],
        ["convert to base", "tukar kepada asas"],
        ["addition in base", "penambahan dalam asas"],
        ["subtraction in base", "penolakan dalam asas"],
        ["₂", "₈", "₁₀"]
    ],
    "signals": [
        ["convert", "conversion", "tukar", "penukaran"],
        ["vertical form", "bentuk lazim"]
    ]
    },
    {
        "form": "Form 4",
        "chapter": "Chapter 3: Logical Reasoning",
        "strong_signals": [
            ["truth value", "nilai kebenaran"],
            ["negation", "penafian"],
            ["compound statement", "pernyataan majmuk", "penyataan majmuk"],
            ["implication", "implikasi"],
            ["if p then q", "jika p maka q"],
            ["converse", "akasan"],
            ["contrapositive", "kontrapositif"],
            ["premise", "premis"],
            ["argument", "hujah"],
            ["inductive", "induktif"],
            ["deductive", "deduktif"]
        ],
        "signals": [
            ["statement", "pernyataan", "penyataan"],
            ["true", "false", "benar", "palsu"],
            ["inverse", "songsangan"],
            ["conclusion", "kesimpulan"]
        ]
    },

    {
        "form": "Form 4",
        "chapter": "Chapter 4: Operations on Sets",
        "strong_signals": [
            ["venn", "venn"],
            ["intersection", "persilangan"],
            ["union", "kesatuan"],
            ["complement", "pelengkap"],
            ["combined operation", "operasi bergabung"],
            ["p ∩ q", "∩"],
            ["p ∪ q", "∪"],
            ["universal set", "set semesta"],
            ["one type only", "satu jenis sahaja"],
            ["neither", "tidak memilih", "tidak makan"]
        ],
        "signals": [
            ["set", "sets", "set"],
            ["p'", "q'", "r'"],
            ["both", "kedua-dua"],
            ["only", "sahaja"],
        ]
    },

    {
        "form": "Form 4",
        "chapter": "Chapter 5: Network in Graph Theory",
        "strong_signals": [
            ["network", "rangkaian"],
            ["graph theory", "teori graf"],
            ["vertex", "vertices", "bucu"],
            ["edge", "edges", "tepi"],
            ["multiple edge", "tepi berganda"],
            ["directed graph", "graf terarah"],
            ["undirected graph", "graf tak terarah"],
            ["weighted graph", "graf berpemberat"],
            ["unweighted graph", "graf tak berpemberat"],
            ["subgraph", "subgraf"]
        ],
        "signals": [
            ["degree", "darjah"],
            ["loop", "gelung"],
            ["tree", "pokok"]
        ]
    },

    {
        "form": "Form 4",
        "chapter": "Chapter 6: Linear Inequalities in Two Variables",
        "strong_signals": [
            ["linear inequality", "linear inequalities", "ketaksamaan linear"],
            ["system of inequalities", "sistem ketaksamaan"],
            ["shaded region", "rantau berlorek"],
            ["shade the region", "lorek rantau"],
            ["common region", "rantau sepunya"],
            ["y > mx + c", "y < mx + c", "y >= mx + c", "y <= mx + c"],
            ["x ≥ 0", "y ≥ 0", "x >= 0", "y >= 0"]
        ],
        "signals": [
            ["two variables", "dua pemboleh ubah"],
            ["dashed line", "garis putus-putus"],
            ["solid line", "garis penuh"],
            ["constraints", "kekangan"],
            ["at most", "selebih-lebihnya"],
            ["not exceed", "tidak melebihi"],
            ["less than", "kurang daripada"],
            ["more than", "lebih daripada"]
        ]
    },

    {
        "form": "Form 4",
        "chapter": "Chapter 7: Graphs of Motion",
        "strong_signals": [
            ["distance-time", "jarak-masa"],
            ["speed-time", "laju-masa"],
            ["distance time graph", "graf jarak masa"],
            ["speed time graph", "graf laju masa"],
            ["average speed", "purata laju"],
            ["uniform speed", "laju seragam"],
            ["acceleration", "pecutan"],
            ["deceleration", "nyahpecutan"],
            ["stationary", "pegun"],
            ["total distance", "jumlah jarak"],
            ["area under graph", "luas di bawah graf"],
            ["kmh", "kmj"]
        ],
        "signals": [
            ["gradient", "kecerunan"],
            ["speed", "laju"]
        ]
    },

    {
        "form": "Form 4",
        "chapter": "Chapter 8: Measures of Dispersion for Ungrouped Data",
        "strong_signals": [
            ["ungrouped data", "data tak terkumpul"],
            ["raw data", "data mentah"],
            ["stem-and-leaf", "batang dan daun"],
            ["dot plot", "plot titik"],
            ["box plot", "plot kotak"],
            ["interquartile range", "julat antara kuartil"]
        ],
        "signals": [
            ["range", "julat"],
            ["quartile", "kuartil"],
            ["q1", "kuartil pertama"],
            ["q3", "kuartil ketiga"],
            ["variance", "varians"],
            ["standard deviation", "sisihan piawai"]
        ]
    },

    {
        "form": "Form 4",
        "chapter": "Chapter 9: Probability of Combined Events",
        "strong_signals": [
            ["combined event", "peristiwa bergabung"],
            ["dependent event", "peristiwa bersandar"],
            ["independent event", "peristiwa tak bersandar"],
            ["mutually exclusive", "saling eksklusif"],
            ["non-mutually exclusive", "tak saling eksklusif"],
            ["addition rule", "petua penambahan"],
            ["multiplication rule", "petua pendaraban"],
            ["p(a ∩ b)", "p(a and b)"],
            ["p(a ∪ b)", "p(a or b)"],
            ["tree diagram", "gambar rajah pokok"],
            ["without replacement", "tanpa pemulangan"],
            ["with replacement", "dengan pemulangan"],
            ["probability", "kebarangkalian"],
            ["tree diagram", "gambar rajah pokok"]
        ]
    },

    {
        "form": "Form 4",
        "chapter": "Chapter 10: Consumer Mathematics: Financial Management",
        "strong_signals": [
            ["financial planning", "perancangan kewangan"],
            ["financial management", "pengurusan kewangan"],
            ["financial goal", "matlamat kewangan"],
            ["budget", "belanjawan"],
            ["cash inflow", "aliran tunai masuk"],
            ["cash outflow", "aliran tunai keluar"],
            ["cash flow", "aliran tunai"],
            ["active income", "pendapatan aktif"],
            ["passive income", "pendapatan pasif"],
            ["fixed expenses", "perbelanjaan tetap"],
            ["variable expenses", "perbelanjaan berubah"],
            ["surplus", "lebihan"],
            ["deficit", "defisit"],
            ["emergency fund", "dana kecemasan"]
        ],
        "signals": [
            ["smart", "smart"],
            ["income", "pendapatan"],
            ["savings", "simpanan"]
        ]
    },

    # =========================
    # FORM 5
    # =========================

    {
        "form": "Form 5",
        "chapter": "Chapter 1: Variation",
        "strong_signals": [
            ["variation", "ubahan"],
            ["direct variation", "ubahan langsung"],
            ["inverse variation", "ubahan songsang"],
            ["joint variation", "ubahan tercantum"],
            ["combined variation", "ubahan bergabung"],
            ["varies directly", "berubah secara langsung"],
            ["varies inversely", "berubah secara songsang"],
            ["constant of variation", "pemalar ubahan"],
            ["y ∝ x", "y ∝ 1/x"],
            ["y = kx", "y = k/x"],
            ["power variation", "ubahan kuasa"]
        ],
        "signals": [
            ["constant k", "pemalar k"]
        ]
    },

    {
        "form": "Form 5",
        "chapter": "Chapter 2: Matrices",
        "strong_signals": [
            ["matrix", "matrices", "matriks"],
            ["order of matrix", "peringkat matriks"],
            ["matrix order", "tertib matriks"],
            ["equal matrices", "matriks sama"],
            ["matrix addition", "penambahan matriks"],
            ["matrix subtraction", "penolakan matriks"],
            ["scalar multiplication", "pendaraban skalar"],
            ["matrix multiplication", "pendaraban matriks"],
            ["identity matrix", "matriks identiti"],
            ["inverse matrix", "matriks songsang"],
            ["determinant", "penentu"],
            ["a^-1", "a inverse"],
            ["matrix method", "kaedah matriks"]
        ],
        "signals": [
            ["element", "unsur"],
            ["simultaneous linear equations", "persamaan linear serentak"]
        ]
    },

    {
        "form": "Form 5",
        "chapter": "Chapter 3: Consumer Mathematics: Insurance",
        "strong_signals": [
            ["insurance", "insurans"],
            ["policy", "polisi"],
            ["premium", "premium"],
            ["face value", "nilai muka"],
            ["life insurance", "insurans hayat"],
            ["general insurance", "insurans am"],
            ["motor insurance", "insurans motor"],
            ["fire insurance", "insurans kebakaran"],
            ["medical insurance", "insurans perubatan"],
            ["personal accident", "kemalangan diri"],
            ["travel insurance", "insurans perjalanan"],
            ["deductible", "deduktibel"],
            ["co-insurance", "ko-insurans"],
            ["ncd", "diskaun tanpa tuntutan"],
            ["compensation", "pampasan"],
            ["claim", "tuntutan"],
            ["sum insured", "jumlah diinsuranskan"]
        ],
        "signals": [
            ["risk", "risiko"],
            ["coverage", "perlindungan"]
        ]
    },

    {
        "form": "Form 5",
        "chapter": "Chapter 4: Consumer Mathematics: Taxation",
        "strong_signals": [
            ["tax", "taxation", "cukai", "percukaian"],
            ["income tax", "cukai pendapatan"],
            ["chargeable income", "pendapatan bercukai"],
            ["tax relief", "pelepasan cukai"],
            ["rebate", "rebat"],
            ["zakat", "zakat"],
            ["road tax", "cukai jalan"],
            ["property assessment tax", "cukai pintu"],
            ["quit rent", "cukai tanah"],
            ["sales and service tax", "sst", "cukai jualan dan perkhidmatan"],
            ["tax rate", "kadar cukai"],
            ["tax bracket", "banjaran pendapatan bercukai"],
            ["joint assessment", "taksiran bersama"],
            ["tax evasion", "pengelakan cukai"]
        ],
        "signals": [
            ["donation", "derma"]
        ]
    },

    {
        "form": "Form 5",
        "chapter": "Chapter 5: Congruency, Enlargement and Combined Transformations",
        "signals": [
            ["congruent", "congruency", "kekongruenan"],
            ["sss", "sas", "asa", "aas", "ssa"],
            ["triangle congruency", "kekongruenan segi tiga"],
            ["enlargement", "pembesaran"],
            ["scale factor", "faktor skala"],
            ["area scale factor", "faktor skala luas"],
            ["centre of enlargement", "pusat pembesaran"],
            ["transformation", "transformasi"],
            ["combined transformation", "gabungan transformasi"],
            ["translation", "translasi"],
            ["reflection", "pantulan"],
            ["rotation", "putaran"],
            ["image", "imej"],
            ["object", "objek"],
            ["transformation ab", "transformasi ab"],
            ["reverse transformation", "tertib songsang"],
            ["tessellation", "teselasi"]
        ]
    },

    {
        "form": "Form 5",
        "chapter": "Chapter 6: Ratios and Graphs of Trigonometric Functions",
        "strong_signals": [
            ["trigonometric ratio", "nisbah trigonometri"],
            ["trigonometric graph", "graf trigonometri"],
            ["unit circle", "bulatan unit"],
            ["quadrant", "sukuan"],
            ["reference angle", "sudut rujukan"],
            ["0° ≤ x ≤ 360°", "0 <= x <= 360"],
            ["y = sin x"],
            ["y = cos x"],
            ["y = tan x"],
            ["positive quadrant", "sukuan positif"],
            ["negative quadrant", "sukuan negatif"]
        ],
        "signals": [
            ["sine", "sin"],
            ["cosine", "cos"],
            ["tangent", "tan"]
        ]
    },

    {
        "form": "Form 5",
        "chapter": "Chapter 7: Measures of Dispersion for Grouped Data",
        "min_score": 1,
        "strong_signals": [
            ["grouped data", "data terkumpul"],
            ["class interval", "selang kelas"],
            ["class midpoint", "titik tengah kelas"],
            ["class boundary", "sempadan kelas"],
            ["upper boundary", "sempadan atas"],
            ["lower boundary", "sempadan bawah"],
            ["histogram", "histogram"],
            ["frequency polygon", "poligon kekerapan"],
            ["ogive", "ogif"],
            ["cumulative frequency", "kekerapan longgokan"],
            ["percentile", "persentil"],
            ["modal class", "kelas mod"]
        ],
        "signals": [
            ["midpoint", "titik tengah"],
            ["variance", "varians"],
            ["standard deviation", "sisihan piawai"],
            ["frequency table", "jadual kekerapan"]
        ]
    },

    {
        "form": "Form 5",
        "chapter": "Chapter 8: Mathematical Modelling",
        "strong_signals": [
            ["mathematical modelling", "mathematical modeling", "pemodelan matematik"],
            ["real-world problem", "masalah dunia sebenar"],
            ["identify the problem", "mengenal pasti masalah"],
            ["define the problem", "mentakrif masalah"],
            ["refine model", "menambah baik model"],
            ["reporting findings", "melaporkan dapatan"]
        ],
        "signals": [
            ["model", "model"],
            ["assumption", "andaian"],
            ["variable", "pemboleh ubah"],
            ["verify", "sahkan"],
            ["interpret solution", "mentafsir penyelesaian"],
            ["make a conclusion", "buat kesimpulan"]
        ]
    },
]
FOUNDATION_RULES = [
    {
        "form": "Foundation",
        "chapter": "Foundation: Numbers and Arithmetic",
        "strong_signals": [
            ["integer", "integer"],
            ["fraction", "pecahan"],
            ["decimal", "perpuluhan"],
            ["percentage", "peratus"],
            ["ratio", "nisbah"],
            ["proportion", "kadaran"],
            ["standard form", "bentuk piawai"],
            ["index", "indices", "indeks"],
            ["square root", "punca kuasa dua"],
            ["cube root", "punca kuasa tiga"]
        ]
    },

    {
        "form": "Foundation",
        "chapter": "Foundation: Algebra",
        "strong_signals": [
            ["algebraic expression", "ungkapan algebra"],
            ["algebraic formula", "rumus algebra"],
            ["expand", "kembangkan"],
            ["factorise", "factorize", "faktorkan"],
            ["simplify", "permudahkan"],
            ["substitution", "penggantian"],
            ["subject of formula", "perkara rumus"],
            ["linear expression", "ungkapan linear"]
        ]
    },

    {
        "form": "Foundation",
        "chapter": "Foundation: Linear Equations",
        "strong_signals": [
            ["linear equation", "persamaan linear"],
            ["simultaneous equations", "persamaan serentak"],
            ["solve the equation", "selesaikan persamaan"],
            ["find the value of x", "cari nilai x"],
            ["find the value of y", "cari nilai y"],
            ["unknown", "anu"],
            ["equation in x", "persamaan dalam x"]
        ]
    },

    {
        "form": "Foundation",
        "chapter": "Foundation: Coordinate Geometry",
        "strong_signals": [
            ["coordinate", "koordinat"],
            ["cartesian plane", "satah cartes"],
            ["straight line", "garis lurus"],
            ["gradient", "kecerunan"],
            ["y-intercept", "pintasan-y"],
            ["x-intercept", "pintasan-x"],
            ["equation of straight line", "persamaan garis lurus"],
            ["parallel line", "garis selari"],
            ["perpendicular line", "garis serenjang"],
            ["midpoint", "titik tengah"],
            ["distance between two points", "jarak antara dua titik"]
        ]
    },

    {
        "form": "Foundation",
        "chapter": "Foundation: Geometry",
        "strong_signals": [
            ["angle", "sudut"],
            ["parallel lines", "garis selari"],
            ["transversal", "rentas lintang"],
            ["triangle", "segi tiga"],
            ["polygon", "poligon"],
            ["circle", "bulatan"],
            ["tangent", "tangen"],
            ["chord", "perentas"],
            ["arc", "lengkok"],
            ["sector", "sektor"],
            ["right angle", "sudut tegak"],
            ["interior angle", "sudut pedalaman"],
            ["exterior angle", "sudut peluaran"]
        ]
    },

    {
        "form": "Foundation",
        "chapter": "Foundation: Mensuration",
        "strong_signals": [
            ["area", "luas"],
            ["perimeter", "perimeter"],
            ["circumference", "lilitan"],
            ["volume", "isi padu", "isipadu"],
            ["surface area", "luas permukaan"],
            ["diameter", "diameter"],
            ["radius", "jejari"],
            ["height", "tinggi"],
            ["base area", "luas tapak"],
            ["cylinder", "silinder"],
            ["cone", "kon"],
            ["sphere", "sfera"],
            ["cuboid", "kuboid"],
            ["prism", "prisma"]
        ]
    },

    {
        "form": "Foundation",
        "chapter": "Foundation: Trigonometry",
        "strong_signals": [
            ["pythagoras", "pythagoras"],
            ["hypotenuse", "hipotenus"],
            ["opposite", "bertentangan"],
            ["adjacent", "bersebelahan"],
            ["sin", "sine"],
            ["cos", "cosine"],
            ["tan", "tangent"],
            ["angle of elevation", "sudut dongakan"],
            ["angle of depression", "sudut tunduk"]
        ]
    },

    {
        "form": "Foundation",
        "chapter": "Foundation: Statistics Basics",
        "strong_signals": [
            ["mean", "min"],
            ["median", "median"],
            ["mode", "mod"],
            ["frequency", "kekerapan"],
            ["frequency table", "jadual kekerapan"],
            ["bar chart", "carta palang"],
            ["pie chart", "carta pai"],
            ["line graph", "graf garis"],
            ["pictograph", "piktograf"]
        ]
    },

    {
        "form": "Foundation",
        "chapter": "Foundation: Probability Basics",
        "strong_signals": [
            ["simple probability", "kebarangkalian mudah"],
            ["outcome", "kesudahan"],
            ["sample space", "ruang sampel"],
            ["event", "peristiwa"],
            ["fair dice", "dadu adil"],
            ["coin", "syiling"],
            ["possible outcomes", "kesudahan yang mungkin"]
        ]
    }
]

def build_question_text(q: dict) -> str:
    text = " ".join(q.get("instructions_en", []))
    text += " " + " ".join(q.get("instructions_ms", []))
    text += " " + " ".join(q.get("equations", []))
    text += " " + " ".join(q.get("expressions", []))
    text += " " + str(q.get("question_type", ""))
    text += " " + str(q.get("diagram_type", ""))
    text += " " + str(q.get("visual_semantic_summary", ""))
    
    # Extract values only, ignore keys!
    if isinstance(q.get("table_data"), dict):
        text += " " + str(q["table_data"])
        
    given_vals = q.get("given_values", {})
    if isinstance(given_vals, dict):
        text += " " + " ".join(str(v) for v in given_vals.values())
        
    constraints = q.get("constraints", {})
    if isinstance(constraints, dict):
        text += " " + " ".join(str(v) for v in constraints.values())
        
    return text


def get_best_rule_match(text: str, rules: list):
    best_rule = None
    best_score = 0
    best_matches = []

    for rule in rules:
        strong_groups = rule.get("strong_signals", [])
        normal_groups = rule.get("signals", [])
        strong_score = 0
        normal_score = 0
        strong_score, strong_matched = count_matched_signal_groups(text, strong_groups)
        normal_score, normal_matched = count_matched_signal_groups(text, normal_groups)

        # Strong signal is worth 2 points
        score = (strong_score * 2) + normal_score
        matched = strong_matched + normal_matched

        if score > best_score:
            best_score = score
            best_rule = rule
            best_matches = matched

    if best_rule is None:
        return None

    return {
        "rule": best_rule,
        "score": best_score,
        "matched": best_matches
    }
def difficulty_label_from_score(score: float):
    if score <= 3:
        level = 1
    elif score <= 4:
        level = 2
    elif score <= 6:
        level = 3
    elif score <= 8:
        level = 4
    else:
        level = 5

    if level <= 2:
        label = "Easy"
    elif level == 3:
        label = "Moderate"
    else:
        label = "Hard"

    return level, label

def confidence_from_score(score: int, max_confidence: float = 0.95) -> float:
    """
    Score 1 = weak
    Score 2 = acceptable
    Score 3+ = strong
    """
    if score <= 0:
        return 0.0
    if score == 1:
        return 0.45
    if score == 2:
        return 0.68
    if score == 3:
        return 0.82
    return max_confidence


def normalize_text(text: str) -> str:
    text = str(text or "").lower()

    # normalize common symbols
    text = text.replace("²", "^2")
    text = text.replace("−", "-")
    text = text.replace("≤", "<=")
    text = text.replace("≥", ">=")
    # Use a safer replacement for bases
    text = text.replace("₂", "base_2")
    text = text.replace("₈", "base_8")
    text = text.replace("₁₀", "base_10")

    # normalize spacing
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def phrase_exists(text: str, phrase: str) -> bool:
    phrase = normalize_text(phrase)

    if not phrase:
        return False

    # If phrase has symbols, use simple substring match
    if re.search(r"[^a-z0-9\s]", phrase):
        return phrase in text

    # For normal words, use word boundaries
    pattern = r"\b" + re.escape(phrase) + r"\b"
    return re.search(pattern, text) is not None


def count_matched_signal_groups(text: str, signal_groups: list) -> tuple[int, list]:
    """
    Counts each concept only once.

    Example:
    ["quadratic", "kuadratik"] = 1 concept.
    If both appear in bilingual paper, score is still +1 only.
    """
    text = normalize_text(text)

    score = 0
    matched = []

    for group in signal_groups:
        if any(phrase_exists(text, variant) for variant in group):
            score += 1
            matched.append(group[0])  # store canonical signal

    return score, matched

def classify_form_chapter(q: dict) -> dict:
    text = build_question_text(q)

    best_main = get_best_rule_match(text, CHAPTER_RULES)

    if best_main:
        min_score = best_main["rule"].get("min_score", 2)

        if best_main["score"] >= min_score:
            confidence = confidence_from_score(best_main["score"], max_confidence=0.95)

            return {
                "verified_form": best_main["rule"]["form"],
                "verified_chapter": best_main["rule"]["chapter"],
                "classification_confidence": round(confidence, 2),
                "classification_status": "verified",
            }

    best_foundation = get_best_rule_match(text, FOUNDATION_RULES)

    if best_foundation:
        min_score = best_foundation["rule"].get("min_score", 2)

        if best_foundation["score"] >= min_score:
            confidence = confidence_from_score(best_foundation["score"], max_confidence=0.85)

            return {
                "verified_form": best_foundation["rule"]["form"],
                "verified_chapter": best_foundation["rule"]["chapter"],
                "classification_confidence": round(confidence, 2),
                "classification_status": "foundation_verified",
            }

    return {
        "verified_form": "",
        "verified_chapter": "",
        "classification_confidence": 0.0,
        "classification_status": "needs_review",
    }

def apply_verified_chapters(questions: list) -> list:
    for q in questions:
        result = classify_form_chapter(q)
        q.update(result)

        status = result.get("classification_status", "")

        if status in ["verified", "foundation_verified"]:
            # Trust classifier
            q["form"] = result.get("verified_form", "")
            q["chapter"] = result.get("verified_chapter", "")

        else:
            # Do NOT trust LLM form/chapter
            q["verified_form"] = ""
            q["verified_chapter"] = ""
            q["form"] = ""
            q["chapter"] = ""
            q["classification_status"] = "needs_review"

    return questions


def apply_question_grouping(questions: list, paper_prefix: str) -> list:
    groups = defaultdict(list)

    for q in questions:
        qno = str(q.get("question_no", "")).strip()
        if not qno:
            continue

        group_id = f"{paper_prefix}_Q{qno}"
        q["group_id"] = group_id
        groups[group_id].append(q)

    for group_id, items in groups.items():
        levels = []

        for q in items:
            try:
                levels.append(int(q.get("difficulty_level", 3)))
            except (TypeError, ValueError):
                levels.append(3)

        group_level = max(levels) if levels else 3

        for q in items:
            q["group_difficulty_level"] = group_level

    return questions

def apply_marking_grouping(markings: list, paper_prefix: str) -> list:
    for m in markings:
        qno = str(m.get("question_no", "")).strip()
        if qno:
            m["group_id"] = f"{paper_prefix}_Q{qno}"

    return markings

def inherit_group_chapter_for_blank_parts(questions: list) -> list:
    groups = defaultdict(list)

    for q in questions:
        group_id = str(q.get("group_id", "")).strip()
        if group_id:
            groups[group_id].append(q)

    for group_id, items in groups.items():
        confident_items = [
            q for q in items
            if q.get("verified_form")
            and q.get("verified_chapter")
            and q.get("classification_status") in ["verified", "foundation_verified"]
        ]

        if not confident_items:
            continue

        chapter_pairs = [
            (q.get("verified_form", ""), q.get("verified_chapter", ""))
            for q in confident_items
        ]

        unique_pairs = set(chapter_pairs)

        for q in items:
            # Do not overwrite already-classified questions
            if q.get("verified_form") and q.get("verified_chapter"):
                continue

            # Case 1: whole group has only one confident chapter
            # Safe to inherit
            if len(unique_pairs) == 1:
                best_form, best_chapter = list(unique_pairs)[0]

                q["verified_form"] = best_form
                q["verified_chapter"] = best_chapter
                q["form"] = best_form
                q["chapter"] = best_chapter
                q["classification_status"] = "inherited_from_group"
                q["classification_confidence"] = 0.0

            # Case 2: mixed group
            # Try same page/stage only
            else:
                same_stage_items = [
                    item for item in confident_items
                    if item.get("exercise_stage_id") == q.get("exercise_stage_id")
                ]

                same_stage_pairs = set(
                    (item.get("verified_form", ""), item.get("verified_chapter", ""))
                    for item in same_stage_items
                )

                if len(same_stage_pairs) == 1:
                    best_form, best_chapter = list(same_stage_pairs)[0]

                    q["verified_form"] = best_form
                    q["verified_chapter"] = best_chapter
                    q["form"] = best_form
                    q["chapter"] = best_chapter
                    q["classification_status"] = "inherited_from_stage"
                    q["classification_confidence"] = 0.0
                else:
                    q["classification_status"] = "needs_review"

    return questions


def is_confident_chapter(q: dict) -> bool:
    status = str(q.get("classification_status", "")).strip()

    return (
        q.get("verified_form")
        and q.get("verified_chapter")
        and status in ["verified", "foundation_verified", "inherited_from_group"]
    )

def apply_group_form_chapter(questions: list) -> list:
    groups = defaultdict(list)

    for q in questions:
        group_id = str(q.get("group_id", "")).strip()
        if group_id:
            groups[group_id].append(q)

    for group_id, items in groups.items():
        confident_items = [q for q in items if is_confident_chapter(q)]

        if not confident_items:
            group_form = ""
            group_chapter = "Mixed"
        else:
            chapter_pairs = [
                (q.get("verified_form", ""), q.get("verified_chapter", ""))
                for q in confident_items
                if q.get("verified_form") and q.get("verified_chapter")
            ]

            counts = Counter(chapter_pairs)

            if len(counts) == 1:
                group_form, group_chapter = list(counts.keys())[0]
            else:
                group_form = ""
                group_chapter = "Mixed"

        for q in items:
            q["group_form"] = group_form
            q["group_chapter"] = group_chapter

            # Only inherit chapter if the whole group is clearly same chapter
            if (
                group_chapter != "Mixed"
                and (not q.get("verified_form") or not q.get("verified_chapter"))
            ):
                q["verified_form"] = group_form
                q["verified_chapter"] = group_chapter
                q["form"] = group_form
                q["chapter"] = group_chapter
                q["classification_status"] = "inherited_from_group"

    return questions

def get_first_source_page(q: dict) -> int:
    try:
        return int(q.get("_page_no", 0) or 0)
    except (TypeError, ValueError):
        return 0


def assign_exercise_stages_by_page(questions: list) -> list:
    groups = defaultdict(list)

    for q in questions:
        group_id = str(q.get("group_id", "")).strip()
        if group_id:
            groups[group_id].append(q)

    for group_id, items in groups.items():
        pages = sorted({
            get_first_source_page(q)
            for q in items
            if get_first_source_page(q) > 0
        })

        if not pages:
            pages = [1]

        page_to_stage = {
            page: index + 1
            for index, page in enumerate(pages)
        }

        for q in items:
            page = get_first_source_page(q)
            stage_index = page_to_stage.get(page, 1)

            q["stage_index"] = stage_index
            q["exercise_stage_id"] = f"{group_id}_S{stage_index}"

            if stage_index > 1:
                q["unlock_after_stage_id"] = f"{group_id}_S{stage_index - 1}"
            else:
                q["unlock_after_stage_id"] = ""

    return questions

def sync_display_marks_from_markings(questions: list, markings: list) -> list:
    marking_map = {}

    for m in markings:
        key = (
            str(m.get("question_no", "")).strip(),
            str(m.get("part", "")).strip(),
            str(m.get("subpart", "")).strip(),
            str(m.get("sub_subpart", "")).strip()
        )

        marking_map[key] = m

    for q in questions:
        key = (
            str(q.get("question_no", "")).strip(),
            str(q.get("part", "")).strip(),
            str(q.get("subpart", "")).strip(),
            str(q.get("sub_subpart", "")).strip()
        )

        m = marking_map.get(key)

        if m:
            try:
                q["display_marks"] = float(m.get("subpart_marks", 0) or 0)
                q["marks_source"] = "marking_scheme"
            except (TypeError, ValueError):
                q["display_marks"] = q.get("marks", 0)
                q["marks_source"] = "question_extraction_fallback"
        else:
            q["display_marks"] = q.get("marks", 0)
            q["marks_source"] = "question_extraction"

    return questions

def apply_group_difficulty_from_stage_logic(questions: list) -> list:
    """
    Calculates group_difficulty_level for the whole exam question.

    Logic:
    - Same page/stage subparts are combined.
    - Diagram/table is counted once per stage, not once per subpart.
    - Then all stage scores are added to form the full group difficulty.
    """

    groups = defaultdict(list)

    for q in questions:
        group_id = str(q.get("group_id", "")).strip()
        if group_id:
            groups[group_id].append(q)

    for group_id, group_items in groups.items():
        stages = defaultdict(list)

        for q in group_items:
            stage_id = str(q.get("exercise_stage_id", "")).strip()

            # fallback if stage_id is missing
            if not stage_id:
                stage_id = f"{group_id}_S1"

            stages[stage_id].append(q)

        group_score = 0.0

        for stage_id, stage_items in stages.items():
            stage_core_score = 0.0

            for q in stage_items:
                try:
                    stage_core_score += float(q.get("difficulty_core_score", 0) or 0)
                except (TypeError, ValueError):
                    pass

            # Count visual/table once per displayed page/stage
            has_any_diagram = any(bool(q.get("has_diagram", False)) for q in stage_items)
            has_any_table = any(bool(q.get("table_data", {})) for q in stage_items)

            stage_visual_bonus = 0.0

            if has_any_diagram:
                stage_visual_bonus += 1

            if has_any_table:
                stage_visual_bonus += 1

            stage_score = stage_core_score + stage_visual_bonus
            group_score += stage_score

        group_level, group_label = difficulty_label_from_score(group_score)

        for q in group_items:
            q["group_difficulty_level"] = group_level
            q["group_difficulty"] = group_label

    return questions