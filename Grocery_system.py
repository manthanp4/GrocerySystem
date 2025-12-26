"""
Grocery Management System - single-file Flask + SQLite app

Features:
- Add / Edit / Delete grocery items
- List and search items
- Track quantity, price, category, expiry date, notes
- Export inventory to CSV
- Simple web UI (Bootstrap CDN) and a tiny CLI fallback

How to run:
1. Install dependencies: pip install Flask
2. Run: python grocery_management_system.py
3. Open http://127.0.0.1:5000 in your browser

This file includes embedded HTML templates using render_template_string, so it's self-contained.
"""
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

from flask import Flask, g, request, redirect, url_for, send_file, flash, jsonify
from flask import render_template_string
from flask import render_template
from flask import session


import sqlite3
from datetime import datetime
import csv
import io
import os
import argparse



DB_PATH = 'grocery.db'

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-key'
app.secret_key = "grocery-secret"
app.secret_key = "supersecretkey"

# -------------------------- Database helpers --------------------------

def get_db():
    conn = sqlite3.connect(
        r"C:\Users\Manthan\Desktop\GrocerySystem\grocery.db"
    )
    conn.row_factory = sqlite3.Row
    return conn



def get_cart():
    if 'cart' not in session:
        session['cart'] = {}
    return session['cart']

def cart_item_count():
    cart = session.get('cart', {})
    return sum(cart.values())
@app.context_processor
def inject_cart_count():
    return dict(cart_item_count=cart_item_count)

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store"
    return response

def admin_required():
    return session.get("admin_logged_in")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        price REAL DEFAULT 0.0,
        quantity INTEGER DEFAULT 0,
        expiry_date TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def normalize_category(category):
    if not category:
        return "Other"

    c = category.strip().lower()

    category_map = {
        "fruit": "Fruits",
        "fruits": "Fruits",
        "vegetable": "Vegetables",
        "vegetables": "Vegetables",
        "veg": "Vegetables",
        "veggies": "Vegetables",
        "dairy": "Dairy",
        "milk": "Dairy",
        "bakery": "Bakery",
        "biscuit": "Bakery",
        "biscuits": "Bakery",
        "drink": "Drinks",
        "drinks": "Drinks",
        "juice": "Drinks",
        "beverage": "Drinks",
    }

    return category_map.get(c, c.capitalize())


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# -------------------------- Routes / Views --------------------------



FORM_HTML = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-4">
  <a href="{{ url_for('index') }}">&larr; Back to list</a>
  <h2 class="mt-2">{{ title }}</h2>
  <form method="post" class="mt-3">
    <div class="mb-3">
      <label class="form-label">Name</label>
      <input name="name" required class="form-control" value="{{ item.name if item else '' }}">
    </div>
    <div class="mb-3 row">
      <div class="col">
        <label class="form-label">Category</label>
        <input name="category" class="form-control" value="{{ item.category if item else '' }}">
      </div>
      <div class="col">
        <label class="form-label">Price</label>
        <input name="price" type="number" step="0.01" class="form-control" value="{{ item.price if item else 0 }}">
      </div>
    </div>
    <div class="mb-3 row">
      <div class="col">
        <label class="form-label">Quantity</label>
        <input name="quantity" type="number" class="form-control" value="{{ item.quantity if item else 0 }}">
      </div>
      <div class="col">
        <label class="form-label">Expiry Date</label>
        <input name="expiry_date" type="date" class="form-control" value="{{ item.expiry_date if item else '' }}">
      </div>
    </div>
    <div class="mb-3">
      <label class="form-label">Notes</label>
      <textarea name="notes" class="form-control">{{ item.notes if item else '' }}</textarea>
    </div>
    <button class="btn btn-primary">Save</button>
  </form>
</div>
</body>
</html>
'''

'''
@app.route('/')
def index():
    db = get_db()
    rows = db.execute("SELECT * FROM items ORDER BY name").fetchall()

    today = datetime.now().date()
    items = []

    total_items = len(rows)
    low_stock = 0
    expiring_soon = 0

    suggested_items = []
    for item in items:
      if item['days_left'] is not None and item['days_left'] < 0:
        suggested_items.append(item)
      elif item['days_left'] is not None and item['days_left'] <= 7:
        suggested_items.append(item)
      elif item['quantity'] <= 2:
        suggested_items.append(item)


    for r in rows:
        item = dict(r)   # convert sqlite row → normal dict

        # ---- LOW STOCK ----
        if item['quantity'] <= 2:
            low_stock += 1

        # ---- EXPIRY LOGIC ----
        days_left = None
        expiry_badge = ''
        row_class = ''

        if item['expiry_date']:
            try:
                exp_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
                days_left = (exp_date - today).days

                if days_left < 0:
                    row_class = 'table-danger'
                    expiry_badge = 'Expired'
                elif days_left == 0:
                    row_class = 'table-warning'
                    expiry_badge = 'Expires today'
                elif days_left <= 7:
                    row_class = 'table-warning'
                    expiry_badge = f'Expiring in {days_left} days'
            except:
                pass

        # attach new UI fields
        item['days_left'] = days_left
        item['expiry_badge'] = expiry_badge
        item['row_class'] = row_class

        items.append(item)
        available_products = [item for item in items if item['quantity'] > 0]

        

        
    return render_template(
    "index.html",
    items=items,
    available_products=available_products,
    suggested_items=suggested_items,
    total_items=total_items,
    low_stock=low_stock,
    expiring_soon=expiring_soon
)
'''


def get_db():
    conn = sqlite3.connect(
        r"C:\Users\Manthan\Desktop\GrocerySystem\grocery.db"
    )
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    conn = sqlite3.connect('grocery.db')
    conn.row_factory = sqlite3.Row
    return conn
  


@app.route("/")
def index():
    search = request.args.get("search", "").strip().lower()

    conn = sqlite3.connect("grocery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch filtered items
    if search:
        cursor.execute("""
            SELECT * FROM items 
            WHERE LOWER(name) LIKE ? 
               OR LOWER(category) LIKE ?
        """, (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM items")

    rows = cursor.fetchall()
    conn.close()

    # ---------- PRICE + DISCOUNT PROCESSING ----------
    products = []
    for row in rows:
        price = row["price"]
        discount = row["discount_percent"]  # this can be NULL

        # Safe handling (if discount is None)
        if discount is None:
            discount = 0

        # Calculate discounted price
        if discount > 0:
            discounted_price = round(price - (price * discount / 100), 2)
        else:
            discounted_price = price

        # Prepare new product dict
        products.append({
            "name": row["name"],
            "category": row["category"],
            "price": price,
            "discount_percent": discount,
            "discounted_price": discounted_price,
            "quantity": row["quantity"]
        })

    # ---------- GROUP BY CATEGORY ----------
    categories = {}
    for product in products:
        cat = product["category"].capitalize()
        categories.setdefault(cat, []).append(product)

        category_icons = {
            "Fruits": "🍎",
            "Vegetables": "🥦",
            "Bakery": "🥖",
            "Dairy": "🥛",
            "Drinks": "🥤" 
        }


    return render_template("index.html", categories=categories, category_icons=category_icons)


@app.route("/suggest")
def suggest():
    query = request.args.get("q", "").strip().lower()

    conn = sqlite3.connect("grocery.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT name FROM items
        WHERE LOWER(name) LIKE ?
        LIMIT 5
    """, (f"%{query}%",))

    results = [row["name"] for row in cur.fetchall()]
    conn.close()

    return jsonify(results)


@app.route("/add-to-cart/<name>")
def add_to_cart(name):
    conn = sqlite3.connect("grocery.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Check stock
    cur.execute("SELECT price, quantity FROM items WHERE name = ?", (name,))
    item = cur.fetchone()

    if not item or item["quantity"] <= 0:
        conn.close()
        return redirect("/cart")  # Out of stock safety

    # 2. Reduce stock by 1
    cur.execute("""
        UPDATE items 
        SET quantity = quantity - 1 
        WHERE name = ?
    """, (name,))

    # 3. Add/update cart
    cur.execute("""
        SELECT quantity FROM cart WHERE name = ?
    """, (name,))
    cart_item = cur.fetchone()

    if cart_item:
        cur.execute("""
            UPDATE cart 
            SET quantity = quantity + 1 
            WHERE name = ?
        """, (name,))
    else:
        cur.execute("""
            INSERT INTO cart (name, price, quantity)
            VALUES (?, ?, 1)
        """, (name, item["price"]))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/increase/<name>")
def increase(name):
    conn = sqlite3.connect("grocery.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Check stock
    cur.execute("SELECT quantity FROM items WHERE name = ?", (name,))
    stock = cur.fetchone()

    if stock and stock["quantity"] > 0:
        cur.execute("UPDATE items SET quantity = quantity - 1 WHERE name = ?", (name,))
        cur.execute("UPDATE cart SET quantity = quantity + 1 WHERE name = ?", (name,))

    conn.commit()
    conn.close()
    return redirect("/cart")

@app.route("/decrease/<name>")
def decrease(name):
    conn = sqlite3.connect("grocery.db")
    cur = conn.cursor()

    # Reduce cart qty
    cur.execute("""
        UPDATE cart
        SET quantity = quantity - 1
        WHERE name = ?
    """, (name,))


    # Restore stock
    cur.execute("""
        UPDATE items 
        SET quantity = quantity + 1 
        WHERE name = ?
    """, (name,))

    # Remove item if qty becomes 0
    cur.execute("""
        DELETE FROM cart WHERE quantity <= 0
    """)

    conn.commit()
    conn.close()
    return redirect("/cart")

@app.route("/remove/<name>")
def remove(name):
    conn = sqlite3.connect("grocery.db")
    cur = conn.cursor()

    cur.execute("SELECT quantity FROM cart WHERE name = ?", (name,))
    qty = cur.fetchone()

    if qty:
        cur.execute("""
            UPDATE items 
            SET quantity = quantity + ? 
            WHERE name = ?
        """, (qty[0], name))

    cur.execute("DELETE FROM cart WHERE name = ?", (name,))
    conn.commit()
    conn.close()

    return redirect("/cart")

@app.route("/cart")
def cart():
    conn = sqlite3.connect("grocery.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch cart table rows
    cur.execute("SELECT * FROM cart")
    rows = cur.fetchall()

    cart_items = []
    total = 0

    for item in rows:
        name = item["name"]
        quantity = item["quantity"]
        price = item["price"]

        # FETCH DISCOUNT FROM ITEMS TABLE
        cur.execute("SELECT discount_percent FROM items WHERE name = ?", (name,))
        d = cur.fetchone()

        discount = d["discount_percent"] if d and d["discount_percent"] else 0

        # CALCULATE DISCOUNTED PRICE
        if discount > 0:
            discounted_price = round(price - (price * discount / 100), 2)
        else:
            discounted_price = price

        subtotal = discounted_price * quantity
        total += subtotal

        cart_items.append({
            "name": name,
            "price": price,                  # original price
            "discount": discount,            # discount percent
            "discounted_price": discounted_price,
            "quantity": quantity,
            "subtotal": subtotal
        })

    conn.close()

    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/checkout")
def checkout():
    conn = sqlite3.connect("grocery.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch cart table items
    cur.execute("SELECT * FROM cart")
    items = cur.fetchall()

    total = sum(item["price"] * item["quantity"] for item in items)

    conn.close()

    return render_template("checkout.html", items=items, total=total)

@app.route("/place-order", methods=["POST"])
def place_order():
    name = request.form["name"]
    phone = request.form["phone"]
    address = request.form["address"]

    # Fetch cart total before clearing it
    conn = sqlite3.connect("grocery.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM cart")
    items = cur.fetchall()

    total = sum(item["price"] * item["quantity"] for item in items)

    # Clear cart
    cur.execute("DELETE FROM cart")
    conn.commit()
    conn.close()

    return render_template("order_success.html", name=name, total=total)

@app.route("/track")
def track():
    return render_template("tracking.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")
        else:
            return render_template(
                "admin_login.html",
                error="Invalid credentials"
            )

    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not admin_required():
        return redirect("/admin/login")

    conn = sqlite3.connect("grocery.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM items")
    items = cur.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        items=items
    )

@app.route("/admin/increase/<name>")
def admin_increase(name):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect("grocery.db")
    cur = conn.cursor()

    cur.execute("""
        UPDATE items
        SET quantity = quantity + 1
        WHERE name = ?
    """, (name,))

    conn.commit()
    conn.close()
    return redirect("/admin/dashboard")


@app.route("/admin/decrease/<name>")
def admin_decrease(name):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect("grocery.db")
    cur = conn.cursor()

    cur.execute("""
        UPDATE items
        SET quantity = quantity - 1
        WHERE name = ? AND quantity > 0
    """, (name,))

    conn.commit()
    conn.close()
    return redirect("/admin/dashboard")


@app.route("/admin/delete/<name>")
def admin_delete(name):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect("grocery.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM items WHERE name = ?", (name,))
    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")

@app.route("/admin/update-discount/<int:id>", methods=["POST"])
def admin_update_discount(id):
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    new_discount = request.form.get("discount", 0)

    conn = sqlite3.connect("grocery.db")
    cur = conn.cursor()

    cur.execute("""
        UPDATE items
        SET discount_percent = ?
        WHERE id = ?
    """, (new_discount, id))

    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin/login")


@app.route('/export')
def export_csv():
    db = get_db()
    rows = db.execute('SELECT * FROM items ORDER BY name').fetchall()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'name', 'category', 'price', 'quantity', 'expiry_date', 'notes', 'created_at'])
    for r in rows:
        cw.writerow([r['id'], r['name'], r['category'], r['price'], r['quantity'], r['expiry_date'], r['notes'], r['created_at']])
    mem = io.BytesIO()
    mem.write(si.getvalue().encode('utf-8'))
    mem.seek(0)
    filename = f'grocery_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=filename)


# -------------------------- Simple CLI for quick tasks --------------------------

def cli_add(args):
    name = args.name
    category = args.category or ''
    price = args.price or 0
    quantity = args.quantity or 0
    expiry = args.expiry or None
    notes = args.notes or None
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT INTO items (name, category, price, quantity, expiry_date, notes) VALUES (?,?,?,?,?,?)',
                 (name, category, price, quantity, expiry, notes))
    conn.commit()
    conn.close()
    print('Added', name)


def cli_list(args):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.execute('SELECT * FROM items ORDER BY name')
    rows = cur.fetchall()
    print(f"{'ID':>3}  {'Name':30} {'Qty':>5} {'Price':>8} {'Expiry':>10}")
    print('-' * 60)
    for r in rows:
        print(f"{r['id']:3}  {r['name'][:30]:30} {r['quantity']:5} {r['price']:8.2f} {r['expiry_date'] or '-':>10}")
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Grocery Management System')
    parser.add_argument('--init-db', action='store_true', help='Initialize the database')
    parser.add_argument('--cli-add', action='store_true', help='Add an item from CLI (use with --name)')
    parser.add_argument('--name', help='Name for CLI add')
    parser.add_argument('--category')
    parser.add_argument('--price', type=float)
    parser.add_argument('--quantity', type=int)
    parser.add_argument('--expiry')
    parser.add_argument('--notes')
    parser.add_argument('--cli-list', action='store_true', help='List items in CLI')
    args = parser.parse_args()

    if args.init_db:
        init_db()
        print('Database initialized at', os.path.abspath(DB_PATH))
        raise SystemExit

    if args.cli_add:
        init_db()
        if not args.name:
            print('Provide --name for --cli-add')
            raise SystemExit(1)
        cli_add(args)
        raise SystemExit

    if args.cli_list:
        init_db()
        cli_list(args)
        raise SystemExit

    # default: run web app
    init_db()
    app.run(debug=True)
