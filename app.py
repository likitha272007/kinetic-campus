from flask import (
    Flask, render_template, request, session,
    redirect, url_for, jsonify, send_from_directory
)
import mysql.connector
import os
import time

# ── AI Engine (GPU/CPU auto-detection) ────────────────────────────────────────
try:
    from ai_engine import (
        semantic_search, gpu_semantic_search,
        enhance_banner, gpu_enhance_image,
        get_device_status,
        cpu_compute_analytics,
        cpu_summarize_text,
        cpu_similarity_matrix,
        cpu_detect_conflicts,
        cpu_trending_score,
        gpu_batch_embed,
        gpu_recommend,
    )
    AI_ENGINE_AVAILABLE = True
except Exception as e:
    AI_ENGINE_AVAILABLE = False
    print(f"[app] AI engine not loaded: {e}")
    def semantic_search(q, evs, top_k=10):   return [(ev, 1.0) for ev in evs]
    def gpu_semantic_search(q, evs, top_k=10): return [(ev, 1.0) for ev in evs]
    def enhance_banner(p):                   return {"success": False}
    def gpu_enhance_image(p):                return {"success": False}
    def get_device_status():                 return {"device_info": "AI engine not installed", "cuda": False, "torch": False}
    def cpu_compute_analytics(evs):          return {}
    def cpu_summarize_text(t, n=2):          return t
    def cpu_similarity_matrix(evs):          return []
    def cpu_detect_conflicts(evs):           return []
    def cpu_trending_score(evs):             return evs
    def gpu_batch_embed(texts):              return None
    def gpu_recommend(v, evs, top_k=3):      return evs[:top_k]

# ─────────────────────────────────────────────
#  App Bootstrap
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "kinetic_campus_secret_key_2026"

# ─────────────────────────────────────────────
#  DB Config — mirror Java credentials exactly
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "root",
    "database": "kinetic_db"
}

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    """Open a fresh connection for each request (mirrors Java per-request JDBC)."""
    return mysql.connector.connect(**DB_CONFIG)


# ─────────────────────────────────────────────
#  Serve uploaded banner images
# ─────────────────────────────────────────────
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ══════════════════════════════════════════════
#  / — Index  (mirrors Index.jsp)
# ══════════════════════════════════════════════
@app.route("/")
def index():
    role      = session.get("role")
    user_name = session.get("userName")
    is_logged_in = user_name is not None

    trending = []
    try:
        con = get_db()
        cur = con.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id, title, event_date, location, semester, purpose,
                   banner_image, capacity,
                   DATEDIFF(event_date, CURDATE()) AS days_away
            FROM   events
            WHERE  event_date >= CURDATE()
            ORDER  BY event_date ASC
            LIMIT  3
            """
        )
        trending = cur.fetchall()
        cur.close()
        con.close()
    except Exception as e:
        print(f"[index] DB error: {e}")

    return render_template(
        "index.html",
        role=role,
        user_name=user_name,
        is_logged_in=is_logged_in,
        trending=trending,
    )


# ══════════════════════════════════════════════
#  /login  — GET → show form  |  POST → auth
#  (mirrors LoginServlet + Register.jsp login mode)
# ══════════════════════════════════════════════
@app.route("/login", methods=["POST"])
def login():
    email    = request.form.get("email", "")
    password = request.form.get("password", "")

    try:
        con = get_db()
        cur = con.cursor(dictionary=True)
        cur.execute(
            "SELECT id, full_name, role FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cur.fetchone()
        cur.close()
        con.close()

        if user:
            session["userId"]   = user["id"]
            session["userName"] = user["full_name"]
            session["role"]     = user["role"]
            return redirect(url_for("index"))
        else:
            return redirect(url_for("register") + "?error=invalid")
    except Exception as e:
        print(f"[login] Error: {e}")
        return redirect(url_for("register") + "?error=invalid")


# ══════════════════════════════════════════════
#  /register  — GET → auth page  |  POST → create user
#  (mirrors RegisterServlet + Register.jsp)
# ══════════════════════════════════════════════
@app.route("/register", methods=["GET", "POST"])
def register():
    # If already logged in, skip to home
    if session.get("userName"):
        return redirect(url_for("index"))

    if request.method == "POST":
        name     = request.form.get("fullName", "")
        email    = request.form.get("email", "")
        password = request.form.get("password", "")
        role     = request.form.get("role", "user")

        try:
            con = get_db()
            cur = con.cursor()
            cur.execute(
                "INSERT INTO users (full_name, email, password, role) VALUES (%s,%s,%s,%s)",
                (name, email, password, role)
            )
            con.commit()
            new_id = cur.lastrowid
            cur.close()
            con.close()

            session["userId"]   = new_id
            session["userName"] = name
            session["role"]     = role
            return redirect(url_for("dashboard"))

        except mysql.connector.IntegrityError:
            return redirect(url_for("register") + "?error=exists")
        except Exception as e:
            print(f"[register] Error: {e}")
            return redirect(url_for("register") + "?error=failed")

    # GET — render the auth page
    error = request.args.get("error")
    mode  = request.args.get("mode", "register")
    return render_template("register.html", error=error, mode=mode)


# ══════════════════════════════════════════════
#  /dashboard  — (mirrors Dashboard.jsp — post-register success)
# ══════════════════════════════════════════════
@app.route("/dashboard")
def dashboard():
    user_name  = session.get("userName", "Guest")
    user_email = session.get("userEmail", "Not Provided")
    role       = session.get("role", "user")
    return render_template("dashboard.html",
                           user_name=user_name,
                           user_email=user_email,
                           role=role)


# ══════════════════════════════════════════════
#  /logout  (mirrors LogoutServlet)
# ══════════════════════════════════════════════
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("register"))


# ══════════════════════════════════════════════
#  /create-event  (mirrors CreateEvent.jsp + CreateEventServlet)
# ══════════════════════════════════════════════
@app.route("/create-event", methods=["GET", "POST"])
def create_event():
    role      = session.get("role")
    user_name = session.get("userName")

    if request.method == "POST":
        title    = request.form.get("eventTitle", "")
        date     = request.form.get("eventDate", "")
        semester = request.form.get("semester", "all")
        purpose  = request.form.get("purpose", "")
        outcome  = request.form.get("outcome", "")
        location = request.form.get("location", "")
        capacity_str = request.form.get("capacity", "")
        capacity = 0
        try:
            capacity = int(capacity_str) if capacity_str.strip() else 0
        except ValueError:
            capacity = 0

        # ── Image upload — mirrors Java MultipartConfig logic ──
        db_image_name = None
        banner_file = request.files.get("bannerImage")
        if banner_file and banner_file.filename:
            safe_name = "".join(
                c if c.isalnum() or c in (".", "-") else "_"
                for c in banner_file.filename
            )
            db_image_name = f"{int(time.time() * 1000)}_{safe_name}"
            banner_file.save(os.path.join(UPLOAD_FOLDER, db_image_name))
            # ── GPU/CPU Auto-enhance the uploaded banner ──
            enhance_banner(os.path.join(UPLOAD_FOLDER, db_image_name))

        try:
            con = get_db()
            cur = con.cursor()
            cur.execute(
                """
                INSERT INTO events
                    (title, event_date, semester, purpose, outcome,
                     location, capacity, banner_image)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (title, date, semester, purpose, outcome,
                 location, capacity, db_image_name)
            )
            con.commit()
            new_event_id = cur.lastrowid

            # ── Notification — mirrors Java's notification insert ──
            cur.execute(
                "INSERT INTO notifications (event_id, message) VALUES (%s,%s)",
                (new_event_id, f"New Event Archive Released: {title}")
            )
            con.commit()
            cur.close()
            con.close()
            return redirect(url_for("success"))
        except Exception as e:
            print(f"[create_event] Error: {e}")
            return f"Archive Error: {e}", 500

    return render_template("create_event.html",
                           role=role, user_name=user_name)


