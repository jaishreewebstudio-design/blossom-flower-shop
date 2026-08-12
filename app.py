from flask import (
    Flask,
    jsonify,
    request,
    render_template,
    redirect,
    url_for,
    session
)

from flask_cors import CORS

import sqlite3
import os
import json

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "blossom-flower-shop-secret-key"
)

CORS(app)


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE = os.path.join(
    BASE_DIR,
    "flower_shop.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    conn = get_db()

    cursor = conn.cursor()


    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT NOT NULL UNIQUE,

            password TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # --------------------------------------------------------
    # FLOWERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flowers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            price REAL NOT NULL DEFAULT 0,

            image TEXT,

            description TEXT,

            stock INTEGER NOT NULL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # --------------------------------------------------------
    # CART
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            flower_id INTEGER NOT NULL,

            quantity INTEGER NOT NULL DEFAULT 1,

            status TEXT NOT NULL DEFAULT 'Cart',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(flower_id)
                REFERENCES flowers(id)
                ON DELETE CASCADE

        )
    """)


    # --------------------------------------------------------
    # ORDERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            customer_name TEXT NOT NULL,

            phone TEXT NOT NULL,

            address TEXT NOT NULL,

            payment TEXT NOT NULL,

            total REAL NOT NULL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'Processing',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE

        )
    """)


    # --------------------------------------------------------
    # ORDER ITEMS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_id INTEGER NOT NULL,

            flower_id INTEGER,

            name TEXT NOT NULL,

            price REAL NOT NULL,

            quantity INTEGER NOT NULL,

            subtotal REAL NOT NULL,

            FOREIGN KEY(order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE

        )
    """)


    conn.commit()


    # ========================================================
    # DEFAULT FLOWERS
    # ========================================================

    cursor.execute(
        "SELECT COUNT(*) AS count FROM flowers"
    )

    count = cursor.fetchone()["count"]


    if count == 0:

        flowers = [

            (
                "Red Rose",
                299,
                "https://images.unsplash.com/photo-1496062031456-07b8f162a322",
                "Beautiful red roses",
                50
            ),

            (
                "Pink Rose",
                349,
                "https://images.unsplash.com/photo-1518709268805-4e9042af9f23",
                "Beautiful pink roses",
                50
            ),

            (
                "Sunflower",
                399,
                "https://images.unsplash.com/photo-1597848212624-e19e7e5b0c7d",
                "Bright yellow sunflower",
                50
            ),

            (
                "Tulip",
                449,
                "https://images.unsplash.com/photo-1520763185298-1b434c919102",
                "Beautiful tulip flowers",
                50
            ),

            (
                "White Lily",
                499,
                "https://images.unsplash.com/photo-1596438459190-0ff7b1e6b7c0",
                "Elegant white lilies",
                50
            )

        ]


        cursor.executemany(
            """
            INSERT INTO flowers
            (
                name,
                price,
                image,
                description,
                stock
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            flowers
        )


        conn.commit()


    conn.close()


# ============================================================
# CURRENT USER
# ============================================================

