from flask import (
    Flask, render_template, request,
    redirect, url_for, make_response,
    abort, flash
)

import sqlite3
import csv
import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "change-this-secret-before-deployment"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "research.db")

RESEARCH_TYPES = [
    "Basic Research",
    "Applied Research",
    "Thought Experiment",
    "Quantitative Research",
    "Qualitative Research",
    "Mixed Methods Research",
    "Experimental Research",
    "Computational Research",
    "Exploratory Research",
    "Theoretical Research"
]

CATEGORIES = [
    "Engineering",
    "Artificial Intelligence",
    "Computer Science",
    "Robotics",
    "Mechanical Engineering",
    "Electrical Engineering",
    "Civil Engineering",
    "Renewable Energy",
    "Biotechnology",
    "Applied Physics",
    "Other Technology"
]


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS research (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            research_type TEXT NOT NULL,
            objective TEXT NOT NULL,
            methodology TEXT NOT NULL,
            abstract TEXT NOT NULL,
            findings TEXT,
            keywords TEXT,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


@app.route("/")
def index():

    connection = get_db()

    research = connection.execute(
        "SELECT * FROM research ORDER BY id DESC"
    ).fetchall()

    total = connection.execute(
        "SELECT COUNT(*) FROM research"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "index.html",
        research=research,
        total=total,
        research_types=RESEARCH_TYPES,
        categories=CATEGORIES
    )


@app.route("/submit", methods=["POST"])
def submit():

    fields = [
        "title",
        "author",
        "category",
        "research_type",
        "objective",
        "methodology",
        "abstract",
        "findings",
        "keywords"
    ]

    data = {
        field: request.form.get(field, "").strip()
        for field in fields
    }

    required = [
        "title",
        "author",
        "category",
        "research_type",
        "objective",
        "methodology",
        "abstract"
    ]

    if any(not data[field] for field in required):
        flash("Please complete all required fields.", "error")
        return redirect(url_for("index"))

    connection = get_db()

    connection.execute("""
        INSERT INTO research (
            title, author, category,
            research_type, objective,
            methodology, abstract,
            findings, keywords, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["title"],
        data["author"],
        data["category"],
        data["research_type"],
        data["objective"],
        data["methodology"],
        data["abstract"],
        data["findings"],
        data["keywords"],
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))

    connection.commit()
    connection.close()

    flash("Research successfully published!", "success")

    return redirect(url_for("index"))


@app.route("/research/<int:research_id>")
def view_research(research_id):

    connection = get_db()

    paper = connection.execute(
        "SELECT * FROM research WHERE id = ?",
        (research_id,)
    ).fetchone()

    connection.close()

    if paper is None:
        abort(404)

    return render_template(
        "index.html",
        research=[paper],
        total=1,
        research_types=RESEARCH_TYPES,
        categories=CATEGORIES,
        selected=paper
    )


@app.route("/delete/<int:research_id>", methods=["POST"])
def delete_research(research_id):

    # Demonstration only: protect this route with
    # administrator authentication before public deployment.

    connection = get_db()

    connection.execute(
        "DELETE FROM research WHERE id = ?",
        (research_id,)
    )

    connection.commit()
    connection.close()

    flash("Research record deleted.", "success")

    return redirect(url_for("index"))


@app.route("/download/csv")
def download_csv():

    connection = get_db()

    papers = connection.execute(
        "SELECT * FROM research ORDER BY id DESC"
    ).fetchall()

    connection.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Title", "Author", "Category",
        "Research Type", "Objective",
        "Methodology", "Abstract",
        "Findings", "Keywords", "Date"
    ])

    for paper in papers:
        writer.writerow(list(paper))

    response = make_response(
        "\ufeff" + output.getvalue()
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=RF_Research_Publications.csv"
    )

    response.headers["Content-Type"] = (
        "text/csv; charset=utf-8"
    )

    return response


@app.route("/download/pdf/<int:research_id>")
def download_pdf(research_id):

    connection = get_db()

    paper = connection.execute(
        "SELECT * FROM research WHERE id = ?",
        (research_id,)
    ).fetchone()

    connection.close()

    if paper is None:
        abort(404)

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch
    )

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "RF | Research Form and Publication",
            styles["Title"]
        )
    )

    content.append(Spacer(1, 20))

    sections = [
        ("Research Title", paper["title"]),
        ("Author", paper["author"]),
        ("Research Category", paper["category"]),
        ("Research Type", paper["research_type"]),
        ("Research Objective", paper["objective"]),
        ("Research Methodology", paper["methodology"]),
        ("Abstract", paper["abstract"]),
        ("Research Findings", paper["findings"] or "Not provided"),
        ("Keywords", paper["keywords"] or "Not provided"),
        ("Publication Date", paper["created_at"])
    ]

    for heading, value in sections:

        content.append(
            Paragraph(heading, styles["Heading2"])
        )

        safe_value = (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )

        content.append(
            Paragraph(safe_value, styles["BodyText"])
        )

        content.append(Spacer(1, 12))

    document.build(content)

    response = make_response(buffer.getvalue())

    response.headers["Content-Type"] = "application/pdf"

    response.headers["Content-Disposition"] = (
        f'attachment; filename="RF_Research_{research_id}.pdf"'
    )

    return response


@app.errorhandler(404)
def not_found(error):
    return "Research document not found.", 404


# Initialize database when the application starts
initialize_database()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )

