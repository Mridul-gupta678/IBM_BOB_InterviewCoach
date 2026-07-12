"""
=============================================================================
  InterviewTrainer — IBM Watsonx.ai Powered AI Interview Coach
  Backend: Flask + ibm-watsonx-ai SDK (Granite models)
=============================================================================
"""

import os
import json
import re
import requests
import uuid
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session, g
from flask_cors import CORS
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# ─────────────────────────────────────────────────────────────────────────────
#  AGENT INSTRUCTIONS — Customise everything here
# ─────────────────────────────────────────────────────────────────────────────
AGENT_INSTRUCTIONS = {

    # ── Identity ──────────────────────────────────────────────────────────────
    "name": "InterviewCoach",
    "persona": (
        "You are InterviewCoach, an expert AI interview trainer with 15+ years of "
        "experience in talent acquisition, technical recruiting, and career coaching. "
        "You conduct realistic mock interviews, provide honest and constructive feedback, "
        "evaluate answers with precision, and guide candidates to present their best selves. "
        "You are encouraging yet rigorous — you celebrate strengths while being direct "
        "about gaps that need work."
    ),

    # ── Tone & Communication Style ────────────────────────────────────────────
    # Options: "professional" | "encouraging" | "strict" | "conversational"
    "tone": "encouraging",
    "use_emojis": True,
    "language_style": (
        "Speak clearly and professionally. Use industry-standard terminology. "
        "Give structured, actionable feedback. Use numbered lists for steps and "
        "bullet points for observations. Keep responses focused and specific. "
        "When evaluating answers, always explain WHY something works or doesn't."
    ),

    # ── Interview Modes ───────────────────────────────────────────────────────
    # Options: "behavioral" | "technical" | "system_design" | "hr_screening" |
    #          "case_study" | "situational" | "competency_based"
    "default_interview_mode": "behavioral",
    "available_modes": [
        "behavioral",
        "technical",
        "system_design",
        "hr_screening",
        "case_study",
        "situational",
    ],

    # ── Difficulty Levels ─────────────────────────────────────────────────────
    # Options: "entry_level" | "mid_level" | "senior" | "lead" | "executive"
    "default_difficulty": "mid_level",
    "difficulty_descriptions": {
        "entry_level":  "0-2 years experience, fundamentals focus, forgiving of gaps",
        "mid_level":    "3-5 years experience, depth of knowledge, practical examples expected",
        "senior":       "6-10 years experience, leadership, architecture, complex problem-solving",
        "lead":         "10+ years, strategic thinking, team influence, organizational impact",
        "executive":    "Director/VP level, business acumen, vision, cross-functional leadership",
    },

    # ── Domain Specialisation ─────────────────────────────────────────────────
    # Add or remove domains as needed
    "supported_domains": [
        "software_engineering",
        "data_science",
        "product_management",
        "devops_cloud",
        "cybersecurity",
        "finance_banking",
        "marketing",
        "human_resources",
        "consulting",
        "general",
    ],
    "domain_context": {
        "software_engineering": (
            "Focus on data structures, algorithms, system design, OOP principles, "
            "coding best practices, debugging, code reviews, and software architecture."
        ),
        "data_science": (
            "Cover statistics, machine learning algorithms, data wrangling, feature "
            "engineering, model evaluation, A/B testing, SQL, Python/R, and storytelling with data."
        ),
        "product_management": (
            "Emphasize product vision, roadmapping, stakeholder management, metrics, "
            "user research, prioritization frameworks (RICE, MoSCoW), and go-to-market."
        ),
        "devops_cloud": (
            "Include CI/CD pipelines, containerization (Docker/Kubernetes), IaC, "
            "monitoring, cloud platforms (AWS/Azure/GCP), SRE practices, and incident response."
        ),
        "finance_banking": (
            "Cover financial modeling, valuation, risk management, regulatory compliance, "
            "capital markets, portfolio management, and analytical frameworks."
        ),
        "general": (
            "Cover universal professional skills: communication, teamwork, leadership, "
            "problem-solving, adaptability, and domain-agnostic behavioral questions."
        ),
    },

    # ── Evaluation Criteria ───────────────────────────────────────────────────
    # Weights for scoring answers (must sum to 100)
    "evaluation_criteria": {
        "relevance":      25,   # Did the answer address the question?
        "depth":          25,   # Was the answer thorough and detailed?
        "structure":      20,   # Was the STAR/PAR framework used clearly?
        "examples":       20,   # Were specific, measurable examples provided?
        "communication":  10,   # Clarity, conciseness, professional language
    },

    # ── Question Generation Rules ─────────────────────────────────────────────
    "question_generation": {
        "use_star_method":     True,   # Encourage STAR for behavioral answers
        "include_follow_ups":  True,   # Generate follow-up probing questions
        "vary_question_types": True,   # Mix open, situational, competency-based
        "questions_per_session": 5,    # Default number of questions per mock session
    },

    # ── Resume Analysis Settings ──────────────────────────────────────────────
    "resume_analysis": {
        "highlight_gaps":        True,
        "suggest_improvements":  True,
        "generate_questions_from_resume": True,
        "ats_compatibility_check": True,
    },

    # ── Feedback Style ─────────────────────────────────────────────────────────
    "feedback_style": {
        "show_score":          True,
        "show_strengths":      True,
        "show_improvements":   True,
        "show_sample_answer":  True,    # Provide a model answer after evaluation
        "show_tips":           True,
    },

    # ── Safety & Ethics Rules ──────────────────────────────────────────────────
    "safety_rules": [
        "Never ask or answer questions related to age, religion, race, gender, "
        "marital status, national origin, disability, or other protected characteristics.",
        "Do not generate discriminatory, offensive, or inappropriate content.",
        "If a user seems distressed about job loss or career failure, respond with "
        "empathy and encouragement before continuing with coaching.",
        "Do not fabricate company-specific information, salaries, or hiring outcomes.",
        "Remind users that AI coaching supplements but does not replace professional career counselors.",
        "Keep all user resume content confidential and do not reference it outside the session.",
    ],

    # ── Response Format ────────────────────────────────────────────────────────
    "response_format": (
        "Structure responses with clear sections using **bold headers**. "
        "For evaluations, always include: Score, Strengths, Areas for Improvement, "
        "and a Sample Better Answer. For questions, number them clearly. "
        "Keep individual responses focused — do not overwhelm with too much at once."
    ),

    # ── Capabilities ───────────────────────────────────────────────────────────
    "capabilities": [
        "Mock interview sessions (behavioral, technical, HR, system design)",
        "Real-time answer evaluation with scoring (0-100)",
        "STAR method coaching and feedback",
        "Resume analysis and gap identification",
        "Personalized question generation based on role & experience",
        "Follow-up probing questions",
        "Interview preparation strategies",
        "Domain-specific technical question banks",
        "Progress tracking across sessions",
        "Salary negotiation tips",
        "Body language and communication advice",
        "Post-interview debrief simulation",
    ],
}
# ─────────────────────────────────────────────────────────────────────────────
#  END AGENT INSTRUCTIONS
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "interviewtrainer-dev-secret-2024")
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload

# ── Watsonx client initialisation ────────────────────────────────────────────
_watsonx_model: ModelInference | None = None

def format_prompt_for_model(messages: list, model_id: str) -> str:
    model_id_lower = model_id.lower()
    if "granite" in model_id_lower:
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            prompt += f"<|start_of_role|>{role}<|end_of_role|>\n{content}<|end_of_text|>\n"
        prompt += "<|start_of_role|>assistant<|end_of_role|>\n"
        return prompt
    elif "llama-3" in model_id_lower or "llama3" in model_id_lower:
        prompt = "<|begin_of_text|>"
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            prompt += f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>"
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        return prompt
    else:
        # Default fallback
        prompt = "<|begin_of_text|>"
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            prompt += f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>"
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        return prompt

def build_chat_messages(user_message: str, chat_history: list, user_profile: dict | None) -> list:
    system_prompt = build_system_prompt(user_profile)
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    for msg in chat_history[-8:]:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    return messages

def generate_huggingface_text(messages: list, api_key: str, model_id: str = "Qwen/Qwen2.5-7B-Instruct") -> tuple[str, str]:
    models_to_try = [model_id]
    if model_id != "Qwen/Qwen2.5-7B-Instruct":
        models_to_try.append("Qwen/Qwen2.5-7B-Instruct")
        
    last_err = None
    for model in models_to_try:
        url = "https://router.huggingface.co/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": int(os.getenv("MAX_NEW_TOKENS", 1200)),
            "temperature": 0.7
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()
            choices = result.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                if content:
                    return content.strip(), model
            raise ValueError(f"Unexpected response payload format: {result}")
        except Exception as e:
            app.logger.warning(f"HF router chat completions failed for model {model}: {e}")
            last_err = e
            
    raise RuntimeError(f"Hugging Face API call failed: {last_err}")

