import sqlite3
import random
import json
import os
import requests
import pypdf
import docx
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "").strip()

# Print partial key for verification
if api_key:
    masked = api_key[:4] + "*" * (len(api_key)-8) + api_key[-4:]
    print(f"--- API KEY VERIFIED: {masked} (length: {len(api_key)}) ---")
else:
    print("--- WARNING: GEMINI_API_KEY NOT FOUND ---")

def init_db():

    conn = sqlite3.connect("gradvox.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        rating INTEGER,
        feedback TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


app = Flask(__name__)
app.secret_key = "gradvox_secret"

# Home
@app.route("/")
def index():
    return render_template("getstarted.html")


# Diagnostic route to see available models
@app.route("/api/check_models")
def check_models():
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
        res = requests.get(url)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)})

# Name page
@app.route("/name", methods=["GET","POST"])
def name():

    if request.method == "POST":

        username = request.form.get("username")

        if username:   # make sure name is not empty
            session["username"] = username

        return redirect(url_for("dashboard"))

    return render_template("name.html")


# Dashboard
@app.route("/dashboard")
def dashboard():

    username = session.get("username","User")

    return render_template(
        "dashboard.html",
        username=username
    )

with open("questions.json") as f:
    db = json.load(f)

current_test=[]


@app.route("/aptitude")
def aptitude():
    return render_template("aptitude.html")

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")

from flask import request, jsonify

# --- AUTO-DETECTION FOR MODEL ---
WORKING_MODEL = None

def _get_working_model():
    global WORKING_MODEL
    if WORKING_MODEL: return WORKING_MODEL
    
    # Use latest available high-speed models verified via CLI
    names = ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-2.5-flash"]
    for name in names:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent?key={api_key}"
        try:
            r = requests.post(url, json={"contents": [{"role": "user", "parts": [{"text": "hi"}]}]}, timeout=10)
            if r.status_code == 200:
                WORKING_MODEL = name
                return WORKING_MODEL
        except:
            continue
    
    WORKING_MODEL = "gemini-2.0-flash" # Fallback to a confirmed model
    return WORKING_MODEL

@app.route("/get_response", methods=["POST"])
def get_response():
    try:
        user_msg = request.json.get("message")
        model = _get_working_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        # Standard single-turn prompt approach
        contents = [
            {
                "role": "user", 
                "parts": [{"text": f"Instructions: You are a highly professional interview expert. Provide crisp, professional answers. DO NOT use markdown like ** or #. Keep it concise.\n\nUser Message: {user_msg}"}]
            }
        ]
        
        res = requests.post(url, json={"contents": contents}, timeout=15)
        data = res.json()
        
        if "error" in data:
            if data["error"]["code"] == 429:
                return jsonify({"reply": "Rate limit reached! Google restricts Free-Tier keys. Please wait about 60 seconds before trying again."})
            return jsonify({"reply": f"API Error: {data['error'].get('message', 'Unknown')}"})
            
        reply = data["candidates"][0]["content"]["parts"][0]["text"]

        return jsonify({"reply": reply})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"reply": "Error: " + str(e)})


@app.route("/start_test/<category>")
def start_test(category):

    global current_test

    category_questions=[q for q in db if q["category"]==category]

    current_test = random.sample(category_questions, min(50, len(category_questions)))

    return render_template(
        "aptitude_test.html",
        questions=current_test
    )


@app.route("/submit_test", methods=["POST"])
def submit_test():

    score = 0
    results = []

    for i, q in enumerate(current_test, 1):

        user = request.form.get(f"q{i}", "Not Answered")
        correct = q["answer"]

        if user == correct:
            score += 1

        results.append({
            "question": q["question"],
            "user": user,
            "correct": correct
        })

    return render_template(
        "aptitude_result.html",
        score=score,
        total=len(current_test),
        results=results
    )
# Company Preparation
@app.route("/company_prep")
def company_prep():
    companies = [
        {
            "name": "Google",
            "focus": "Algorithms and System Design",
            "logo": "/static/google.png",
            "link": "/company_detail/Google",
            "rounds": "5 Rounds",
            "difficulty": "Hard",
            "type": "Product"
        },
        {
            "name": "Amazon",
            "focus": "Data Structures and Leadership Principles",
            "logo": "/static/amazon.png",
            "link": "/company_detail/Amazon",
            "rounds": "4 Rounds", 
            "difficulty": "Hard",
            "type": "Product"
        },
        {
            "name": "Microsoft",
            "focus": "Coding and Problem Solving",
            "logo": "/static/microsoft.png",
            "link": "/company_detail/Microsoft",
            "rounds": "4 Rounds",
            "difficulty": "Hard",
            "type": "Product"
        },
        {
            "name": "TCS",
            "focus": "Aptitude and Technical Basics",
            "logo": "/static/tcs.png",
            "link": "/company_detail/TCS",
            "rounds": "3 Rounds",
            "difficulty": "Medium",
            "type": "Service"
        }
    ]

    return render_template(
        "company_prep.html",
        companies=companies
    )

# Company detail page route
@app.route("/company_detail/<company_name>")
def company_detail(company_name):
    skills = {
        "Google": ["Algorithms", "System Design", "Coding", "Problem Solving"],
        "Amazon": ["Data Structures", "Leadership Principles", "Coding", "Aptitude"],
        "Microsoft": ["Coding", "Problem Solving", "System Design", "Technical Questions"],
        "TCS": ["Aptitude", "Technical Basics", "Coding"],
        "Other": ["General Aptitude", "Coding", "Technical Knowledge"]
    }

    company_skills = skills.get(company_name, skills["Other"])
    logo = f"/static/{company_name.lower()}.png" if company_name != "Other" else "/static/other.png"

    return render_template(
        "company_detail.html",
        company_name=company_name,
        company_skills=company_skills,
        logo=logo
    )
# Interview Setup
@app.route("/interview_setup", methods=["GET","POST"])
def interview_setup():

    if request.method == "POST":

        domain = request.form.get("domain")
        difficulty = request.form.get("difficulty", "Medium")
        print("DOMAIN RECEIVED:", domain, "DIFFICULTY:", difficulty)

        session["domain"] = domain
        session["difficulty"] = difficulty

        return redirect(url_for("interview"))

    return render_template("interview_setup.html")


# Interview Page
@app.route("/interview")
def interview():
    domain = session.get("domain", "General")
    difficulty = session.get("difficulty", "Medium")
    username = session.get("username", "Candidate")
    
    # Initialize the dynamic AI interview state
    session["interview_history"] = []
    session["question_count"] = 0
    
    return render_template(
        "interview.html",
        domain=domain,
        difficulty=difficulty,
        username=username
    )
@app.route("/api/interview_chat", methods=["POST"])
def interview_chat():
    domain = session.get("domain", "General")
    name = session.get("username", "Candidate")
    company = session.get("company", "our company")
    user_msg = request.json.get("message")

    history = session.get("interview_history", [])
    q_count = session.get("question_count", 0)

    # ---------------- PREPARE INPUT ----------------
    # If it's the very start (no user message), we simulate a "Start" message 
    if not user_msg:
        current_user_turn = "Start the interview now please."
        sys_prompt = f"""
        You are a professional, polite, and realistic interviewer for a {domain} role at {company}.
        The candidate's name is {name}.

        Guidelines for Welcome Message:
        - Start by welcoming {name} to the interview for the {domain} position.
        - Ask ONE clear question: 'To get started, could you please tell me about yourself and your background relevant to {domain}?'
        - Keep response short. No markdown.
        """
    else:
        current_user_turn = user_msg
        q_count += 1
        session["question_count"] = q_count
        
        # ---------------- END CHECK ----------------
        if q_count >= 10:
            return jsonify({
                "reply": "Excellent work. We have completed the interview. Generating your performance report now!",
                "is_complete": True
            })

        sys_prompt = f"""
        You are a professional, polite, and realistic interviewer for a {domain} role at {company}.
        The candidate's name is {name}.

        Your Style: Professional, friendly. Keep responses under 2 sentences. 
        No markdown (**, #). Ask ONLY ONE question.
        Progress: question {q_count} of 10.
        """

    # Append latest turn
    history.append({"role": "user", "content": current_user_turn})

    # ---------------- GEMINI PAYLOAD BUILDER ----------------
    contents = []
    instructions_injected = False
    
    for m in history:
        role = "user" if m["role"] == "user" else "model"
        text = m["content"]
        
        if not instructions_injected and role == "user":
            text = f"SYSTEM INSTRUCTIONS: {sys_prompt}\n\nUSER INPUT: {text}"
            instructions_injected = True
            
        if contents and contents[-1]["role"] == role:
            contents[-1]["parts"][0]["text"] += "\n" + text
        else:
            contents.append({"role": role, "parts": [{"text": text}]})

    # ---------------- GEMINI CALL ----------------
    model = _get_working_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    try:
        res = requests.post(url, json={"contents": contents}, timeout=25)
        data = res.json()
        
        if "error" in data:
            err_msg = data["error"].get("message", "Unknown API error")
            if data["error"].get("code") == 429:
                return jsonify({"error": "rate_limit", "reply": "Thinking...", "is_complete": False})
            return jsonify({"error": "api", "reply": f"API Error: {err_msg}", "is_complete": False})

        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        
        # SAVE HISTORY
        history.append({"role": "assistant", "content": reply})
        session["interview_history"] = history
        
        is_complete = session.get("question_count", 0) >= 10
        
        return jsonify({
            "reply": reply,
            "is_complete": is_complete,
            "count": session.get("question_count", 0)
        })
        
    except Exception as e:
        print("INTERVIEW ERROR:", e)
        return jsonify({
            "error": "connectivity",
            "reply": "Connection glitch. Please try again.",
            "is_complete": False
        })

# Result
@app.route("/result")
def result():

    domain = session.get("domain")

    score = random.randint(60,95)

    skills = {

    "Communication": random.randint(60,90),
    "Technical": random.randint(65,95),
    "Confidence": random.randint(60,90),
    "Clarity": random.randint(60,90)

    }

    domain_skills = {

    "Data Scientist":[
"Python programming",
"Statistics and probability",
"Machine learning algorithms",
"Data preprocessing and cleaning",
"Feature engineering",
"Model evaluation techniques",
"Data visualization",
"SQL and database querying",
"Deep learning basics",
"Business problem solving"
],

"Data Analyst":[
"Excel and spreadsheet analysis",
"SQL and database querying",
"Data cleaning and preprocessing",
"Exploratory data analysis (EDA)",
"Data visualization tools",
"Dashboard creation",
"Statistical analysis",
"Business intelligence tools",
"Reporting and storytelling with data",
"Problem solving with data"
],

"HR Interview":[
"Communication skills",
"Confidence and body language",
"Self introduction and storytelling",
"Teamwork and collaboration",
"Problem solving ability",
"Leadership qualities",
"Time management",
"Adaptability",
"Professional ethics",
"Career goal clarity"
],

"Full Stack Developer":[
"HTML CSS and JavaScript",
"Frontend frameworks like React",
"Backend development with Node.js or similar",
"REST API development",
"Database design (SQL or NoSQL)",
"Authentication and security",
"Version control with Git",
"Deployment and cloud basics",
"Debugging and testing",
"System design fundamentals"
],

"Backend Developer":[
"Server side programming",
"API design and development",
"Database management",
"Authentication and authorization",
"Performance optimization",
"Caching techniques",
"Microservices architecture",
"Cloud services basics",
"Security best practices",
"Scalability concepts"
],

"Frontend Developer":[
"HTML CSS and JavaScript",
"Responsive web design",
"JavaScript frameworks like React or Angular",
"DOM manipulation",
"State management",
"Cross browser compatibility",
"Web performance optimization",
"UI component design",
"Accessibility standards",
"Frontend debugging"
],

"Software Engineer":[
"Data structures and algorithms",
"Object oriented programming",
"System design",
"Version control (Git)",
"Software development lifecycle",
"Problem solving and coding",
"Testing and debugging",
"Database concepts",
"Operating system basics",
"Networking fundamentals"
],

"UI/UX Designer":[
"User research",
"Wireframing and prototyping",
"Design thinking",
"User interface design",
"Typography and color theory",
"Usability testing",
"Interaction design",
"Accessibility principles",
"Design tools like Figma",
"User centered design"
]


    }

    attempt = {

    "domain":domain,
    "score":score

    }

    history = session.get("history",[])

    history.append(attempt)

    session["history"] = history

    return render_template(
"result.html",
score=score,
domain=domain,
domain_skills=domain_skills,
speaking_time=75,
confidence=85,
clarity=80,
answer_length=70
)


# History
@app.route("/history")
def history():

    history = session.get("history",[])

    return render_template(
        "history.html",
        history=history
    )


# Analytics
@app.route("/analytics")
def analytics():

    history = session.get("history",[])

    scores = [attempt["score"] for attempt in history]

    avg_score = 0

    if scores:
        avg_score = sum(scores)/len(scores)

    return render_template(
        "analytics.html",
        scores=scores,
        avg_score=avg_score
    )


# Feedback
@app.route("/feedback", methods=["GET","POST"])
def feedback():

    if request.method == "POST":

        rating = request.form.get("rating")

        return redirect(url_for("dashboard"))

    return render_template("feedback.html")


@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():

    username = session.get("username")

    rating = request.form.get("rating")
    feedback = request.form.get("feedback")

    conn = sqlite3.connect("gradvox.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO feedback (name, rating, feedback) VALUES (?, ?, ?)",
        (username, rating, feedback)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route("/owner_feedback")
def owner_feedback():

    conn = sqlite3.connect("gradvox.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, rating, feedback FROM feedback")

    data = cursor.fetchall()

    conn.close()

    return render_template("owner_feedback.html", data=data)


# ──────────────────────────────────────────────
# Debugging Challenge — AI-generated questions
# ──────────────────────────────────────────────

# Topic pool to keep variety across questions
DEBUG_TOPICS = [
    "missing closing parenthesis or bracket",
    "wrong comparison operator (= instead of ==)",
    "missing colon after if/for/while/def",
    "off-by-one error in a loop range",
    "TypeError mixing string and int",
    "indentation error inside a function",
    "wrong variable name (typo)",
    "missing return statement",
    "IndexError accessing out-of-bounds index",
    "comparing with wrong data type",
    "reading variable before assignment",
    "string not converted before concatenation",
    "using = inside a conditional expression",
]

import re as _re

@app.route("/debugging_challenge")
def debugging_challenge():
    return render_template("debugging_challenge.html")


@app.route("/api/generate_challenge", methods=["GET"])
def generate_challenge():
    """
    Calls Gemini to generate a unique Python debugging challenge.
    Returns a JSON object the frontend can directly use.
    """
    try:
        topic = random.choice(DEBUG_TOPICS)

        prompt = f"""You are a Python mentor creating simple debugging puzzles for beginners.
Generate ONE easy Python debugging challenge about: "{topic}"

Return ONLY a valid JSON object with these keys:
- title: Short title (max 5 words)
- difficulty: "easy"
- time: 25
- bugDesc: One short sentence describing the issue (no spoilers)
- buggyCode: 3-6 lines of simple Python with 1 clear bug
- hint: A helpful nudge
- fix: The correct code
- keywords: 2-3 short strings that must be in the user's fix
- xpReward: 15

Rules:
- THE CHALLENGE MUST BE SIMPLE AND EASY.
- Return PURE JSON only. No markdown fences.
"""

        contents = [
            {"role": "user", "parts": [{"text": f"INSTRUCTIONS: {prompt}\n\nGenerate the JSON now."}]}
        ]

        model = _get_working_model()
        url = (
            f"https://generativelanguage.googleapis.com/v1/models/"
            f"{model}:generateContent?key={api_key}"
        )
        res = requests.post(url, json={"contents": contents})
        data = res.json()

        if "error" in data:
            if data["error"].get("code") == 429:
                return jsonify({"error": "rate_limit"}), 429
            raise Exception(data["error"]["message"])

        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        # Clean up JSON text
        raw_text = _re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = _re.sub(r"\s*```$", "", raw_text)

        challenge = json.loads(raw_text)

        # Basic validation
        for key in ["title", "buggyCode", "fix", "keywords"]:
            if key not in challenge:
                raise ValueError(f"Missing key: {key}")

        return jsonify(challenge)

    except Exception as e:
        print("generate_challenge ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/resume_analyzer")
def resume_analyzer():
    return render_template("resume_analyzer.html")

@app.route("/api/analyze_resume", methods=["POST"])
def analyze_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["resume"]
    filename = file.filename
    ext = filename.split(".")[-1].lower()
    
    try:
        text = ""
        if ext == "pdf":
            pdf = pypdf.PdfReader(file)
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        elif ext == "docx":
            doc = docx.Document(file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            text = file.read().decode("utf-8", errors="ignore")
            
        if not text.strip():
            return jsonify({"error": "The resume appears to be empty or unreadable."}), 400
            
        # Limit text size to avoid token limits
        text = text[:8000]
        
        # Prepare the Gemini prompt
        prompt = f"""You are a professional Executive Recruiter and ATS Specialist. 
Analyze this resume text and provide a detailed analysis.

Return ONLY a JSON object with these keys:
- score: (Integer between 0-100)
- strengths: (List of 4 strong points)
- weaknesses: (List of 4 missing or weak points)
- suggestions: (List of 5 actionable improvement tips)
- skillsDetected: (List of top 6 technical or soft skills found)
- professionalSummary: (One sentence summary of the profile)

RESUME TEXT:
{text}
"""
        model = _get_working_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        contents = [
            {"role": "user", "parts": [{"text": "INSTRUCTIONS: Return PURE JSON only. No markdown fences. Analyze the resume below.\n\n" + prompt}]}
        ]
        
        res = requests.post(url, json={"contents": contents}, timeout=45)
        data = res.json()
        
        if "error" in data:
            return jsonify({"error": data["error"].get("message", "API Error")}), 500
        
        raw_reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Clean up JSON if LLM included backticks
        import re
        raw_reply = re.sub(r"^```(?:json)?\s*", "", raw_reply)
        raw_reply = re.sub(r"\s*```$", "", raw_reply)
        
        analysis = json.loads(raw_reply)
        return jsonify(analysis)
        
    except Exception as e:
        print("RESUME ERROR:", str(e))
        return jsonify({"error": f"Failed to process resume: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)