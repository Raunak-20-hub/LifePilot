from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import date, datetime

app = Flask(__name__)

DATABASE = "lifepilot.db"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# --------------------------------------------------
# CREATE DATABASE
# --------------------------------------------------

def initialize_database():

    connection = get_db()

    connection.executescript("""

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT DEFAULT 'Personal',
        priority TEXT DEFAULT 'Medium',
        due_date TEXT,
        due_time TEXT,
        completed INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT DEFAULT 'Other',
        spent_on TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        progress INTEGER DEFAULT 0,
        deadline TEXT
    );

    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        emoji TEXT DEFAULT '🔥',
        streak INTEGER DEFAULT 0,
        checked_today INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        created_at TEXT NOT NULL
    );

    """)

    # Demo tasks
    if connection.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0] == 0:

        connection.executemany(
            """
            INSERT INTO tasks
            (title, category, priority, due_date, due_time)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    "Finish Python assignment",
                    "College",
                    "High",
                    str(date.today()),
                    "19:00"
                ),
                (
                    "Practice Flutter",
                    "Skills",
                    "Medium",
                    str(date.today()),
                    "21:00"
                ),
                (
                    "Plan tomorrow",
                    "Personal",
                    "Low",
                    str(date.today()),
                    "22:30"
                )
            ]
        )

    # Demo goals
    if connection.execute(
        "SELECT COUNT(*) FROM goals"
    ).fetchone()[0] == 0:

        connection.executemany(
            """
            INSERT INTO goals
            (title, description, progress, deadline)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    "Become better at Python",
                    "Build 3 useful Python projects",
                    55,
                    "2026-10-01"
                ),
                (
                    "Build a strong portfolio",
                    "Finish 4 polished projects",
                    30,
                    "2026-12-15"
                )
            ]
        )

    # Demo habits
    if connection.execute(
        "SELECT COUNT(*) FROM habits"
    ).fetchone()[0] == 0:

        connection.executemany(
            """
            INSERT INTO habits
            (title, emoji, streak)
            VALUES (?, ?, ?)
            """,
            [
                ("Study for 45 minutes", "📚", 5),
                ("Code every day", "💻", 8),
                ("Read / learn", "🧠", 3)
            ]
        )

    connection.commit()
    connection.close()


# --------------------------------------------------
# DASHBOARD STATISTICS
# --------------------------------------------------

def get_statistics():

    connection = get_db()

    total_tasks = connection.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0]

    completed_tasks = connection.execute(
        "SELECT COUNT(*) FROM tasks WHERE completed = 1"
    ).fetchone()[0]

    today_tasks = connection.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE due_date = ?
        AND completed = 0
        """,
        (str(date.today()),)
    ).fetchone()[0]

    total_spending = connection.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses"
    ).fetchone()[0]

    total_goals = connection.execute(
        "SELECT COUNT(*) FROM goals"
    ).fetchone()[0]

    total_habits = connection.execute(
        "SELECT COUNT(*) FROM habits"
    ).fetchone()[0]

    connection.close()

    if total_tasks > 0:
        completion = round(
            (completed_tasks / total_tasks) * 100
        )
    else:
        completion = 0

    life_score = min(
        100,
        round(
            completion * 0.45
            + min(total_goals * 12, 30)
            + min(total_habits * 6, 20)
        )
    )

    return {
        "total": total_tasks,
        "done": completed_tasks,
        "today_tasks": today_tasks,
        "spent": round(total_spending, 2),
        "goals": total_goals,
        "habits": total_habits,
        "completion": completion,
        "life_score": life_score
    }


# --------------------------------------------------
# HOME / DASHBOARD
# --------------------------------------------------

@app.route("/")
def home():

    statistics = get_statistics()

    connection = get_db()

    tasks = connection.execute(
        """
        SELECT *
        FROM tasks
        ORDER BY completed, due_date, due_time
        LIMIT 6
        """
    ).fetchall()

    goals = connection.execute(
        """
        SELECT *
        FROM goals
        ORDER BY progress ASC
        LIMIT 3
        """
    ).fetchall()

    habits = connection.execute(
        """
        SELECT *
        FROM habits
        ORDER BY streak DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "index.html",
        stats=statistics,
        tasks=tasks,
        goals=goals,
        habits=habits
    )


# ==================================================
# TASKS
# ==================================================

@app.route("/tasks", methods=["GET", "POST"])
def tasks():

    connection = get_db()

    if request.method == "POST":

        title = request.form["title"]

        category = request.form.get(
            "category",
            "Personal"
        )

        priority = request.form.get(
            "priority",
            "Medium"
        )

        due_date = request.form.get(
            "due_date",
            ""
        )

        due_time = request.form.get(
            "due_time",
            ""
        )

        connection.execute(
            """
            INSERT INTO tasks
            (title, category, priority, due_date, due_time)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                title,
                category,
                priority,
                due_date,
                due_time
            )
        )

        connection.commit()

    task_list = connection.execute(
        """
        SELECT *
        FROM tasks
        ORDER BY completed, due_date, due_time
        """
    ).fetchall()

    connection.close()

    return render_template(
        "tasks.html",
        tasks=task_list
    )


@app.post("/tasks/<int:task_id>/toggle")
def toggle_task(task_id):

    connection = get_db()

    connection.execute(
        """
        UPDATE tasks
        SET completed =
            CASE completed
                WHEN 0 THEN 1
                ELSE 0
            END
        WHERE id = ?
        """,
        (task_id,)
    )

    connection.commit()
    connection.close()

    return redirect(
        request.referrer or url_for("tasks")
    )


@app.post("/tasks/<int:task_id>/delete")
def delete_task(task_id):

    connection = get_db()

    connection.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    connection.commit()
    connection.close()

    return redirect(
        request.referrer or url_for("tasks")
    )


# ==================================================
# MONEY
# ==================================================

@app.route("/money", methods=["GET", "POST"])
def money():

    connection = get_db()

    if request.method == "POST":

        title = request.form["title"]

        amount = float(
            request.form["amount"]
        )

        category = request.form.get(
            "category",
            "Other"
        )

        spent_on = request.form.get(
            "spent_on",
            str(date.today())
        )

        connection.execute(
            """
            INSERT INTO expenses
            (title, amount, category, spent_on)
            VALUES (?, ?, ?, ?)
            """,
            (
                title,
                amount,
                category,
                spent_on
            )
        )

        connection.commit()

    expenses = connection.execute(
        """
        SELECT *
        FROM expenses
        ORDER BY spent_on DESC, id DESC
        """
    ).fetchall()

    categories = connection.execute(
        """
        SELECT category,
               SUM(amount) AS total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        """
    ).fetchall()

    total = sum(
        expense["amount"]
        for expense in expenses
    )

    connection.close()

    return render_template(
        "money.html",
        expenses=expenses,
        categories=categories,
        total=total
    )


@app.post("/money/<int:expense_id>/delete")
def delete_expense(expense_id):

    connection = get_db()

    connection.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("money")
    )


# ==================================================
# GOALS
# ==================================================

@app.route("/goals", methods=["GET", "POST"])
def goals():

    connection = get_db()

    if request.method == "POST":

        title = request.form["title"]

        description = request.form.get(
            "description",
            ""
        )

        progress = int(
            request.form.get(
                "progress",
                0
            )
        )

        deadline = request.form.get(
            "deadline",
            ""
        )

        connection.execute(
            """
            INSERT INTO goals
            (title, description, progress, deadline)
            VALUES (?, ?, ?, ?)
            """,
            (
                title,
                description,
                progress,
                deadline
            )
        )

        connection.commit()

    goal_list = connection.execute(
        """
        SELECT *
        FROM goals
        ORDER BY deadline
        """
    ).fetchall()

    connection.close()

    return render_template(
        "goals.html",
        goals=goal_list
    )


@app.post("/goals/<int:goal_id>/progress")
def update_goal_progress(goal_id):

    progress = int(
        request.form["progress"]
    )

    progress = max(
        0,
        min(100, progress)
    )

    connection = get_db()

    connection.execute(
        """
        UPDATE goals
        SET progress = ?
        WHERE id = ?
        """,
        (
            progress,
            goal_id
        )
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("goals")
    )


@app.post("/goals/<int:goal_id>/delete")
def delete_goal(goal_id):

    connection = get_db()

    connection.execute(
        "DELETE FROM goals WHERE id = ?",
        (goal_id,)
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("goals")
    )


# ==================================================
# HABITS
# ==================================================

@app.route("/habits", methods=["GET", "POST"])
def habits():

    connection = get_db()

    if request.method == "POST":

        title = request.form["title"]

        emoji = request.form.get(
            "emoji",
            "🔥"
        )

        connection.execute(
            """
            INSERT INTO habits
            (title, emoji, streak)
            VALUES (?, ?, 0)
            """,
            (
                title,
                emoji
            )
        )

        connection.commit()

    habit_list = connection.execute(
        """
        SELECT *
        FROM habits
        ORDER BY streak DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "habits.html",
        habits=habit_list
    )


