import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist
from typing import List


class Order(BaseModel):
    order_id : int = 0
    timestamp : str = ''
    customer_id : int
    notes : str
    item_list : conlist(int, min_length=1)

class Item(BaseModel):
    item_id : int = 0
    name : str
    price : float

class Customer(BaseModel):
    customer_id : int = 0
    name : str
    phone : str

app = FastAPI()

###########################################
""" ORDER APIs"""
###########################################

#get order
@app.get("/order/{order_id}")
def get_order(order_id):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    res = cursor.execute("SELECT id, timestamp, customer_id, notes FROM orders WHERE id=?", (order_id,))
    row = res.fetchone()
    order_id = row[0]
    timestamp = row[1]
    customer_id = row[2]
    notes = row[3]

    #get items within orders
    item_list = []
    res = cursor.execute("SELECT item_id FROM item_list WHERE order_id=?;", (order_id,))
    for row in res.fetchall():
        item_list.append(row[0])

    return {
        "order_id" : order_id, 
        "timestamp" : timestamp,
        "customer_id" : customer_id,
        "notes" : notes, 
        "items" : item_list,
    }

#post order
@app.post("/order")
def create_order(order : Order):
    #connect to DB
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    #check for referential integrity (customer_id & item_id)
    res = cursor.execute("SELECT * FROM customers WHERE id=?;", (order.customer_id,))
    if res.fetchone() == None:
        raise HTTPException(404, "customer_id is not in the database")
    for item_id in order.item_list:
        res = cursor.execute("SELECT * FROM items WHERE id=?;", (item_id,))
        if res.fetchone() == None:
            raise HTTPException(404, "item_id is not in the database")

    #insert new order
    cursor.execute("INSERT INTO orders (customer_id, notes) VALUES (?, ?);", (order.customer_id, order.notes))
    order_id = cursor.lastrowid
    #get timestamp
    res = cursor.execute("SELECT timestamp FROM orders WHERE id=?;", (order_id,))
    row = res.fetchone
    timestamp = row[0]
    # add the items to the item_list
    for item_id in order.item_list:
        cursor.execute("INSERT INTO item_list (order_id, item_id) VALUES (?, ?);", (order_id, item_id))
    # commit and close DB
    connection.commit()
    connection.close()
    order.order_id = order_id
    order.timestamp = timestamp
    return order

#put order
@app.put("/order/{order_id}")
def update_order(order : Order, order_id: int):
    #connect to DB
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    #check for referential integrity (customer_id & item_id)
    res = cursor.execute("SELECT * FROM customers WHERE id=?;", (order.customer_id,))
    if res.fetchone() == None:
        raise HTTPException(404, "customer_id is not in the database")
    for item_id in order.item_list:
        res = cursor.execute("SELECT * FROM items WHERE id=?;", (item_id,))
        if res.fetchone() == None:
            raise HTTPException(404, "item_id is not in the database")
   
    #update order
    cursor.execute("UPDATE orders SET notes=?, timestamp=CURRENT_TIMESTAMP WHERE id=?;", (order.notes, order_id))
    #delete existing items from this order
    cursor.execute("DELETE FROM item_list WHERE order_id=?;", (order_id,))
    #add new item(s) to order
    for item_id in order.item_list:
        cursor.execute("INSERT INTO item_list (order_id, item_id) VALUES (?, ?);", (order_id, item_id))
    
    #get timestamp
    res = cursor.execute("SELECT timestamp FROM orders WHERE id=?;", (order.order_id,))
    row = res.fetchone()
    if row:
        timestamp = row[0]
    else:
        raise HTTPException(404, f"Order with id {order_id} not found")
    # commit and close DB
    connection.commit()
    connection.close()
    order.order_id = order_id
    order.timestamp = timestamp
    return order

#delete order
@app.delete("/order/{order_id}")
def delete_order(order_id):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM orders WHERE id=?;", (order_id,))
    if (cursor.rowcount == 0):
        connection.close()
        raise HTTPException(404, "The order you are trying to delete is not found in database")
    connection.commit()
    connection.close() 


###########################################
""" ITEM APIs"""
###########################################

#get item
@app.get("/item/{item_id}")
def get_item(item_id):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    res = cursor.execute("SELECT id, name, price FROM items WHERE id=?;", (item_id,))
    row = res.fetchone()   

    item_id = row[0]
    name = row[1]
    price = row[2]

    return {
        "item_id" : item_id, 
        "name" : name,
        "price" : price
    }

#post item
@app.post("/item")
def create_item(item : Item):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    cursor.execute("INSERT INTO items (name, price) VALUES (?, ?);", (item.name, item.price))
    item_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return {
        "item_id" : item_id,
        "name" : item.name,
        "price" : item.price
    }

#put item
@app.put("/item/{item_id}")
def update_item(item : Item):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    cursor.execute("UPDATE items SET name=?, price=? WHERE id=?;", (item.name, item.price, item.item_id))
    if (cursor.rowcount == 0):
        connection.close()
        raise HTTPException(404, "The item you are trying to update is not found in database")
    connection.commit()
    connection.close()
    return {
        "item_id" : item.item_id,
        "name" : item.name,
        "price" : item.price
    }

#delete item
@app.delete("/item/{item_id}")
def delete_item(item_id):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM items WHERE id=?;", (item_id,))
    if (cursor.rowcount == 0):
        connection.close()
        raise HTTPException(404, "The item you are trying to delete is not found in database")
    connection.commit()
    connection.close() 


###########################################
"""CUSTOMER APIs"""
###########################################

#get customer 
@app.get("/customer/{customer_id}")
def get_customer(customer_id):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    res = cursor.execute("SELECT id, name, phone FROM customers WHERE id=?;", (customer_id,))
    row = res.fetchone()   

    customer_id = row[0]
    name = row[1]
    phone = row[2]

    return {
        "customer_id" : customer_id, 
        "name" : name,
        "phone" : phone
    }

#post customer
@app.post("/customer")
def create_customer(customer : Customer):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?);", (customer.name, customer.phone))
    customer_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return {
        "customer_id" : customer_id,
        "name" : customer.name,
        "phone" : customer.phone
    }

#put customer
@app.put("/customer/{customer_id}")
def update_customer(customer : Customer):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    cursor.execute("UPDATE customers SET name=?, phone=? WHERE id=?;", (customer.name, customer.phone, customer.customer_id))
    if (cursor.rowcount == 0):
        connection.close()
        raise HTTPException(404, "The customer you are trying to update is not found in database")
    connection.commit()
    connection.close()
    return {
        "customer_id" : customer.customer_id,
        "name" : customer.name,
        "phone" : customer.phone
    }

#delete customer
@app.delete("/customer/{customer_id}")
def delete_customer(customer_id):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM customers WHERE id=?;", (customer_id,))
    if (cursor.rowcount == 0):
        connection.close()
        raise HTTPException(404, "The customer you are trying to delete is not found in database")
    connection.commit()
    connection.close()     

