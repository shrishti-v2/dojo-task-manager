from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime, date
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MongoDB Config
app.config["MONGO_URI"] = "mongodb://localhost:27017/dojo_db"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

@app.context_processor
def inject_notifications():
    notifications = []
    if "user" in session:   # ✅ FIX: use "user" instead of "user_id"
        user_id = ObjectId(session["user"])
        categories = list(mongo.db.categories.find({"user_id": user_id}))

        for cat in categories:
            for task in cat.get("tasks", []):
                due_raw = task.get("due_date")
                if not due_raw:
                    continue

                due = None
                # Case 1: Already a datetime (BSON Date)
                if isinstance(due_raw, datetime):
                    due = due_raw.date()
                # Case 2: String stored
                elif isinstance(due_raw, str):
                    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
                        try:
                            due = datetime.strptime(due_raw, fmt).date()
                            break
                        except ValueError:
                            continue

                if due and due <= date.today() and not task.get("done", False):
                    notifications.append({
                        "category": cat.get("name"),
                        "task": task.get("task"),
                        "due": due.strftime("%Y-%m-%d")
                    })

    print("DEBUG NOTIFICATIONS:", notifications)
    return dict(notifications=notifications)

# ---------------- AUTH ROUTES ---------------- #
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = mongo.db.users
        username = request.form["username"].strip()
        password_raw = request.form["password"]

        if users.find_one({"username": username}):
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))

        password = bcrypt.generate_password_hash(password_raw).decode("utf-8")
        user_id = users.insert_one({"username": username, "password": password}).inserted_id

        categories = ["Personal", "Work", "Health"]
        for cat in categories:
            mongo.db.categories.insert_one({"user_id": user_id, "name": cat, "tasks": []})

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = mongo.db.users
        username = request.form["username"].strip()
        password = request.form["password"]

        user = users.find_one({"username": username})
        if user and bcrypt.check_password_hash(user["password"], password):
            session["user"] = str(user["_id"])
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("username", None)
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))

# ---------------- DASHBOARD ---------------- #
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    user_id = ObjectId(session["user"])

    sort_by = request.args.get("sort", "created_at")
    filter_priority = request.args.get("priority")

    categories = list(mongo.db.categories.find({"user_id": user_id}))

    for cat in categories:
        tasks = cat.get("tasks", [])
        # Filtering
        if filter_priority:
            tasks = [t for t in tasks if t.get("priority") == filter_priority]
        # Sorting
        if sort_by == "priority":
            priority_order = {"High": 1, "Medium": 2, "Low": 3}
            tasks.sort(key=lambda t: priority_order.get(t.get("priority", "Medium"), 99))
        elif sort_by == "due_date":
            tasks.sort(key=lambda t: (t.get("due_date") or "9999-12-31"))
        else:  # default created_at
            tasks.sort(key=lambda t: t.get("created_at", datetime.utcnow()))

        cat["tasks"] = tasks

    return render_template("dashboard.html", categories=categories, sort_by=sort_by, filter_priority=filter_priority)

# ---------------- CATEGORY CRUD ---------------- #
@app.route("/add_category", methods=["POST"])
def add_category():
    if "user" not in session:
        return redirect(url_for("login"))
    name = request.form.get("name", "").strip()
    if name:
        mongo.db.categories.insert_one({"user_id": ObjectId(session["user"]), "name": name, "tasks": []})
    return redirect(url_for("dashboard"))

@app.route("/edit_category/<category_id>", methods=["POST"])
def edit_category(category_id):
    if "user" not in session:
        return redirect(url_for("login"))
    name = request.form.get("name", "").strip()
    if name:
        mongo.db.categories.update_one({"_id": ObjectId(category_id)}, {"$set": {"name": name}})
    return redirect(url_for("dashboard"))

@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    if "user" not in session:
        return redirect(url_for("login"))
    mongo.db.categories.delete_one({"_id": ObjectId(category_id)})
    return redirect(url_for("dashboard"))

