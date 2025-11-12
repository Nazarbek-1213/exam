import psycopg2
from psycopg2.extras import RealDictCursor
from hi import DB_CONFIG
from datetime import datetime

# Bazaga ulanish
def get_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["Nazarbek"],
        password=DB_CONFIG["Safarov2"]
    )

# Mijoz buyurtma qo'shish
def add_order(customer_name, bread_type, quantity, address, phone, order_time, price):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (customer_name, bread_type, quantity, address, phone, order_time, price)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (customer_name, bread_type, quantity, address, phone, order_time, price))
    conn.commit()
    cursor.close()
    conn.close()

# Bitta mijoz buyurtmasini olish
def get_customer_order(customer_name):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM orders WHERE customer_name=%s ORDER BY order_time ASC", (customer_name,))
    order = cursor.fetchone()
    cursor.close()
    conn.close()
    return order

# Admin uchun barcha buyurtmalarni olish
def get_all_orders():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM orders ORDER BY order_time ASC")
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return orders