def current_user():

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return None


    conn = get_db()

    user = conn.execute(
        """
        SELECT
            id,
            name,
            email
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    return user


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home_page():

    return render_template(
        "register.html"
    )


# ============================================================
# REGISTER PAGE
# ============================================================

@app.route("/register")
def register_page():

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN PAGE
# ============================================================

@app.route("/login")
def login_page():

    return render_template(
        "login.html"
    )


# ============================================================
# FORGOT PASSWORD PAGE
# ============================================================

@app.route("/forgot-password")
def forgot_password_page():

    return render_template(
        "forgot-password.html"
    )


# ============================================================
# DASHBOARD PAGE
# ============================================================

@app.route("/dashboard")
def dashboard_page():

    return render_template(
        "dashboard.html"
    )


# ============================================================
# FLOWERS PAGE
# ============================================================

@app.route("/flowers")
def flowers_page():

    return render_template(
        "flowers.html"
    )


# ============================================================
# CART PAGE
# ============================================================

@app.route("/cart")
def cart_page():

    return render_template(
        "cart.html"
    )


# ============================================================
# CHECKOUT PAGE
# ============================================================

@app.route("/checkout")
def checkout_page():

    return render_template(
        "checkout.html"
    )


# ============================================================
# ORDERS PAGE
# ============================================================

@app.route("/orders")
def orders_page():

    return render_template(
        "orders.html"
    )


# ============================================================
# REGISTER API
# ============================================================

@app.route(
    "/api/register",
    methods=["POST"]
)
def register_api():

    data = request.get_json(
        silent=True
    ) or {}


    name = str(
        data.get("name", "")
    ).strip()


    email = str(
        data.get("email", "")
    ).strip().lower()


    password = str(
        data.get("password", "")
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not name:

        return jsonify({
            "success": False,
            "message": "Name is required."
        }), 400


    if not email:

        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400


    if len(password) < 6:

        return jsonify({
            "success": False,
            "message":
                "Password must be at least 6 characters."
        }), 400


    conn = get_db()


    # --------------------------------------------------------
    # CHECK EMAIL
    # --------------------------------------------------------

    existing = conn.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()


    if existing:

        conn.close()

        return jsonify({
            "success": False,
            "message":
                "Email already registered."
        }), 409


    # --------------------------------------------------------
    # HASH PASSWORD
    # --------------------------------------------------------

    hashed_password = generate_password_hash(
        password
    )


    # --------------------------------------------------------
    # INSERT USER
    # --------------------------------------------------------

    cursor = conn.execute(
        """
        INSERT INTO users
        (
            name,
            email,
            password
        )
        VALUES (?, ?, ?)
        """,
        (
            name,
            email,
            hashed_password
        )
    )


    conn.commit()


    user_id = cursor.lastrowid


    conn.close()


    return jsonify({

        "success": True,

        "message":
            "Registration successful.",

        "user": {

            "id": user_id,

            "name": name,

            "email": email

        }

    }), 201


# ============================================================
# LOGIN API
# ============================================================

@app.route(
    "/api/login",
    methods=["POST"]
)
def login_api():

    data = request.get_json(
        silent=True
    ) or {}


    email = str(
        data.get("email", "")
    ).strip().lower()


    password = str(
        data.get("password", "")
    )


    if not email or not password:

        return jsonify({
            "success": False,
            "message":
                "Email and password are required."
        }), 400


    conn = get_db()


    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()


    conn.close()


    if not user:

        return jsonify({
            "success": False,
            "message":
                "Invalid email or password."
        }), 401


    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify({
            "success": False,
            "message":
                "Invalid email or password."
        }), 401


    # --------------------------------------------------------
    # SESSION
    # --------------------------------------------------------

    session["user_id"] = user["id"]

    session["user_name"] = user["name"]

    session["user_email"] = user["email"]


    return jsonify({

        "success": True,

        "message":
            "Login successful.",

        "user": {

            "id": user["id"],

            "name": user["name"],

            "email": user["email"]

        }

    })


# ============================================================
# LOGOUT API
# ============================================================

@app.route(
    "/api/logout",
    methods=["POST"]
)
def logout_api():

    session.clear()


    return jsonify({

        "success": True,

        "message":
            "Logout successful."

    })


# ============================================================
# CURRENT USER API
# ============================================================

@app.route(
    "/api/me",
    methods=["GET"]
)
def me_api():

    user = current_user()


    if not user:

        return jsonify({

            "success": False,

            "message":
                "Not logged in."

        }), 401


    return jsonify({

        "success": True,

        "user": {

            "id": user["id"],

            "name": user["name"],

            "email": user["email"]

        }

    })


# ============================================================
# FORGOT PASSWORD API
# ============================================================

@app.route(
    "/api/forgot-password",
    methods=["POST"]
)
def forgot_password_api():

    data = request.get_json(
        silent=True
    ) or {}


    email = str(
        data.get("email", "")
    ).strip().lower()


    new_password = str(
        data.get("new_password", "")
    )


    confirm_password = str(
        data.get("confirm_password", "")
    )


    if not email:

        return jsonify({
            "success": False,
            "message":
                "Please enter your email."
        }), 400


    if len(new_password) < 6:

        return jsonify({
            "success": False,
            "message":
                "Password must be at least 6 characters."
        }), 400


    if new_password != confirm_password:

        return jsonify({
            "success": False,
            "message":
                "Passwords do not match."
        }), 400


    conn = get_db()


    user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()


    if not user:

        conn.close()

        return jsonify({
            "success": False,
            "message":
                "No account found with this email."
        }), 404


    hashed_password = generate_password_hash(
        new_password
    )


    conn.execute(
        """
        UPDATE users
        SET password = ?
        WHERE id = ?
        """,
        (
            hashed_password,
            user["id"]
        )
    )


    conn.commit()

    conn.close()


    return jsonify({

        "success": True,

        "message":
            "Password reset successfully."

    })


# ============================================================
# GET FLOWERS
# ============================================================

@app.route(
    "/api/flowers",
    methods=["GET"]
)
def get_flowers():

    conn = get_db()


    flowers = conn.execute(
        """
        SELECT *
        FROM flowers
        ORDER BY id DESC
        """
    ).fetchall()


    conn.close()


    result = []


    for flower in flowers:

        result.append({

            "id": flower["id"],

            "name": flower["name"],

            "price": flower["price"],

            "image": flower["image"],

            "description":
                flower["description"],

            "stock": flower["stock"]

        })


    return jsonify({

        "success": True,

        "flowers": result

    })


# ============================================================
# ADD TO CART
# ============================================================

@app.route(
    "/api/cart",
    methods=["POST"]
)
def add_to_cart():

    data = request.get_json(
        silent=True
    ) or {}


    user_id = data.get(
        "user_id"
    )


    flower_id = data.get(
        "flower_id"
    )


    quantity = int(
        data.get(
            "quantity",
            1
        )
    )


    if not user_id or not flower_id:

        return jsonify({

            "success": False,

            "message":
                "User ID and flower ID are required."

        }), 400


    if quantity < 1:

        quantity = 1


    conn = get_db()


    flower = conn.execute(
        """
        SELECT *
        FROM flowers
        WHERE id = ?
        """,
        (flower_id,)
    ).fetchone()


    if not flower:

        conn.close()

        return jsonify({

            "success": False,

            "message":
                "Flower not found."

        }), 404


    existing = conn.execute(
        """
        SELECT *
        FROM cart
        WHERE user_id = ?
        AND flower_id = ?
        AND status = 'Cart'
        """,
        (
            user_id,
            flower_id
        )
    ).fetchone()


    if existing:

        conn.execute(
            """
            UPDATE cart
            SET quantity = quantity + ?
            WHERE id = ?
            """,
            (
                quantity,
                existing["id"]
            )
        )

    else:

        conn.execute(
            """
            INSERT INTO cart
            (
                user_id,
                flower_id,
                quantity,
                status
            )
            VALUES (?, ?, ?, 'Cart')
            """,
            (
                user_id,
                flower_id,
                quantity
            )
        )


    conn.commit()

    conn.close()


    return jsonify({

        "success": True,

        "message":
            "Flower added to cart."

    })


# ============================================================
# GET CART
# ============================================================

@app.route(
    "/api/cart/<int:user_id>",
    methods=["GET"]
)
def get_cart(user_id):

    conn = get_db()


    rows = conn.execute(
        """
        SELECT

            cart.id,

            cart.user_id,

            cart.flower_id,

            cart.quantity,

            cart.status,

            flowers.name,

            flowers.price,

            flowers.image,

            flowers.description,

            (
                flowers.price *
                cart.quantity
            ) AS subtotal

        FROM cart

        INNER JOIN flowers
            ON flowers.id = cart.flower_id

        WHERE cart.user_id = ?

        ORDER BY cart.id DESC
        """,
        (user_id,)
    ).fetchall()


    conn.close()


    cart = []


    for row in rows:

        cart.append({

            "id": row["id"],

            "user_id":
                row["user_id"],

            "flower_id":
                row["flower_id"],

            "name":
                row["name"],

            "price":
                row["price"],

            "image":
                row["image"],

            "description":
                row["description"],

            "quantity":
                row["quantity"],

            "status":
                row["status"],

            "subtotal":
                row["subtotal"]

        })


    return jsonify({

        "success": True,

        "cart": cart

    })


# ============================================================
# UPDATE CART
# ============================================================

@app.route(
    "/api/cart/<int:cart_id>",
    methods=["PUT"]
)
def update_cart(cart_id):

    data = request.get_json(
        silent=True
    ) or {}


    quantity = int(
        data.get(
            "quantity",
            1
        )
    )


    if quantity < 1:

        quantity = 1


    conn = get_db()


    row = conn.execute(
        """
        SELECT *
        FROM cart
        WHERE id = ?
        """,
        (cart_id,)
    ).fetchone()


    if not row:

        conn.close()

        return jsonify({

            "success": False,

            "message":
                "Cart item not found."

        }), 404


    conn.execute(
        """
        UPDATE cart
        SET quantity = ?
        WHERE id = ?
        """,
        (
            quantity,
            cart_id
        )
    )


    conn.commit()

    conn.close()


    return jsonify({

        "success": True,

        "message":
            "Cart updated."

    })


# ============================================================
# DELETE CART ITEM
# ============================================================

@app.route(
    "/api/cart/<int:cart_id>",
    methods=["DELETE"]
)
def delete_cart(cart_id):

    conn = get_db()


    row = conn.execute(
        """
        SELECT id
        FROM cart
        WHERE id = ?
        """,
        (cart_id,)
    ).fetchone()


    if not row:

        conn.close()

        return jsonify({

            "success": False,

            "message":
                "Cart item not found."

        }), 404


    conn.execute(
        """
        DELETE FROM cart
        WHERE id = ?
        """,
        (cart_id,)
    )


    conn.commit()

    conn.close()


    return jsonify({

        "success": True,

        "message":
            "Cart item removed."

    })


# ============================================================
# CREATE ORDER
# ============================================================

@app.route(
    "/api/orders",
    methods=["POST"]
)
def create_order():

    data = request.get_json(
        silent=True
    ) or {}


    user_id = data.get(
        "user_id"
    )


    customer_name = str(
        data.get(
            "customer_name",
            ""
        )
    ).strip()


    phone = str(
        data.get(
            "phone",
            ""
        )
    ).strip()


    address = str(
        data.get(
            "address",
            ""
        )
    ).strip()


    payment = str(
        data.get(
            "payment",
            ""
        )
    ).strip()


    cart_ids = data.get(
        "cart_ids",
        []
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not user_id:

        return jsonify({

            "success": False,

            "message":
                "User ID is required."

        }), 400


    if not customer_name:

        return jsonify({

            "success": False,

            "message":
                "Customer name is required."

        }), 400


    if not phone:

        return jsonify({

            "success": False,

            "message":
                "Phone number is required."

        }), 400


    if not address:

        return jsonify({

            "success": False,

            "message":
                "Delivery address is required."

        }), 400


    if not payment:

        return jsonify({

            "success": False,

            "message":
                "Payment method is required."

        }), 400


    if not isinstance(
        cart_ids,
        list
    ) or len(cart_ids) == 0:

        return jsonify({

            "success": False,

            "message":
                "Please select at least one cart item."

        }), 400


    conn = get_db()


    # --------------------------------------------------------
    # GET SELECTED CART ITEMS
    # --------------------------------------------------------

    placeholders = ",".join(
        ["?"] * len(cart_ids)
    )


    query = f"""
        SELECT

            cart.id,

            cart.user_id,

            cart.flower_id,

            cart.quantity,

            cart.status,

            flowers.name,

            flowers.price,

            flowers.image

        FROM cart

        INNER JOIN flowers
            ON flowers.id = cart.flower_id

        WHERE cart.user_id = ?

        AND cart.id IN ({placeholders})

    """


    params = [
        user_id
    ] + cart_ids


    items = conn.execute(
        query,
        params
    ).fetchall()


    if not items:

        conn.close()

        return jsonify({

            "success": False,

            "message":
                "Selected cart items not found."

        }), 404


    # --------------------------------------------------------
    # CALCULATE TOTAL
    # --------------------------------------------------------

    total = 0


    for item in items:

        total += (
            float(item["price"])
            *
            int(item["quantity"])
        )


    # --------------------------------------------------------
    # CREATE ORDER
    # --------------------------------------------------------

    cursor = conn.execute(
        """
        INSERT INTO orders
        (
            user_id,
            customer_name,
            phone,
            address,
            payment,
            total,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, 'Processing')
        """,
        (
            user_id,
            customer_name,
            phone,
            address,
            payment,
            total
        )
    )


    order_id = cursor.lastrowid


    # --------------------------------------------------------
    # CREATE ORDER ITEMS
    # --------------------------------------------------------

    for item in items:

        price = float(
            item["price"]
        )


        quantity = int(
            item["quantity"]
        )


        subtotal = (
            price * quantity
        )


        conn.execute(
            """
            INSERT INTO order_items
            (
                order_id,
                flower_id,
                name,
                price,
                quantity,
                subtotal
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                item["flower_id"],
                item["name"],
                price,
                quantity,
                subtotal
            )
        )


        # ----------------------------------------------------
        # IMPORTANT:
        # Keep item inside cart.
        # Just mark it Ordered.
        # ----------------------------------------------------

        conn.execute(
            """
            UPDATE cart
            SET status = 'Ordered'
            WHERE id = ?
            """,
            (item["id"],)
        )


    conn.commit()


    # --------------------------------------------------------
    # GET CREATED ORDER
    # --------------------------------------------------------

    order = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    ).fetchone()


    conn.close()


    return jsonify({

        "success": True,

        "message":
            "Order placed successfully.",

        "order": {

            "id":
                order["id"],

            "user_id":
                order["user_id"],

            "customer_name":
                order["customer_name"],

            "phone":
                order["phone"],

            "address":
                order["address"],

            "payment":
                order["payment"],

            "total":
                order["total"],

            "status":
                order["status"],

            "created_at":
                order["created_at"]

        }

    }), 201


# ============================================================
# GET USER ORDERS
# ============================================================

@app.route(
    "/api/orders/<int:user_id>",
    methods=["GET"]
)
def get_orders(user_id):

    conn = get_db()


    orders = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()


    result = []


    for order in orders:

        items = conn.execute(
            """
            SELECT
                id,
                order_id,
                flower_id,
                name,
                price,
                quantity,
                subtotal
            FROM order_items
            WHERE order_id = ?
            ORDER BY id ASC
            """,
            (order["id"],)
        ).fetchall()


        products = []


        for item in items:

            products.append({

                "id":
                    item["id"],

                "order_id":
                    item["order_id"],

                "flower_id":
                    item["flower_id"],

                "name":
                    item["name"],

                "price":
                    item["price"],

                "quantity":
                    item["quantity"],

                "subtotal":
                    item["subtotal"]

            })


        result.append({

            "id":
                order["id"],

            "user_id":
                order["user_id"],

            "customer_name":
                order["customer_name"],

            "phone":
                order["phone"],

            "address":
                order["address"],

            "payment":
                order["payment"],

            "total":
                order["total"],

            "status":
                order["status"],

            "created_at":
                order["created_at"],

            "items":
                products

        })


    conn.close()


    return jsonify({

        "success": True,

        "orders":
            result

    })


# ============================================================
# DELETE ORDER
# ============================================================

@app.route(
    "/api/orders/<int:order_id>",
    methods=["DELETE"]
)
def delete_order(order_id):

    conn = get_db()


    order = conn.execute(
        """
        SELECT id
        FROM orders
        WHERE id = ?
        """,
        (order_id,)
    ).fetchone()


    if not order:

        conn.close()

        return jsonify({

            "success": False,

            "message":
                "Order not found."

        }), 404


    conn.execute(
        """
        DELETE FROM orders
        WHERE id = ?
        """,
        (order_id,)
    )


    conn.commit()

    conn.close()


    return jsonify({

        "success": True,

        "message":
            "Order deleted successfully."

    })


# ============================================================
# DASHBOARD API
# ============================================================

@app.route(
    "/api/dashboard",
    methods=["GET"]
)
def dashboard_api():

    conn = get_db()


    users = conn.execute(
        "SELECT COUNT(*) AS count FROM users"
    ).fetchone()["count"]


    flowers = conn.execute(
        "SELECT COUNT(*) AS count FROM flowers"
    ).fetchone()["count"]


    cart_items = conn.execute(
        "SELECT COUNT(*) AS count FROM cart"
    ).fetchone()["count"]


    orders = conn.execute(
        "SELECT COUNT(*) AS count FROM orders"
    ).fetchone()["count"]


    conn.close()


    return jsonify({

        "success": True,

        "users":
            users,

        "flowers":
            flowers,

        "cart_items":
            cart_items,

        "orders":
            orders

    })


# ============================================================
# SWAGGER-LIKE API INFORMATION
# ============================================================

@app.route(
    "/api",
    methods=["GET"]
)
def api_home():

    return jsonify({

        "success": True,

        "application":
            "Blossom Flower Shop API",

        "endpoints": [

            "POST /api/register",

            "POST /api/login",

            "POST /api/logout",

            "GET /api/me",

            "POST /api/forgot-password",

            "GET /api/flowers",

            "POST /api/cart",

            "GET /api/cart/<user_id>",

            "PUT /api/cart/<cart_id>",

            "DELETE /api/cart/<cart_id>",

            "POST /api/orders",

            "GET /api/orders/<user_id>",

            "DELETE /api/orders/<order_id>",

            "GET /api/dashboard"

        ]

    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "success": False,

        "message":
            "Page or API endpoint not found."

    }), 404


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    init_db()

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
