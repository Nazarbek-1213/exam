import psycopg2
from datetime import date


def get_connection():
    return psycopg2.connect(
        dbname="Database_1",
        user="postgres",
        password="Safarov2",
        host="localhost",
        port=5432
    )


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id SERIAL PRIMARY KEY,
            name VARCHAR(50),
            price NUMERIC,
            quantity INT
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS persons (
            person_id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(50),
            phone VARCHAR(20),
            types VARCHAR(20),
            balance NUMERIC DEFAULT 0
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY,
            customer_id INT REFERENCES persons(person_id),
            order_date DATE
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS order_details (
            order_detail_id SERIAL PRIMARY KEY,
            order_id INT REFERENCES orders(order_id),
            product_id INT REFERENCES products(product_id),
            quantity INT,
            total_price NUMERIC
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS supermarket_balance (
            id SERIAL PRIMARY KEY,
            total_balance NUMERIC DEFAULT 0
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS history (
            history_id SERIAL PRIMARY KEY,
            person_id INT REFERENCES persons(person_id),
            product_name VARCHAR(50),
            quantity INT,
            total_price NUMERIC,
            order_date DATE
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS basket (
            basket_id SERIAL PRIMARY KEY,
            person_id INT REFERENCES persons(person_id),
            product_id INT REFERENCES products(product_id),
            quantity INT
        );
    ''')

    cur.execute("SELECT COUNT(*) FROM supermarket_balance;")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO supermarket_balance (total_balance) VALUES (0);")

    conn.commit()
    conn.close()

def add_product():
    conn = get_connection()
    cur = conn.cursor()
    name = input("Product name: ")
    price = float(input("Price: "))
    qty = int(input("Quantity: "))
    cur.execute("INSERT INTO products (name,price,quantity) VALUES (%s,%s,%s);", (name, price, qty))
    conn.commit()
    conn.close()
    print("Product added!")


def view_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products;")
    rows = cur.fetchall()
    print("\n---  Product List ---")
    for row in rows:
        print(f"ID:{row[0]} | Name:{row[1]} | Price:{row[2]} | Stock:{row[3]}")
    conn.close()

def register_user():
    conn = get_connection()
    cur = conn.cursor()
    username = input("Username: ")
    password = input("Password: ")
    phone = input("Phone: ")
    types = input("Type (client/staff): ").lower()
    balance = float(input("Initial balance (for client): ")) if types == "client" else 0
    cur.execute("INSERT INTO persons (username,password,phone,types,balance) VALUES (%s,%s,%s,%s,%s);",
                (username, password, phone, types, balance))
    conn.commit()
    conn.close()
    print(" User registered!")


def login_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM persons WHERE username=%s AND password=%s;", (username, password))
    user = cur.fetchone()
    conn.close()
    return user


def add_to_basket(user):
    view_products()
    conn = get_connection()
    cur = conn.cursor()
    pid = int(input("Enter product ID to add: "))
    qty = int(input("Quantity: "))

    cur.execute("SELECT quantity FROM products WHERE product_id=%s;", (pid,))
    stock = cur.fetchone()
    if not stock or qty > stock[0]:
        print(" Not enough stock.")
        conn.close()
        return

    cur.execute('''
        INSERT INTO basket (person_id, product_id, quantity)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING;
    ''', (user[0], pid, qty))
    conn.commit()
    conn.close()
    print(" Added to basket!")


def view_basket(user):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT b.basket_id, p.name, p.price, b.quantity, (p.price * b.quantity)
        FROM basket b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.person_id=%s;
    ''', (user[0],))
    rows = cur.fetchall()
    if not rows:
        print("Basket is empty.")
    else:
        print("\n--- Your Basket ---")
        total = 0
        for r in rows:
            print(f"ID:{r[0]} | {r[1]} × {r[3]} | Price: {r[2]} | Total: {r[4]}")
            total += r[4]
        print(f"Total amount: {total}")
    conn.close()


def edit_basket(user):
    view_basket(user)
    conn = get_connection()
    cur = conn.cursor()
    bid = int(input("Basket ID to edit: "))
    new_qty = int(input("New quantity: "))
    cur.execute("UPDATE basket SET quantity=%s WHERE basket_id=%s AND person_id=%s;", (new_qty, bid, user[0]))
    conn.commit()
    conn.close()
    print(" Basket updated!")


def delete_from_basket(user):
    view_basket(user)
    conn = get_connection()
    cur = conn.cursor()
    bid = int(input("Basket ID to delete: "))
    cur.execute("DELETE FROM basket WHERE basket_id=%s AND person_id=%s;", (bid, user[0]))
    conn.commit()
    conn.close()
    print(" Item removed from basket!")


def purchase_basket(user):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
        SELECT b.product_id, b.quantity, p.price, p.name
        FROM basket b
        JOIN products p ON b.product_id = p.product_id
        WHERE b.person_id=%s;
    ''', (user[0],))
    items = cur.fetchall()

    if not items:
        print(" Basket is empty.")
        conn.close()
        return

    total_sum = sum(i[1] * i[2] for i in items)
    cur.execute("SELECT balance FROM persons WHERE person_id=%s;", (user[0],))
    balance = cur.fetchone()[0]

    if balance < total_sum:
        print(" Not enough balance!")
        conn.close()
        return

    cur.execute("INSERT INTO orders (customer_id, order_date) VALUES (%s, %s) RETURNING order_id;", (user[0], date.today()))
    order_id = cur.fetchone()[0]

    for pid, qty, price, name in items:
        total = qty * price
        cur.execute("INSERT INTO order_details (order_id, product_id, quantity, total_price) VALUES (%s,%s,%s,%s);",
                    (order_id, pid, qty, total))
        cur.execute("UPDATE products SET quantity=quantity-%s WHERE product_id=%s;", (qty, pid))
        cur.execute("INSERT INTO history (person_id, product_name, quantity, total_price, order_date) VALUES (%s,%s,%s,%s,%s);",
                    (user[0], name, qty, total, date.today()))

    cur.execute("UPDATE persons SET balance=balance-%s WHERE person_id=%s;", (total_sum, user[0]))
    cur.execute("UPDATE supermarket_balance SET total_balance=total_balance+%s WHERE id=1;", (total_sum,))
    cur.execute("DELETE FROM basket WHERE person_id=%s;", (user[0],))

    conn.commit()
    conn.close()
    print(f" Purchase successful! You spent {total_sum} so'm.")

def view_history(user):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_name, quantity, total_price, order_date FROM history WHERE person_id=%s;", (user[0],))
    rows = cur.fetchall()
    if not rows:
        print("No purchases yet.")
    else:
        print("\n--- Purchase History ---")
        for row in rows:
            print(f"{row[3]} | {row[0]} ×{row[1]} | {row[2]} so'm")
    conn.close()


def view_market_balance():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT total_balance FROM supermarket_balance WHERE id=1;")
    total = cur.fetchone()[0]
    conn.close()
    print(f" Supermarket balance: {total} so'm")


def staff_menu():
    while True:
        print('''
--- STAFF MENU ---
1. Add product
2. View products
3. View supermarket balance
0. Logout
''')
        c = input("Choose: ")
        if c == "1":
            add_product()
        elif c == "2":
            view_products()
        elif c == "3":
            view_market_balance()
        elif c == "0":
            break


def client_menu(user):
    while True:
        print(f'''
--- CLIENT MENU ({user[1]}) ---
Balance: {user[5]} so'm
1. View products
2. Add to basket
3. View basket
4. Edit basket
5. Delete from basket
6. Purchase basket
7. View purchase history
0. Logout
''')
        c = input("Choose: ")
        if c == "1":
            view_products()
        elif c == "2":
            add_to_basket(user)
        elif c == "3":
            view_basket(user)
        elif c == "4":
            edit_basket(user)
        elif c == "5":
            delete_from_basket(user)
        elif c == "6":
            purchase_basket(user)
        elif c == "7":
            view_history(user)
        elif c == "0":
            break

def main():
    create_tables()
    print("Tables ready.")

    while True:
        print('''
====== MAIN MENU ======
1. Register
2. Login
0. Exit
''')
        opt = input("Choose: ")
        if opt == "1":
            register_user()
        elif opt == "2":
            u = input("Username: ")
            p = input("Password: ")
            user = login_user(u, p)
            if user:
                print(f"Welcome {user[1]} ({user[4]})!")
                if user[4] == "staff":
                    staff_menu()
                else:
                    client_menu(user)
            else:
                print(" Invalid credentials.")
        elif opt == "0":
            print("Goodbye!")
            break
main()