# ══════════════════════════════════════════════
#  /success  (mirrors Success.jsp)
# ══════════════════════════════════════════════
@app.route("/success")
def success():
    return render_template("success.html")


# ══════════════════════════════════════════════
#  /explore  (mirrors explore.jsp)
# ══════════════════════════════════════════════
@app.route("/explore")
def explore():
    role      = session.get("role")
    user_name = session.get("userName")
    is_logged_in = user_name is not None

    events    = []
    db_error  = ""
    try:
        con = get_db()
        cur = con.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM events ORDER BY event_date ASC, id DESC"
        )
        rows = cur.fetchall()
        cur.close()
        con.close()

        for ev in rows:
            date_val = ev.get("event_date")
            image_url = "https://images.unsplash.com/photo-1540575467063-178a50c2df87?q=80&w=800"
            banner = ev.get("banner_image")
            if banner and banner.strip():
                image_url = f"/uploads/{banner}"
            events.append({
                "id":       str(ev.get("id", "")),
                "title":    ev.get("title") or "Untitled Event",
                "purpose":  ev.get("purpose") or "",
                "location": ev.get("location") or "TBA",
                "date":     str(date_val) if date_val else "",
                "semester": str(ev.get("semester") or ""),
                "category": str(ev.get("category") or ""),
                "image":    image_url,
            })
    except Exception as e:
        db_error = str(e).replace("\\", "\\\\").replace('"', '\\"')

    return render_template(
        "explore.html",
        role=role,
        user_name=user_name,
        is_logged_in=is_logged_in,
        events=events,
        db_error=db_error,
    )


# ══════════════════════════════════════════════
#  /my-events  (mirrors MyEvents.jsp)
# ══════════════════════════════════════════════
@app.route("/my-events")
def my_events():
    user_name = session.get("userName")
    role      = session.get("role")

    if not user_name:
        return redirect(url_for("register"))

    registrations = []
    error_msg     = None
    flash         = request.args.get("msg")

    try:
        con = get_db()
        cur = con.cursor(dictionary=True)
        cur.execute(
            """
            SELECT er.id AS reg_id, er.section, er.university_id,
                   er.registration_date,
                   e.id AS event_id, e.title, e.event_date,
                   e.location, e.semester
            FROM   event_registrations er
            JOIN   events e ON er.event_id = e.id
            WHERE  er.student_name = %s
            ORDER  BY er.registration_date DESC
            """,
            (user_name,)
        )
        registrations = cur.fetchall()
        cur.close()
        con.close()
    except Exception as e:
        error_msg = str(e)
        print(f"[my_events] Error: {e}")

    return render_template(
        "my_events.html",
        user_name=user_name,
        role=role,
        registrations=registrations,
        error_msg=error_msg,
        flash=flash,
    )


# ══════════════════════════════════════════════
#  /event-details/<id>  (mirrors EventDetails.jsp)
# ══════════════════════════════════════════════
@app.route("/event-details")
def event_details():
    event_id = request.args.get("id")
    if not event_id or not event_id.strip():
        return redirect(url_for("explore"))

    user_name = session.get("userName")
    role      = session.get("role")
    event     = None
    error     = None

    try:
        eid = int(event_id.strip())
        con = get_db()
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM events WHERE id=%s", (eid,))
        event = cur.fetchone()
        cur.close()
        con.close()
    except ValueError:
        error = "invalid_id"
    except Exception as e:
        error = str(e)
        print(f"[event_details] Error: {e}")

    return render_template(
        "event_details.html",
        event=event,
        event_id=event_id,
        user_name=user_name,
        role=role,
        error=error,
    )


