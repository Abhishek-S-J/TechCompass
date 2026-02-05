from flask import Flask, render_template, request,jsonify
from groq import Groq
from flask_cors import CORS
import markdown
from PyPDF2 import PdfReader
from flask import session
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)
app.secret_key = "techcompass-secret"
CORS(app)

# 🔑 Your Groq API key (later regenerate this)
client = Groq(api_key=GROQ_API_KEY)

# ================= HOME PAGE =================

@app.route("/")
def home():
    return render_template("home.html")

# ================= ROADMAP MODULE =================

@app.route("/roadmap", methods=["GET", "POST"])
def roadmap():
    output = ""
    if request.method == "POST":
        goal = request.form.get("goal")

        prompt = f"""
        You are an expert career mentor.
        Create a clear, structured learning roadmap for:
        {goal}

        Include:
        - Skills to learn
        - Order of learning
        - Tools to use
        - Timeline
        If the {goal} coumpulsary needs to complete a course state it too,like for example medical related topics.
        If the {goal} cannot be completed in the stated time then offer the user withreasonable time or just give the most important topics to cover at that time.

        """

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )

        raw_output = chat_completion.choices[0].message.content
        output = markdown.markdown(raw_output)

    return render_template("index.html", output=output)


# ================= STUDY PLAN MODULE =================

@app.route("/study", methods=["GET", "POST"])
def study():
    output = ""
    if request.method == "POST":
        goal = request.form.get("goal")

        prompt = f"""
You are an expert syllabus designer.

User goal:
{goal}

Your task:
- Extract the EXACT topic from the goal
- Create a learning plan ONLY for that topic
- Do NOT include any prerequisite topics unless absolutely required
- Do NOT teach full Python or full programming
- Focus STRICTLY on the requested subject

Plan rules:
- Organize by Weeks
- Each week must contain:
  • Concepts to master
  • Hands-on practice tasks
  • Mini assignment or mini project
- End with ONE final capstone project
- Respect the given time duration in the goal
- If goal is "Python OOP", do NOT teach Python basics, syntax, loops, etc.

Output format:
- Clear Week-wise headings
- Bullet points only
- No motivational text
- No daily routines
- No generic advice
"""

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )

        raw_output = chat_completion.choices[0].message.content
        output = markdown.markdown(raw_output)

    return render_template("study.html", output=output)


# ================= RESUME ANALYZER MODULE =================

@app.route("/resume", methods=["GET", "POST"])
def resume():
    output = ""

    if request.method == "POST":
        resume_text = ""

        # 1️⃣ FIRST priority: pasted text
        pasted_text = request.form.get("resume_text")
        if pasted_text and pasted_text.strip():
            resume_text = pasted_text.strip()

        # 2️⃣ SECOND priority: PDF upload (only if no pasted text)
        else:
            file = request.files.get("resume_file")
            if file and file.filename.endswith(".pdf"):
                reader = PdfReader(file)
                for page in reader.pages:
                    resume_text += page.extract_text() or ""

        # 3️⃣ Final safety check
        if not resume_text.strip():
            output = "<p style='color:red'>❌ No readable resume content found.</p>"
            return render_template("resume.html", output=output)

        prompt = f"""
        You are a professional resume reviewer.
        Analyze the resume strictly based on the given content.
        Do NOT invent skills, experience, or education.
        Provide a score out of 10 based on the analysed resume.



        Resume:
        {resume_text}
        """

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )

        raw_output = chat_completion.choices[0].message.content
        output = markdown.markdown(raw_output)

    return render_template("resume.html", output=output)
# ================= MOCK INTERVIEW MODULE =================

@app.route("/interview", methods=["GET", "POST"])
def interview():
    output = None
    MAX_QUESTIONS = 5

    if "interview_started" not in session:
        session["interview_started"] = False

    if "q_count" not in session:
        session["q_count"] = 0

    if "messages" not in session:
        session["messages"] = []

    if request.method == "POST":

        # START INTERVIEW
        if "start" in request.form:
            role = request.form.get("role")
            level = request.form.get("level")

            session["interview_started"] = True
            session["q_count"] = 0

            system_prompt = f"""
You are a professional interviewer.
Start with a friendly greeting.
Interview for the role: {role}
Experience level: {level}
Ask ONE question at a time.
Wait for the candidate's answer.

After the final question:
- STOP asking questions
- Give a detailed evaluation with:
  • Overall score out of 10
  • Technical skills score
  • Communication score
  • Strengths
  • Weaknesses
  • Improvement tips

Do NOT ask any more questions after evaluation.
"""

            session["messages"] = [
                {"role": "system", "content": system_prompt}
            ]

            chat = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=session["messages"]
            )

            output = chat.choices[0].message.content
            session["messages"].append({"role": "assistant", "content": output})

        # USER ANSWER
        elif "answer" in request.form and session["interview_started"]:
            answer = request.form.get("answer")
            session["q_count"] += 1

            session["messages"].append({"role": "user", "content": answer})

            # STOP AFTER MAX QUESTIONS
            if session["q_count"] >= MAX_QUESTIONS:
                output = "🎉 Interview completed! Thanks for participating."

                session.clear()
                return render_template("interview.html", output=output)

            chat = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=session["messages"]
            )   
            raw_output = chat.choices[0].message.content
            output = markdown.markdown(raw_output, extensions=["extra"])

            session["messages"].append({"role": "assistant", "content": output})

    return render_template(
        "interview.html",
        output=output,
        started=session.get("interview_started", False)
    )
# ================= CHAT APPLICATION MODULE =================
@app.route("/chat", methods=["GET", "POST"])
def chat():
    try:
        if "messages" not in session:
            session["messages"] = []

        if request.method == "POST":
            user_input = request.json.get("message", "")

            system_prompt = """
You are TechCompass AI Assistant.
Rules:
- Be friendly, calm, and professional.
- If user is abusive, reply politely and de-escalate.
- Detect language and reply in the same language.
- If user asks for code, return clean code blocks.
- Keep answers concise but helpful.
"""

            # ADD system prompt only once
            if len(session["messages"]) == 0:
                session["messages"].append(
                    {"role": "system", "content": system_prompt}
                )

            # ADD user message to memory
            session["messages"].append(
                {"role": "user", "content": user_input}
            )

            chat_completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=session["messages"]
            )

            response = chat_completion.choices[0].message.content

            # ADD AI response to memory
            session["messages"].append(
                {"role": "assistant", "content": response}
            )

            session.modified = True

            return jsonify({"reply": response})

    except Exception as e:
        return jsonify({"reply": "⚠️ AI service unavailable. Please try again."})

    return render_template("chat.html")


# ================= RUN =================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
