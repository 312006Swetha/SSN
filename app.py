import time
from flask import Flask, flash, render_template, request ,redirect,session, jsonify,url_for
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import logging
from flask import Flask, render_template, Response
from datetime import timedelta
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from io import BytesIO
from twilio.rest import Client  # Twilio import
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import datetime as dt
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import re
import sqlite3
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import pytz
import math
from flask import Flask, render_template, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from transformers import pipeline
from xhtml2pdf import pisa
import io 
import math
from fpdf import FPDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask import make_response
from reportlab.lib import colors
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.ticker as ticker
from matplotlib.ticker import FuncFormatter
from transformers import BartForConditionalGeneration, BartTokenizer
from reportlab.lib import colors as reportlab_colors
from reportlab.platypus import Image as PlatypusImage
from PIL import Image as PILImage  # Importing PIL Image with a new name
from reportlab.platypus import Image as ReportlabImage
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from collections import defaultdict
from datetime import datetime
from flask import Flask
from flask_apscheduler import APScheduler
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from flask_apscheduler import APScheduler


app = Flask(__name__)



def import_excel_to_db():                          #inventory.db
    conn = sqlite3.connect('inventory.db')  # Connect to the database
    cursor = conn.cursor()
    
    # Create table if it does not exist, adding the supplier column
    cursor.execute('''  
        CREATE TABLE IF NOT EXISTS inventory (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT UNIQUE,  
            quantity INTEGER,
            threshold INTEGER,
            price REAL,
            supplier TEXT,  -- New supplier column
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # Check if the inventory table is empty
    cursor.execute('SELECT COUNT(*) FROM inventory')
    count = cursor.fetchone()[0]
    
    if count == 0:  # Import data only if the table is empty
        df = pd.read_excel('medi - Copy.xlsx')  # Replace with your actual file path
        
        for index, row in df.iterrows():
            # Insert new item if the table is empty
            cursor.execute(''' 
                INSERT INTO inventory (item_name, quantity, threshold, price, supplier)
                VALUES (?, ?, ?, ?, ?)
            ''', (row['Item'], row['Quantity'], row['Threshold'], row['Price'], row['Supplier']))
    
    # Commit and close connection
    conn.commit()
    conn.close()



def get_ist_timestamp():                                          #supplier.db
    """Return the current timestamp in Indian Standard Time (IST)."""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

# Step 1: Import Excel data into supplier.db
def import_excel_to_supplier_db():
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('supplier.db')
    cursor = conn.cursor()

    # Drop the existing supplier table if it exists
    cursor.execute("DROP TABLE IF EXISTS supplier")
    
    # Create the 'supplier' table
    cursor.execute('''  
        CREATE TABLE IF NOT EXISTS supplier (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT,  
            item_name TEXT UNIQUE,  
            supplier_quantity INTEGER,
            supplier_threshold INTEGER,
            supplier_number TEXT,
            per_price REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # Drop the trigger if it exists
    cursor.execute("DROP TRIGGER IF EXISTS auto_restock")
    
    # Create a trigger to auto-restock when the quantity is below the threshold
    cursor.execute(''' 
        CREATE TRIGGER auto_restock
        AFTER UPDATE OF supplier_quantity ON supplier
        WHEN NEW.supplier_quantity < NEW.supplier_threshold
        BEGIN
            UPDATE supplier
            SET supplier_quantity = supplier_quantity + 100,  -- Increment current value by 100
                last_updated = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
            WHERE item_id = NEW.item_id;
        END;
    ''')
    
    # Read data from the Excel file
    try:
        df = pd.read_excel('Book31.xlsx')  # Ensure Book1.xlsx is in the same directory
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Print the column names to ensure they match
    print("Columns in the Excel file:", df.columns)
    
    # Clean column names by stripping any extra spaces
    df.columns = df.columns.str.strip()
    
    # Required columns for the supplier table
    required_columns = ['supplier_name', 'item_name', 'supplier_quantity', 'supplier_threshold', 'supplier_number', 'per_price']
    for col in required_columns:
        if col not in df.columns:
            print(f"Error: Column '{col}' not found in the Excel file.")
            return

    # Insert each row from the DataFrame into the supplier table
    for index, row in df.iterrows():
        try:
            cursor.execute(''' 
                INSERT INTO supplier (supplier_name, item_name, supplier_quantity, supplier_threshold, supplier_number, per_price, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (row['supplier_name'], row['item_name'], row['supplier_quantity'], row['supplier_threshold'], row['supplier_number'], row['per_price'], get_ist_timestamp()))
        except Exception as e:
            print(f"Error inserting row {index + 1}: {e}")
            continue

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    print("Data imported successfully and trigger created.")


import_excel_to_supplier_db()

def get_db_connection():                     #order table              
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn



def create_orders_table():
    try:
        conn = sqlite3.connect('inventory.db')  # Use the same database as your inventory
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                order_sales INTEGER,
                order_date TEXT,
                total_price REAL,
                price REAL,
                order_time TEXT,
                username TEXT,
                item_id INTEGER,
                FOREIGN KEY (item_id) REFERENCES inventory(item_id)
            );
        ''')
        conn.commit()
        conn.close()
        print("Orders table created successfully!")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

# Call the function to create the orders table when the app starts
create_orders_table()


# Create 'predictions' table if it doesn't exist
def create_predictions_table():                                    #predict.db
    # Connect to the database where predictions will be stored
    predict_conn = sqlite3.connect('predict.db')
    predict_cursor = predict_conn.cursor()

    # Create the 'predictions' table
    predict_cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        predict_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        item_name TEXT,
        predicted_sales INTEGER,
        record_updated TEXT,
        FOREIGN KEY (item_id) REFERENCES inventory(item_id)
    );
    """)

    # Commit the changes and close the connection
    predict_conn.commit()
    predict_conn.close()

# Call the function to create the table when the app starts
create_predictions_table()


#report 

def generate_summary(inventory_data):
    low_stock_items = inventory_data[inventory_data['Status'] == "Low Stock"]
    close_to_threshold_items = inventory_data[inventory_data['Status'] == "Close to Threshold"]
    sufficient_items = inventory_data[inventory_data['Status'] == "Sufficient"]

    total_items = len(inventory_data)
    low_stock_count = len(low_stock_items)
    close_to_threshold_count = len(close_to_threshold_items)
    sufficient_count = len(sufficient_items)

    # Summarize the inventory
    summary = (
        f"The inventory contains {total_items} items in total. "
        f"Among these, {low_stock_count} items are in low stock, "
        f"{close_to_threshold_count} items are close to their threshold, "
        f"and {sufficient_count} items have sufficient stock levels. "
    )

    # Add low stock items to the summary
    if low_stock_count > 0:
        low_stock_list = ", ".join(low_stock_items['item_name'].tolist())
        summary += f"The items in low stock include: {low_stock_list}. "

    # Add close to threshold items to the summary
    if close_to_threshold_count > 0:
        close_to_threshold_list = ", ".join(close_to_threshold_items['item_name'].tolist())
        summary += f"The items close to threshold include: {close_to_threshold_list}. "

    # Add information about orders placed
    if 'Supplier_Name' in inventory_data.columns:
        orders = inventory_data[inventory_data['Status'].isin(["Low Stock", "Close to Threshold"])]
        if not orders.empty:
            order_details = "; ".join(
                f"{row['item_name']} (Supplier: {row['Supplier_Name']})"
                for _, row in orders.iterrows()
            )
            summary += f"Orders have been placed for the following items: {order_details}. "


    summary += "Monitoring these items ensures efficient inventory management and timely replenishment."
    bart_summary = summarizer(summary, max_length=130, min_length=30, do_sample=False)
    return bart_summary[0]['summary_text']



def fetch_supplier_info(item_name):
    """Fetch supplier information for a given item name from supplier.db."""
    conn = sqlite3.connect('supplier.db')
    cursor = conn.cursor()
    query = "SELECT supplier_name FROM supplier WHERE item_name = ?"
    cursor.execute(query, (item_name,))
    supplier = cursor.fetchone()
    conn.close()
    return supplier[0] if supplier else "Unknown Supplier"


def fetch_predicted_sales():
                              #predict.db' database
    conn = sqlite3.connect('predict.db')
    cursor = conn.cursor()

    # Query to fetch item names and their predicted sales
    cursor.execute("SELECT item_name, predicted_sales FROM predictions")
    
    # Fetch all rows
    predicted_sales_data = cursor.fetchall()

    # Close the database connection
    conn.close()

    return predicted_sales_data

def fetch_actual_sales():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()

    cursor.execute("SELECT item_name, SUM(order_sales) AS actual_sales FROM orders GROUP BY item_name")
    actual_sales_data = cursor.fetchall()

    conn.close()
    return actual_sales_data
                                 
def restock_items():                      #update spplier to inventory 1 day
    # Connect to the SQLite databases
    inventory_conn = sqlite3.connect('inventory.db')
    supplier_conn = sqlite3.connect('supplier.db')
    predict_conn = sqlite3.connect('predict.db')

    inventory_cursor = inventory_conn.cursor()
    supplier_cursor = supplier_conn.cursor()
    predict_cursor = predict_conn.cursor()

    # Current time for comparison
    current_time = datetime.now()

    # Get items in the inventory where quantity is below the threshold
    inventory_cursor.execute(''' 
        SELECT item_name, quantity, threshold, last_updated FROM inventory 
        WHERE quantity <= threshold;
    ''')
    low_stock_items = inventory_cursor.fetchall()

    if not low_stock_items:
        print("No items require restocking.")
        inventory_conn.close()
        supplier_conn.close()
        predict_conn.close()
        return

    for item in low_stock_items:
        item_name, quantity, threshold, last_updated = item
        last_updated = datetime.strptime(last_updated, '%Y-%m-%d %H:%M:%S')

        # Check if at least one day has passed since the last update in inventory
        if (current_time - last_updated).days < 1:
            print(f"Restock for item '{item_name}' skipped as it was updated less than a day ago.")
            continue

        # Fetch the predicted sales for the item from predict.db
        predict_cursor.execute(''' 
            SELECT predicted_sales FROM predictions WHERE item_name = ?; 
        ''', (item_name,))
        predicted_data = predict_cursor.fetchone()

        if not predicted_data:
            print(f"No prediction found for item '{item_name}'. Skipping restock.")
            continue

        predicted_sales = predicted_data[0]

        # Check if the supplier has enough stock for the predicted quantity
        supplier_cursor.execute(''' 
            SELECT supplier_quantity FROM supplier WHERE item_name = ?; 
        ''', (item_name,))
        supplier_data = supplier_cursor.fetchone()

        if not supplier_data:
            print(f"No supplier data found for item '{item_name}'. Skipping restock.")
            continue

        supplier_quantity = supplier_data[0]

        # Determine the number of units to restock
        units_to_add = min(predicted_sales, supplier_quantity)

        if units_to_add > 0:
            # Deduct the restocked amount from the supplier's stock and update supplier_last_updated
            supplier_cursor.execute(''' 
                UPDATE supplier 
                SET supplier_quantity = supplier_quantity - ?, last_updated = ? 
                WHERE item_name = ?; 
            ''', (units_to_add, current_time.strftime('%Y-%m-%d %H:%M:%S'), item_name))

            # Commit supplier changes to ensure updates are saved
            supplier_conn.commit()

            # Add the restocked amount to the inventory
            inventory_cursor.execute(''' 
                UPDATE inventory 
                SET quantity = quantity + ?, last_updated = ? 
                WHERE item_name = ?; 
            ''', (units_to_add, current_time.strftime('%Y-%m-%d %H:%M:%S'), item_name))

            # Commit inventory changes to ensure updates are saved
            inventory_conn.commit()

            print(f"Restocked {units_to_add} units of item '{item_name}'.")
            print(f"New inventory quantity: {quantity + units_to_add}, Remaining supplier stock: {supplier_quantity - units_to_add}.")
        else:
            print(f"Insufficient supplier stock for item '{item_name}' (Required: {predicted_sales}, Available: {supplier_quantity}).")

    # Commit changes and close the connections
    inventory_conn.close()
    supplier_conn.close()
    predict_conn.close()

# Call the function to manage restocking
restock_items()

# Run the function whe
app.secret_key = "your_secret_key"  # Make sure to use a more secure secret key in production

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Initialize the BART model and tokenizer
tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')



summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

DATABASE_PATH = 'inventory.db'
engine = create_engine(f'sqlite:///{DATABASE_PATH}')

  # Ensure the path to the file is correct
df = pd.read_excel('medi.xlsx')  

logging.basicConfig(level=logging.DEBUG)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phonenumber = db.Column(db.String(15), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')  # Add a role column, default to 'user'



def get_inventory():                         #index3
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory')
    inventory = cursor.fetchall()
    conn.close()
    return inventory


# Step 1: Fetch data from the existing inventory.db                      #notify
def fetch_data_from_db():
    conn = sqlite3.connect('inventory.db')  # Connect to your existing inventory.db
    cursor = conn.cursor()

    try:
        # Query to fetch data from the inventory table with the correct column names
        cursor.execute("SELECT item_name, quantity, threshold FROM inventory")
        rows = cursor.fetchall()  # Fetch all rows

        # Transform rows into a list of dictionaries
        data = [{'Item': row[0], 'Quantity': row[1], 'Threshold': row[2]} for row in rows]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        data = []
    finally:
        conn.close()  # Always close the connection

    return data



# Fetch inventory data function
def fetch_inventory_data():            #index4
    conn = sqlite3.connect('inventory.db')
    query = """
    SELECT item_id, item_name, quantity, threshold, price 
    FROM inventory
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_items_close_to_threshold():                            
    connection = sqlite3.connect('inventory.db')
    cursor = connection.cursor()

    query = """
    SELECT item_name, quantity, threshold
    FROM inventory
    WHERE quantity <= threshold + 5  -- Close to threshold, within a buffer of 5
    """
    cursor.execute(query)
    items = cursor.fetchall()

    connection.close()

    return [
        {"Item": item[0], "Quantity": item[1], "Threshold": item[2]}
        for item in items
    ]



# Function for handling low stock notifications
def handle_low_stock_notifications():
    conn_inventory = sqlite3.connect('inventory.db')
    cursor_inventory = conn_inventory.cursor()

    low_stock_notifications = []

    cursor_inventory.execute('SELECT item_name, quantity, threshold FROM inventory')
    items = cursor_inventory.fetchall()

    for item in items:
        item_name, quantity, threshold = item
        if quantity < threshold:
            low_stock_notification = f"Low stock alert: {item_name} is below the threshold. Please restock!"
            low_stock_notifications.append(low_stock_notification)
            

    conn_inventory.close()
    return low_stock_notifications

def handle_order_notifications():
    now = datetime.now()
    conn_inventory = sqlite3.connect('inventory.db')
    cursor_inventory = conn_inventory.cursor()

    conn_supplier = sqlite3.connect('supplier.db')
    cursor_supplier = conn_supplier.cursor()

    order_notifications = []

    # Get items that are close to the threshold (orange color) or below the threshold (red color)
    cursor_inventory.execute('SELECT item_name, quantity, threshold FROM inventory')
    items = cursor_inventory.fetchall()

    for item in items:
        item_name, quantity, threshold = item

        # Include both orange (close to threshold) and red (low stock) items
        if quantity <= threshold + 5:  
            # Check if it's been a day since last update
            cursor_inventory.execute('SELECT last_updated FROM inventory WHERE item_name = ?', (item_name,))
            last_updated = cursor_inventory.fetchone()[0]
            last_updated = datetime.strptime(last_updated, '%Y-%m-%d %H:%M:%S')

            if (now - last_updated) >= timedelta():  # If it's been a day
                # Fetch supplier details
                cursor_supplier.execute('SELECT supplier_name FROM supplier WHERE item_name = ?', (item_name,))
                supplier_name = cursor_supplier.fetchone()

                if supplier_name:
                    supplier_name = supplier_name[0]
                    status = "low stock" if quantity <= threshold else "close to threshold"
                    order_notifications.append(f"Placed order to {supplier_name} for {item_name} ({status}).")

    conn_inventory.close()
    conn_supplier.close()

    return order_notifications

def handle_restock_notifications():
    now = datetime.now()

    try:
        # Connect to databases
        conn_inventory = sqlite3.connect('inventory.db')
        cursor_inventory = conn_inventory.cursor()

        conn_supplier = sqlite3.connect('supplier.db')
        cursor_supplier = conn_supplier.cursor()

        conn_predict = sqlite3.connect('predict.db')
        cursor_predict = conn_predict.cursor()

        restock_notifications = []

        # Fetch items from inventory
        cursor_inventory.execute('SELECT item_name, quantity, threshold, last_updated FROM inventory')
        items = cursor_inventory.fetchall()

        for item in items:
            item_name, quantity, threshold, last_updated = item

            # Fetch supplier data
            cursor_supplier.execute('SELECT supplier_quantity, supplier_name FROM supplier WHERE item_name = ?', (item_name,))
            supplier_data = cursor_supplier.fetchone()

            if supplier_data:
                supplier_quantity, supplier_name = supplier_data

                # Fetch predicted restock quantity
                cursor_predict.execute('SELECT predicted_sales FROM predictions WHERE item_name = ?', (item_name,))
                predicted_data = cursor_predict.fetchone()

                # Debugging prints
                print(f"Processing {item_name}:")
                print(f"  - Supplier Stock: {supplier_quantity}")
                print(f"  - Current Inventory: {quantity}")
                print(f"  - Threshold: {threshold}")
                print(f"  - Predicted Sales: {predicted_data}")

                if predicted_data and predicted_data[0] is not None:
                    restock_quantity = predicted_data[0]

                    if supplier_quantity >= restock_quantity:  # Supplier has enough stock
                        cursor_inventory.execute(
                            'UPDATE inventory SET quantity = quantity + ?, last_updated = ? WHERE item_name = ?',
                            (restock_quantity, now.strftime('%Y-%m-%d %H:%M:%S'), item_name)
                        )
                        cursor_supplier.execute(
                            'UPDATE supplier SET supplier_quantity = supplier_quantity - ? WHERE item_name = ?',
                            (restock_quantity, item_name)
                        )
                        restock_notification = f"{item_name} has been restocked with {restock_quantity} units from {supplier_name}."
                        restock_notifications.append(restock_notification)
                        
                    else:
                        restock_notification = f"Not enough stock from {supplier_name} for {item_name}. Only {supplier_quantity} units available."
                        restock_notifications.append(restock_notification)
                        
                else:
                    print(f"  - Skipping {item_name}: No valid prediction data.")

        # Commit changes
        conn_inventory.commit()
        conn_supplier.commit()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Ensure all connections are closed
        conn_inventory.close()
        conn_supplier.close()
        conn_predict.close()

    if not restock_notifications:
        print("No restock notifications at the moment!")  # Debugging
    return restock_notifications


# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rsrrgy06@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'fuhp xhld ufuq fcjv'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'rsrrgy06@gmail.com'  # Replace with your email

mail = Mail(app)

# Flask-APScheduler Configuration
class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "Asia/Kolkata"  # Adjust this timezone to IST

app.config.from_object(Config)
scheduler = APScheduler()  # Use APScheduler from flask_apscheduler
scheduler.init_app(app)  # Initialize the scheduler with Flask app
scheduler.start()  # Start the scheduler
# Example report file path
REPORT_FILE_PATH = "temp/inventory_report.pdf"  # Ensure this file exists for testing

# Function to log current time for time zone check
def print_current_time():
    tz = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(tz)
    print(f"Current time (Asia/Kolkata): {current_time}")

# Define the email sending function with an attachment
def send_weekly_email():
    with app.app_context():  # Ensure we are within the Flask app context
        recipient_email = "rsrrgy06@gmail.com"  # Replace with the recipient's email
        subject = "Weekly Update"
        message = "This is your weekly static message with the report attached!"

        try:
            msg = Message(subject=subject, recipients=[recipient_email], body=message)
            
            # Attach the report file
            with app.open_resource(REPORT_FILE_PATH) as report:
                msg.attach("inventory_report.pdf", "application/pdf", report.read())
            
            mail.send(msg)
            print(f"Email sent to {recipient_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")
            print(f"Error details: {str(e)}")

# Schedule the email job to run every Friday at 6:30 PM IST
@scheduler.task("cron", id="weekly_email_job", day_of_week="Tue", hour=21, minute=28)
def scheduled_email_job():
    print("Scheduled job started.")  # Log to verify it's triggered
    send_weekly_email()


def should_update_prices():
    """Check if prices were updated this month."""
    conn = sqlite3.connect('price_update_log.db')
    conn.execute("CREATE TABLE IF NOT EXISTS update_log (last_update TEXT)")
    cursor = conn.cursor()
    
    cursor.execute("SELECT last_update FROM update_log ORDER BY ROWID DESC LIMIT 1")
    last_update = cursor.fetchone()
    today = datetime.now().date()
    
    if last_update:
        last_update_date = datetime.strptime(last_update[0], "%Y-%m-%d").date()
        # Check if it's still the same month
        if last_update_date.year == today.year and last_update_date.month == today.month:
            return False  # Prices have already been updated this month

    cursor.execute("DELETE FROM update_log")  # Clear old entries
    cursor.execute("INSERT INTO update_log (last_update) VALUES (?)", (today,))
    conn.commit()
    conn.close()
    return True


# Function to connect to the SQLite database
def connect_db():
    db_path = "inventory.db"
    if not os.path.exists(db_path):
        print("Error: Database file 'inventory.db' not found!")
        return None
    try:
        conn = sqlite3.connect(db_path)
        print("Database connected successfully")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

# Function to handle user queries
def handle_query(user_message):
    conn = connect_db()
    if conn is None:
        return "Error: Unable to connect to the database."

    try:
        cursor = conn.cursor()
        user_message = user_message.lower().strip()
        print(f"User message: {user_message}")

        # Greeting responses
        if user_message in ["hi", "hello", "hey", "greetings"]:
            return "Hello! How can I assist you with inventory or orders today?"

        # Query for stock/availability of an item
        elif any(phrase in user_message for phrase in ["stock of", "inventory of", "availability of"]):
            item_name = user_message.split("of")[-1].strip()
            if not item_name:
                return "Please specify an item name, e.g., 'stock of rice'."
            
            query = "SELECT item_name, quantity FROM inventory WHERE item_name LIKE ?"
            cursor.execute(query, (f"%{item_name}%",))
            result = cursor.fetchone()

            return f"The stock for '{result[0]}' is {result[1]} units." if result else f"Sorry, no stock information found for '{item_name}'."

        # Query for low stock items
        elif any(phrase in user_message for phrase in ["low stock", "stock shortage", "items running out"]):
            query = "SELECT item_name, quantity, threshold FROM inventory WHERE quantity <= threshold"
            cursor.execute(query)
            results = cursor.fetchall()

            return "The following items are low in stock:\n" + "\n".join(
                f"- {item[0]}: {item[1]} units (Threshold: {item[2]} units)" for item in results
            ) if results else "All items are sufficiently stocked."

        # Query for total orders of a specific item
        elif any(phrase in user_message for phrase in ["total orders of", "orders for", "orders of"]):
            item_name = user_message.split("of")[-1].strip()
            if not item_name:
                return "Please specify an item, e.g., 'total orders of rice'."

            query = "SELECT SUM(order_sales) FROM orders WHERE item_name LIKE ?"
            cursor.execute(query, (f"%{item_name}%",))
            total_orders = cursor.fetchone()[0]

            return f"The total number of orders for '{item_name}' is {total_orders}." if total_orders else f"No orders found for '{item_name}'."

        # Query for total orders
        elif any(phrase in user_message for phrase in ["total orders", "overall orders"]):
            query = "SELECT SUM(order_sales) FROM orders"
            cursor.execute(query)
            total_orders = cursor.fetchone()[0]
            return f"The total number of orders placed is {total_orders}."

        # Query for who ordered a specific item
        elif "who ordered" in user_message:
            item_name = user_message.split("who ordered")[-1].strip()
            if not item_name:
                return "Please specify the item, e.g., 'Who ordered rice?'."

            query = """
                SELECT o.username, o.order_sales, o.order_date, o.order_time
                FROM orders o
                INNER JOIN inventory i ON o.item_id = i.item_id
                WHERE i.item_name LIKE ?
            """
            cursor.execute(query, (f"%{item_name}%",))
            results = cursor.fetchall()

            return f"Users who ordered '{item_name}':\n" + "\n".join(
                f"- {row[0]} ordered {row[1]} units on {row[2]} at {row[3]}." for row in results
            ) if results else f"No users have ordered '{item_name}'."

        # Query for item details
        elif "details about" in user_message:
            item_name = user_message.split("details about")[-1].strip()
            if not item_name:
                return "Please specify the item name you are looking for."

            query = """
                SELECT i.item_name, i.quantity, i.price, i.last_updated, o.order_sales, o.order_date, o.order_time, o.username
                FROM inventory i
                LEFT JOIN orders o ON i.item_id = o.item_id
                WHERE i.item_name LIKE ?
            """
            cursor.execute(query, (f"%{item_name}%",))
            results = cursor.fetchall()

            if results:
                response = f"Details about '{item_name}':\n"
                response += f"  - Quantity in stock: {results[0][1]} units\n  - Price: ${results[0][2]:.2f}\n  - Last Updated: {results[0][3]}\n"

                order_details = "Order details:\n"
                for row in results:
                    if row[4]:
                        order_details += f"  - Ordered by {row[7]}: {row[4]} units on {row[5]} at {row[6]}\n"
                
                response += order_details if "Ordered by" in order_details else "\n  - No users have ordered this item yet."
                return response.strip()

            else:
                return f"No details found for '{item_name}'."

        else:
            return "Sorry, I didn't understand your query. Please try again."

    except Exception as e:
        print(f"⚠️ DEBUG ERROR: {e}")  # Prints the actual error
        return f"Error: {e}"  # Shows error message in chatbot

    finally:
        conn.close()

# Function to generate chatbot responses based on user messages
def chatbot_response(user_message):
    return handle_query(user_message)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error_message = None  # Initialize error_message variable
    password_message = None  # Initialize password error message
    phone_message = None  # Initialize phone number error message

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phonenumber = request.form['phonenumber']

        # Phone number validation: Starts with 7, 8, or 9 and is exactly 10 digits
        if not re.match(r'^[789]\d{9}$', phonenumber):
            phone_message = "Enter a valid number."

        # Check if the username already exists
        elif User.query.filter_by(username=username).first():
            error_message = "Username already exists! Please choose another."

        role = 'owner' if username.lower() == 'admin@123' else 'user'  # Admin becomes owner


        # If no errors, save the user to the database
        if not error_message and not password_message and not phone_message:
            new_user = User(username=username, password=password, phonenumber=phonenumber,role=role)

            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))  # Redirect to login page after successful signup

    return render_template('signup_alt.html', error_message=error_message, password_message=password_message, phone_message=phone_message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None  # Initialize error_message variable

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate user credentials
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user'] = user.username  # Store the username in session
            session['role'] = user.role  # Store the role in session
            if user.role == 'owner':
                return redirect(url_for('index1'))
            else:
                return redirect(url_for('customer'))  # Redirect to home after successful login
        else:
            error_message = "Invalid username or password! Please try again."  # Error message on invalid login

    return render_template('login_alt.html', error_message=error_message)  # Pass error_message to the template


# Route: Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))  # Redirect to homepage after logout

  # Render homepage if not logged in
@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')


@app.route('/')
def index1():
    if 'user' in session and session['role'] == 'owner':
        return render_template("index1.html")
    return redirect(url_for('home'))

@app.route('/index2')
def index2():
    # Connect to the databases
    conn_supplier = sqlite3.connect('supplier.db')  # Supplier database
    conn_predictions = sqlite3.connect('predict.db')  # Predictions database
    conn_inventory = sqlite3.connect('inventory.db')  # Inventory database

    cursor_supplier = conn_supplier.cursor()
    cursor_predictions = conn_predictions.cursor()
    cursor_inventory = conn_inventory.cursor()

    # Fetch data from supplier, predictions, and inventory tables
    cursor_supplier.execute('''SELECT s.item_id, s.per_price 
                                FROM supplier s''')
    supplier_data = cursor_supplier.fetchall()

    cursor_predictions.execute('''SELECT p.item_id, p.predicted_sales 
                                  FROM predictions p''')
    predictions_data = cursor_predictions.fetchall()

    cursor_inventory.execute('''SELECT i.item_id, i.item_name 
                                FROM inventory i''')
    inventory_data = cursor_inventory.fetchall()

    conn_supplier.close()
    conn_predictions.close()
    conn_inventory.close()

    # Merge data (assuming item_ids match across tables)
    merged_data = []
    for item_id, per_price in supplier_data:
        predicted_sales = next((ps for id, ps in predictions_data if id == item_id), 0)
        item_name = next((name for id, name in inventory_data if id == item_id), "Unknown Item")
        merged_data.append((item_id, item_name, per_price, predicted_sales))

    # Prepare data for graph
    item_names = [row[1] for row in merged_data]  # Item Names
    per_prices = [row[2] for row in merged_data]  # Supplier price per item
    predicted_sales = [row[3] for row in merged_data]  # Predicted sales

    # Calculate total money needed for next week
    money_needed = [predicted_sales[i] * per_prices[i] for i in range(len(per_prices))]
    total_cost = sum(money_needed)

    # Create the Plotly bar chart
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=item_names,
        y=money_needed,
        marker=dict(
             color=money_needed,  # Gradient color based on money_needed
        colorscale='Viridis',  # Gradient color scale
        line=dict(color='rgb(0,0,0)', width=1.5),  # Bar border
        colorbar=dict(
            title="Amount (₹)",  # Title for the color bar
            titleside="right",
            ticks="outside",
            ticklen=5,
            tickcolor='black',
            tickfont=dict(size=12, color='black'),
        ),
        ),
        name='Money Needed',
    ))

    # Add annotation for the total cost
    fig1.add_annotation(
        text=f"Total Money Needed: ₹{total_cost:,.2f}",
        x=0.95, y=1.1,  # Position at the top-right corner
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=18, color='white'),
        align="center",
        bgcolor='rgb(34, 139, 34)',  # Green background for total cost
        bordercolor='rgb(0, 100, 0)',  # Dark green border
        borderwidth=3,
        borderpad=8,
    )
        # Calculate the maximum value and round it up to the nearest 10k
    max_value = max(money_needed)
    rounded_max_value = math.ceil(max_value / 10000) * 10000  # Round up to the nearest 10,000

    # Set the tick interval dynamically
    tick_interval = rounded_max_value // 5  # Divide the range into 5 intervals

    # Add a gradient box on the graph (background)
    fig1.update_layout(
        shapes=[dict(
            type="rect",
            x0=0.1, x1=0.9, y0=0.6, y1=1,
            xref="paper", yref="paper",
            line=dict(color="rgba(0,0,0,0)"),  # No border line
            fillcolor="rgba(0, 0, 0, 0)",  # Transparent for a gradient background
        )],
        
        title="Weekly Money Needed for Predicted Sales",
        xaxis=dict(
            title='Item Names',
            tickangle=45,
            tickfont=dict(size=12, color='black'), 
        ),
        yaxis=dict(
            title='Amount Needed (₹)',  # Remove grid lines
            tick0=0,  # Start the y-axis at 1000
            dtick=tick_interval,  # Dynamic tick interval
            range=[0, rounded_max_value],  # Adjust the range dynamically
            tickformat="d",  # Ensure whole numbers
              
        ),
        template='plotly_white',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=50, r=50, t=80, b=150),
        font=dict(family='Arial, sans-serif', size=14, color='black'),
        showlegend=False,
        height=600,  # Increase the height of the graph for more space
    )

    # Add hover effect for better insights
    fig1.update_traces(hoverinfo='x+y', hoverlabel=dict(bgcolor='white', font_size=12, font_family='Arial'))

    # Convert the figure to an HTML div
    graph_html1 = pio.to_html(fig1, full_html=False)

    # Pass the graph HTML to the template
    
    start_time = time.time()


    try:
        # Connect to the databases with timeout to avoid waiting indefinitely
        conn_inventory = sqlite3.connect('inventory.db', timeout=10)
        conn_supplier = sqlite3.connect('supplier.db', timeout=10)

        # Create cursors
        cur_inventory = conn_inventory.cursor()
        cur_supplier = conn_supplier.cursor()

        # Fetch data from inventory and supplier tables
        cur_inventory.execute("SELECT item_name, price FROM inventory")
        inventory_data = cur_inventory.fetchall()

        cur_supplier.execute("SELECT item_name, per_price FROM supplier")
        supplier_data = cur_supplier.fetchall()

        # Create a dictionary for supplier data to easily match item names
        supplier_dict = {row[0]: row[1] for row in supplier_data}

        # Calculate profit for each item
        profits = []
        items = []
        total_profit = 0
        total_actual_price = 0

        for item_name, price in inventory_data:
            if item_name in supplier_dict:
                per_price = supplier_dict[item_name]
                profit = price - per_price  # Profit calculation (without multiplication by quantity)
                profits.append(profit)
                items.append(item_name)
                total_profit += profit
                total_actual_price += price

        # Generate the graph using Plotly
        fig2 = go.Figure()

        # Adding bars for Inventory Price and Supplier Price
        fig2.add_trace(go.Bar(
            x=items,
            y=[price for _, price in inventory_data],
            name='Inventory Price',
            marker=dict(color='#1f77b4')  # Professional blue for Inventory Price
        ))

        fig2.add_trace(go.Bar(
            x=items,
            y=[supplier_dict.get(item, 0) for item in items],
            name='Supplier Price',
            marker=dict(color='#ff7f0e')  # Vibrant orange for Supplier Price
        ))

        # Customize the graph layout for full transparency and no white lines
        fig2.update_layout(
            barmode='group',
            xaxis_title="Items",
            yaxis_title="Price (INR)",
            xaxis_tickangle=-45,
            showlegend=True,
            template="plotly_white",  # Clean white theme, ensures no unwanted lines
            height=600,  # Larger height for better view
            plot_bgcolor='rgba(0, 0, 0, 0)',  # No background color for the graph
            paper_bgcolor='rgba(0, 0, 0, 0)',  # No background for the entire figure
            margin={"t": 40, "b": 100, "l": 60, "r": 40},  # Adjust margins for space
            font=dict(family="Arial, sans-serif", size=12),
            xaxis=dict(showline=False, zeroline=False),  # Remove axis lines
            yaxis=dict(showline=False, zeroline=False)   # Remove axis lines
        )

        # Add total profit annotation to the graph with a distinct design
        fig2.add_annotation(
            x=0.98,
            y=0.98,
            text=f"<b>Total Profit: ₹{total_profit:,.2f}</b>",
            showarrow=False,
            font=dict(
                size=16,
                color="black",  # Change text color to black
                family="Arial, sans-serif",
                weight="bold"
            ),
            bgcolor="rgba(189, 195, 199, 0.7)",  # bg color of total profit box
            borderpad=10,
            borderwidth=2,
            bordercolor="white",
            xref="paper",
            yref="paper",
            xanchor="right",
            yanchor="top"
        )

        # Convert plotly figure to HTML for embedding
        graph_html2 = fig2.to_html(full_html=False)

        # Check for execution time to prevent long loading times
        if time.time() - start_time > 15:
            return "Server is taking too long to respond. Please try again later."

        # Return the rendered HTML with the graph and profit information
        return render_template('index2.html', graph_html1=graph_html1,graph_html2=graph_html2, total_profit=total_profit)

    except Exception as e:
        # Log the error and return an error message
        logging.error(f"An error occurred: {e}")
        return f"An error occurred: {e}"

    finally:
        # Ensure the database connections are closed
        conn_inventory.close()
        conn_supplier.close()