def get_llm_generation(messages: list, data: dict) -> tuple[str, str]:
    """
    Generate response based on selected provider using chat templates.
    Returns (generated_text, active_provider).
    Also sets flask.g.actual_model.
    """
    provider = data.get("llm_provider") or os.getenv("LLM_PROVIDER") or "auto"
    
    watsonx_api_key = os.getenv("IBM_API_KEY")
    watsonx_project_id = os.getenv("WATSONX_PROJECT_ID")
    watsonx_model_id = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")
    
    hf_api_key = data.get("huggingface_api_key") or os.getenv("HUGGINGFACE_API_KEY")
    hf_model = data.get("huggingface_model_id") or os.getenv("HUGGINGFACE_MODEL_ID") or "Qwen/Qwen2.5-7B-Instruct"

    errors = []

    def try_watsonx():
        model = get_watsonx_model()
        if model is None:
            raise ValueError("Watsonx credentials not configured.")
        prompt = format_prompt_for_model(messages, watsonx_model_id)
        result = model.generate_text(prompt=prompt)
        return result.strip() if isinstance(result, str) else str(result)

    def try_huggingface():
        if not hf_api_key:
            raise ValueError("Hugging Face API token not provided.")
        return generate_huggingface_text(messages, hf_api_key, hf_model)

    # Explicit provider check
    if provider == "watsonx":
        try:
            res = try_watsonx()
            try:
                g.actual_model = watsonx_model_id
            except Exception:
                pass
            return res, "watsonx"
        except Exception as e:
            app.logger.warning(f"Watsonx explicit request failed: {e}")
            errors.append(f"Watsonx: {e}")
            
    elif provider == "huggingface":
        try:
            res_txt, res_model = try_huggingface()
            try:
                g.actual_model = res_model
            except Exception:
                pass
            return res_txt, "huggingface"
        except Exception as e:
            app.logger.warning(f"Hugging Face explicit request failed: {e}")
            errors.append(f"Hugging Face: {e}")
            
    elif provider == "demo":
        try:
            g.actual_model = "demo"
        except Exception:
            pass
        return "", "demo"

    # Cascade / Auto fallbacks
    if watsonx_api_key and watsonx_project_id and "Watsonx" not in str(errors):
        try:
            res = try_watsonx()
            try:
                g.actual_model = watsonx_model_id
            except Exception:
                pass
            return res, "watsonx"
        except Exception as e:
            app.logger.warning(f"Fallback Watsonx failed: {e}")
            errors.append(f"Watsonx: {e}")

    if hf_api_key and "Hugging Face" not in str(errors):
        try:
            res_txt, res_model = try_huggingface()
            try:
                g.actual_model = res_model
            except Exception:
                pass
            return res_txt, "huggingface"
        except Exception as e:
            app.logger.warning(f"Fallback Hugging Face failed: {e}")
            errors.append(f"Hugging Face: {e}")

    if errors:
        app.logger.error(f"All LLM generation paths failed: {errors}. Falling back to Demo mode.")
    try:
        g.actual_model = "demo"
    except Exception:
        pass
    return "", "demo"




_watsonx_init_error = None

def get_watsonx_model() -> ModelInference | None:
    """Lazy-initialise and return the Watsonx ModelInference instance."""
    global _watsonx_model, _watsonx_init_error
    if _watsonx_model is not None:
        return _watsonx_model

    api_key    = os.getenv("IBM_API_KEY")
    project_id = os.getenv("WATSONX_PROJECT_ID")
    url        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").rstrip("/")
    model_id   = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")

    if not api_key or not project_id:
        app.logger.warning(
            "IBM_API_KEY or WATSONX_PROJECT_ID not set — running in demo mode."
        )
        return None

    try:
        credentials = Credentials(url=url, api_key=api_key)
        params = {
            GenParams.MAX_NEW_TOKENS: int(os.getenv("MAX_NEW_TOKENS", 1200)),
            GenParams.TEMPERATURE:    float(os.getenv("TEMPERATURE", 0.7)),
            GenParams.TOP_P:          float(os.getenv("TOP_P", 0.9)),
            GenParams.STOP_SEQUENCES: ["Human:", "User:", "Candidate:", "<|eot_id|>", "<|end_of_text|>"],
        }
        _watsonx_model = ModelInference(
            model_id=model_id,
            params=params,
            credentials=credentials,
            project_id=project_id,
        )
        app.logger.info(f"Watsonx model '{model_id}' initialised successfully.")
    except Exception as exc:
        app.logger.error(f"Failed to initialise Watsonx model: {exc}")
        _watsonx_init_error = str(exc)
        _watsonx_model = None

    return _watsonx_model


# ── System prompt builder ─────────────────────────────────────────────────────
def build_system_prompt(user_profile: dict | None = None) -> str:
    ai       = AGENT_INSTRUCTIONS
    safety   = "\n".join(f"- {r}" for r in ai["safety_rules"])
    caps     = "\n".join(f"- {c}" for c in ai["capabilities"])

    profile_section = ""
    if user_profile:
        domain = user_profile.get("domain", "general")
        domain_ctx = ai["domain_context"].get(domain, ai["domain_context"]["general"])
        difficulty = user_profile.get("difficulty", ai["default_difficulty"])
        diff_desc  = ai["difficulty_descriptions"].get(difficulty, "")
        criteria   = "\n".join(
            f"  - {k.capitalize()} ({v}%)"
            for k, v in ai["evaluation_criteria"].items()
        )
        profile_section = f"""
**Candidate Profile:**
- Name: {user_profile.get('name', 'Candidate')}
- Target Role: {user_profile.get('role', 'Not specified')}
- Domain: {domain.replace('_', ' ').title()}
- Years of Experience: {user_profile.get('experience', 'Not specified')}
- Interview Mode: {user_profile.get('mode', ai['default_interview_mode']).replace('_', ' ').title()}
- Difficulty Level: {difficulty.replace('_', ' ').title()} — {diff_desc}
- Company Target: {user_profile.get('company', 'Not specified')}
- Interview Round: {user_profile.get('round', 'General')}

**Domain Context:**
{domain_ctx}

**Evaluation Criteria (scoring weights):**
{criteria}
"""

    return f"""You are {ai['name']}.

{ai['persona']}

**Communication Style:**
{ai['language_style']}

**Response Format:**
{ai['response_format']}

**Your Capabilities:**
{caps}

**Safety Rules (always follow):**
{safety}
{profile_section}
Respond as {ai['name']} directly. Do not include "AI:", "Assistant:", or "{ai['name']}:" prefixes in your response."""


def build_chat_prompt(user_message: str, chat_history: list, user_profile: dict | None) -> str:
    system    = build_system_prompt(user_profile)
    user_name = "Candidate"
    if user_profile and isinstance(user_profile, dict):
        user_name = user_profile.get("name", "Candidate").strip() or "Candidate"

    history_text = ""
    for msg in chat_history[-8:]:
        role = user_name if msg["role"] == "user" else AGENT_INSTRUCTIONS["name"]
        history_text += f"{role}: {msg['content']}\n"

    return (
        f"{system}\n\n"
        f"Conversation so far:\n{history_text}"
        f"{user_name}: {user_message}\n"
        f"{AGENT_INSTRUCTIONS['name']}:"
    )


def clean_response(response: str, user_profile: dict | None = None) -> str:
    """Strip chat template tokens and trailing role-label artifacts from generated text."""
    response = response.replace("<|eot_id|>", "").replace("<|end_of_text|>", "")
    response = response.replace("<|start_header_id|>assistant<|end_header_id|>", "")
    response = response.replace("<|start_of_role|>assistant<|end_of_role|>", "")
    response = response.strip()

    user_name = "Candidate"
    if user_profile and isinstance(user_profile, dict):
        user_name = user_profile.get("name", "Candidate").strip() or "Candidate"

    coach_name = AGENT_INSTRUCTIONS["name"]
    for prefix in [f"{coach_name}:", f"{user_name}:", "AI:", "Assistant:", "User:", "Human:"]:
        if response.lower().startswith(prefix.lower()):
            response = response[len(prefix):].strip()

    labels = ["User", "Human", "Candidate", "AI", "Assistant",
              re.escape(coach_name), re.escape(user_name)]
    labels = list(set(l for l in labels if l))
    pattern = r'\s*(?:' + '|'.join(labels) + r')\s*:\s*$'
    return re.sub(pattern, '', response, flags=re.IGNORECASE).strip()



# ── Demo mode responses ───────────────────────────────────────────────────────
DEMO_RESPONSES = [
    (
        "**Welcome to InterviewCoach! 🎯**\n\n"
        "I'm running in **demo mode** (no IBM API key configured).\n\n"
        "To enable full AI-powered coaching:\n"
        "1. Copy `.env.example` → `.env`\n"
        "2. Add your `IBM_API_KEY` and `WATSONX_PROJECT_ID`\n"
        "3. Restart the server\n\n"
        "**I can help you with:**\n"
        "- Mock interview sessions (behavioral, technical, HR)\n"
        "- Real-time answer evaluation & scoring\n"
        "- Resume analysis & feedback\n"
        "- Interview preparation strategies\n\n"
        "Try asking: *\"Start a mock behavioral interview for a Software Engineer role\"*"
    ),
    (
        "**Sample Behavioral Question 📋**\n\n"
        "**Q: Tell me about a time you led a team through a difficult technical challenge.**\n\n"
        "**Strong Answer Structure (STAR Method):**\n\n"
        "**Situation:** 'Our team was tasked with migrating a legacy monolith to microservices '  \n"
        "with a 3-month deadline and only 4 engineers.'\n\n"
        "**Task:** 'As tech lead, I needed to design the migration strategy, '  \n"
        "'keep the existing system stable, and upskill two junior engineers.'\n\n"
        "**Action:** 'I broke the migration into 8 bounded contexts, implemented '  \n"
        "'feature flags for gradual rollout, and held weekly knowledge-sharing sessions.'\n\n"
        "**Result:** 'We completed migration in 11 weeks, reduced API latency by 40%, '  \n"
        "'and both juniors now lead their own microservices independently.'\n\n"
        "**Score: 88/100** ✅ — Strong quantified impact, clear leadership ownership.\n\n"
        "*Configure IBM API key for real-time AI evaluation of your own answers!*"
    ),
]
_demo_idx = 0


def demo_response() -> str:
    global _demo_idx
    resp = DEMO_RESPONSES[_demo_idx % len(DEMO_RESPONSES)]
    _demo_idx += 1
    return resp


# ══════════════════════════════════════════════════════════════════════════════
#  Flask Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html", agent_name=AGENT_INSTRUCTIONS["name"])


# ── Chat / coaching endpoint ──────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    data         = request.get_json(force=True)
    user_message = data.get("message", "").strip()
    chat_history = data.get("history", [])
    user_profile = data.get("profile")

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        messages = build_chat_messages(user_message, chat_history, user_profile)
        response, provider = get_llm_generation(messages, data)
        if provider == "demo":
            return jsonify({
                "response":  demo_response(),
                "mode":      "demo",
                "timestamp": datetime.now().isoformat(),
            })
        response = clean_response(response, user_profile)
        
        # Get active model ID
        model_key = f"{provider.upper()}_MODEL_ID"
        model_name = g.get("actual_model") or data.get(f"{provider}_model_id") or os.getenv(model_key, "unknown")
        
        return jsonify({
            "response":  response,
            "mode":      provider,
            "timestamp": datetime.now().isoformat(),
            "model":     model_name,
        })
    except Exception as exc:
        app.logger.error(f"Chat generation error: {exc}")
        return jsonify({"error": f"Model error: {str(exc)}"}), 500



# ── Generate interview questions ──────────────────────────────────────────────
@app.route("/api/generate-questions", methods=["POST"])
def generate_questions():
    data         = request.get_json(force=True)
    user_profile = data.get("profile", {})
    mode         = data.get("mode", AGENT_INSTRUCTIONS["default_interview_mode"])
    count        = min(int(data.get("count", AGENT_INSTRUCTIONS["question_generation"]["questions_per_session"])), 10)

    ai     = AGENT_INSTRUCTIONS
    domain = user_profile.get("domain", "general")
    domain_ctx = ai["domain_context"].get(domain, ai["domain_context"]["general"])
    difficulty = user_profile.get("difficulty", ai["default_difficulty"])
    role       = user_profile.get("role", "professional")
    experience = user_profile.get("experience", "3-5 years")

    system_prompt = build_system_prompt(user_profile)
    user_instruction = (
        f"Generate exactly {count} {mode.replace('_', ' ')} interview questions for a "
        f"**{role}** position at **{difficulty.replace('_', ' ')} level** "
        f"({experience} experience).\n\n"
        f"Domain context: {domain_ctx}\n\n"
        f"Requirements:\n"
        f"- Number each question (1. 2. 3. ...)\n"
        f"- Mix question types (open-ended, situational, competency-based)\n"
        f"- Include one follow-up hint in parentheses after each question\n"
        f"- Make questions realistic and company-agnostic\n"
        f"- Vary difficulty within the level"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_instruction}
    ]

    try:
        questions, provider = get_llm_generation(messages, data)
        if provider == "demo":
            sample_questions = (
                f"**{mode.replace('_', ' ').title()} Interview Questions — {role}**\n\n"
                "1. Tell me about yourself and your journey to this point in your career.\n"
                "   *(Follow-up: What specific achievement are you most proud of?)*\n\n"
                "2. Describe a situation where you had to handle competing priorities under tight deadlines.\n"
                "   *(Follow-up: How did you communicate trade-offs to stakeholders?)*\n\n"
                "3. Give an example of a time you disagreed with your manager's decision. What did you do?\n"
                "   *(Follow-up: What was the outcome and what did you learn?)*\n\n"
                "4. Tell me about a project that failed. What was your role and what did you take away?\n"
                "   *(Follow-up: What would you do differently today?)*\n\n"
                "5. Where do you see yourself in 3-5 years, and how does this role fit that vision?\n"
                "   *(Follow-up: What skills are you actively developing toward that goal?)*\n\n"
                "*Configure API keys in Settings for role-specific AI-generated questions.*"
            )
            return jsonify({"questions": sample_questions, "mode": "demo", "count": count})

        if not questions:
            return jsonify({"error": "Model returned empty response. Please try again."}), 500
        return jsonify({"questions": questions, "mode": provider, "count": count, "model": g.get("actual_model")})
    except Exception as exc:
        app.logger.error(f"Question generation error: {exc}")
        return jsonify({"error": str(exc)}), 500



# ── Evaluate an answer ─────────────────────────────────────────────────────────
@app.route("/api/evaluate-answer", methods=["POST"])
def evaluate_answer():
    data         = request.get_json(force=True)
    question     = data.get("question", "").strip()
    answer       = data.get("answer", "").strip()
    user_profile = data.get("profile", {})

    if not question or not answer:
        return jsonify({"error": "Provide both question and answer"}), 400

    ai         = AGENT_INSTRUCTIONS
    criteria   = "\n".join(
        f"- {k.replace('_', ' ').title()} (weight: {v}%)"
        for k, v in ai["evaluation_criteria"].items()
    )
    mode       = user_profile.get("mode", ai["default_interview_mode"])
    difficulty = user_profile.get("difficulty", ai["default_difficulty"])

    system_prompt = build_system_prompt(user_profile)
    user_instruction = (
        f"Evaluate the following interview answer.\n\n"
        f"**Interview Mode:** {mode.replace('_', ' ').title()}\n"
        f"**Difficulty:** {difficulty.replace('_', ' ').title()}\n\n"
        f"**Question:** {question}\n\n"
        f"**Candidate's Answer:** {answer}\n\n"
        f"Evaluate using these weighted criteria:\n{criteria}\n\n"
        f"Provide your evaluation in this exact structure:\n"
        f"**Overall Score: X/100**\n\n"
        f"**Strengths:**\n[list what was done well]\n\n"
        f"**Areas for Improvement:**\n[specific, actionable feedback]\n\n"
        f"**STAR Method Check:**\n[assess Situation/Task/Action/Result usage]\n\n"
        f"**Sample Strong Answer:**\n[provide a model answer for this question]\n\n"
        f"**Quick Tips:**\n[2-3 specific tips to improve this answer]"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_instruction}
    ]

    try:
        evaluation, provider = get_llm_generation(messages, data)
        if provider == "demo":
            sample_eval = (
                "**Overall Score: 72/100** ⭐⭐⭐\n\n"
                "**Strengths:**\n"
                "- Clearly described the situation and your individual contribution\n"
                "- Good use of specific technical terminology\n"
                "- Professional tone throughout\n\n"
                "**Areas for Improvement:**\n"
                "- Missing quantified results (e.g., 'reduced by 30%', 'saved 2 hours/week')\n"
                "- The Action section could be more specific about your decision-making process\n"
                "- No mention of team dynamics or stakeholder impact\n\n"
                "**STAR Method Check:**\n"
                "- ✅ Situation: Clear context set\n"
                "- ✅ Task: Your responsibility defined\n"
                "- ⚠️ Action: Steps described but not detailed enough\n"
                "- ❌ Result: No measurable outcomes provided\n\n"
                "**Quick Tips:**\n"
                "1. Always end with a quantified result ('reduced latency by 40%', 'increased team velocity by 20%')\n"
                "2. Use the word 'I' specifically — interviewers want to know YOUR contribution\n"
                "3. Practice the 30-second summary version of this answer for rapid-fire rounds\n\n"
                "*Configure API keys in Settings for real AI-powered answer evaluation.*"
            )
            return jsonify({"evaluation": sample_eval, "mode": "demo"})

        if not evaluation:
            return jsonify({"error": "Model returned empty response."}), 500
        return jsonify({"evaluation": evaluation, "mode": provider, "model": g.get("actual_model")})
    except Exception as exc:
        app.logger.error(f"Answer evaluation error: {exc}")
        return jsonify({"error": str(exc)}), 500



# ── Resume analysis endpoint ───────────────────────────────────────────────────
@app.route("/api/analyze-resume", methods=["POST"])
def analyze_resume():
    resume_text  = ""
    user_profile = {}

    # Accept multipart (file) or JSON (pasted text)
    if request.content_type and "multipart" in request.content_type:
        file = request.files.get("resume")
        if file and file.filename:
            resume_text = file.read().decode("utf-8", errors="ignore")
        profile_raw = request.form.get("profile", "{}")
        try:
            user_profile = json.loads(profile_raw)
        except json.JSONDecodeError:
            user_profile = {}
    else:
        data         = request.get_json(force=True)
        resume_text  = data.get("resume_text", "").strip()
        user_profile = data.get("profile", {})

    if not resume_text:
        return jsonify({"error": "No resume content provided"}), 400

    ai   = AGENT_INSTRUCTIONS
    role = user_profile.get("role", "the target position")

    system_prompt = build_system_prompt(user_profile)
    user_instruction = (
        f"Analyze the following resume for a candidate applying to a **{role}** position.\n\n"
        f"--- RESUME START ---\n{resume_text[:3000]}\n--- RESUME END ---\n\n"
        f"Provide a comprehensive analysis with these sections:\n\n"
        f"**1. Overall Impression (Score: X/100)**\n"
        f"[First impression, professional presentation]\n\n"
        f"**2. Key Strengths**\n"
        f"[What stands out positively]\n\n"
        f"**3. Critical Gaps & Red Flags**\n"
        f"[Missing skills, experience gaps, concerns]\n\n"
        f"**4. ATS Compatibility**\n"
        f"[Keyword analysis, formatting issues for ATS systems]\n\n"
        f"**5. Suggested Improvements**\n"
        f"[Specific, actionable rewrites or additions]\n\n"
        f"**6. Interview Questions Likely to be Asked**\n"
        f"[5 questions this resume will likely generate in an interview]\n\n"
        f"**7. Preparation Strategy**\n"
        f"[3-step action plan to strengthen candidacy]"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_instruction}
    ]

    try:
        analysis, provider = get_llm_generation(messages, user_profile)
        if provider == "demo":
            sample = (
                "**Resume Analysis Report 📄**\n\n"
                "**1. Overall Impression (Score: 76/100)**\n"
                "Solid foundation with relevant experience. Needs stronger quantification and clearer impact statements.\n\n"
                "**2. Key Strengths**\n"
                "- Relevant technical skills listed clearly\n"
                "- Progressive career growth visible\n"
                "- Education well-positioned\n\n"
                "**3. Critical Gaps**\n"
                "- No measurable achievements (add % improvements, revenue impact, team sizes)\n"
                "- Skills section lacks modern tools/frameworks\n"
                "- No personal projects, open-source, or certifications\n\n"
                "**4. ATS Compatibility**\n"
                "- Use standard section headers (not creative names)\n"
                "- Add role-specific keywords from job descriptions\n"
                "- Avoid tables/columns — ATS scanners often mis-read them\n\n"
                "**5. Suggested Improvements**\n"
                "- Replace: 'Responsible for managing projects'\n"
                "- With: 'Led cross-functional team of 8, delivering 3 projects on time, 15% under budget'\n\n"
                "*Configure API keys in Settings for full AI-powered resume analysis.*"
            )
            return jsonify({"analysis": sample, "mode": "demo"})

        if not analysis:
            return jsonify({"error": "Model returned empty response."}), 500
        return jsonify({"analysis": analysis, "mode": provider, "model": g.get("actual_model")})
    except Exception as exc:
        app.logger.error(f"Resume analysis error: {exc}")
        return jsonify({"error": str(exc)}), 500



# ── Interview preparation strategy ────────────────────────────────────────────
@app.route("/api/prep-strategy", methods=["POST"])
def prep_strategy():
    data         = request.get_json(force=True)
    user_profile = data.get("profile", {})
    days_until   = int(data.get("days_until_interview", 7))

    ai         = AGENT_INSTRUCTIONS
    role       = user_profile.get("role", "the target position")
    company    = user_profile.get("company", "the target company")
    domain     = user_profile.get("domain", "general")
    difficulty = user_profile.get("difficulty", ai["default_difficulty"])

    system_prompt = build_system_prompt(user_profile)
    user_instruction = (
        f"Create a {days_until}-day interview preparation strategy for:\n"
        f"- Role: {role}\n"
        f"- Company: {company}\n"
        f"- Domain: {domain.replace('_', ' ').title()}\n"
        f"- Level: {difficulty.replace('_', ' ').title()}\n"
        f"- Days until interview: {days_until}\n\n"
        f"Include:\n"
        f"1. Daily study schedule (what to focus on each day)\n"
        f"2. Key topics to master\n"
        f"3. Practice question types to focus on\n"
        f"4. Resources and tools to use\n"
        f"5. Day-before and day-of interview tips\n"
        f"6. Common mistakes to avoid for this role"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_instruction}
    ]

    try:
        strategy, provider = get_llm_generation(messages, data)
        if provider == "demo":
            sample = (
                f"**{days_until}-Day Interview Prep Strategy 🗓️**\n\n"
                f"**Days 1-2: Research & Foundation**\n"
                f"- Deep-dive into {company}'s products, culture, recent news\n"
                f"- Review job description — highlight every keyword\n"
                f"- List your top 10 career stories in STAR format\n\n"
                f"**Days 3-4: Technical & Domain Prep**\n"
                f"- Practice 20 domain-specific questions daily\n"
                f"- Review fundamentals: data structures, system design (if technical)\n"
                f"- Do 2 mock interviews with a friend or record yourself\n\n"
                f"**Days 5-6: Behavioral & Soft Skills**\n"
                f"- Refine your 'Tell me about yourself' (under 2 minutes)\n"
                f"- Prepare 5 strong STAR stories covering: leadership, conflict, failure, success, initiative\n"
                f"- Prepare 5 smart questions to ask the interviewer\n\n"
                f"**Day 7: Final Prep**\n"
                f"- Light review only — don't cram\n"
                f"- Prepare logistics: outfit, commute, documents\n"
                f"- 8 hours sleep, healthy meal, arrive 15 minutes early\n\n"
                f"*Configure API keys in Settings for a fully personalized AI prep strategy.*"
            )
            return jsonify({"strategy": sample, "mode": "demo"})

        if not strategy:
            return jsonify({"error": "Model returned empty response."}), 500
        return jsonify({"strategy": strategy, "mode": provider, "model": g.get("actual_model")})
    except Exception as exc:
        app.logger.error(f"Prep strategy error: {exc}")
        return jsonify({"error": str(exc)}), 500



# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET", "POST"])
def health():
    data = {}
    if request.method == "POST":
        try:
            data = request.get_json(force=True) or {}
        except Exception:
            pass

    provider = data.get("llm_provider") or os.getenv("LLM_PROVIDER") or "auto"
    
    watsonx_ok = False
    try:
        model = get_watsonx_model()
        watsonx_ok = model is not None
    except Exception:
        pass

    hf_api_key = data.get("huggingface_api_key") or os.getenv("HUGGINGFACE_API_KEY")

    # Determine status based on provider selection
    if provider == "watsonx":
        status = "connected" if watsonx_ok else "demo_mode"
        active = "watsonx"
    elif provider == "huggingface":
        status = "connected" if hf_api_key else "demo_mode"
        active = "huggingface"
    elif provider == "demo":
        status = "demo_mode"
        active = "demo"
    else: # auto mode
        if watsonx_ok:
            status = "connected"
            active = "watsonx"
        elif hf_api_key:
            status = "connected"
            active = "huggingface"
        else:
            status = "demo_mode"
            active = "demo"

    model_name = "Static Demo"
    if active == "watsonx":
        model_name = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")
    elif active == "huggingface":
        model_name = data.get("huggingface_model_id") or os.getenv("HUGGINGFACE_MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")

    return jsonify({
        "status":    "ok",
        "watsonx":   status,
        "active_provider": active,
        "active_model": model_name,
        "agent":     AGENT_INSTRUCTIONS["name"],
        "timestamp": datetime.now().isoformat(),
    })



