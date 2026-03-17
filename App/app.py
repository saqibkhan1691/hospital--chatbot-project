# # app.py
# from flask import Flask, request, render_template, jsonify
# from langdetect import detect, DetectorFactory
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# from rapidfuzz import fuzz
# import sqlite3, re
# from dateutil import parser as dateparser
# from datetime import datetime

# DetectorFactory.seed = 0

# app = Flask(__name__)

# DOCTORS = [
#     {"id":1, "name":"Dr. A. Sharma", "specialty":"cardiology", "slots":["10:00","11:00","14:00"]},
#     {"id":2, "name":"Dr. R. Rao", "specialty":"ent", "slots":["09:00","13:00"]},
#     {"id":3, "name":"Dr. S. Gupta", "specialty":"pediatrics", "slots":["10:30","15:00"]},
# ]

# FAQS = {
#     "timing": "Hospital timing: Mon-Sat 08:00 - 20:00. Emergency 24x7.",
#     "xray": "X-ray charges start from ₹500 (approx). For accurate quote contact billing.",
#     "visitors": "Visitors allowed 4-7 PM only. Check department-specific rules."
# }

# INTENTS = {
#     "book_appointment": [
#         "I want to book an appointment",
#         "Book appointment with cardiologist",
#         "Mujhe cardiologist ka appointment chahiye",
#         "20 Nov ko appointment book kar do",
#         "Book Dr. Sharma for 21/11 at 10am",
#         "appointment chahiye",
#         "Doctor ka slot chahiye"
#     ],
#     "search_doctor": [
#         "Find a cardiologist",
#         "Who is the neurologist",
#         "ENT doctor timing",
#         "kisi ent doctor ka number do",
#         "doctor list"
#     ],
#     "symptom_check": [
#         "I have fever and cough",
#         "Mujhe bukhar aur khaansi hai",
#         "chest pain ho raha hai",
#         "my head hurts",
#         "I feel dizzy"
#     ],
#     "cancel_appointment": [
#         "Cancel my appointment",
#         "Mera appointment cancel kar do",
#         "I want to cancel booking on 21 Nov"
#     ],
#     "faq": [
#         "What are your timings?",
#         "How much is X-ray?",
#         "Visitor rules"
#     ],
#     "escalate": [
#         "Talk to human",
#         "I want to speak to staff",
#         "human help chahiye"
#     ]
# }

# examples = []
# labels = []
# for intent, phrases in INTENTS.items():
#     for p in phrases:
#         examples.append(p)
#         labels.append(intent)

# vectorizer = TfidfVectorizer(ngram_range=(1,2)).fit(examples)
# X = vectorizer.transform(examples)

# conn = sqlite3.connect("hospital_bot.db", check_same_thread=False)
# c = conn.cursor()
# c.execute("""CREATE TABLE IF NOT EXISTS appointments
#              (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, contact TEXT, doctor TEXT, date TEXT, time TEXT)""")
# c.execute("""CREATE TABLE IF NOT EXISTS logs
#              (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, response TEXT, ts TEXT)""")
# conn.commit()

# def normalize_text(text):
#     text = text.lower().strip()
#     text = re.sub(r"[^\w\s\/:-]", " ", text)
#     text = re.sub(r"\s+", " ", text)
#     return text

# def extract_date_time(text):
#     try:
#         dt = dateparser.parse(text, fuzzy=True, dayfirst=True)
#         if dt:
#             return dt.date().isoformat(), dt.time().isoformat(timespec='minutes')
#     except Exception:
#         pass
#     m = re.search(r'(\d{1,2}[\/\-\s](?:\d{1,2}|[a-zA-Z]{3,}))', text)
#     if m:
#         try:
#             dt = dateparser.parse(m.group(1), fuzzy=True, dayfirst=True)
#             return dt.date().isoformat(), None
#         except Exception:
#             return None, None
#     return None, None

# def detect_language(text):
#     try:
#         lang = detect(text)
#         return lang
#     except Exception:
#         return "en"

# def predict_intent(text, threshold=0.45):
#     norm = normalize_text(text)
#     v = vectorizer.transform([text])
#     sims = cosine_similarity(v, X).flatten()
#     best_idx = sims.argmax()
#     best_score = sims[best_idx]
#     cand_intent = labels[best_idx]

#     best_fuzz = 0
#     for ex in INTENTS[cand_intent]:
#         best_fuzz = max(best_fuzz, fuzz.token_set_ratio(norm, normalize_text(ex)))

#     if best_score >= threshold or best_fuzz >= 60:
#         return cand_intent, float(best_score), int(best_fuzz)

#     global_best = ("unknown", 0)
#     for intent, exs in INTENTS.items():
#         for ex in exs:
#             s = fuzz.token_set_ratio(norm, normalize_text(ex))
#             if s > global_best[1]:
#                 global_best = (intent, s)
#     if global_best[1] >= 55:
#         return global_best[0], 0.0, int(global_best[1])
#     return "unknown", float(best_score), int(best_fuzz)

# def book_appointment_db(name, contact, doctor, date, time):
#     c.execute("INSERT INTO appointments(name,contact,doctor,date,time) VALUES (?,?,?,?,?)",
#               (name, contact, doctor, date or "", time or ""))
#     conn.commit()
#     return c.lastrowid

# def log_interaction(msg, resp):
#     c.execute("INSERT INTO logs(message,response,ts) VALUES (?,?,?)",
#               (msg, resp, datetime.utcnow().isoformat()))
#     conn.commit()

# @app.route("/chat", methods=["POST"])
# def chat():
#     data = request.json
#     text = data.get("message", "")
#     user_name = data.get("name", "") or "Anonymous"

#     lang = detect_language(text)
#     intent, simscore, fuzzscore = predict_intent(text)

#     response = ""
#     # handle intents
#     if intent == "book_appointment":
#         specialty = None
#         doctor_name = None
#         for d in DOCTORS:
#             if d["specialty"] in text.lower() or d["name"].split()[-1].lower() in text.lower():
#                 doctor_name = d["name"]
#                 specialty = d["specialty"]
#                 break
#         date, time = extract_date_time(text)
#         # try phone
#         phone = None
#         m = re.search(r'(\+?\d[\d\s-]{6,}\d)', text)
#         if m:
#             phone = re.sub(r'\s+','',m.group(1))
#         missing = []
#         if not doctor_name and not specialty:
#             missing.append("doctor/specialty")
#         if not date:
#             missing.append("date")
#         if not time:
#             missing.append("time")
#         if not phone:
#             missing.append("contact number")
#         if missing:
#             response = "Please provide: " + ", ".join(missing) + ". Example: 'Book cardiologist with Dr. Sharma on 21 Nov 10:00, my number 9876543210'"
#         else:
#             appt_id = book_appointment_db(user_name, phone, doctor_name or specialty, date, time)
#             response = f"✅ Appointment booked (id {appt_id}) with {doctor_name or specialty} on {date} at {time}. We'll notify you."
#     elif intent == "search_doctor":
#         found = []
#         for d in DOCTORS:
#             if d["specialty"] in text.lower() or d["name"].split()[-1].lower() in text.lower():
#                 found.append(d)
#         if not found:
#             # return all doctors with specialties as hint
#             response = "Available doctors:\n" + "\n".join([f'{d["name"]} ({d["specialty"]})' for d in DOCTORS])
#         else:
#             response = "Found:\n" + "\n".join([f'{d["name"]} - slots: {", ".join(d["slots"])}' for d in found])
#     elif intent == "symptom_check":
#         # a tiny rule-based triage
#         t = text.lower()
#         if any(x in t for x in ["chest pain", "chest tight", "dard seena", "sansein nahi"]):
#             response = "Chest pain or trouble breathing — this may be serious. Please call emergency immediately or visit ER."
#         elif any(x in t for x in ["fever","bukhar","temperature"]):
#             response = "For fever: rest, fluids, paracetamol if necessary. If >38.5°C or symptoms severe, book appointment."
#         else:
#             response = "Describe main symptom briefly (duration, severity). I'm a triage assistant, not a doctor."
#     elif intent == "cancel_appointment":
#         # very basic cancel by name + date attempt
#         date, _ = extract_date_time(text)
#         if date:
#             c.execute("DELETE FROM appointments WHERE name=? AND date=?", (user_name, date))
#             conn.commit()
#             response = f"If matching appointment existed, it's deleted for {date} (check appointments table)."
#         else:
#             response = "Provide appointment date to cancel (e.g., 'cancel my appointment on 21 Nov')."
#     elif intent == "faq":
#         # map to FAQ by keyword
#         if "time" in text.lower() or "timing" in text.lower():
#             response = FAQS["timing"]
#         elif "x-ray" in text.lower() or "xray" in text.lower():
#             response = FAQS["xray"]
#         else:
#             response = "Common info: " + FAQS["timing"]
#     elif intent == "escalate":
#         response = "Connecting to human staff. Please call +91-12345-67890 or reply with 'contact' to receive details."
#     else:
#         # fallback: show suggestions (try to be helpful)
#         response = ("Sorry, I didn't understand that clearly. You can ask things like:\n"
#                     "- 'Book cardiologist 21 Nov 10:00 my number 98xxxx'\n"
#                     "- 'I have fever and cough'\n"
#                     "- 'Show doctors' or 'doctor list'\n"
#                     "Or type 'help' for examples.")
#     # log
#     log_interaction(text, response)
#     return jsonify({"response": response, "intent": intent, "lang": lang, "sim": simscore, "fuzz": fuzzscore})

# @app.route("/")
# def index():
#     return render_template("index.html")

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)






















# app.py (final)
import os, re, io, csv, time, json
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file, abort
from dateutil import parser as dateparser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from langdetect import detect, DetectorFactory
import sqlite3

# Optional OpenAI support
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
USE_OPENAI = bool(OPENAI_KEY)
if USE_OPENAI:
    import openai
    openai.api_key = OPENAI_KEY

DetectorFactory.seed = 0
app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "hospital_bot.db")

# --- DB setup ---
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, contact TEXT, doctor_id INTEGER, doctor_name TEXT, specialty TEXT,
    gender TEXT, date TEXT, time TEXT, created_at TEXT)""")
c.execute("""CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT, response TEXT, intent TEXT, moderated INTEGER, ts TEXT)""")
conn.commit()

# --- Doctors with gender and logo ---
DOCTORS = [
 {"id":1, "name":"Dr. A. Sharma", "specialty":"Physician", "gender":"Male","slots":["09:00","11:00","15:00"], "logo":"1.png"},
 {"id":2, "name":"Dr. R. Rao", "specialty":"Surgeon", "gender":"Male","slots":["10:00","14:00"], "logo":"2.png"},
 {"id":3, "name":"Dr. S. Gupta", "specialty":"Pediatrics", "gender":"Female","slots":["09:30","13:00","16:00"], "logo":"3.png"},
 {"id":4, "name":"Dr. M. Khan", "specialty":"Obstetrics & Gynecology", "gender":"Female","slots":["10:30","14:30"], "logo":"4.png"},
 {"id":5, "name":"Dr. P. Roy", "specialty":"Orthopedics", "gender":"Male","slots":["09:00","12:00","15:00"], "logo":"5.png"},
 {"id":6, "name":"Dr. N. Verma", "specialty":"ENT", "gender":"Female","slots":["09:00","11:30","14:00"], "logo":"6.png"},
 {"id":7, "name":"Dr. K. Singh", "specialty":"Cardiology", "gender":"Male","slots":["10:00","13:00","16:00"], "logo":"7.png"},
 {"id":8, "name":"Dr. V. Patel", "specialty":"Neurology", "gender":"Male","slots":["11:00","14:00"], "logo":"8.png"},
 {"id":9, "name":"Dr. B. Iyer", "specialty":"Dermatology", "gender":"Female","slots":["09:30","12:30"], "logo":"9.png"},
 {"id":10,"name":"Dr. R. Mehta", "specialty":"Pulmonology", "gender":"Male","slots":["10:00","15:00"], "logo":"10.png"},
 {"id":11,"name":"Dr. S. Bhat", "specialty":"Ophthalmology", "gender":"Female","slots":["09:00","13:00"], "logo":"11.png"},
 {"id":12,"name":"Dr. D. Das", "specialty":"Urology", "gender":"Male","slots":["09:30","16:00"], "logo":"12.png"},
 {"id":13,"name":"Dr. T. Roy", "specialty":"Gastroenterology", "gender":"Male","slots":["11:00","14:30"], "logo":"13.png"},
 {"id":14,"name":"Dr. A. Kapoor", "specialty":"Endocrinology", "gender":"Female","slots":["10:30","15:30"], "logo":"14.png"},
 {"id":15,"name":"Dr. L. Nair", "specialty":"Nephrology", "gender":"Female","slots":["09:00","12:00"], "logo":"15.png"},
 {"id":16,"name":"Dr. O. Singh", "specialty":"General Surgery", "gender":"Male","slots":["10:00","13:30"], "logo":"16.png"},
 {"id":17,"name":"Dr. H. Rao", "specialty":"Psychiatry", "gender":"Male","slots":["11:00","16:00"], "logo":"17.png"},
 {"id":18,"name":"Dr. Y. Das", "specialty":"Emergency Medicine", "gender":"Male","slots":["00:00"], "logo":"18.png"},
 {"id":19,"name":"Dr. F. Khan", "specialty":"Oncology", "gender":"Female","slots":["10:00","14:00"], "logo":"19.png"},
 {"id":20,"name":"Dr. G. Thomas", "specialty":"Rheumatology", "gender":"Male","slots":["09:30","15:00"], "logo":"20.png"},
 {"id":21,"name":"Dr. V. Singh", "specialty":"Family Medicine", "gender":"Female","slots":["09:00","11:00","16:00"], "logo":"21.png"},
 {"id":22,"name":"Dr. R. Patel", "specialty":"Physiotherapy", "gender":"Male","slots":["10:00","14:00"], "logo":"22.png"},
 {"id":23,"name":"Dr. S. Das", "specialty":"Dental", "gender":"Female","slots":["09:00","12:00"], "logo":"23.png"},
 {"id":24,"name":"Dr. K. Roy", "specialty":"Audiology (ENT)", "gender":"Male","slots":["10:00","15:00"], "logo":"24.png"},
 {"id":25,"name":"Dr. P. Menon", "specialty":"Palliative Care", "gender":"Female","slots":["11:00","14:00"], "logo":"25.png"},
]
DOCTOR_BY_ID = {d["id"]: d for d in DOCTORS}

# --- intents & simple model ---
INTENTS = {
 "book_appointment":["book appointment","book slot","appointment chahiye","schedule appointment","book Dr","book with"],
 "symptom_check":["fever","bukhar","cough","chest pain","dizziness","headache","pain"],
 "search_doctor":["find doctor","doctor list","cardiologist","pediatrician","who is the surgeon","surgeon"],
 "cancel_appointment":["cancel appointment","cancel my booking","delete appointment"],
 "faq":["timing","charges","visiting hours","how much","fees"],
 "escalate":["talk to human","contact staff","speak with staff","human help"]
}
examples, labels = [], []
for k,v in INTENTS.items():
    for p in v:
        examples.append(p); labels.append(k)
vectorizer = TfidfVectorizer(ngram_range=(1,2)).fit(examples)
X = vectorizer.transform(examples)

# --- simple moderation keywords (basic fallback) ---
SEXUAL_KEYWORDS = {"porn","sex","nude","naked","xxx","fuck","erotic","masturbate","child sexual"}

# --- utils ---
def normalize_text(t): return re.sub(r"\s+"," ", re.sub(r"[^\w\s\/:-]"," ", t.lower())).strip()
def extract_phone(text):
    m = re.search(r'(\+?\d[\d\s-]{6,}\d)', text)
    if m: return re.sub(r'\D','', m.group(1))
    return None
def extract_date_time(text):
    try:
        dt = dateparser.parse(text, fuzzy=True, dayfirst=True)
        if dt:
            date = dt.date().isoformat()
            t = dt.time().isoformat(timespec='minutes') if dt.time() else None
            return date, t
    except: pass
    m = re.search(r'(\d{1,2}[\/\-\s](?:\d{1,2}|[A-Za-z]{3,}))', text)
    if m:
        try:
            dt = dateparser.parse(m.group(1), fuzzy=True, dayfirst=True)
            return dt.date().isoformat(), None
        except: return None, None
    return None, None

def simple_keyword_moderation(text):
    t = text.lower()
    for kw in SEXUAL_KEYWORDS:
        if kw in t: return True
    return False

def predict_intent(text, threshold=0.45):
    v = vectorizer.transform([text])
    sims = cosine_similarity(v, X).flatten()
    best_idx = sims.argmax(); best_score = sims[best_idx]; cand = labels[best_idx]
    best_fuzz = max((fuzz.token_set_ratio(normalize_text(text), normalize_text(ex)) for ex in INTENTS[cand]), default=0)
    if best_score>=threshold or best_fuzz>=65: return cand, float(best_score), int(best_fuzz)
    global_best = ("unknown",0)
    for it,exs in INTENTS.items():
        for ex in exs:
            s = fuzz.token_set_ratio(normalize_text(text), normalize_text(ex))
            if s>global_best[1]: global_best=(it,s)
    if global_best[1]>=60: return global_best[0], 0.0, int(global_best[1])
    return "unknown", float(best_score), int(best_fuzz)

def book_appointment_db(name, contact, doctor_id, date, time_):
    d = DOCTOR_BY_ID.get(doctor_id)
    doc_name = d["name"] if d else None
    specialty = d["specialty"] if d else None
    gender = d["gender"] if d else None
    created = datetime.utcnow().isoformat()
    c.execute("INSERT INTO appointments(name,contact,doctor_id,doctor_name,specialty,gender,date,time,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
              (name, contact, doctor_id, doc_name, specialty, gender, date or "", time_ or "", created))
    conn.commit()
    return c.lastrowid

def log_interaction(msg, resp, intent='unknown', moderated=0):
    c.execute("INSERT INTO logs(message,response,intent,moderated,ts) VALUES (?,?,?,?,?)",
              (msg, resp, intent, moderated, datetime.utcnow().isoformat()))
    conn.commit()

# --- routes ---
@app.route("/")
def index(): return render_template("index.html")

@app.route("/doctors")
def api_doctors():
    out=[]
    for d in DOCTORS:
        dd = dict(d); dd["logo_url"]=f"/static/logos/{d['logo']}"; out.append(dd)
    return jsonify(out)

@app.route("/appointments")
def api_appointments():
    c.execute("SELECT id,name,contact,doctor_name,specialty,gender,date,time,created_at FROM appointments ORDER BY created_at DESC")
    rows=c.fetchall(); cols=["id","name","contact","doctor_name","specialty","gender","date","time","created_at"]
    return jsonify([dict(zip(cols,r)) for r in rows])

@app.route("/appointments/export")
def export_appointments():
    c.execute("SELECT id,name,contact,doctor_name,specialty,gender,date,time,created_at FROM appointments ORDER BY created_at DESC")
    rows=c.fetchall()
    si=io.StringIO(); cw=csv.writer(si); cw.writerow(["id","name","contact","doctor_name","specialty","gender","date","time","created_at"]); cw.writerows(rows)
    out=io.BytesIO(); out.write(si.getvalue().encode("utf-8")); out.seek(0)
    return send_file(out, mimetype="text/csv", as_attachment=True, download_name="appointments.csv")

@app.route("/chat", methods=["POST"])
def chat():
    data=request.json or {}; text=(data.get("message","") or "").strip(); user_name=(data.get("name") or "Anonymous").strip()
    ip = request.remote_addr or "unknown"
    # basic moderation
    if USE_OPENAI:
        try:
            mod = openai.Moderation.create(input=text)
            flagged = mod["results"][0].get("flagged", False)
            if flagged:
                resp="I understand your question, but I can't assist with that content."
                log_interaction(text, resp, intent='moderation', moderated=1); return jsonify({"response":resp})
        except Exception:
            if simple_keyword_moderation(text):
                resp="I understand your question, but I can't assist with that content."
                log_interaction(text, resp, intent='moderation', moderated=1); return jsonify({"response":resp})
    else:
        if simple_keyword_moderation(text):
            resp="I understand your question, but I can't assist with that content."
            log_interaction(text, resp, intent='moderation', moderated=1); return jsonify({"response":resp})

    intent, sim, fuzzscore = predict_intent(text)
    # OpenAI answer for unknown if available (optional)
    if USE_OPENAI and intent=="unknown":
        try:
            sys_prompt = ("You are a hospital assistant. Be helpful, concise. Refuse adult or illegal requests with the phrase: "
                          "\"I understand your question, but I can't assist with that content.\". For medical advice, add 'I am not a doctor'.")
            res = openai.ChatCompletion.create(model="gpt-4o", messages=[{"role":"system","content":sys_prompt},{"role":"user","content":text}], max_tokens=300, temperature=0.2)
            out = res["choices"][0]["message"]["content"].strip()
            log_interaction(text,out,intent='openai_fallback',moderated=0); return jsonify({"response":out})
        except Exception:
            pass

    # Local rule flows
    if intent=="book_appointment":
        found=None
        for d in DOCTORS:
            if d["specialty"].lower() in text.lower() or d["name"].split()[-1].lower() in text.lower():
                found=d; break
        date,time_ = extract_date_time(text); phone = extract_phone(text)
        missing=[]
        if not found: missing.append("doctor/specialty")
        if not date: missing.append("date")
        if not time_: missing.append("time")
        if not phone: missing.append("contact number")
        if missing:
            resp = "To book I need: " + ", ".join(missing) + ". Example: 'Book cardiology with Dr. X on 21 Nov 10:00, my number 98xxxx'"
            log_interaction(text,resp,'book_ask',0); return jsonify({"response":resp})
        appt_id = book_appointment_db(user_name or "Anonymous", phone, found["id"], date, time_)
        resp = f"✅ Appointment booked (id {appt_id}) with {found['name']} ({found['specialty']}) on {date} at {time_}."
        log_interaction(text,resp,'book_appointment',0); return jsonify({"response":resp})

    if intent=="search_doctor":
        found=[d for d in DOCTORS if d["specialty"].lower() in text.lower() or d["name"].split()[-1].lower() in text.lower()]
        if not found:
            resp = "Available doctors:\n" + "\n".join([f'{d["id"]}. {d["name"]} ({d["specialty"]}) [{d["gender"]}]' for d in DOCTORS])
            log_interaction(text,resp,'list_doctors',0); return jsonify({"response":resp})
        resp = "Found:\n" + "\n".join([f'{d["id"]}. {d["name"]} - slots: {", ".join(d["slots"])}' for d in found])
        log_interaction(text,resp,'search_doctor',0); return jsonify({"response":resp})

    if intent=="symptom_check":
        t=text.lower()
        if any(x in t for x in ["chest pain","difficulty breathing","loss of consciousness","severe bleeding"]):
            resp="This sounds potentially serious. Please call emergency or visit ER immediately."
        elif any(x in t for x in ["fever","bukhar","cough","sore throat"]):
            resp="For mild fever/cough: rest, fluids, paracetamol. If fever >38.5°C or severe symptoms, book appointment. I am not a doctor."
        else:
            resp="Describe symptom (duration, severity). I can provide general advice but I am not a substitute for a clinician."
        log_interaction(text,resp,'symptom_check',0); return jsonify({"response":resp})

    if intent=="cancel_appointment":
        date,_ = extract_date_time(text)
        if date:
            c.execute("DELETE FROM appointments WHERE name=? AND date=?", (user_name, date)); conn.commit()
            resp = f"If matching appointment existed, it's removed for {date}."
        else:
            resp = "Please provide appointment date to cancel. Example: 'Cancel my appointment on 21 Nov'"
        log_interaction(text,resp,'cancel_appointment',0); return jsonify({"response":resp})

    if intent=="faq":
        t=text.lower()
        if "tim" in t: resp="Hospital timing: Mon-Sat 08:00 - 20:00. Emergency 24x7."
        elif "xray" in t or "x-ray" in t: resp="X-ray charges from approx ₹500. Contact billing for exact charges."
        else: resp="For common info: Hospital timing: Mon-Sat 08:00 - 20:00. Emergency 24x7."
        log_interaction(text,resp,'faq',0); return jsonify({"response":resp})

    if intent=="escalate":
        resp="Connecting to human staff. Please call +91-12345-67890 or reply 'contact' to receive details."
        log_interaction(text,resp,'escalate',0); return jsonify({"response":resp})

    # final fallback
    fallback = ("Sorry I didn't understand fully. Ask me to: book appointment, check symptoms, or 'show doctors'.")
    log_interaction(text,fallback,'fallback',0); return jsonify({"response":fallback})

@app.route("/static/logos/<path:filename>")
def logo_files(filename):
    p=os.path.join(app.root_path,"static","logos",filename)
    if os.path.isfile(p): return send_file(p)
    abort(404)

if __name__=="__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