@app.route('/customer')
def customer():
    if 'user' in session and session['role'] == 'user':
        return render_template('customer.html', user=session['user'])  # Render home if logged in
    return redirect(url_for('home'))

@app.route('/customer1')
def customer1():
    inventory = get_inventory()  # Get the inventory to display in the HTML
    return render_template('customer1.html', inventory=inventory)

# Place an order route
@app.route('/place_order/<int:item_id>', methods=['POST'])
def place_order(item_id):
    try:
        data = request.get_json()  # Get JSON data from the request
        
        if not data or 'quantity' not in data:
            return jsonify({'success': False, 'message': 'Quantity not provided in request data.'})

        order_sales = int(data['quantity'])  # Extract order_sales (formerly quantity)

        if 'user' not in session:
            return jsonify({'success': False, 'message': 'User not logged in'})

        username = session['user']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch item details from inventory
        cursor.execute('SELECT item_id, item_name, quantity, price FROM inventory WHERE item_id = ?', (item_id,))
        item = cursor.fetchone()

        if not item:
            return jsonify({'success': False, 'message': 'Item not found'})

        item_id, item_name, current_quantity, price = item

        if current_quantity >= order_sales:
            total_price = order_sales * price  # Calculate the total price for the order
            new_quantity = current_quantity - order_sales

            now = datetime.now()
            order_date = now.strftime('%Y-%m-%d')
            order_time = now.strftime('%H:%M:%S')
            last_updated = now.strftime('%Y-%m-%d %H:%M:%S')  # Current timestamp

            # Update inventory after placing the order
            cursor.execute('UPDATE inventory SET quantity = ?, last_updated = ? WHERE item_id = ?', 
                           (new_quantity, last_updated, item_id))

            # Insert the order into the orders table
            cursor.execute(''' 
                INSERT INTO orders (item_id, item_name, order_sales, order_date, order_time, username, price, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_id, item_name, order_sales, order_date, order_time, username, price, total_price))

            order_id = cursor.lastrowid

            conn.commit()
            return jsonify({'success': True, 'message': 'Order placed successfully.',
                            'total_price': total_price, 'updated_quantity': new_quantity, 'order_id': order_id,
                            'last_updated': last_updated})
        else:
            return jsonify({'success': False, 'message': 'Not enough stock available'})

    except Exception as e:
        return jsonify({'success': False, 'message': f"Error placing order: {str(e)}"})
    finally:
        conn.close()


@app.route('/cancel_order/<int:item_id>', methods=['POST'])
def cancel_order(item_id):
    try:
        # Parse the incoming JSON data
        data = request.get_json()

        # Connect to the database
        conn = sqlite3.connect('inventory.db')  # Use the correct database here
        cursor = conn.cursor()

        # First, check if the order exists in the orders table
        cursor.execute('''SELECT order_sales FROM orders WHERE item_id = ?''', (item_id,))
        order = cursor.fetchone()

        if not order:
            return jsonify({'success': False, 'message': 'Order not found in the orders table'})

        # Retrieve the quantity of the canceled order
        order_sales = order[0]

        # Update stock and last_updated if you want to increase the stock when an order is canceled
        now = datetime.now()
        last_updated = now.strftime('%Y-%m-%d %H:%M:%S')  # Current timestamp

        cursor.execute('''UPDATE inventory 
                          SET quantity = quantity + ?, last_updated = ? 
                          WHERE item_id = ?''', 
                       (order_sales, last_updated, item_id))

        # Delete the corresponding order record from the orders table
        cursor.execute('''DELETE FROM orders WHERE item_id = ?''', (item_id,))

        # Commit the changes
        conn.commit()

        # Return a success message
        return jsonify({'success': True, 'message': 'Order canceled successfully!', 'last_updated': last_updated})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'Error canceling order.'})

    finally:
        # Close the database connection
        conn.close()

@app.route('/index3')
def index3():

    try:
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inventory')
        inventory_data = cursor.fetchall()  # Fetch all data from the inventory table
        conn.close()

        if not inventory_data:
            flash("No inventory data found.", 'error')

        return render_template('index3.html', inventory_data=inventory_data)
    except Exception as e:
        flash(f"Error fetching inventory data: {e}", 'error')
        return render_template(url_for('index3'))
    
@app.route('/product_analytics/<product_name>', methods=['GET', 'POST'])
def product_analytics(product_name):
    try:
        # Fetch order data for the specific product, sorted by order_date and order_time
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.order_time, o.order_date, o.order_sales, o.item_name, o.username
            FROM orders o
            WHERE o.item_name = ?
            ORDER BY o.order_date ASC, o.order_time ASC
        ''', (product_name,))
        order_data = cursor.fetchall()
        conn.close()

        # Convert data to DataFrame
        if order_data:
            df = pd.DataFrame(order_data, columns=["order_time", "order_date", "order_sales", "item_name", "username"])

            # Combine order_date and order_time into a single datetime column
            df['order_datetime'] = pd.to_datetime(df['order_date'] + ' ' + df['order_time'])

            # Prepare table data
            table_data = df[["order_time", "order_date", "order_sales", "username"]].values.tolist()

            # Create a Plotly line graph with datetime on x-axis
            fig = px.line(df, x="order_datetime", y="order_sales", markers=True,
                          title=f"Order Quantity Over Time for {product_name}")
            fig.update_layout(
                plot_bgcolor="white",
                xaxis_title="Order Date & Time",
                yaxis_title="Quantity",
                title_font=dict(size=24, color="#2C3E50", family="Arial, sans-serif"),
                xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#e6e6e6'),
                yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#e6e6e6'),
                font=dict(family="Arial, sans-serif", color="#2C3E50")
            )
            graph_html = pio.to_html(fig, full_html=False)
        else:
            # If no data exists, show an empty graph and message
            table_data = []
            graph_html = "<p style='color:red; font-size:20px;'>No order data available for this product.</p>"

        # Render template with or without data
        return render_template(
            'product_analytics.html', 
            product_name=product_name, 
            order_data=table_data, 
            graph_html=graph_html
        )

    except Exception as e:
        flash(f"Error fetching product data for analytics: {e}", 'error')
        return render_template('product_analytics.html', product_name=product_name, order_data=[], graph_html=None)
    
