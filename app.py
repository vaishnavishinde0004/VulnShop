from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)

# ==========================================
# VULNSHOP - INTENTIONALLY VULNERABLE LAB
# ==========================================

app.secret_key = "vulnshop-secret-key"

DATABASE = "database/vulnshop.db"


# ==========================================
# DATABASE
# ==========================================

def get_db():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def init_db():

    connection = get_db()

    # USERS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE,

            email TEXT,

            password TEXT,

            role TEXT DEFAULT 'user'

        )
    """)

    # PRODUCTS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT,

            description TEXT,

            price INTEGER

        )
    """)

    # REVIEWS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS reviews (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT,

            review TEXT

        )
    """)

    # ======================================
    # DEMO USERS
    # ======================================

    existing_users = connection.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    if existing_users == 0:

        connection.execute("""
            INSERT INTO users
            (username, email, password, role)

            VALUES
            ('admin',
             'admin@vulnshop.local',
             'admin123',
             'admin')
        """)

        connection.execute("""
            INSERT INTO users
            (username, email, password, role)

            VALUES
            ('testuser',
             'test@vulnshop.local',
             'password123',
             'user')
        """)

    # ======================================
    # DEMO PRODUCTS
    # ======================================

    existing_products = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if existing_products == 0:

        products = [

            (
                "Laptop Pro",
                "High performance laptop",
                45999
            ),

            (
                "Gaming Headset",
                "Immersive gaming headset",
                2499
            ),

            (
                "Mechanical Keyboard",
                "RGB mechanical keyboard",
                1999
            ),

            (
                "Wireless Mouse",
                "Ergonomic wireless mouse",
                999
            )

        ]

        connection.executemany("""
            INSERT INTO products
            (name, description, price)

            VALUES (?, ?, ?)
        """, products)

    connection.commit()

    connection.close()


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


# ==========================================
# LOGIN
# INTENTIONALLY VULNERABLE TO SQL INJECTION
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "")

        password = request.form.get("password", "")

        connection = get_db()

        # ==================================
        # INTENTIONAL SQL INJECTION
        # ==================================

        query = f"""
            SELECT *

            FROM users

            WHERE username = '{username}'

            AND password = '{password}'
        """

        try:

            user = connection.execute(query).fetchone()

        except Exception as error:

            connection.close()

            return f"""
                <h2>Database Error</h2>

                <pre>{error}</pre>
            """

        connection.close()

        if user:

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            session["role"] = user["role"]

            return redirect(
                url_for("dashboard")
            )

        return """
            <div style="
                font-family: Arial;
                padding: 40px;
            ">

                <h2>Login Failed</h2>

                <p>
                    Invalid username or password.
                </p>

                <a href="/login">
                    Try Again
                </a>

            </div>
        """

    return render_template("login.html")


# ==========================================
# REGISTER
# INTENTIONALLY VULNERABLE TO SQL INJECTION
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        )

        email = request.form.get(
            "email", ""
        )

        password = request.form.get(
            "password", ""
        )

        connection = get_db()

        # ==================================
        # INTENTIONAL SQL INJECTION
        # ==================================

        query = f"""
            INSERT INTO users
            (username, email, password)

            VALUES
            ('{username}',
             '{email}',
             '{password}')
        """

        try:

            connection.execute(query)

            connection.commit()

        except Exception as error:

            connection.close()

            return f"""
                <h2>Database Error</h2>

                <pre>{error}</pre>
            """

        connection.close()

        return redirect(
            url_for("login")
        )

    return render_template("register.html")


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "dashboard.html",

        username=session["username"],

        role=session["role"]
    )


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ==========================================
# PRODUCT
# INTENTIONALLY VULNERABLE TO SQL INJECTION
# ==========================================

@app.route("/product")
def product():

    product_id = request.args.get(
        "id",
        "1"
    )

    connection = get_db()

    # ==================================
    # INTENTIONAL SQL INJECTION
    # ==================================

    query = f"""
        SELECT *

        FROM products

        WHERE id = {product_id}
    """

    try:

        product = connection.execute(
            query
        ).fetchone()

    except Exception as error:

        connection.close()

        return f"""
            <h2>Database Error</h2>

            <pre>{error}</pre>
        """

    connection.close()

    if not product:

        return """
            <h2>Product not found</h2>

            <a href="/">
                Back to Home
            </a>
        """

    return render_template(
        "product.html",
        product=product
    )


# ==========================================
# SEARCH
# INTENTIONALLY VULNERABLE TO REFLECTED XSS
# ==========================================

@app.route("/search")
def search():

    search_query = request.args.get(
        "q",
        ""
    )

    # INTENTIONAL XSS

    return f"""
        <!DOCTYPE html>

        <html>

        <head>

            <title>
                Search - VulnShop
            </title>

            <link
                href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
                rel="stylesheet"
            >

        </head>

        <body>

        <div class="container py-5">

            <h1>
                VulnShop Search
            </h1>

            <form>

                <div class="input-group mb-4">

                    <input
                        class="form-control"
                        name="q"
                        value="{search_query}"
                        placeholder="Search products..."
                    >

                    <button
                        class="btn btn-dark"
                        type="submit"
                    >
                        Search
                    </button>

                </div>

            </form>

            <h4>
                Search results for:
            </h4>

            <div class="alert alert-secondary">

                {search_query}

            </div>

            <a href="/">
                ← Back to Home
            </a>

        </div>

        </body>

        </html>
    """


# ==========================================
# REVIEWS
# INTENTIONALLY VULNERABLE TO STORED XSS
# ==========================================

@app.route("/reviews", methods=["GET", "POST"])
def reviews():

    connection = get_db()

    if request.method == "POST":

        username = request.form.get(
            "username",
            "anonymous"
        )

        review = request.form.get(
            "review",
            ""
        )

        connection.execute(
            """
            INSERT INTO reviews
            (username, review)

            VALUES (?, ?)
            """,

            (
                username,
                review
            )
        )

        connection.commit()

    all_reviews = connection.execute(
        "SELECT * FROM reviews"
    ).fetchall()

    connection.close()

    return render_template(
        "reviews.html",
        reviews=all_reviews
    )


# ==========================================
# ADMIN PANEL
# INTENTIONALLY VULNERABLE
# NO AUTHORIZATION CHECK
# ==========================================

@app.route("/admin")
def admin():

    connection = get_db()

    users = connection.execute(
        """
        SELECT
            id,
            username,
            email,
            role
        FROM users
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin.html",
        users=users
    )


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )