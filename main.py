import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter


class BMICalculator:
    def __init__(self, master):
        self.master = master
        self.master.title("BMI Calculator")
        self.master.geometry("800x650")
        self.master.configure(bg="#f0f0f0")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", background="#4CAF50", foreground="white", font=("Arial", 12))
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 12))
        self.style.configure("TEntry", font=("Arial", 12))

        self.create_widgets()
        self.connect_to_database()
        self.current_user_id = None

    def create_widgets(self):
        # User Information Frame
        info_frame = ttk.Frame(self.master, padding="10")
        info_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ttk.Label(info_frame, text="Email:").grid(row=0, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(info_frame, width=30)
        self.email_entry.grid(row=0, column=1, pady=5)

        ttk.Label(info_frame, text="Name:").grid(row=1, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(info_frame, width=30)
        self.name_entry.grid(row=1, column=1, pady=5)

        ttk.Label(info_frame, text="Weight (kg):").grid(row=2, column=0, sticky="w", pady=5)
        self.weight_entry = ttk.Entry(info_frame, width=30)
        self.weight_entry.grid(row=2, column=1, pady=5)

        ttk.Label(info_frame, text="Height (cm):").grid(row=3, column=0, sticky="w", pady=5)
        self.height_entry = ttk.Entry(info_frame, width=30)
        self.height_entry.grid(row=3, column=1, pady=5)

        calculate_button = ttk.Button(info_frame, text="Calculate BMI", command=self.calculate_bmi)
        calculate_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Results Frame
        results_frame = ttk.Frame(self.master, padding="10")
        results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.result_label = ttk.Label(results_frame, text="", font=("Arial", 14, "bold"))
        self.result_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Graph Frame
        graph_frame = ttk.Frame(self.master, padding="10")
        graph_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="nsew")

        self.figure, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Load Data Button
        load_button = ttk.Button(self.master, text="Load User Data", command=self.load_user_data)
        load_button.grid(row=2, column=0, pady=10)

        # Create New User Button
        create_user_button = ttk.Button(self.master, text="Create New User", command=self.create_new_user)
        create_user_button.grid(row=3, column=0, pady=10)

    def connect_to_database(self):
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Thunder@456",
                database="bmi_calculator"
            )
            self.cursor = self.conn.cursor()

            # Create users table if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE,
                    name VARCHAR(255)
                )
            """)

            # Create bmi_records table if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS bmi_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    weight FLOAT,
                    height FLOAT,
                    bmi FLOAT,
                    category VARCHAR(50),
                    date DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            self.conn.commit()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error connecting to database: {err}")

    def create_new_user(self):
        email = self.email_entry.get()
        name = self.name_entry.get()

        if not email or not name:
            messagebox.showerror("Input Error", "Please enter both email and name")
            return

        try:
            query = "INSERT INTO users (email, name) VALUES (%s, %s)"
            self.cursor.execute(query, (email, name))
            self.conn.commit()
            self.current_user_id = self.cursor.lastrowid
            messagebox.showinfo("Success", f"New user created: {name}")
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry error
                messagebox.showerror("Error", "This email is already registered")
            else:
                messagebox.showerror("Database Error", f"Error creating new user: {err}")

    def load_user_data(self):
        email = self.email_entry.get()

        if not email:
            messagebox.showerror("Input Error", "Please enter an email to load data")
            return

        try:
            # Get user id and name
            query = "SELECT id, name FROM users WHERE email = %s"
            self.cursor.execute(query, (email,))
            user_result = self.cursor.fetchone()

            if user_result:
                self.current_user_id, name = user_result
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, name)

                # Get latest BMI record
                query = "SELECT weight, height, bmi, category FROM bmi_records WHERE user_id = %s ORDER BY date DESC LIMIT 1"
                self.cursor.execute(query, (self.current_user_id,))
                bmi_result = self.cursor.fetchone()

                if bmi_result:
                    weight, height, bmi, category = bmi_result
                    self.weight_entry.delete(0, tk.END)
                    self.weight_entry.insert(0, str(weight))
                    self.height_entry.delete(0, tk.END)
                    self.height_entry.insert(0, str(height))

                    result_text = f"BMI: {bmi:.2f}\nCategory: {category}"
                    self.result_label.config(text=result_text)

                    self.update_graph()
                else:
                    messagebox.showinfo("No Data", f"No BMI data found for {name}")
            else:
                messagebox.showinfo("No User", f"No user found with email: {email}")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error loading data: {err}")

    def calculate_bmi(self):
        if not self.current_user_id:
            messagebox.showerror("Error", "Please load user data or create a new user first")
            return

        try:
            weight = float(self.weight_entry.get())
            height = float(self.height_entry.get()) / 100  # Convert cm to m

            if weight <= 0 or height <= 0:
                raise ValueError("Weight and height must be positive numbers")

            bmi = weight / (height ** 2)
            category = self.get_bmi_category(bmi)

            result_text = f"BMI: {bmi:.2f}\nCategory: {category}"
            self.result_label.config(text=result_text)

            # Save to database
            self.save_to_database(weight, height * 100, bmi, category)

            # Update graph
            self.update_graph()

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def get_bmi_category(self, bmi):
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 25:
            return "Normal weight"
        elif 25 <= bmi < 30:
            return "Overweight"
        else:
            return "Obese"

    def save_to_database(self, weight, height, bmi, category):
        try:
            query = """
                INSERT INTO bmi_records (user_id, weight, height, bmi, category, date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (self.current_user_id, weight, height, bmi, category, datetime.now())
            self.cursor.execute(query, values)
            self.conn.commit()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error saving to database: {err}")

    def update_graph(self):
        try:
            query = "SELECT date, bmi FROM bmi_records WHERE user_id = %s ORDER BY date"
            self.cursor.execute(query, (self.current_user_id,))
            results = self.cursor.fetchall()

            dates = [row[0] for row in results]
            bmis = [row[1] for row in results]

            self.ax.clear()
            self.ax.plot(dates, bmis, marker='o')
            self.ax.set_title(f"BMI History for {self.name_entry.get()}")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("BMI")
            self.ax.tick_params(axis='x', rotation=45)
            self.ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
            self.figure.tight_layout()
            self.canvas.draw()

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error retrieving data: {err}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BMICalculator(root)
    root.mainloop()