# ── Diagnostics ────────────────────────────────────────────────────────────────
@app.route("/api/debug-llm")
def debug_llm():
    watsonx_err = None
    hf_err = None
    
    # Test DNS resolution
    import socket
    dns_resolved = {}
    for host in ["iam.cloud.ibm.com", "au-syd.ml.cloud.ibm.com", "api-inference.huggingface.co", "router.huggingface.co", "api.huggingface.co", "huggingface.co", "google.com"]:
        try:
            ip = socket.gethostbyname(host)
            dns_resolved[host] = ip
        except Exception as e:
            dns_resolved[host] = f"Error: {e}"

    # Test Watsonx
    try:
        model = get_watsonx_model()
        if model is None:
            watsonx_err = f"Credentials not configured or init failed: {_watsonx_init_error}"
        else:
            prompt = format_prompt_for_model([{"role": "user", "content": "Hello"}], os.getenv("WATSONX_MODEL_ID", ""))
            model.generate_text(prompt=prompt)
            watsonx_err = "Success!"
    except Exception as e:
        watsonx_err = f"Error: {str(e)}"

    # Test Hugging Face endpoints
    hf_endpoints_status = {}
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    model_id = os.getenv("HUGGINGFACE_MODEL_ID", "meta-llama/Llama-3.3-70B-Instruct")
    prompt = format_prompt_for_model([{"role": "user", "content": "Hello"}], model_id)
    
    endpoints = {
        "legacy": f"https://api-inference.huggingface.co/models/{model_id}",
        "router_models": f"https://router.huggingface.co/models/{model_id}",
        "router_hf_inference": f"https://router.huggingface.co/hf-inference/models/{model_id}",
        "api": f"https://api.huggingface.co/models/{model_id}"
    }
    
    for name, url in endpoints.items():
        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"inputs": prompt, "parameters": {"max_new_tokens": 10, "temperature": 0.7}}
            r = requests.post(url, headers=headers, json=payload, timeout=8)
            hf_endpoints_status[name] = f"Status: {r.status_code}, Body: {r.text[:120]}"
        except Exception as e:
            hf_endpoints_status[name] = f"Error: {e}"

    # Also test the default fallback models
    for fb_model in ["Qwen/Qwen2.5-7B-Instruct", "meta-llama/Llama-3.3-70B-Instruct"]:
        fb_url = f"https://router.huggingface.co/hf-inference/models/{fb_model}"
        fb_prompt = format_prompt_for_model([{"role": "user", "content": "Hello"}], fb_model)
        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"inputs": fb_prompt, "parameters": {"max_new_tokens": 10, "temperature": 0.7}}
            r = requests.post(fb_url, headers=headers, json=payload, timeout=8)
            hf_endpoints_status[f"fallback_{fb_model.replace('/', '_')}"] = f"Status: {r.status_code}, Body: {r.text[:120]}"
        except Exception as e:
            hf_endpoints_status[f"fallback_{fb_model.replace('/', '_')}"] = f"Error: {e}"

    # Test OpenAI compatible router
    for model_name in ["Qwen/Qwen2.5-7B-Instruct", "meta-llama/Llama-3.3-70B-Instruct", "microsoft/Phi-3-mini-4k-instruct"]:
        try:
            r = requests.post(
                "https://router.huggingface.co/hf-inference/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                },
                timeout=8
            )
            hf_endpoints_status[f"v1_chat_{model_name.replace('/', '_')}"] = f"Status: {r.status_code}, Body: {r.text[:120]}"
        except Exception as e:
            hf_endpoints_status[f"v1_chat_{model_name.replace('/', '_')}"] = f"Error: {e}"
    # Test InferenceClient from huggingface_hub
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(token=api_key)
        res = client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="Qwen/Qwen2.5-7B-Instruct",
            max_tokens=10
        )
        hf_endpoints_status["InferenceClient_chat"] = f"Success: {res.choices[0].message.content}"
    except Exception as e:
        hf_endpoints_status["InferenceClient_chat"] = f"Error: {e}"

    # Test base router v1 completions (without provider name)
    try:
        r = requests.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            },
            timeout=8
        )
        hf_endpoints_status["base_router_v1_chat"] = f"Status: {r.status_code}, Body: {r.text[:120]}"
    except Exception as e:
        hf_endpoints_status["base_router_v1_chat"] = f"Error: {e}"
    return jsonify({
        "watsonx": watsonx_err,
        "huggingface_endpoints": hf_endpoints_status,
        "dns": dns_resolved,
        "env_keys": {
            "has_ibm_key": os.getenv("IBM_API_KEY") is not None,
            "has_project_id": os.getenv("WATSONX_PROJECT_ID") is not None,
            "has_hf_key": os.getenv("HUGGINGFACE_API_KEY") is not None,
            "watsonx_model": os.getenv("WATSONX_MODEL_ID"),
            "hf_model": os.getenv("HUGGINGFACE_MODEL_ID")
        }
    })


# ── Agent info ─────────────────────────────────────────────────────────────────
@app.route("/api/agent-info")
def agent_info():
    ai = AGENT_INSTRUCTIONS
    return jsonify({
        "name":             ai["name"],
        "capabilities":     ai["capabilities"],
        "domains":          ai["supported_domains"],
        "modes":            ai["available_modes"],
        "difficulty_levels": list(ai["difficulty_descriptions"].keys()),
        "default_mode":     ai["default_interview_mode"],
        "default_difficulty": ai["default_difficulty"],
        "tone":             ai["tone"],
    })


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
