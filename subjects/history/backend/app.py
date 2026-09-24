from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials, firestore, auth
from flask_cors import CORS
import random, json
from datetime import datetime
import torch
import numpy as np
import re
from sentence_transformers import SentenceTransformer, util
from google import genai

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://easy-learn-fe.vercel.app", "http://localhost:3000"]}}, supports_credentials= True)

# 1. Load the Semantic Model once at startup
# Using 'all-MiniLM-L6-v2' as it is efficient for local deployment
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Firebase
cred = credentials.Certificate("sejarah-app-a47cb-firebase-adminsdk-fbsvc-7b55baca5e.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
questions_ref = db.collection('Question')
options_ref = db.collection('Option')
user_interactions_ref = db.collection('user_interactions')


def interaction_correct_value(record):
    """Return a safe 0/1 value for both legacy and unified Firestore events."""
    value = record.get("is_correct")
    if value is None:
        percentage = record.get("percentage")
        if percentage is not None:
            try:
                return int(float(percentage) >= 50)
            except (TypeError, ValueError):
                pass
        score = record.get("score")
        max_score = record.get("max_score")
        if score is not None and max_score:
            try:
                return int(float(score) >= (float(max_score) / 2))
            except (TypeError, ValueError, ZeroDivisionError):
                pass
        return 0
    if isinstance(value, str):
        return int(value.strip().lower() in {"1", "true", "yes", "correct"})
    return int(bool(value))

# 🔹 Load JSON files into memory once at startup
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

with open("options.json", "r", encoding="utf-8") as f:
    OPTIONS = json.load(f)

# 🔹 Load the new Bucket Game JSON into memory at startup
with open("game.json", "r", encoding="utf-8") as f:
    BUCKET_GAME_DATA = json.load(f)

# Verify Firebase ID Token
@app.route('/verify_token', methods=['POST'])
def verify_token():
    try:
        data = request.get_json()
        id_token = data.get("token")

        if not id_token:
            return jsonify({"error": "Missing token"}), 400

        # Verify the token with Firebase Admin SDK
        decoded = auth.verify_id_token(id_token)

        # Extract user info from Google OAuth
        uid = decoded["uid"]
        email = decoded.get("email")
        name = decoded.get("name")
        picture = decoded.get("picture")

        return jsonify({
            "message": "Token verified successfully",
            "uid": uid,
            "email": email,
            "name": name,
            "picture": picture
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 401

# Fetch all questions
@app.route('/questions', methods=['GET'])
def get_questions():
    questions = [ {**doc.to_dict(), "id": doc.id} for doc in questions_ref.stream() ]
    return jsonify(questions), 200

@app.route('/question/<id>', methods=['GET'])
def get_question(id):
    # Firestore stores numbers as int, so convert id to int if needed
    try:
        id = int(id)
    except ValueError:
        return jsonify({"error": "Invalid question ID"}), 400

    # Query Firestore
    docs = questions_ref.where("question_id", "==", id).stream()

    # Convert to list
    result = [doc.to_dict() for doc in docs]

    if not result:
        return jsonify({"error": "Question not found"}), 404

    # If there should only be one, return the first one
    return jsonify(result[0]), 200


# Fetch questions by chapter with options
# @app.route('/questions/chapter', methods=['GET'])
# def get_questions_by_chapter():
#     # Get query parameter ?chapter=1
#     chapter = request.args.get('chapter', type=int)
#
#     if chapter is None:
#         return jsonify({"error": "Missing 'chapter' parameter"}), 400
#
#     # 1️⃣ Filter questions by chapter
#     questions = [
#         {**doc.to_dict(), "id": doc.id}
#         for doc in questions_ref.where("chapter", "==", chapter).stream()
#     ]
#
#     if not questions:
#         return jsonify({"error": "No questions found for this chapter"}), 404
#
#     # 2️⃣ Randomly select up to 5
#     selected = random.sample(questions, min(5, len(questions)))
#
#     result = []
#
#     for q in selected:
#         qid = q["question_id"]
#
#         # 3️⃣ Fetch all options with matching question_id
#         opts = [
#             opt.to_dict()
#             for opt in options_ref.where("question_id", "==", qid).stream()
#         ]
#
#         # Optional: shuffle options for variety
#         random.shuffle(opts)
#
#         # 4️⃣ Combine question + options
#         result.append({
#             "question_id": qid,
#             "question": q["question"],
#             "chapter": q["chapter"],
#             "form": q["form"],
#             "explaination": q["explaination"],
#             "options": opts
#         })
#
#     return jsonify(result), 200

@app.route('/questions/chapter', methods=['GET'])
def get_questions_by_chapter(chapter=None):
    # Get ?chapter=1
    if chapter is None:
        chapter = request.args.get('chapter', type=int)
    if chapter is None:
        return jsonify({"error": "Missing 'chapter' parameter"}), 400

    # 1️⃣ Filter questions by chapter
    questions = [q for q in QUESTIONS if int(q.get("chapter", 0)) == chapter]
    if not questions:
        return jsonify({"error": "No questions found for this chapter"}), 404

    # 2️⃣ Randomly select up to 5 questions
    selected = random.sample(questions, min(5, len(questions)))

    # 3️⃣ Build result with options
    result = []
    for q in selected:
        qid = str(q.get("question id"))  # match string type

        # Match options with same question id
        opts = [
            {
                "option_id": o.get("option id"),
                "option_text": o.get("option text"),
                "is_correct": int(o.get("is correct", "0")),
            }
            for o in OPTIONS if str(o.get("question id")) == qid
        ]

        random.shuffle(opts)

        result.append({
            "question_id": qid,
            "question": q.get("question"),
            "chapter": int(q.get("chapter")),
            "form": int(q.get("form")),
            "explaination": q.get("explaination"),
            "options": opts
        })

    return jsonify(result), 200

# Fetch dashboard data
@app.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    # 1. Get the Authorization header
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    try:
        # 2. Extract the token (Remove "Bearer " prefix if present)
        id_token = auth_header.split(" ")[1] if " " in auth_header else auth_header

        # 3. Verify the token with Firebase to get the secure UID
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']  # <--- This is the SECURE uid

        # 4. Proceed with your existing query using this secure uid
        docs = user_interactions_ref.where("user_uid", "==", uid) \
            .order_by("timestamp", direction=firestore.Query.DESCENDING) \
            .stream()

        interactions = [doc.to_dict() for doc in docs]

        # --- (Rest of your calculation logic remains exactly the same) ---
        if not interactions:
            return jsonify({
                "streak": 0,
                "average_score": 0,
                "total_questions": 0,
                "total_minutes": 0.0,
                "history": []
            }), 200

        total_correct = 0
        total_questions = len(interactions)
        total_minutes = 0.0
        unique_activity_dates = set()
        daily_stats = {}

        for record in interactions:
            is_correct = interaction_correct_value(record)
            total_correct += is_correct
            ts = record.get("timestamp")
            if ts:
                date_obj = ts.date() if hasattr(ts, 'date') else ts.replace(tzinfo=None).date()
                date_str = date_obj.strftime("%Y-%m-%d")
                unique_activity_dates.add(date_obj)
                if date_str not in daily_stats:
                    daily_stats[date_str] = {"correct": 0, "total": 0, "minutes": 0.0}

                # New EasyLearn History events store the real elapsed question
                # time as time_taken_ms. Older records may not have it; those
                # contribute 0 minutes rather than an invented estimate.
                duration_minutes = 0.0
                try:
                    if record.get("time_taken_ms") is not None:
                        duration_minutes = max(0.0, float(record.get("time_taken_ms") or 0) / 60000.0)
                    elif record.get("duration_minutes") is not None:
                        duration_minutes = max(0.0, float(record.get("duration_minutes") or 0))
                except (TypeError, ValueError):
                    duration_minutes = 0.0

                total_minutes += duration_minutes
                daily_stats[date_str]["total"] += 1
                daily_stats[date_str]["correct"] += is_correct
                daily_stats[date_str]["minutes"] += duration_minutes

        average_score = round((total_correct / total_questions) * 100, 1) if total_questions > 0 else 0

        sorted_dates = sorted(list(unique_activity_dates), reverse=True)
        streak = 0
        today = datetime.now().date()

        if sorted_dates:
            latest_activity = sorted_dates[0]
            if (today - latest_activity).days > 1:
                streak = 0
            else:
                streak = 1
                for i in range(len(sorted_dates) - 1):
                    if (sorted_dates[i] - sorted_dates[i + 1]).days == 1:
                        streak += 1
                    else:
                        break

        history_data = []
        for date_key, stats in daily_stats.items():
            accuracy = round((stats["correct"] / stats["total"]) * 100, 1)
            history_data.append({
                "date": date_key,
                "accuracy": accuracy,
                "questions_answered": stats["total"],
                "minutes": round(stats.get("minutes", 0.0), 1)
            })
        history_data.sort(key=lambda x: x['date'])

        return jsonify({
            "streak": streak,
            "average_score": average_score,
            "total_questions": total_questions,
            "total_minutes": round(total_minutes, 1),
            "history": history_data
        }), 200

    except Exception as e:
        return jsonify({"error": "Invalid Token", "details": str(e)}), 401


# Fetch Bucket & Card Game Data
@app.route('/game/bucket', methods=['GET'])
def get_bucket_game():
    # Get subtopic from query param, e.g., ?subtopic=1.1
    subtopic = request.args.get('subtopic')

    if not subtopic:
        return jsonify({"error": "Missing 'subtopic' parameter"}), 400

    # Find the matching chapter in your list
    game_set = next((item for item in BUCKET_GAME_DATA if item["chapter"] == subtopic), None)

    if not game_set:
        return jsonify({"error": "Game data not found for this subtopic"}), 404

    # Optional: Shuffle cards before sending to frontend so every game is different
    random.shuffle(game_set["cards"])

    return jsonify(game_set), 200

# ========================= Recommended Question =======================
from cskt import CSKT

student_chapter_mastery_ref = db.collection('recommend_quiz')
MODEL_PARAMS = {
    "n_question": 11,
    "n_pid": 312,
    "d_model": 256,
    "n_blocks": 3,
    "dropout": 0.6,
}

kt_model = None
try:
    kt_model = CSKT(**MODEL_PARAMS) # Uncomment when you have the class imported
    state_dict = torch.load("cskt_best_model.pth", map_location="cpu", weights_only=False)
    if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
        state_dict = state_dict["model_state_dict"]
    kt_model.load_state_dict(state_dict)
    kt_model.eval()

    # Placeholder for the loaded model to prevent errors before you import the class
    # kt_model = None
    print("✅ CSKT Model loaded successfully.")
except Exception as e:
    print(f"⚠️ Failed to load CSKT model: {e}")
    kt_model = None

def parse_chapter_id(raw):
    """Extract numeric chapter from any format: 'ch3', 'chp3', '3' -> 3. Returns None if invalid."""
    digits = ''.join(filter(str.isdigit, str(raw)))
    return int(digits) if digits else None


def mastery_dict_to_list(mastery_dict):
    """Convert {chapter_str: score} dict -> sorted list of {chapter, mastery} objects."""
    result = []
    for ch_key, score in mastery_dict.items():
        ch_num = parse_chapter_id(ch_key)
        if ch_num is not None:
            result.append({"chapter": ch_num, "mastery": score})
    result.sort(key=lambda x: x["chapter"])
    return result

def compute_mastery_tensor(model, q_encoded, c_encoded, r, c_mapping_inv, max_seq_len=200):
    """Handles the PyTorch tensor math and inference."""
    q_arr = np.array(q_encoded, dtype=np.int64)
    c_arr = np.array(c_encoded, dtype=np.int64)
    r_arr = np.array(r, dtype=np.int64)

    length = len(q_arr)
    if length < 2:
        return {}  # Requires at least 2 interactions to form a sequence

    pad_len = max(0, max_seq_len - length)
    q_pad = np.pad(q_arr, (0, pad_len))
    c_pad = np.pad(c_arr, (0, pad_len))
    r_pad = np.pad(r_arr, (0, pad_len))

    # Prepare current and shifted sequences
    dcur = {
        "qseqs": torch.tensor(q_pad[:-1]).unsqueeze(0).long(),
        "cseqs": torch.tensor(c_pad[:-1]).unsqueeze(0).long(),
        "rseqs": torch.tensor(r_pad[:-1]).unsqueeze(0).long(),
        "shft_qseqs": torch.tensor(q_pad[1:]).unsqueeze(0).long(),
        "shft_cseqs": torch.tensor(c_pad[1:]).unsqueeze(0).long(),
        "shft_rseqs": torch.tensor(r_pad[1:]).unsqueeze(0).long(),
    }

    with torch.no_grad():
        output = model(dcur, train=False)
        preds = output[0] if isinstance(output, tuple) else output

    preds_np = preds.squeeze(0).cpu().numpy()
    full_c = np.concatenate([c_pad[:-1][:1], c_pad[1:]])

    mastery = {}
    all_chapter_ids = set(c_encoded)
    all_chapter_ids.discard(0)  # Remove padding ID

    for encoded_id in all_chapter_ids:
        chapter_mask = full_c == encoded_id
        if chapter_mask.sum() > 0:
            score = float(np.clip(preds_np[chapter_mask].mean(), 0.0, 1.0))
            chapter_label = c_mapping_inv.get(encoded_id, str(encoded_id))
            mastery[chapter_label] = round(score, 4)

    return mastery



def predict_quiz_mastery(student_id):
    """Core function: Fetch from Firebase -> Preprocess -> Predict"""
    # 1. Retrieve the student's learning history from Firestore
    docs = user_interactions_ref.where("user_uid", "==", student_id) \
        .order_by("timestamp", direction=firestore.Query.ASCENDING) \
        .stream()
    # interactions = [doc.to_dict() for doc in docs]

    interactions = []

    for doc in docs:
        data = doc.to_dict()

        # Convert ch1/ch2/ch3 -> 1/2/3
        chapter_str = str(data.get("chapter_id", data.get("chapter", "")))  # example: ch3
        # Strip any non-numeric prefix (handles "ch3", "chp3", "3", etc.)
        chapter_id = int(''.join(filter(str.isdigit, chapter_str))) if any(c.isdigit() for c in chapter_str) else 0

        data["chapter_id"] = chapter_id

        interactions.append(data)

    if len(interactions) < 2:
        return {"error": "Not enough data. Student needs at least 2 interactions."}

    # 2. Preprocess data (Map string IDs to 1-indexed integers for PyTorch)
    unique_qs = list({str(i.get("question_id")) for i in interactions})
    unique_cs = list({str(i.get("chapter_id")) for i in interactions})  # Use cleaned int chapter_id

    q_map = {qid: idx + 1 for idx, qid in enumerate(unique_qs)}
    c_map = {cid: idx + 1 for idx, cid in enumerate(unique_cs)}
    c_map_inv = {v: k for k, v in c_map.items()}

    q_enc = [q_map[str(i.get("question_id"))] for i in interactions]
    c_enc = [c_map[str(i.get("chapter_id"))] for i in interactions]  # Use cleaned int chapter_id
    r = [interaction_correct_value(i) for i in interactions]

    # 3. Load and run model
    if not kt_model:
        # Mock data for testing until model is fully imported
        return {ch: round(random.uniform(0.3, 0.95), 4) for ch in unique_cs}

    mastery = compute_mastery_tensor(kt_model, q_enc, c_enc, r, c_map_inv)
    return mastery


# APIs
@app.route('/quiz/mastery', methods=['POST'])
def get_student_mastery():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    try:
        # 2. Extract and verify the token
        id_token = auth_header.split(" ")[1] if " " in auth_header else auth_header
        decoded_token = auth.verify_id_token(id_token)

        # 3. Get the SECURE uid directly from Firebase
        user_uid = decoded_token['uid']

    except Exception as e:
        return jsonify({"error": "Invalid Token", "details": str(e)}), 401

    mastery_levels = predict_quiz_mastery(user_uid)

    # Returns a dict with 'error' on failure, or a list [{chapter, mastery}] on success
    if isinstance(mastery_levels, dict) and "error" in mastery_levels:
        return jsonify(mastery_levels), 400

    return jsonify({
        "user_uid": user_uid,
        "mastery_levels": mastery_levels  # Sorted list: [{chapter: 1, mastery: 0.93}, ...]
    }), 200


@app.route('/quiz/recommendation', methods=['POST'])
def generate_recommendation():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    try:
        # 2. Extract and verify the token
        id_token = auth_header.split(" ")[1] if " " in auth_header else auth_header
        decoded_token = auth.verify_id_token(id_token)

        # 3. Get the SECURE uid directly from Firebase
        user_uid = decoded_token['uid']

    except Exception as e:
        return jsonify({"error": "Invalid Token", "details": str(e)}), 401

    mastery_levels = predict_quiz_mastery(user_uid)

    if "error" in mastery_levels:
        return jsonify(mastery_levels), 400

    # Find the chapter with the LOWEST mastery level
    lowest_chapter = min(mastery_levels, key=mastery_levels.get)
    lowest_score = mastery_levels[lowest_chapter]

    # Check if a recommendation record already exists for this user
    existing_docs = student_chapter_mastery_ref.where("user_uid", "==", user_uid).limit(1).stream()

    # We use a flag to track if we found and updated a document
    is_update = False

    for doc in existing_docs:
        # Record exists! Update it.
        student_chapter_mastery_ref.document(doc.id).update({
            "chapter_id": lowest_chapter,
            "mastery_prob": lowest_score,
            "last_updated": firestore.SERVER_TIMESTAMP
        })
        is_update = True
        break  # We only expect one record per user, so we can stop after the first match

    if not is_update:
        # No record exists! Add a new one.
        student_chapter_mastery_ref.add({
            "chapter_id": lowest_chapter,
            "mastery_prob": lowest_score,
            "user_uid": user_uid,
            "last_updated": firestore.SERVER_TIMESTAMP
        })

    return jsonify({
        "message": "Recommendation updated successfully" if is_update else "Recommendation added successfully",
        "recommendation": {
            "chapter_id": lowest_chapter,
            "mastery_prob": lowest_score,
            "user_uid": user_uid,
            "last_updated": "SERVER_TIMESTAMP"
            # Sent as string to avoid JSON serialization errors with Firestore objects
        }
    }), 200


@app.route('/allStudent/quiz/mastery', methods=['GET'])
def get_all_students_mastery():
    try:
        # Fetch ALL interactions to avoid N+1 querying (querying the DB for every single user)
        docs = user_interactions_ref.stream()

        # Group interactions by user_uid in memory
        user_histories = {}  # uid -> {email, interactions}
        for doc in docs:
            data = doc.to_dict()
            uid = data.get("user_uid")
            if uid:
                if uid not in user_histories:
                    user_histories[uid] = {
                        "email": data.get("user_email", ""),
                        "interactions": []
                    }
                user_histories[uid]["interactions"].append(data)

        results = []

        for uid, user_data in user_histories.items():
            interactions = user_data["interactions"]
            user_email = user_data["email"]

            # Sort by timestamp for sequential processing
            interactions.sort(key=lambda x: x.get("timestamp"))

            if len(interactions) < 2:
                continue

            # Parse and clean chapter IDs, skip invalid records
            clean_interactions = []
            for i in interactions:
                raw = i.get("chapter_id", i.get("chapter", ""))
                ch = parse_chapter_id(raw)
                if ch is not None:
                    i["chapter_id"] = ch
                    clean_interactions.append(i)
            if len(clean_interactions) < 2:
                continue

            # Preprocess inline for batch efficiency
            unique_qs = list({str(i.get("question_id")) for i in clean_interactions})
            unique_cs = list({str(i.get("chapter_id")) for i in clean_interactions})

            q_map = {qid: idx + 1 for idx, qid in enumerate(unique_qs)}
            c_map = {cid: idx + 1 for idx, cid in enumerate(unique_cs)}
            c_map_inv = {v: k for k, v in c_map.items()}

            q_enc = [q_map[str(i.get("question_id"))] for i in clean_interactions]
            c_enc = [c_map[str(i.get("chapter_id"))] for i in clean_interactions]
            r = [interaction_correct_value(i) for i in clean_interactions]

            if not kt_model:
                # Mock result if model isn't hooked up yet
                mastery_dict = {ch: round(random.uniform(0.3, 0.95), 4) for ch in unique_cs}
                mastery = mastery_dict_to_list(mastery_dict)
            else:
                mastery_dict = compute_mastery_tensor(kt_model, q_enc, c_enc, r, c_map_inv)
                mastery = mastery_dict_to_list(mastery_dict)

            results.append({
                "user_uid": uid,
                "user_email": user_email,
                "total_interactions": len(clean_interactions),
                "mastery_levels": mastery  # Sorted list: [{chapter: 1, mastery: 0.93}, ...]
            })

        return jsonify({
            "total_students_processed": len(results),
            "student_masteries": results
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/recommend/quiz', methods=['GET'])
def get_recommended_quiz():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    try:
        id_token = auth_header.split(" ")[1] if " " in auth_header else auth_header
        decoded_token = auth.verify_id_token(id_token)
        user_uid = decoded_token['uid']
    except Exception as e:
        return jsonify({"error": "Invalid Token", "details": str(e)}), 401

    # 1. Look up the recommended chapter for this user from recommend_quiz collection
    docs = list(student_chapter_mastery_ref.where("user_uid", "==", user_uid).limit(1).stream())

    if not docs:
        return jsonify({"error": "No recommendation found. Call POST /quiz/recommendation first."}), 404

    rec_data = docs[0].to_dict()
    chapter = rec_data.get("chapter_id")

    # chapter_id may be stored as string or int, ensure it's an int
    try:
        chapter = int(chapter)
    except (TypeError, ValueError):
        return jsonify({"error": f"Invalid chapter_id in recommendation: {chapter}"}), 500

    # 2. Delegate to get_questions_by_chapter, passing chapter directly
    return get_questions_by_chapter(chapter=chapter)


#==========================Essay Marking===================================

# 2. Initialize Grader with your essay.json data
with open("essay.json", "r", encoding="utf-8") as f:
    ESSAY_DB = json.load(f)

# API 1: --------------GET QUESTION ------------------
@app.route('/essay/get', methods=['GET'])
def get_random_essay():
    # 1. Get the chapter from the URL (e.g., ?chapter=1)
    chapter = request.args.get('chapter', type=int)

    # 2. Find all questions for this chapter
    candidates = [q for q in ESSAY_DB if q.get("chapter") == chapter]

    if not candidates:
        return jsonify({"error": "No questions found"}), 404

    # 3. Pick one random question
    selected = random.choice(candidates)

    # 4. Return ONLY what the user needs to see (NO ANSWER SCHEME)
    return jsonify({
        "question_id": selected["question_id"],
        "section_type": selected["section_type"],
        "question_text": selected["question_text"],
        "total_marks": selected["total_marks"]
    }), 200


# API 2: -----------------SUBMIT ANSWER----------------------
class SejarahGrader:
    def __init__(self, data_list):
        self.db = data_list # List of dictionaries
        self.similarity_threshold = 0.65

    def find_question(self, section_type, q_id):
        """Locates the question in the flat list."""
        for q in self.db:
            # Check all 3 identifiers to be unique
            if (q['section_type'] == section_type and
                q['question_id'] == q_id):
                return q
        return None

    def grade(self, section_type, q_id, student_text):
        q_data = self.find_question(section_type, q_id)
        if not q_data:
            return {"error": "Question not found"}

        scheme = q_data['answer_scheme']
        max_marks = q_data['total_marks']

        # Segment student text
        student_sentences = re.split(r'[.!?]\s*', student_text.strip())
        student_sentences = [s for s in student_sentences if len(s) > 5]

        if not student_sentences:
            return {"question_id": q_id, "marks_awarded": 0, "total_marks": max_marks, "breakdown": []}

        # Vectorize
        scheme_embeddings = model.encode(scheme, convert_to_tensor=True)
        student_embeddings = model.encode(student_sentences, convert_to_tensor=True)

        awarded_marks = 0
        matched_indices = set()
        details = []

        for i, s_embed in enumerate(student_embeddings):
            cosine_scores = util.cos_sim(s_embed, scheme_embeddings)[0]
            best_score = float(max(cosine_scores))
            best_idx = int(cosine_scores.argmax())

            if best_score >= self.similarity_threshold:
                if best_idx not in matched_indices:
                    awarded_marks += 1
                    matched_indices.add(best_idx)
                    details.append({
                        "student_sentence": student_sentences[i],
                        "matched_fact": scheme[best_idx],
                        "score": round(best_score, 2)
                    })

            if awarded_marks >= max_marks:
                break

        return {
            "question_id": q_id,
            "marks_awarded": min(awarded_marks, max_marks),
            "total_marks": max_marks,
            "is_kbat": "KBAT" in q_data.get("type", ""),
            "breakdown": details
        }

# Initialize Grader with the list
grader = SejarahGrader(ESSAY_DB)


@app.route('/api/grade', methods=['POST'])
def handle_grading():
    data = request.get_json()

    # 1. Get data from Frontend
    section_type = data.get('section_type')
    q_id = data.get('question_id')
    student_text = data.get('student_text')

    # 2. Run the AI Grading Logic (using your existing grader class)
    # Note: Ensure your 'grader' instance is initialized with ESSAY_DB
    result = grader.grade(section_type, q_id, student_text)

    if "error" in result:
        return jsonify(result), 404

    # 3. Return the score
    return jsonify(result), 200


# AI Draft Email
@app.route('/draft_email', methods=['POST'])
def ai_draft_email():
    data = request.get_json()
    email = data.get("email")
    mastery = data.get("mastery")
    weak_areas = data.get("weak_areas", [])

    if not email:
        return jsonify({"error": "Missing student email"}), 400

    # Prompt gives Gemini context about the student's performance
    prompt = f"""
    You are an empathetic, encouraging instructor writing to a student ({email}).
    They are currently 'at-risk' in your course with an average mastery of {mastery}%.
    They are struggling the most with these chapters: {', '.join(map(str, weak_areas))}.

    Draft a brief, supportive email offering help and suggesting they review those specific chapters. 
    Keep the tone positive and academic, focusing on growth. 
    CRITICAL INSTRUCTIONS:
    - Do not include a subject line.
    - Do not include any greeting or salutation (e.g., skip "Dear student", "Hi", etc.). Start the very first sentence of the email immediately.
    - Keep it to 3 short paragraphs max.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt,
        )
        return jsonify({"draft_email": response.text.strip()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)


