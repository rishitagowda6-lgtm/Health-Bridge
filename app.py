from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "healthbridge-demo-key"

# Keep database in the same folder as app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "healthbridge.db")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

def init_db():

    conn = db()

    conn.executescript("""
    
    CREATE TABLE IF NOT EXISTS hospitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        beds INTEGER DEFAULT 0,
        phone TEXT,
        emergency TEXT
    );

    CREATE TABLE IF NOT EXISTS blood_banks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        blood_group TEXT,
        units INTEGER DEFAULT 0,
        phone TEXT
    );

    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        store TEXT NOT NULL,
        city TEXT NOT NULL,
        price REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        phone TEXT
    );

    """)

    # =====================================================
    # ADD DEMO DATA ONLY IF DATABASE IS EMPTY
    # =====================================================

    hospital_count = conn.execute(
        "SELECT COUNT(*) FROM hospitals"
    ).fetchone()[0]

    if hospital_count == 0:

        conn.executemany(
            """
            INSERT INTO hospitals
            (name, city, beds, phone, emergency)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    "Apollo Care Hospital",
                    "Navi Mumbai",
                    12,
                    "022-41002000",
                    "24/7"
                ),
                (
                    "SIES Community Hospital",
                    "Nerul",
                    7,
                    "022-27701111",
                    "24/7"
                ),
                (
                    "Harbor Multispeciality",
                    "Vashi",
                    4,
                    "022-27881234",
                    "24/7"
                )
            ]
        )

    blood_count = conn.execute(
        "SELECT COUNT(*) FROM blood_banks"
    ).fetchone()[0]

    if blood_count == 0:

        conn.executemany(
            """
            INSERT INTO blood_banks
            (name, city, blood_group, units, phone)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    "LifeLine Blood Bank",
                    "Nerul",
                    "O+",
                    18,
                    "022-40001122"
                ),
                (
                    "RedDrop Blood Centre",
                    "Vashi",
                    "A+",
                    11,
                    "022-40003344"
                ),
                (
                    "CarePlus Blood Bank",
                    "Belapur",
                    "B+",
                    9,
                    "022-40005566"
                )
            ]
        )

    medicine_count = conn.execute(
        "SELECT COUNT(*) FROM medicines"
    ).fetchone()[0]

    if medicine_count == 0:

        conn.executemany(
            """
            INSERT INTO medicines
            (name, store, city, price, stock, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "Paracetamol 500mg",
                    "MediCare Pharmacy",
                    "Nerul",
                    28,
                    45,
                    "9000011111"
                ),
                (
                    "Paracetamol 500mg",
                    "HealthFirst Store",
                    "Vashi",
                    24,
                    32,
                    "9000022222"
                ),
                (
                    "Amoxicillin 500mg",
                    "MediCare Pharmacy",
                    "Nerul",
                    92,
                    18,
                    "9000011111"
                ),
                (
                    "Amoxicillin 500mg",
                    "City Meds",
                    "Belapur",
                    86,
                    12,
                    "9000033333"
                )
            ]
        )

    conn.commit()
    conn.close()


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    conn = db()

    stats = {
        "hospitals": conn.execute(
            "SELECT COUNT(*) FROM hospitals"
        ).fetchone()[0],

        "blood": conn.execute(
            "SELECT COUNT(*) FROM blood_banks"
        ).fetchone()[0],

        "medicines": conn.execute(
            "SELECT COUNT(*) FROM medicines"
        ).fetchone()[0]
    }

    conn.close()

    return render_template(
        "index.html",
        stats=stats
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    conn = db()

    # Get hospitals
    hospitals = conn.execute(
        """
        SELECT *
        FROM hospitals
        ORDER BY beds DESC
        """
    ).fetchall()

    # Get blood banks
    blood = conn.execute(
        """
        SELECT *
        FROM blood_banks
        ORDER BY units DESC
        """
    ).fetchall()

    # Get medicines
    medicines = conn.execute(
        """
        SELECT *
        FROM medicines
        ORDER BY price ASC
        """
    ).fetchall()

    # Dashboard statistics
    stats = {

        "hospitals": conn.execute(
            "SELECT COUNT(*) FROM hospitals"
        ).fetchone()[0],

        "beds": conn.execute(
            "SELECT COALESCE(SUM(beds), 0) FROM hospitals"
        ).fetchone()[0],

        "blood": conn.execute(
            "SELECT COALESCE(SUM(units), 0) FROM blood_banks"
        ).fetchone()[0],

        "medicines": conn.execute(
            "SELECT COUNT(*) FROM medicines"
        ).fetchone()[0]
    }

    conn.close()

    return render_template(
        "dashboard.html",
        hospitals=hospitals,
        blood=blood,
        medicines=medicines,
        stats=stats
    )


# =========================================================
# RESOURCES PAGE
# =========================================================

@app.route("/resources")
def resources():

    q = request.args.get("q", "").strip()

    conn = db()

    like = f"%{q}%"

    hospitals = conn.execute(
        """
        SELECT *
        FROM hospitals
        WHERE name LIKE ?
           OR city LIKE ?
        ORDER BY beds DESC
        """,
        (like, like)
    ).fetchall()

    blood = conn.execute(
        """
        SELECT *
        FROM blood_banks
        WHERE name LIKE ?
           OR city LIKE ?
           OR blood_group LIKE ?
        ORDER BY units DESC
        """,
        (like, like, like)
    ).fetchall()

    medicines = conn.execute(
        """
        SELECT *
        FROM medicines
        WHERE name LIKE ?
           OR store LIKE ?
           OR city LIKE ?
        ORDER BY price ASC
        """,
        (like, like, like)
    ).fetchall()

    conn.close()

    return render_template(
        "resources.html",
        hospitals=hospitals,
        blood=blood,
        medicines=medicines,
        q=q
    )


# =========================================================
# MEDICINE PRICE COMPARISON
# =========================================================

@app.route("/compare")
def compare():

    q = request.args.get(
        "q",
        "Paracetamol 500mg"
    ).strip()

    conn = db()

    rows = conn.execute(
        """
        SELECT *
        FROM medicines
        WHERE name LIKE ?
        ORDER BY price ASC
        """,
        (f"%{q}%",)
    ).fetchall()

    conn.close()

    return render_template(
        "compare.html",
        rows=rows,
        q=q
    )


# =========================================================
# SOS PAGE
# =========================================================

@app.route("/sos")
def sos():

    return render_template("sos.html")


# =========================================================
# PROVIDER PAGE
# =========================================================

@app.route("/provider")
def provider():

    return render_template("provider.html")


# =========================================================
# PROVIDER - ADD RESOURCE
# =========================================================

@app.route("/provider/add", methods=["POST"])
def provider_add():

    # -----------------------------------------------------
    # Get resource type
    # -----------------------------------------------------

    kind = request.form.get("kind", "").strip()

    if not kind:

        flash("Please select a resource type.")

        return redirect(url_for("provider"))


    conn = db()


    # =====================================================
    # HOSPITAL
    # =====================================================

    if kind == "hospital":

        name = request.form.get("name", "").strip()
        city = request.form.get("city", "").strip()
        beds = request.form.get("beds", "0").strip()
        phone = request.form.get("phone", "").strip()
        emergency = request.form.get(
            "emergency",
            "24/7"
        ).strip()

        # Basic validation
        if not name or not city or not phone:

            conn.close()

            flash(
                "Please enter hospital name, city and phone number."
            )

            return redirect(url_for("provider"))

        try:
            beds = int(beds or 0)
        except ValueError:
            beds = 0

        conn.execute(
            """
            INSERT INTO hospitals
            (name, city, beds, phone, emergency)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                city,
                beds,
                phone,
                emergency
            )
        )

        flash(
            "Hospital resource added successfully!"
        )


    # =====================================================
    # BLOOD BANK
    # =====================================================

    elif kind == "blood":

        name = request.form.get(
            "name",
            ""
        ).strip()

        city = request.form.get(
            "city",
            ""
        ).strip()

        blood_group = request.form.get(
            "blood_group",
            ""
        ).strip()

        units = request.form.get(
            "units",
            "0"
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()


        if not name or not city or not blood_group or not phone:

            conn.close()

            flash(
                "Please enter all blood bank details."
            )

            return redirect(url_for("provider"))


        try:
            units = int(units or 0)
        except ValueError:
            units = 0


        conn.execute(
            """
            INSERT INTO blood_banks
            (name, city, blood_group, units, phone)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                city,
                blood_group,
                units,
                phone
            )
        )

        flash(
            "Blood bank resource added successfully!"
        )


    # =====================================================
    # MEDICAL STORE / MEDICINE
    # =====================================================

    elif kind == "medicine":

        # IMPORTANT:
        # Using .get() prevents the BadRequestKeyError
        # you were getting earlier.

        medicine = request.form.get(
            "medicine",
            ""
        ).strip()

        store = request.form.get(
            "store",
            ""
        ).strip()

        city = request.form.get(
            "city",
            ""
        ).strip()

        price = request.form.get(
            "price",
            "0"
        ).strip()

        stock = request.form.get(
            "stock",
            "0"
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()


        if not medicine or not store or not city or not phone:

            conn.close()

            flash(
                "Please enter all medical store details."
            )

            return redirect(url_for("provider"))


        try:
            price = float(price or 0)
        except ValueError:
            price = 0


        try:
            stock = int(stock or 0)
        except ValueError:
            stock = 0


        conn.execute(
            """
            INSERT INTO medicines
            (name, store, city, price, stock, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                medicine,
                store,
                city,
                price,
                stock,
                phone
            )
        )

        flash(
            "Medicine resource added successfully!"
        )


    # =====================================================
    # INVALID RESOURCE
    # =====================================================

    else:

        conn.close()

        flash(
            "Invalid resource type."
        )

        return redirect(url_for("provider"))


    # =====================================================
    # SAVE DATABASE
    # =====================================================

    conn.commit()
    conn.close()


    # After saving, go to dashboard
    # so we can immediately see the new resource.

    return redirect(url_for("dashboard"))


# =========================================================
# LOGIN PAGE
# =========================================================

@app.route("/login")
def login():

    return render_template("login.html")


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )