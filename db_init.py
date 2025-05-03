import sqlite3
import json


connection = sqlite3.connect("db.sqlite")
cursor = connection.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS customers(
	id INTEGER PRIMARY KEY,
	name CHAR(64) NOT NULL,
	phone CHAR(10) NOT NULL
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS items(
	id INTEGER PRIMARY KEY,
	name CHAR(64) NOT NULL,
	price REAL NOT NULL
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
	id INTEGER PRIMARY KEY,
	timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	customer_id INT NOT NULL,
    notes TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS item_list(
    order_id NOT NULL,
    item_id NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(item_id) REFERENCES items(id)
);
""")

#ETL process script

#Open and load JSON examples data to 
with open("example_orders.json") as fp:
    order_list = json.load(fp)
    for order in order_list:
        timestamp = order["timestamp"]
        name = order["name"]
        phone = order["phone"]
        item_list = order["items"]
        notes = order["notes"]

        #if customer not already in table
        res = cursor.execute("SELECT * FROM customers WHERE phone=?;", (phone,))
        if (res.fetchone() == None):
            cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?);", (name, phone))

        #orders table ETL
        res = cursor.execute("SELECT * FROM customers WHERE phone=?;", (phone,))
        #want first value of that tuple [0]
        customer_id = res.fetchone()[0]
        cursor.execute("INSERT INTO orders (timestamp, customer_id, notes) VALUES (?, ?, ?);", 
                       (timestamp, customer_id, notes))
        order_id = cursor.lastrowid

        #items table ETL
        for item in item_list:
            item_name = item["name"]
            item_price = item["price"]
            # if item not already in table
            res = cursor.execute("SELECT * FROM items WHERE name=?;", (item_name,))
            if (res.fetchone() == None):
                cursor.execute("INSERT INTO items (name, price) VALUES (?, ?);", (item_name, item_price))

            # make link between order_id and item_id
            res = cursor.execute("SELECT id FROM items WHERE name=?;", (item_name,))
            item_id = res.fetchone()[0]
            cursor.execute("INSERT INTO item_list (order_id, item_id) VALUES (?, ?);", (order_id, item_id))

#ETL process done

#commit & close DB         
connection.commit()
connection.close()