# ══════════════════════════════════════════════
#  /register-event  POST  (mirrors RegisterEventServlet)
# ══════════════════════════════════════════════
@app.route("/register-event", methods=["POST"])
def register_event():
    event_id     = request.form.get("eventId", "")
    student_name = request.form.get("studentName", "")
    semester     = request.form.get("semester", "")
    department   = request.form.get("department", "")
    section      = request.form.get("section", "")
    university_id = request.form.get("universityId", "")

    try:
        con = get_db()
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO event_registrations
                (event_id, student_name, semester, department,
                 section, university_id, registration_date)
            VALUES (%s,%s,%s,%s,%s,%s,NOW())
            """,
            (int(event_id), student_name, semester,
             department, section, university_id)
        )
        con.commit()

        # Update join_count — mirrors Java's updateCount PreparedStatement
        cur.execute(
            "UPDATE events SET join_count = COALESCE(join_count,0)+1 WHERE id=%s",
            (int(event_id),)
        )
        con.commit()
        cur.close()
        con.close()
        return redirect(url_for("explore"))
    except Exception as e:
        print(f"[register_event] Error: {e}")
        return f"Registration Error: {e}", 500


# ══════════════════════════════════════════════
#  /deregister  POST  (mirrors DeregisterServlet)
# ══════════════════════════════════════════════
@app.route("/deregister", methods=["POST"])
def deregister():
    user_name  = session.get("userName")
    reg_id_str = request.form.get("regId", "").strip()

    if not user_name or not reg_id_str:
        return redirect(url_for("my_events") + "?msg=error")

    try:
        reg_id = int(reg_id_str)
        con = get_db()
        cur = con.cursor()
        cur.execute(
            "DELETE FROM event_registrations WHERE id=%s AND student_name=%s",
            (reg_id, user_name)
        )
        con.commit()
        rows = cur.rowcount
        print(f"[deregister] Deleted {rows} row(s) for regId={reg_id}")
        cur.close()
        con.close()
        return redirect(url_for("my_events") + "?msg=deregistered")
    except ValueError:
        return redirect(url_for("my_events") + "?msg=error")
    except Exception as e:
        print(f"[deregister] Error: {e}")
        return redirect(url_for("my_events") + "?msg=error")


# ══════════════════════════════════════════════
#  /admin  (mirrors AdminDashboard.jsp)
# ══════════════════════════════════════════════
@app.route("/admin")
def admin_dashboard():
    role      = session.get("role")
    user_name = session.get("userName")

    if role != "admin":
        return redirect(url_for("index"))

    total_events        = 0
    total_registrations = 0
    total_students      = 0
    event_rows          = []
    error_msg           = None

    try:
        con = get_db()
        cur = con.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) AS cnt FROM events")
        total_events = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(*) AS cnt FROM event_registrations")
        total_registrations = cur.fetchone()["cnt"]

        cur.execute("SELECT COUNT(DISTINCT student_name) AS cnt FROM event_registrations")
        total_students = cur.fetchone()["cnt"]

        cur.execute(
            """
            SELECT e.id, e.title, e.event_date, e.location, e.semester,
                   COALESCE(e.capacity, 0) AS capacity,
                   COUNT(er.id) AS reg_count
            FROM   events e
            LEFT   JOIN event_registrations er ON e.id = er.event_id
            GROUP  BY e.id, e.title, e.event_date, e.location, e.semester, e.capacity
            ORDER  BY e.id DESC
            """
        )
        raw_events = cur.fetchall()

        for ev in raw_events:
            cap = ev["capacity"] or 0
            reg = ev["reg_count"] or 0
            fill_pct = min(100, int((reg * 100.0) / cap)) if cap > 0 else 0
            bar_color = "bg-red-500" if fill_pct >= 90 else ("bg-yellow-400" if fill_pct >= 60 else "bg-green-400")
            badge_color = ("bg-red-500/20 text-red-400" if fill_pct >= 90
                           else ("bg-yellow-400/20 text-yellow-400" if fill_pct >= 60
                                 else "bg-green-400/20 text-green-400"))

            # Fetch students for this event
            cur.execute(
                """
                SELECT student_name, semester, department, section,
                       university_id, registration_date
                FROM   event_registrations
                WHERE  event_id = %s
                ORDER  BY registration_date ASC
                """,
                (ev["id"],)
            )
            # Fetch student feedback for this event
            cur.execute(
                """
                SELECT student_name, rating, comments, created_at
                FROM   feedback
                WHERE  event_id = %s
                ORDER  BY created_at DESC
                """,
                (ev["id"],)
            )
            event_feedback = cur.fetchall()
            avg_rating = round(sum(f["rating"] for f in event_feedback) / len(event_feedback), 1) if event_feedback else 0.0

            event_rows.append({
                **ev,
                "fill_pct":       fill_pct,
                "bar_color":      bar_color,
                "badge_color":    badge_color,
                "students":       students,
                "feedback":       event_feedback,
                "avg_rating":     avg_rating,
                "feedback_count": len(event_feedback)
            })

        # Fetch all feedback across all events for the Admin Portal
        cur.execute("""
            SELECT f.id, f.student_name, f.rating, f.comments, f.created_at, e.title AS event_title
            FROM   feedback f
            JOIN   events e ON f.event_id = e.id
            ORDER  BY f.created_at DESC
        """)
        all_feedback = cur.fetchall()

        cur.close()
        con.close()
    except Exception as e:
        error_msg = str(e)
        all_feedback = []
        print(f"[admin] Error: {e}")

    return render_template(
        "admin_dashboard.html",
        user_name=user_name,
        total_events=total_events,
        total_registrations=total_registrations,
        total_students=total_students,
        event_rows=event_rows,
        all_feedback=all_feedback,
        error_msg=error_msg,
    )


# ══════════════════════════════════════════════
#  /check-notifications  (mirrors CheckNotificationServlet)
# ══════════════════════════════════════════════
@app.route("/check-notifications")
def check_notifications():
    try:
        con = get_db()
        cur = con.cursor(dictionary=True)
        cur.execute(
            "SELECT COUNT(*) AS total FROM notifications WHERE is_read = FALSE"
        )
        row = cur.fetchone()
        cur.close()
        con.close()
        count = row["total"] if row else 0
        if count > 0:
            return jsonify({"new_event": True, "count": count})
        return jsonify({"new_event": False, "count": 0})
    except Exception:
        return jsonify({"new_event": False, "count": 0})


# ══════════════════════════════════════════════
#  /get-previous-events  (mirrors GetPreviousEventsServlet)
# ══════════════════════════════════════════════
@app.route("/get-previous-events")
def get_previous_events():
    results = []
    try:
        con = get_db()
        cur = con.cursor(dictionary=True)
        cur.execute(
            "SELECT id, title, event_date FROM events ORDER BY id DESC LIMIT 5"
        )
        rows = cur.fetchall()
        cur.close()
        con.close()

        for r in rows:
            date_val = r.get("event_date")
            date_str = date_val.strftime("%d %b %Y") if date_val else "Date TBA"
            results.append({
                "id":    r["id"],
                "title": r.get("title") or "Untitled Event",
                "date":  date_str,
            })
    except Exception:
        pass
    return jsonify(results)


# ══════════════════════════════════════════════
#  /api/events-for-chat  (Rich data for AI Chatbot)
# ══════════════════════════════════════════════
@app.route("/api/events-for-chat")
def events_for_chat():
    results = []
    try:
        con = get_db()
        cur = con.cursor(dictionary=True)
        cur.execute(
            """
            SELECT e.id, e.title, e.event_date, e.location, e.semester,
                   e.purpose, e.outcome, e.capacity,
                   COUNT(er.id) AS registered
            FROM   events e
            LEFT   JOIN event_registrations er ON e.id = er.event_id
            GROUP  BY e.id
            ORDER  BY e.event_date ASC
            """
        )
        rows = cur.fetchall()
        cur.close()
        con.close()
        for r in rows:
            date_val = r.get("event_date")
            results.append({
                "id":         r["id"],
                "title":      r.get("title") or "Untitled",
                "date":       str(date_val) if date_val else "",
                "location":   r.get("location") or "TBA",
                "semester":   str(r.get("semester") or "All"),
                "purpose":    r.get("purpose") or "",
                "outcome":    r.get("outcome") or "",
                "capacity":   r.get("capacity") or 0,
                "registered": r.get("registered") or 0,
            })
    except Exception as e:
        print(f"[events_for_chat] Error: {e}")
    return jsonify(results)


# ══════════════════════════════════════════════════════════════════
#  CPU ROUTES
# ══════════════════════════════════════════════════════════════════

def _fetch_events_with_reg():
    """Helper: fetch all events with registration counts."""
    con = get_db()
    cur = con.cursor(dictionary=True)
    cur.execute("""
        SELECT e.id, e.title, e.event_date AS date, e.location, e.semester,
               e.purpose, e.outcome, e.capacity,
               COUNT(er.id) AS registered
        FROM   events e
        LEFT   JOIN event_registrations er ON e.id = er.event_id
        GROUP  BY e.id ORDER BY e.event_date ASC
    """)
    rows = cur.fetchall()
    cur.close(); con.close()
    return [dict(r) for r in rows]


@app.route("/api/cpu/analytics")
def api_cpu_analytics():
    """CPU — numpy vectorized event statistics + department breakdown."""
    try:
        events = _fetch_events_with_reg()

        # Fetch department stats
        dept_stats = {}
        try:
            con = get_db()
            cur = con.cursor(dictionary=True)
            cur.execute("""
                SELECT department, COUNT(*) AS count
                FROM   event_registrations
                WHERE  department IS NOT NULL AND TRIM(department) != ''
                GROUP  BY department
                ORDER  BY count DESC
            """)
            d_rows = cur.fetchall()
            cur.close(); con.close()
            dept_stats = {r["department"]: r["count"] for r in d_rows}
        except Exception:
            pass

        if events:
            events[0]["_dept_stats"] = dept_stats

        result = cpu_compute_analytics(events)
        return jsonify({"ok": True, "data": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/cpu/summarize")
def api_cpu_summarize():
    """CPU — extractive text summarizer."""
    text = request.args.get("text", "").strip()
    n    = int(request.args.get("sentences", 2))
    if not text:
        return jsonify({"ok": False, "error": "No text provided"}), 400
    summary = cpu_summarize_text(text, max_sentences=n)
    return jsonify({"ok": True, "summary": summary, "engine": "CPU Extractive"})


@app.route("/api/cpu/similarity")
def api_cpu_similarity():
    """CPU — TF-IDF cosine similarity matrix between all events."""
    try:
        events = _fetch_events_with_reg()
        pairs  = cpu_similarity_matrix(events)
        return jsonify({"ok": True, "pairs": pairs, "engine": "CPU TF-IDF + NumPy"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/cpu/conflicts")
def api_cpu_conflicts():
    """CPU — detect events with date/location conflicts."""
    try:
        events    = _fetch_events_with_reg()
        conflicts = cpu_detect_conflicts(events)
        return jsonify({"ok": True, "conflicts": conflicts, "count": len(conflicts)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/cpu/trending")
def api_cpu_trending():
    """CPU — score and rank events by trending formula."""
    try:
        events = _fetch_events_with_reg()
        ranked = cpu_trending_score(events)
        # Return only safe fields
        out = [{"id": e.get("id"), "title": e.get("title"),
                "trending_score": e.get("trending_score"),
                "registered": e.get("registered"),
                "date": str(e.get("date") or "")} for e in ranked]
        return jsonify({"ok": True, "ranked": out, "engine": "CPU Weighted Score"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════
#  GPU ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/api/gpu/enhance-image", methods=["POST"])
def api_gpu_enhance():
    """GPU — enhance an already-uploaded banner image."""
    filename = request.json.get("filename", "") if request.json else ""
    if not filename:
        return jsonify({"ok": False, "error": "No filename"}), 400
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
        return jsonify({"ok": False, "error": "File not found"}), 404
    result = gpu_enhance_image(path)
    return jsonify({"ok": result.get("success", False), "detail": result})


@app.route("/api/gpu/recommend")
def api_gpu_recommend():
    """GPU — personalised event recommendations via tensor similarity."""
    viewed_raw = request.args.get("viewed", "")
    viewed_ids = [v.strip() for v in viewed_raw.split(",") if v.strip()]
    try:
        events = _fetch_events_with_reg()
        picks  = gpu_recommend(viewed_ids, events, top_k=3)
        out    = [{"id": e.get("id"), "title": e.get("title"),
                   "date": str(e.get("date") or ""),
                   "location": e.get("location")} for e in picks]
        return jsonify({"ok": True, "recommendations": out,
                        "engine": "GPU Tensor Similarity" if viewed_ids else "CPU Popularity"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/gpu/embed")
def api_gpu_embed():
    """GPU — encode a text into a sentence embedding vector."""
    text = request.args.get("text", "").strip()
    if not text:
        return jsonify({"ok": False, "error": "No text"}), 400
    embeddings = gpu_batch_embed([text])
    if embeddings is None:
        return jsonify({"ok": False, "error": "Model not available (install sentence-transformers)"}), 503
    vec = embeddings[0].tolist()
    return jsonify({"ok": True, "text": text, "dims": len(vec),
                    "vector_preview": vec[:8],
                    "engine": "GPU sentence-transformers" if str(embeddings) else "CPU"})


# ── Existing semantic search + device status ───────────────────────────────────
@app.route("/api/semantic-search")
def api_semantic_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": [], "device": get_device_status()})
    try:
        events = _fetch_events_with_reg()
        ranked = gpu_semantic_search(query, events, top_k=10)
        return jsonify({
            "results": [{"event": ev, "score": round(sc, 4)} for ev, sc in ranked],
            "device":  get_device_status(),
            "query":   query,
        })
    except Exception as e:
        return jsonify({"error": str(e), "results": []}), 500


@app.route("/delete-event/<int:event_id>", methods=["POST", "GET"])
def delete_event(event_id):
    """Delete an event and all associated registrations (Admin only)."""
    if session.get("role") != "admin":
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    try:
        con = get_db()
        cur = con.cursor()
        # Delete registrations first
        cur.execute("DELETE FROM event_registrations WHERE event_id = %s", (event_id,))
        # Delete event
        cur.execute("DELETE FROM events WHERE id = %s", (event_id,))
        con.commit()
        cur.close(); con.close()
        return redirect(url_for("admin_dashboard"))
    except Exception as e:
        return f"Error deleting event: {e}", 500


@app.route("/api/submit-feedback", methods=["POST"])
def api_submit_feedback():
    """Submit student event rating & review."""
    user_name = session.get("userName", "Anonymous Student")
    event_id = request.form.get("event_id") or (request.json.get("event_id") if request.is_json else None)
    rating   = request.form.get("rating")   or (request.json.get("rating") if request.is_json else None)
    comments = request.form.get("comments") or (request.json.get("comments") if request.is_json else "")

    if not event_id or not rating:
        return jsonify({"ok": False, "error": "Missing event_id or rating"}), 400

    try:
        con = get_db()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO feedback (event_id, student_name, rating, comments)
            VALUES (%s, %s, %s, %s)
        """, (event_id, user_name, rating, comments))
        con.commit()
        cur.close(); con.close()
        return jsonify({"ok": True, "message": "Thank you for your feedback!"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/device-status")
def api_device_status():
    return jsonify(get_device_status())


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