@app.route('/index4')
def index4():
    # Fetch the inventory data (make sure it's a DataFrame)
    stock_data = fetch_inventory_data()

    # Generate the stock level graph
    stock_graph = plot_inventory_graph(stock_data)

    # Check if the graph was generated successfully
    if stock_graph is None:
        stock_graph = "No data available to display the graph."

    return render_template('index4.html', stock_graph=stock_graph, stock_data=stock_data)

def plot_inventory_graph(df):
    # Define a buffer value
    buffer = 5  # Adjust this as needed

    # Add conditions for 'close_to_threshold' and 'below_threshold'
    df['below_threshold'] = df['quantity'] <= df['threshold']  # Below or at threshold
    df['close_to_threshold'] = (df['quantity'] > df['threshold']) & (df['quantity'] <= df['threshold'] + buffer)

    # Create the base line graph for stock levels
    fig = go.Figure()

    # Add the stock level line
    fig.add_trace(go.Scatter(
        x=df['item_name'],
        y=df['quantity'],
        mode='lines+markers',
        name='Sufficient Stock',  # All points start as 'Sufficient Stock'
        marker=dict(size=10, color='blue')
    ))

    # Add markers for items close to the threshold (orange)
    fig.add_trace(go.Scatter(
        x=df[df['close_to_threshold']]['item_name'],
        y=df[df['close_to_threshold']]['quantity'],
        mode='markers',
        name='Alert: Close to Threshold',  # Only one entry in the legend
        marker=dict(color='darkorange', size=15, opacity=0.8, symbol='circle'),
        hoverinfo='text',
        text=df[df['close_to_threshold']]['item_name'].apply(lambda x: f"{x}: Alert for low stock")
    ))

    # Add markers for items below or at the threshold (red)
    fig.add_trace(go.Scatter(
        x=df[df['below_threshold']]['item_name'],
        y=df[df['below_threshold']]['quantity'],
        mode='markers',
        name='Alert: Low Stock',  # Only one entry in the legend
        marker=dict(color='red', size=15, opacity=1, symbol='circle'),
        hoverinfo='text',
        text=df[df['below_threshold']]['item_name'].apply(lambda x: f"{x}: Low stock")
    ))

    # Layout settings for the plot
    fig.update_layout(
        title="Inventory Stock Levels",
        xaxis_title="Item Name",
        yaxis_title="Quantity",
        xaxis=dict(tickangle=45),
        template="plotly_white",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.1),  # Move legend to the side
        margin=dict(l=0, r=150, t=50, b=50)  # Add space for side legend
    )

    # Get the HTML representation of the figure
    graph_html = pio.to_html(fig, full_html=False)  # full_html=False generates just the div
    return graph_html

@app.route('/index6')
def index6():
    data = get_items_close_to_threshold()
    low_stock_items = [item for item in data if item['Quantity'] < item['Threshold']]
    order_notifications = handle_order_notifications()
    restock_messages = handle_restock_notifications()
    return render_template(
        'index6.html',
        order_notifications=order_notifications,
        restock_notifications=restock_messages,
        low_stock_items=low_stock_items
    )





@app.route('/index')
def index():
    return render_template('index.html')

@app.route("/predict_sales")
def predict_sales():
    # Get the current date and calculate the date 7 days ago
    current_date = datetime.now()
    start_date = (current_date - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Connect to the database
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()

    # Get data from the 'inventory' and 'orders' tables
    inventory_query = "SELECT item_id, item_name, quantity, threshold FROM inventory"
    orders_query = f"""
    SELECT item_id, SUM(order_sales) AS order_sales, order_date
    FROM orders
    WHERE order_date >= '{start_date}'
    GROUP BY item_id, order_date
    """
    
    # Load data into pandas DataFrames
    inventory = pd.read_sql_query(inventory_query, conn)
    orders = pd.read_sql_query(orders_query, conn)

    # Ensure 'order_date' is in datetime format
    orders['order_date'] = pd.to_datetime(orders['order_date'])

    # Group orders by 'item_id' and sum 'order_sales' to avoid repetition
    orders_grouped = orders.groupby('item_id').agg({
        'order_sales': 'sum',
        'order_date': 'max'  # Keep the latest order date for reference
    }).reset_index()

    # Add month start/end trends to the orders dataframe
    orders_grouped['month_start'] = orders_grouped['order_date'].dt.day <= 7
    orders_grouped['month_end'] = orders_grouped['order_date'].dt.day >= orders_grouped['order_date'].dt.days_in_month - 7

    # Merge the data on item_id
    merged_data = pd.merge(orders_grouped, inventory[['item_id', 'item_name', 'quantity', 'threshold']], on='item_id', how='inner')

    # Create feature columns for predicting sales
    merged_data['avg_sales_last_7_days'] = merged_data['order_sales'] / 7  # Average daily sales over the last 7 days

    # Prepare features and target for prediction
    X = merged_data[['avg_sales_last_7_days', 'quantity', 'month_start', 'month_end']]
    y = merged_data['order_sales']  # Using total sales as the target variable

    # Train a Random Forest model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    merged_data['predicted_sales'] = model.predict(X)

    # Apply rounding logic
    merged_data['predicted_sales'] = merged_data['predicted_sales'].apply(lambda x: round(x) if (x % 1) != 0.5 else int(x) + 1)
    r2 = r2_score(y, merged_data['predicted_sales'])

    # Insert or update predictions in 'predict.db'
    predict_conn = sqlite3.connect('predict.db')
    predict_cursor = predict_conn.cursor()

    for index, row in merged_data.iterrows():
        item_id = row['item_id']
        item_name = row['item_name']
        predicted_sales = row['predicted_sales']
        record_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        predict_cursor.execute("SELECT * FROM predictions WHERE item_id = ?", (item_id,))
        existing_row = predict_cursor.fetchone()

        if existing_row:
            predict_cursor.execute("""
            UPDATE predictions
            SET predicted_sales = ?, record_updated = ?
            WHERE item_id = ?""", (predicted_sales, record_updated, item_id))
        else:
            predict_cursor.execute("""
            INSERT INTO predictions (item_id, item_name, predicted_sales, record_updated)
            VALUES (?, ?, ?, ?)""", (item_id, item_name, predicted_sales, record_updated))

    predict_conn.commit()
    predict_conn.close()

    # Create a bar graph comparing actual vs predicted sales using Plotly
    fig = px.bar(merged_data, 
                 x='item_name', 
                 y=['order_sales', 'predicted_sales'], 
                 barmode='group', 
                 labels={'item_name': 'Item Name', 'value': 'Sales'},
                 title='Actual vs Predicted Sales')

    graph_data = pio.to_html(fig, full_html=False)
    total_actual_sales = merged_data['order_sales'].sum()
    total_predicted_sales = merged_data['predicted_sales'].sum()

    return render_template(
        'results.html',
        metrics={'r2_score': r2},
        total_actual_sales=total_actual_sales,
        total_predicted_sales=total_predicted_sales,
        predictions=merged_data[['item_name', 'order_sales', 'predicted_sales']].to_dict(orient='records'),
        graph_path=graph_data
    )

@app.route('/download_report')
def download_report():
    try:

        temp_report_path = os.path.join(app.root_path, 'temp', 'inventory_report.pdf')


        # Fetch inventory data
        inventory_data = fetch_inventory_data()

        # Add conditions for 'low stock' and 'close to threshold'
        buffer = 5
        inventory_data['Status'] = inventory_data.apply(
            lambda row: "Low Stock" if row['quantity'] <= row['threshold'] else
            "Close to Threshold" if row['quantity'] <= row['threshold'] + buffer
            else "Sufficient", axis=1)

        # Connect to supplier and prediction databases
        conn_supplier = sqlite3.connect('supplier.db')
        conn_predict = sqlite3.connect('predict.db')

        supplier_data = pd.read_sql_query("SELECT item_name, per_price FROM supplier", conn_supplier)
        predictions_data = pd.read_sql_query("SELECT item_name, predicted_sales FROM predictions", conn_predict)

        conn_supplier.close()
        conn_predict.close()

        # Ensure the columns exist and handle missing data
        if 'predicted_sales' not in predictions_data.columns:
            predictions_data['predicted_sales'] = 0  # Set default value if missing

        # Merge data
        merged_data = pd.merge(inventory_data, supplier_data, on='item_name', how='left')
        merged_data = pd.merge(merged_data, predictions_data, on='item_name', how='left')

        # Fill any missing predicted sales values with 0 or 'N/A'
        merged_data['predicted_sales'].fillna(0, inplace=True)

        # Calculate money needed
        merged_data['money_needed'] = merged_data['predicted_sales'] * merged_data['per_price']
        total_money_needed = merged_data['money_needed'].sum()

        # Calculate financial stats
        highest_money = merged_data['money_needed'].max()
        highest_item_name = merged_data.loc[merged_data['money_needed'] == highest_money, 'item_name'].iloc[0]
        min_money_needed = merged_data['money_needed'].min()
        average_cost = merged_data['money_needed'].mean()
        total_items = len(merged_data)

        # Graph 1: Inventory vs Supplier Prices
        plt.figure(figsize=(10, 6))
        x = range(len(merged_data))
        plt.bar(x, merged_data['price'], width=0.4, label='Inventory Price', color='#1f77b4', align='center')
        plt.bar(x, merged_data['per_price'], width=0.4, label='Supplier Price', color='#ff7f0e', align='edge')
        plt.xticks(ticks=x, labels=merged_data['item_name'], rotation=45, ha='right')
        plt.xlabel('Items')
        plt.ylabel('Price (INR)')
        plt.title('Inventory vs Supplier Prices')
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        graph1_buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(graph1_buffer, format='png')
        plt.close()
        graph1_buffer.seek(0)

        # Graph 2: Money Needed for Next Week
        plt.figure(figsize=(10, 6))
        bars = plt.bar(merged_data['item_name'], merged_data['money_needed'], color='skyblue')
        rounded_max_value = math.ceil(max(merged_data['money_needed']) / 10000) * 10000
        tick_interval = rounded_max_value // 5
        plt.ylim(0, rounded_max_value)
        plt.yticks(range(0, rounded_max_value + 1, tick_interval))
        plt.xlabel('Item Name')
        plt.ylabel('Money Needed (₹)')
        plt.title('Money Needed for Each Item and Total Money Needed for Next Week')
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.tight_layout(pad=4.0)

        graph2_buffer = io.BytesIO()
        plt.savefig(graph2_buffer, format='png')
        plt.close()
        graph2_buffer.seek(0)

        # Stock table
        table_data = [["No", "Item Name", "Quantity", "Threshold", "Predicted Sales", "Price", "Status"]]
        for i, row in merged_data.iterrows():
            item_name = row['item_name']
            quantity = int(row['quantity'])
            threshold = int(row['threshold'])
            predicted_sales = int(row['predicted_sales']) if not pd.isna(row['predicted_sales']) else "N/A"
            price = row['price']
            status = row['Status']
            if status == "Low Stock":
                status_col = Paragraph(f"<font color='red'>{status}</font>", getSampleStyleSheet()["Normal"])
            elif status == "Close to Threshold":
                status_col = Paragraph(f"<font color='orange'>{status}</font>", getSampleStyleSheet()["Normal"])
            else:
                status_col = Paragraph(f"<font color='green'>{status}</font>", getSampleStyleSheet()["Normal"])
            table_data.append([i + 1, item_name, quantity, threshold, predicted_sales, price, status_col])

        

        # Prediction summary
        predicted_sales_data = merged_data[['item_name', 'predicted_sales']]
        total_predicted_sales = predicted_sales_data['predicted_sales'].sum()
        highest_predicted_sales_item = predicted_sales_data.loc[predicted_sales_data['predicted_sales'].idxmax()]
        lowest_predicted_sales_item = predicted_sales_data.loc[predicted_sales_data['predicted_sales'].idxmin()]
        
                # Fetch predicted sales data
        predicted_sales_data = fetch_predicted_sales()
        actual_sales_data = fetch_actual_sales()

        # Calculate total predicted and actual sales
        total_predicted_sales = sum([pred[1] for pred in predicted_sales_data if pred[1] is not None])
        total_actual_sales = sum([actual[1] for actual in actual_sales_data if actual[1] is not None])

        # Calculate the percentage difference
        if total_predicted_sales and total_actual_sales:
            difference = total_actual_sales - total_predicted_sales
            percentage_difference = (difference / total_actual_sales) * 100
        else:
            difference = 0
            percentage_difference = 0

        # Find the max and min predicted sales for this week
        if predicted_sales_data:
            highest_predicted_sales = max(predicted_sales_data, key=lambda x: x[1])
            lowest_predicted_sales = min(predicted_sales_data, key=lambda x: x[1])
            highest_item_name = highest_predicted_sales[0]
            highest_sales_value = highest_predicted_sales[1]
            lowest_item_name = lowest_predicted_sales[0]
            lowest_sales_value = lowest_predicted_sales[1]
        else:
            highest_item_name = "N/A"
            highest_sales_value = 0
            lowest_item_name = "N/A"
            lowest_sales_value = 0

            # Identify trends and critical items
        critical_items = [
            item[0] for item in predicted_sales_data
            if item[1] > 0 and item[0] in inventory_data[inventory_data['Status'] == "Low Stock"]['item_name'].values
        ]




            # Generate prediction summary
        prediction_summary = (
            f"The total predicted sales are {total_predicted_sales}, while the actual sales recorded are {total_actual_sales}. "
            f"The percentage difference between predicted and actual sales is {percentage_difference:.2f}%. "
            f"The item with the highest predicted sales is {highest_item_name} with {highest_sales_value} predicted sales, "
            f"while the item with the lowest predicted sales is {lowest_item_name} with {lowest_sales_value} predicted sales.\n\n"
            f"- Critical items (low stock): {', '.join(critical_items) if critical_items else 'None'}\n"
        )
        
                # Place orders for 'Low Stock' and 'Close to Threshold' items
        orders_placed = []
        for _, row in inventory_data[inventory_data['Status'] != "Sufficient"].iterrows():
            supplier_name = fetch_supplier_info(row['item_name'])
            orders_placed.append((row['item_name'], row['Status'], supplier_name))


                # Update summary with order information
        summary = generate_summary(inventory_data)
        if orders_placed:
            order_details = "\n".join([f"- {item_name} ({status}) from {supplier}" for item_name, status, supplier in orders_placed])
            summary += f"\n\nOrders have been placed for the following items:\n{order_details}"


        # Graph description and recommendation
        graph_description = (
            f"The financial summary shows a total money needed of Rs.{total_money_needed:,.2f}, "
            f"with the highest money needed being Rs.{highest_money:,.2f} for the item \"{highest_item_name}\". "
            f"The lowest money needed is Rs.{min_money_needed:,.2f}, and the average money needed per item is Rs.{average_cost:,.2f}. "
            f"In total, {total_items} items were evaluated."
        )

        recommendation = (
        f"It is recommended to focus on high-demand, high-cost items like \"{highest_item_name}\", also "
        f"monitoring low-cost,\nlow-demand items to optimize inventory management and reduce waste."
        f"Items like \"{highest_item_name}\" that contribute significantly to the total money needed "
        f"should be prioritized for purchasing and stocking to meet predicted demand. "
        f"Items with a low money contribution, especially those that require minimal investment, should be reevaluated. "
        f"These items could either be discontinued or optimized for more efficient purchasing."
        )

        # Generate PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()

        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])

        stock_table = Table(table_data, colWidths=[50, 100, 80, 80, 80, 100, 100])
        stock_table.setStyle(table_style)

        img1_object = Image(io.BytesIO(graph1_buffer.read()), width=400, height=300)
        img1_object.hAlign = 'CENTER'
        img2_object = Image(io.BytesIO(graph2_buffer.read()), width=400, height=300)
        img2_object.hAlign = 'CENTER'
        
                # Profit calculation: Inventory Price vs Supplier Price
        merged_data['profit_per_item'] = (merged_data['price'] - merged_data['per_price'])
        total_profit = merged_data['profit_per_item'].sum()

        # Calculate maximum and minimum profit
        highest_profit_item = merged_data.loc[merged_data['profit_per_item'].idxmax()]
        lowest_profit_item = merged_data.loc[merged_data['profit_per_item'].idxmin()]


                
                # Profit summary description
        profit_summary = (
            f"The total profit expected is Rs.{total_profit:,.2f}. "
            f"The item with the highest profit contribution is \"{highest_profit_item['item_name']}\" with Rs.{highest_profit_item['profit_per_item']:,.2f}. "
            f"The item with the lowest profit contribution is \"{lowest_profit_item['item_name']}\" with Rs.{lowest_profit_item['profit_per_item']:,.2f}.\n\n"
            
           
        )

        

            # Preparing the report content with profit summary and seasonal trend
        content = [
                Paragraph("Inventory Report", styles["Title"]),
                Spacer(1, 12),
                stock_table,
                Spacer(1, 12),
                Paragraph("Stock Summary:", styles["Heading2"]),
                Spacer(1, 12),
                Paragraph(summary, styles["BodyText"]),
                Spacer(1, 12),
                Paragraph("Prediction Summary:", styles["Heading2"]),
                Spacer(1, 12),
                Paragraph(prediction_summary, styles["BodyText"]),
                Spacer(1, 12),
                Paragraph("Profit Analysis", styles["Heading2"]),
                Spacer(1, 12),
                img1_object,
                Spacer(1, 12),
                Paragraph("Profit Summary:", styles["Heading2"]),
                Spacer(1, 12),
                Paragraph(profit_summary, styles["BodyText"]),
                Spacer(1, 12),
                Paragraph("Money Needed for Next Week", styles["Heading2"]),
                Spacer(1, 12),
                img2_object,
                Spacer(1, 12),
                Paragraph("<b>Graph Description:</b> " + graph_description, styles["BodyText"]),
                Spacer(1, 12),
                Paragraph("<b>Recommendation:</b> " + recommendation, styles["BodyText"]),
            ]



        doc.build(content)
        pdf_buffer.seek(0)

                # Ensure the temp directory exists
        temp_dir = os.path.join(app.root_path, 'temp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Save the PDF file in the temp folder
        with open(temp_report_path, 'wb') as f:
            f.write(pdf_buffer.read())

        # Serve the PDF as a downloadable file
        return send_file(temp_report_path, as_attachment=True, download_name="inventory_report.pdf", mimetype='application/pdf')



        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return f"An error occurred: {e}"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    import_excel_to_db()
    app.run(debug=True)
 
