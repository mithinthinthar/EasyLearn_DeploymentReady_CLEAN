from __future__ import annotations

from typing import Dict, Any


def safe_percent(value, default=0):
    try:
        return float(value or 0)
    except Exception:
        return default


def detect_requested_paper_type(user_message: str) -> str:
    text = (user_message or "").strip().lower()

    if any(word in text for word in [
        "kertas 2", "paper 2", "structured", "subjective",  "k2", "p2",
        "soalan struktur", "soalan subjektif"
    ]):
        return "kertas2"

    if any(word in text for word in [
        "kertas 1", "paper 1", "mcq", "multiple choice",  "k1", "p1",
        "objective", "objektif", "pilihan jawapan"
    ]):
        return "kertas1"

    return "default"


def detect_solution_request(user_message: str) -> bool:
    text = (user_message or "").strip().lower()

    return any(phrase in text for phrase in [
        "with answer",
        "with solution",
        "and answer",
        "and solution",
        "show answer",
        "show solution",
        "give answer",
        "give solution",
        "step by step",
        "full solution",
        "answer and working",
        "solution and working",
        "jawapan",
        "penyelesaian",
        "langkah"
    ])


def detect_question_intent(user_message: str) -> str:
    text = (user_message or "").strip().lower()

    if not text:
        return "explain"

    # Short MCQ answer, useful after chatbot gives Kertas 1 quiz
    if text in ["a", "b", "c", "d", "a.", "b.", "c.", "d.", "a)", "b)", "c)", "d)"]:
        return "quiz_answer"

    if any(phrase in text for phrase in [
        "show you my solution",
        "show my solution",
        "show my working",
        "show my work",
        "check my work",
        "check my working",
        "check my solution",
        "can mark",
        "mark my thing",
        "mark my work",
        "mark my step",
        "mark the step",
        "mark my answer",
        "mark my solution",
        "upload my solution",
        "upload my answer",
        "send my working",
        "snap my answer",
        "snap my solution",
        "how can i show you my solution",
        "how can i show my solution",
        "how can you check my work",
        "semak jawapan saya",
        "semak jalan kerja",
        "boleh semak?",
        "semak kerja saya",
        "muat naik jawapan",
    ]):
        return "quick_snap_help"

    if any(word in text for word in [
        "motivate", "stress", "give up", "tired", "confused",
        "bad at maths", "bad at math", "i can't do math", "i feel lost", "bad at this",
        "i feel loss", "lost", "tak faham", "susah", "penat",
        "putus asa", "lemah matematik"
    ]):
        return "motivation"

    if any(word in text for word in [
        "what should i revise", "what topic", "recommend",
        "study plan", "next topic", "weak topic", "revise next",
        "topik apa", "cadang", "ulang kaji", "topik lemah"
    ]):
        return "coach"

    if any(word in text for word in [
        "hint", "don't give answer", "do not give answer", "guide me",
        "hint only", "petunjuk", "beri hint", "beri petunjuk", "bimbing"
    ]):
        return "guided_hint"

    if any(word in text for word in [
        "play", "game", "quiz me", "mini quiz", "let's play",  "create quiz",
        "main", "kuiz", "permainan"
    ]):
        return "activity"

    # Practice/question generation request.
    # This handles:
    # - "give me a question in transformation"
    # - "give me a paper 2 type of question about number bases"
    # - "can you give me some kertas 2 question about number bases"
    if (
        "question" in text
        and any(word in text for word in [
            "give", "ask", "practice", "latihan", "beri", "buat"
        ])
    ) or any(phrase in text for phrase in [
        "give me a question",
        "give me one question",
        "give me some question",
        "give me some questions",
        "ask me a question",
        "question in",
        "question about",
        "practice question",
        "paper 1 question",
        "paper 2 question",
        "kertas 1 question",
        "kertas 2 question",
        "paper 1 type of question",
        "paper 2 type of question",
        "kertas 1 type of question",
        "kertas 2 type of question",
        "give question",
        "can you give me a question",
        "buat soalan",
        "beri soalan",
        "soalan latihan",
        "beri saya soalan"
    ]):
        return "practice_question"

    if any(word in text for word in [
        "solve", "calculate", "find", "show steps",
        "answer", "step by step", "work out",
        "selesaikan", "kira", "cari", "langkah"
    ]):
        return "solve"

    if any(word in text for word in [
        "what is", "explain", "teach me", "meaning of",
        "why", "how does", "apa itu", "terangkan", "maksud"
    ]):
        return "explain"

    # Conservative off-topic detector
    if any(word in text for word in [
        "weather", "movie", "song", "football", "food", "restaurant",
        "travel", "shopping", "politics", "news"
    ]):
        return "off_topic"

    return "explain"