# ---------------- TASK MANAGEMENT ---------------- #
@app.route("/add_task/<category_id>", methods=["POST"])
def add_task(category_id):
    if "user" not in session:
        return redirect(url_for("login"))
    task = request.form.get("task", "").strip()
    due_date = request.form.get("due_date")
    priority = request.form.get("priority", "Medium")
    if task:
        task_data = {
            "task": task,
            "done": False,
            "priority": priority,
            "created_at": datetime.utcnow(),
            "due_date": due_date if due_date else None
        }
        mongo.db.categories.update_one(
            {"_id": ObjectId(category_id)},
            {"$push": {"tasks": task_data}}
        )
    return redirect(url_for("dashboard"))

@app.route("/toggle_task/<category_id>/<int:task_index>")
def toggle_task(category_id, task_index):
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    if category:
        tasks = category.get("tasks", [])
        if 0 <= task_index < len(tasks):
            if not tasks[task_index].get("done", False):
                # Mark as done and record completion time
                tasks[task_index]["done"] = True
                tasks[task_index]["completed_at"] = datetime.utcnow()
            else:
                # Undo completion
                tasks[task_index]["done"] = False
                tasks[task_index].pop("completed_at", None)

            mongo.db.categories.update_one(
                {"_id": ObjectId(category_id)},
                {"$set": {"tasks": tasks}}
            )
    return redirect(url_for("dashboard"))

@app.route("/delete_task/<category_id>/<int:task_index>")
def delete_task(category_id, task_index):
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    if category:
        tasks = category.get("tasks", [])
        if 0 <= task_index < len(tasks):
            tasks.pop(task_index)
            mongo.db.categories.update_one({"_id": ObjectId(category_id)}, {"$set": {"tasks": tasks}})
    return redirect(url_for("dashboard"))

@app.route("/progress_analytics")
def progress_analytics():
    if "user" not in session:
        return redirect(url_for("login"))
    user_id = ObjectId(session["user"])
    categories = list(mongo.db.categories.find({"user_id": user_id}))

    completed_per_category = {}
    overdue_vs_ontime = {"Overdue": 0, "On-Time": 0}
    completed_over_time = {}

    today = datetime.utcnow().date()

    for cat in categories:
        for task in cat.get("tasks", []):
            due_date_raw = task.get("due_date")
            done = task.get("done", False)

            # Convert due_date into date object if possible
            due_date = None
            if isinstance(due_date_raw, str):
                try:
                    due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date()
                except:
                    pass
            elif isinstance(due_date_raw, datetime):
                due_date = due_date_raw.date()

            # Count completed tasks per category
            if done:
                completed_per_category[cat["name"]] = completed_per_category.get(cat["name"], 0) + 1

                # Track completion time (group by week)
                created_at = task.get("created_at")
                if isinstance(created_at, datetime):
                    week = created_at.strftime("%Y-%W")  # Year-Week format
                    completed_over_time[week] = completed_over_time.get(week, 0) + 1

                # On-time vs Overdue (for completed tasks)
                if due_date:
                    if created_at.date() > due_date:
                        overdue_vs_ontime["Overdue"] += 1
                    else:
                        overdue_vs_ontime["On-Time"] += 1
                else:
                    overdue_vs_ontime["On-Time"] += 1

            else:
                # Count overdue unfinished tasks as "Overdue"
                if due_date and due_date < today:
                    overdue_vs_ontime["Overdue"] += 1

    return render_template(
        "progress_analytics.html",
        completed_per_category=completed_per_category,
        overdue_vs_ontime=overdue_vs_ontime,
        completed_over_time=completed_over_time
    )

app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/edit_profile", methods=["POST"])
def edit_profile():
    if "user" not in session:
        return redirect(url_for("login"))

    user_id = ObjectId(session["user"])
    new_username = request.form.get("username").strip()

    update_data = {"username": new_username}

    if "photo" in request.files and request.files["photo"].filename != "":
        photo = request.files["photo"]
        filename = secure_filename(photo.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)
        update_data["photo"] = filename

    mongo.db.users.update_one({"_id": user_id}, {"$set": update_data})

    session["username"] = new_username
    if "photo" in update_data:
        session["photo"] = update_data["photo"]

    flash("Profile updated successfully!", "success")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)