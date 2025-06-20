import customtkinter as ctk
import sqlite3
import cv2
from pyzbar.pyzbar import decode
from datetime import datetime
import json

def setup_database():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventory_in (
                    package_id TEXT PRIMARY KEY,
                    item_name TEXT,
                    quantity INTEGER,
                    time_in TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory_out (
                    package_id TEXT,
                    item_name TEXT,
                    quantity INTEGER,
                    time_out TEXT
                )''')
    conn.commit()
    conn.close()

def add_item(data):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    time_in = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO inventory_in VALUES (?, ?, ?, ?)", 
                  (data['package_id'], data['item_name'], data['quantity'], time_in))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Package already exists.")
    conn.close()

def remove_item(package_id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM inventory_in WHERE package_id=?", (package_id,))
    row = c.fetchone()
    if row:
        time_out = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO inventory_out VALUES (?, ?, ?, ?)", (row[0], row[1], row[2], time_out))
        c.execute("DELETE FROM inventory_in WHERE package_id=?", (package_id,))
        conn.commit()
    else:
        print("Package not found.")
    conn.close()

def scan_qr():
    cap = cv2.VideoCapture(0)
    package_data = None
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break
            for barcode in decode(frame):
                data = barcode.data.decode('utf-8')
                try:
                    package_data = json.loads(data)
                    package_data['package_id'] = package_data['package_id'].strip().upper()
                    cv2.rectangle(frame, (barcode.rect.left, barcode.rect.top),
                                  (barcode.rect.left + barcode.rect.width, barcode.rect.top + barcode.rect.height),
                                  (0, 255, 0), 2)
                    cv2.imshow('Scan QR Code', frame)
                    cv2.waitKey(1000)
                    return package_data
                except json.JSONDecodeError:
                    print("Invalid QR Code content")
            cv2.imshow('Scan QR Code', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
    return None

def handle_in():
    data = scan_qr()
    if data:
        add_item(data)
        result_label.configure(text=f"✅ {data['package_id']} added to inventory.")
    else:
        result_label.configure(text="❌ No valid QR code scanned.")

def handle_out():
    data = scan_qr()
    if data:
        remove_item(data['package_id'])
        result_label.configure(text=f"📦 {data['package_id']} removed from inventory.")
    else:
        result_label.configure(text="❌ No valid QR code scanned.")

setup_database()
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("500x400")
app.title("📦 Inventory Management System")

title = ctk.CTkLabel(app, text="QR Inventory Manager", font=ctk.CTkFont(size=24, weight="bold"))
title.pack(pady=40)

in_btn = ctk.CTkButton(app, text="Scan IN", command=handle_in)
in_btn.pack(pady=10)

out_btn = ctk.CTkButton(app, text="Scan OUT", command=handle_out)
out_btn.pack(pady=10)

result_label = ctk.CTkLabel(app, text="", font=ctk.CTkFont(size=16))
result_label.pack(pady=20)

app.mainloop()