def build_student_state(db_summary: Dict[str, Any] | None = None) -> Dict[str, Any]:
    db_summary = db_summary or {}

    overall_accuracy = safe_percent(db_summary.get("overall_accuracy_percent"))
    recent_accuracy = safe_percent(
        db_summary.get("recent_accuracy_percent"),
        overall_accuracy
    )
    total_attempts = int(db_summary.get("total_questions_attempted") or 0)

    weak_topics = db_summary.get("weak_topics") or []
    strong_topics = db_summary.get("strong_topics") or []
    study_pattern = db_summary.get("study_pattern") or "unknown"

    if recent_accuracy < 45:
        confidence_level = "low"
    elif recent_accuracy < 70:
        confidence_level = "medium"
    else:
        confidence_level = "high"

    if total_attempts < 10:
        learner_stage = "new_or_insufficient_data"
    elif recent_accuracy < 50:
        learner_stage = "struggling"
    elif recent_accuracy < 75:
        learner_stage = "developing"
    else:
        learner_stage = "strong"

    return {
        "overall_accuracy_percent": overall_accuracy,
        "recent_accuracy_percent": recent_accuracy,
        "total_questions_attempted": total_attempts,
        "weak_topics": weak_topics[:3],
        "strong_topics": strong_topics[:3],
        "study_pattern": study_pattern,
        "confidence_level": confidence_level,
        "learner_stage": learner_stage,
    }


def select_tutoring_strategy(
    user_message: str,
    student_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Controlled learner-aware decision layer.
    Decides HOW the chatbot should tutor BEFORE GPT generates the response.
    """

    intent = detect_question_intent(user_message)
    requested_paper_type = detect_requested_paper_type(user_message)
    wants_solution = detect_solution_request(user_message)

    confidence = student_state.get("confidence_level", "medium")
    learner_stage = student_state.get("learner_stage", "developing")
    weak_topics = student_state.get("weak_topics", [])
    primary_weak_topic = weak_topics[0] if weak_topics else "general SPM Mathematics"
    strong_topics = student_state.get("strong_topics", [])
    study_pattern = student_state.get("study_pattern", "unknown")
    recent_accuracy = safe_percent(student_state.get("recent_accuracy_percent"))

    # 1. Decide tutoring mode
    if intent == "motivation":
        mode = "motivation"

    elif intent in ["coach", "activity", "practice_question", "quiz_answer", "off_topic", "quick_snap_help"]:
        mode = "coach"

    elif intent == "guided_hint":
        mode = "guided_hint"

    elif learner_stage == "strong" and intent in ["solve", "explain"]:
        mode = "challenge"

    elif intent == "solve" and confidence == "low":
        mode = "guided_hint"

    else:
        mode = "explainer"

    # 2. Decide retrieval mode
    # This prevents casual/navigation messages from always searching Pinecone.
    if intent in ["motivation", "quiz_answer", "off_topic", "quick_snap_help"]:
        retrieval_mode = "none"

    elif intent == "coach":
        retrieval_mode = "concept_only"

    elif intent in ["activity", "practice_question"]:
        retrieval_mode = "practice"

    elif intent == "solve":
        retrieval_mode = "full"

    else:
        retrieval_mode = "concept_only"

    # 3. Decide tone, depth, support
    if confidence == "low":
        tone = "supportive, calm, and reassuring"
        explanation_depth = "simple and not overwhelming"
        support_level = "high"

    elif mode == "challenge":
        tone = "encouraging and slightly challenging"
        explanation_depth = "medium to deep"
        support_level = "low"

    elif learner_stage == "new_or_insufficient_data":
        tone = "friendly and exploratory"
        explanation_depth = "simple to medium"
        support_level = "medium"

    else:
        tone = "friendly and clear"
        explanation_depth = "medium"
        support_level = "medium"

    # 4. Decide next-step guidance
    if intent == "quick_snap_help":
        next_step_guidance = (
            "Explain that to check written working, the student should use the Quick Snap feature, "
            "not upload inside the chatbot. Tell them to go to Quick Snap, choose 'Check My Work', "
            "then upload or snap clear images of both the question and their written solution. "
            "Mention that including the question is important so the system can understand what they are solving. "
            "Explain that Quick Snap can check and mark their written working step by step. "
            "Keep the explanation short and friendly."
        )

    if intent == "coach":
        if weak_topics:
            next_step_guidance = (
                f"Recommend this one weak topic first: {weak_topics[0]}. "
                "Explain why it matters and give only 2-3 next actions."
            )
        else:
            next_step_guidance = (
                "No clear weak topic is available. Recommend one general revision action "
                "based on the student's current question."
            )

    elif intent == "motivation":
        if weak_topics:
            next_step_guidance = (
                f"Mention one small starting action from this weak topic: {weak_topics[0]}. "
                "Do not overload the student."
            )
        else:
            next_step_guidance = (
                "Give one small, easy action the student can do now."
            )

    elif intent == "activity":
        if weak_topics:
            next_step_guidance = (
                f"Offer only ONE short Kertas 1 style multiple-choice quiz question first, "
                f"based on this topic: {weak_topics[0]}. "
                f"Before showing the question, briefly tell the student that the quiz is based on {weak_topics[0]} "
                "because it is a good topic for them to strengthen. "
                "Use encouraging wording. Do not say they are bad or weak. "
                "Do not show the answer yet. Ask the student to reply A, B, C, or D. "
                "After the student answers, explain briefly and ask whether they want the next question."
            )
        else:
            next_step_guidance = (
                "Offer only ONE short Kertas 1 style multiple-choice quiz question first. "
                "Before showing the question, say it is based on SPM Mathematics practice. "
                "Do not show the answer yet. Ask the student to reply A, B, C, or D. "
                "After the student answers, explain briefly and ask whether they want the next question."
            )

    elif intent == "practice_question":
        if requested_paper_type == "kertas2":
            if wants_solution:
                next_step_guidance = (
                    "Generate exactly ONE Kertas 2 structured SPM-style question based on the requested topic. "
                    "Since the student asked for the answer or solution, include the answer after the question. "
                    "If they asked for step-by-step solution, show clear SPM-level working. "
                    "Keep the solution readable and not too long."
                )
            else:
                next_step_guidance = (
                    "Generate exactly ONE Kertas 2 structured SPM-style practice question "
                    "based on the topic requested by the student. "
                    "Do NOT provide the solution, marking scheme, steps, or final answer yet. "
                    "Because typing full working in chat is difficult, ask the student to try it on paper first. "
                    "Tell the student they may reply with their final answer, ask for a hint, or ask for the full solution." \
                    "If they want their full handwritten working checked, gently suggest using Quick Snap to upload or snap the question with their written solution. "
                    "Do not ask them to type long step-by-step working in the chatbot."
                )
        else:
            if wants_solution:
                next_step_guidance = (
                    "Generate exactly ONE Kertas 1 multiple-choice SPM-style practice question "
                    "based on the topic requested by the student. "
                    "Include four options A, B, C, and D. "
                    "Since the student asked for the answer or solution, provide the correct option and a brief explanation after the question."
                )
            else:
                next_step_guidance = (
                    "Generate exactly ONE Kertas 1 multiple-choice SPM-style practice question "
                    "based on the topic requested by the student. "
                    "Include four options A, B, C, and D. "
                    "Do NOT provide the answer, solution, steps, or final answer yet. "
                    "Ask the student to reply A, B, C, or D."
                )

    elif intent == "quiz_answer":
        next_step_guidance = (
            "The student appears to be answering a previous MCQ. "
            "Use recent conversation history to check whether the answer is correct. "
            "Give brief feedback and ask if they want another question. "
            "Do not generate a new question unless the student asks."
        )

    elif intent == "off_topic":
        next_step_guidance = (
            "Politely explain that EasyLearn focuses on SPM Mathematics. "
            "Invite the student to ask a maths question or request a quiz."
        )

    elif mode == "challenge":
        if strong_topics:
            next_step_guidance = (
                f"If relevant, connect to the student's strength: {strong_topics[0]}. "
                "Ask them to attempt one step before revealing the full answer."
            )
        else:
            next_step_guidance = (
                "Ask the student to try the first step before revealing the full answer."
            )

    elif study_pattern in ["irregular", "last-minute"] and intent in ["coach", "motivation"]:
        next_step_guidance = (
            "Briefly remind the student to practise in short consistent sessions."
        )

    else:
        next_step_guidance = (
            "Respect the student's current question. Do not force weak-topic recommendations "
            "unless the student asks what to revise next."
        )

    # 5. Extra guardrails
    adaptation_rules = []

    if confidence == "low":
        adaptation_rules.append(
            "Use shorter explanations, simple wording, and avoid too many formulas at once."
        )

    if learner_stage == "new_or_insufficient_data":
        adaptation_rules.append(
            "Do not overclaim about the student's ability because there is limited practice data."
        )

    if recent_accuracy < 50 and intent == "solve":
        adaptation_rules.append(
            "For solving questions, guide step-by-step and check understanding before moving too fast."
        )

    if intent in ["explain", "solve", "practice_question"]:
        adaptation_rules.append(
            "Stay focused on the topic the student just asked about, even if their weak topic is different."
        )

    if intent in ["activity", "practice_question"] and not wants_solution:
        adaptation_rules.append(
            "Do not provide the answer immediately. Wait for the student to attempt first."
        )

    if requested_paper_type == "kertas2" and intent == "practice_question" and not wants_solution:
        adaptation_rules.append(
            "For Kertas 2 practice in chatbot, do not require the student to type full working. "
            "Ask them to try on paper and reply with final answer, hint request, or solution request."
        )

    adaptation_rules.append(
        "Use 1-2 emojis only when they naturally fit the response, especially motivation, or congratulation on answering correctly, or long message about concept and welcoming message. Do not use the same emoji repeatedly. Avoid emojis in formal explanations, calculations, or step-by-step solutions."
        "Avoid emojis inside formal calculations."
    )

    if intent == "activity":
        retrieval_query = f"SPM Mathematics Kertas 1 MCQ {primary_weak_topic}"

    elif intent == "practice_question":
        if requested_paper_type == "kertas2":
            retrieval_query = f"SPM Mathematics Kertas 2 structured question {user_message}"
        else:
            retrieval_query = f"SPM Mathematics Kertas 1 MCQ question {user_message}"

    elif intent == "solve":
        retrieval_query = user_message

    elif intent == "explain":
        retrieval_query = user_message

    else:
        retrieval_query = user_message

    return {
        "tutoring_mode": mode,
        "intent": intent,
        "requested_paper_type": requested_paper_type,
        "wants_solution": wants_solution,
        "retrieval_mode": retrieval_mode,
        "tone": tone,
        "explanation_depth": explanation_depth,
        "support_level": support_level,
        "next_step_guidance": next_step_guidance,
        "adaptation_rules": adaptation_rules,
        "retrieval_query": retrieval_query,
        "show_quick_snap_cta": intent == "quick_snap_help",
    }


def build_agent_instruction(strategy: Dict[str, Any], student_state: Dict[str, Any]) -> str:
    mode = strategy.get("tutoring_mode", "explainer")
    intent = strategy.get("intent", "explain")

    mode_rules = {
        "explainer": """
Use Explainer Mode.
Explain the concept clearly using simple SPM-level wording.
Use short sections.
If there is a formula, explain what each variable means.
Give one simple example only if useful.
Do not force revision advice unless the student asks for revision guidance.
""",

        "guided_hint": """
Use Guided Hint Mode.
Do NOT immediately give the full final answer unless the student clearly asks for it.
Give only the next 1-2 helpful hints.
Ask the student to try the next step.
If the student seems weak or confused, make the hint easier.
Keep the tone supportive.
""",

        "coach": """
Use Coach Mode.
Focus on revision direction, learning planning, quiz, or light learning activity.
Use the student's weak topics and study pattern only when relevant.
For quiz or practice requests, give only one question first.
Do not overload the student with too many subtopics.
""",

        "motivation": """
Use Motivation Mode.
Be supportive, calm, and confidence-building.
Acknowledge the student's feeling.
Avoid long explanations.
Give one small topic or action to start with.
Remind the student that improvement comes from small consistent practice.
""",

        "challenge": """
Use Challenge Mode.
Assume the student can think more independently.
Do not give the full solution immediately unless the student clearly asks for it.
Ask the student to attempt the first step first.
Give a short clue or challenge question.
If the student asks for the full solution, then provide it clearly.
"""
    }

    adaptation_rules = strategy.get("adaptation_rules") or []
    adaptation_text = "\n".join([f"- {rule}" for rule in adaptation_rules])

    return f"""
Learner-aware tutoring strategy:

Tutoring mode: {mode}
Detected intent: {intent}
Requested paper type: {strategy.get("requested_paper_type")}
Wants solution: {strategy.get("wants_solution")}
Retrieval mode: {strategy.get("retrieval_mode")}
Tone: {strategy.get("tone")}
Explanation depth: {strategy.get("explanation_depth")}
Support level: {strategy.get("support_level")}

Student state summary:
- Confidence level: {student_state.get("confidence_level")}
- Learner stage: {student_state.get("learner_stage")}
- Recent accuracy: {student_state.get("recent_accuracy_percent")}%
- Overall accuracy: {student_state.get("overall_accuracy_percent")}%
- Total questions attempted: {student_state.get("total_questions_attempted")}
- Weak topics: {student_state.get("weak_topics")}
- Strong topics: {student_state.get("strong_topics")}
- Study pattern: {student_state.get("study_pattern")}

Mode rule:
{mode_rules.get(mode, mode_rules["explainer"])}

Adaptive behaviour rules:
{adaptation_text if adaptation_text else "- Use normal student-friendly SPM tutoring behaviour."}

Next-step guidance:
{strategy.get("next_step_guidance")}

Important:
- The student's current message has priority.
- Do not keep forcing a previous weak topic if the student asks about a new topic.
- Use weak topics mainly for revision planning, motivation, or when clearly relevant.
- If the detected intent is practice_question, give only one practice question.
- For practice_question intent, use retrieved question-bank examples as format/style references, not as answers to reveal.
- If the detected intent is practice_question and wants_solution is False, do not solve it yet.
- If the detected intent is practice_question and wants_solution is True, include the answer or solution according to what the student asked.
- If the detected intent is activity, give only one quiz question first and wait for the student's answer.
- If the student does not specify paper type, default quiz/practice questions to Kertas 1 MCQ.
- If the student specifically asks for Kertas 2, give one Kertas 2 structured question.
- For Kertas 2 typed chatbot practice, do not ask the student to type long full working. Ask them to try on paper and reply with final answer, hint request, or solution request.
- If the student wants full Kertas 2 working to be checked, gently suggest using the Quick Snap feature to upload or snap question with their written solution instead of typing long working in chat.
- Keep the response friendly, natural, and student-appropriate.
- If the detected intent is quick_snap_help, do not say the student can upload inside the chatbot. Direct them to Quick Snap > Check My Work.
- For Check My Work, remind the student to snap the question and their written solution in 2 images, and the Quick Snap will check their work
- Explain that Quick Snap can check and mark their written working step by step.
""".strip()