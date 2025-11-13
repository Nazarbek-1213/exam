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


    cur.execute("SELECT COUNT(*) FROM supermarket_balance;")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO supermarket_balance (total_balance) VALUES (0);")

    conn.commit()
    conn.close(       )


def add_product():
    conn = get_connection()
    cur = conn.cursor()
    name = input("Product name: ")
    price = float(input("Price: "))
    qty = int(input("Quantity: "))
    cur.execute("INSERT INTO products (name,price,quantity) VALUES (%s,%s,%s);", (name, price, qty))
    conn.commit()
    conn.close()
    print(" Product added!")


def view_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products;")
    rows = cur.fetchall()
    print("\n--- Product List ---")
    for row in rows:
        print(f"ID:{row[0]} | Name:{row[1]} | Price:{row[2]} | Stock:{row[3]}")
    conn.close()


def edit_product():
    view_products()
    conn = get_connection()
    cur = conn.cursor()
    pid = int(input("Enter product ID to edit: "))
    name = input("New name: ")
    price = float(input("New price: "))
    qty = int(input("New quantity: "))
    cur.execute("UPDATE products SET name=%s, price=%s, quantity=%s WHERE product_id=%s;", (name, price, qty, pid))
    conn.commit()
    conn.close()
    print(" Product updated!")


def remove_product():
    view_products()
    conn = get_connection()
    cur = conn.cursor()
    pid = int(input("Enter product ID to delete: "))
    cur.execute("DELETE FROM products WHERE product_id=%s;", (pid,))
    conn.commit()
    conn.close()
    print(" Product deleted!")



def register_user():
    conn = get_connection()
    cur = conn.cursor()
    username = input("Username: ")
    password = input("Password: ")
    phone = input("Phone: ")
    types = input("Type (client/staff): ").lower()
    balance = float(input("Enter initial balance (for client): ")) if types == "client" else 0
    cur.execute("INSERT INTO persons (username,password,phone,types,balance) VALUES (%s,%s,%s,%s,%s);",
                (username, password, phone, types, balance))
    conn.commit()
    conn.close()
    print(" User registered successfully!")


def login_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM persons WHERE username=%s AND password=%s;", (username, password))
    user = cur.fetchone()
    conn.close()
    return user



def buying(user):
    view_products()
    conn = get_connection()
    cur = conn.cursor()
    pid = int(input("Enter product ID: "))
    qty = int(input("Enter quantity: "))

    cur.execute("SELECT name, price, quantity FROM products WHERE product_id=%s;", (pid,))
    result = cur.fetchone()
    if not result:
        print(" Product not found.")
        conn.close()
        return
    name, price, stock = result
    if qty > stock:
        print("Not enough stock!")
        conn.close()
        return

    total = price * qty
    cur.execute("SELECT balance FROM persons WHERE person_id=%s;", (user[0],))
    balance = cur.fetchone()[0]

    if balance < total:
        print(" Not enough balance!")
        conn.close()
        return


    cur.execute("UPDATE persons SET balance=balance-%s WHERE person_id=%s;", (total, user[0]))

    cur.execute("UPDATE supermarket_balance SET total_balance=total_balance+%s WHERE id=1;", (total,))

    cur.execute("UPDATE products SET quantity=quantity-%s WHERE product_id=%s;", (qty, pid))

    cur.execute("INSERT INTO orders (customer_id, order_date) VALUES (%s,%s) RETURNING order_id;", (user[0], date.today()))
    order_id = cur.fetchone()[0]

    cur.execute("INSERT INTO order_details (order_id, product_id, quantity, total_price) VALUES (%s,%s,%s,%s);",
                (order_id, pid, qty, total))

    cur.execute("INSERT INTO history (person_id, product_name, quantity, total_price, order_date) VALUES (%s,%s,%s,%s,%s);",
                (user[0], name, qty, total, date.today()))

    conn.commit()
    conn.close()
    print(f" Purchase successful! You bought {qty} × {name} for {total}.")

def list_orders():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''SELECT * FROM order_details''')
    data = cur.fetchall()
    if not data:
        print("No orders yet.")
    else:
        print("\n--- All Orders ---")
        for i in data:
            print(f"OrderDetail_ID:{i[0]} | Order_ID:{i[1]} | Product_ID:{i[2]} | Quantity:{i[3]} | Total:{i[4]}")
    conn.close()

def edit_order():
    conn = get_connection()
    cur = conn.cursor()
    list_orders()
    order_detail_id = input("Enter order_detail_id: ")
    new_qty = int(input('New quantity: '))

    cur.execute("SELECT product_id FROM order_details WHERE order_detail_id=%s;", (order_detail_id,))
    product = cur.fetchone()
    if not product:
        print("Order not found!")
        conn.close()
        return

    pid = product[0]
    cur.execute("SELECT price FROM products WHERE product_id=%s;", (pid,))
    price = cur.fetchone()[0]
    new_total = new_qty * price

    cur.execute("UPDATE order_details SET quantity=%s, total_price=%s WHERE order_detail_id=%s;", (new_qty, new_total, order_detail_id))
    conn.commit()
    conn.close()
    print(" Order successfully updated!")

def delete_order():
    conn = get_connection()
    cur = conn.cursor()
    list_orders()
    order_id = input("id: ")
    cur.execute('''delete from order_details where order_id=%s''',(order_id,))
    conn.commit()

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
3. Edit product
4. Remove product
5. View supermarket balance
0. Logout
''')
        choice = input("Choose: ")
        if choice == "1":
            add_product()
        elif choice == "2":
            view_products()
        elif choice == "3":
            edit_product()
        elif choice == "4":
            remove_product()
        elif choice == "5":
            view_market_balance()
        elif choice == "0":
            break


def client_menu(user):
    while True:
        print(f'''
--- CLIENT MENU ({user[1]}) ---
Balance: {user[5]} so'm
1. View products
2. Buy product
3.list_orders
4.edit orders
5.delete orders
6. View purchase history
0. Logout
''')
        choice = input("Choose: ")
        if choice == "1":
            view_products()
        elif choice == "2":
            buying(user)
        elif choice=='3':
            list_orders()
        elif choice=="4":
            edit_order()
        elif choice=='5':
            delete_order()
        elif choice == "6":
            view_history(user)
        elif choice == "0":
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
        option = input("Choose: ")
        if option == "1":
            register_user()
        elif option == "2":
            username = input("Username: ")
            password = input("Password: ")
            user = login_user(username, password)
            if user:
                print(f"Welcome {user[1]} ({user[4]})!")
                if user[4] == "staff":
                    staff_menu()
                else:
                    client_menu(user)
            else:
                print("invalid username or password.")
        elif option == "0":
            print("Goodbye!")
            break

main()