@app.post("/habits/<int:habit_id>/check")
def check_habit(habit_id):

    connection = get_db()

    habit = connection.execute(
        """
        SELECT *
        FROM habits
        WHERE id = ?
        """,
        (habit_id,)
    ).fetchone()

    if habit:

        if habit["checked_today"] == 0:

            connection.execute(
                """
                UPDATE habits
                SET checked_today = 1,
                    streak = streak + 1
                WHERE id = ?
                """,
                (habit_id,)
            )

        else:

            connection.execute(
                """
                UPDATE habits
                SET checked_today = 0,
                    streak = MAX(0, streak - 1)
                WHERE id = ?
                """,
                (habit_id,)
            )

    connection.commit()
    connection.close()

    return redirect(
        url_for("habits")
    )


@app.post("/habits/<int:habit_id>/delete")
def delete_habit(habit_id):

    connection = get_db()

    connection.execute(
        "DELETE FROM habits WHERE id = ?",
        (habit_id,)
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("habits")
    )


# ==================================================
# SKILL ROADMAPS
# ==================================================

@app.route("/skills")
def skills():

    roadmaps = [

        (
            "Web Developer",
            "🌐",
            [
                "HTML & CSS",
                "JavaScript",
                "Git & GitHub",
                "Frontend Framework",
                "APIs",
                "Real Projects",
                "Portfolio"
            ]
        ),

        (
            "App Developer",
            "📱",
            [
                "Dart Basics",
                "Flutter UI",
                "Navigation",
                "Forms",
                "State Management",
                "APIs",
                "Projects"
            ]
        ),

        (
            "Data Analyst",
            "📊",
            [
                "Excel",
                "SQL",
                "Python",
                "Pandas",
                "Data Visualization",
                "Statistics",
                "Portfolio"
            ]
        ),

        (
            "AI / ML Beginner",
            "🤖",
            [
                "Python",
                "NumPy",
                "Pandas",
                "Math Basics",
                "Machine Learning",
                "Model Training",
                "Projects"
            ]
        ),

        (
            "UI/UX Designer",
            "🎨",
            [
                "Design Principles",
                "Figma",
                "Wireframes",
                "User Flows",
                "Prototypes",
                "Usability",
                "Case Studies"
            ]
        )
    ]

    return render_template(
        "skills.html",
        roadmaps=roadmaps
    )


# ==================================================
# NOTES
# ==================================================

@app.route("/notes", methods=["GET", "POST"])
def notes():

    connection = get_db()

    if request.method == "POST":

        title = request.form["title"]

        content = request.form.get(
            "content",
            ""
        )

        created_at = datetime.now().strftime(
            "%d %b %Y, %I:%M %p"
        )

        connection.execute(
            """
            INSERT INTO notes
            (title, content, created_at)
            VALUES (?, ?, ?)
            """,
            (
                title,
                content,
                created_at
            )
        )

        connection.commit()

    note_list = connection.execute(
        """
        SELECT *
        FROM notes
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "notes.html",
        notes=note_list
    )


@app.post("/notes/<int:note_id>/delete")
def delete_note(note_id):

    connection = get_db()

    connection.execute(
        "DELETE FROM notes WHERE id = ?",
        (note_id,)
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("notes")
    )


# ==================================================
# API
# ==================================================

@app.route("/api/stats")
def api_stats():

    return jsonify(
        get_statistics()
    )


# ==================================================
# RESET DEMO
# ==================================================

@app.post("/reset-demo")
def reset_demo():

    connection = get_db()

    tables = [
        "tasks",
        "expenses",
        "goals",
        "habits",
        "notes"
    ]

    for table in tables:
        connection.execute(
            f"DELETE FROM {table}"
        )

    connection.commit()
    connection.close()

    initialize_database()

    return redirect(
        url_for("home")
    )


# ==================================================
# START APPLICATION
# ==================================================

if __name__ == "__main__":

    initialize_database()

    app.run(
        debug=True
    )