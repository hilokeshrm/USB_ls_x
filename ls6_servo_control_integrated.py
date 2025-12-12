#!/usr/bin/env python3
"""
LS6 Integrated Logs Reader and Servo Control
Combines serial log reading with USB-based servo control
"""

import serial
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from robot_servo_control_usb import RobotServoControllerUSB


class LS6IntegratedControl:
    def __init__(self, root):
        self.root = root
        self.root.title("LS6 Integrated Control - Logs & Servos")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Serial connection variables (for logs)
        self.ser = None
        self.is_connected = False
        self.read_thread = None
        self.stop_reading = False
        
        # Servo controller
        self.servo_controller = None
        self.servo_connected = False
        
        # Default settings
        self.port_var = tk.StringVar(value="COM20")
        self.baud_var = tk.StringVar(value="57600")
        
        # Servo settings
        self.servo_port_var = tk.StringVar(value="COM20")
        self.servo_baud_var = tk.StringVar(value="57600")
        
        # Search variables
        self.search_matches = []
        self.current_match_index = -1
        self.case_sensitive = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=50)
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="LS6 Integrated Control - Serial Logs & Servo Control",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=12)
        
        # Main container with two columns
        main_container = tk.Frame(self.root, bg="#f0f0f0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side - Logs
        left_frame = tk.Frame(main_container, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right side - Servo Control
        right_frame = tk.Frame(main_container, bg="#f0f0f0", width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        self.create_logs_panel(left_frame)
        self.create_servo_panel(right_frame)
        
    def create_logs_panel(self, parent):
        """Create the logs reading panel"""
        # Connection frame
        conn_frame = tk.Frame(parent, bg="#ecf0f1", relief=tk.RAISED, bd=2)
        conn_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(conn_frame, text="Serial Logs", bg="#ecf0f1", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Port configuration
        tk.Label(conn_frame, text="Port:", bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Entry(conn_frame, textvariable=self.port_var, width=12, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        tk.Label(conn_frame, text="Baud:", bg="#ecf0f1", font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Entry(conn_frame, textvariable=self.baud_var, width=10, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        # Connect/Disconnect button
        self.conn_button = tk.Button(
            conn_frame,
            text="Connect Logs",
            command=self.toggle_connection,
            bg="#27ae60",
            fg="white",
            font=("Arial", 9, "bold"),
            width=12,
            cursor="hand2"
        )
        self.conn_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Status indicator
        self.status_label = tk.Label(
            conn_frame,
            text="● Disconnected",
            bg="#ecf0f1",
            fg="#e74c3c",
            font=("Arial", 9, "bold")
        )
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Logs display area
        logs_frame = tk.Frame(parent, bg="#ffffff", relief=tk.SUNKEN, bd=2)
        logs_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Logs header with search
        logs_header = tk.Frame(logs_frame, bg="#ffffff")
        logs_header.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            logs_header,
            text="Logs Output:",
            bg="#ffffff",
            font=("Arial", 10, "bold"),
            anchor=tk.W
        ).pack(side=tk.LEFT)
        
        # Search frame
        search_frame = tk.Frame(logs_header, bg="#ffffff")
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        tk.Label(search_frame, text="Search:", bg="#ffffff", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        
        self.search_entry = tk.Entry(search_frame, font=("Arial", 8), width=15)
        self.search_entry.pack(side=tk.LEFT, padx=2)
        self.search_entry.bind("<Return>", lambda e: self.search_text())
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_text())
        
        self.case_var = tk.BooleanVar()
        tk.Checkbutton(
            search_frame,
            text="Case",
            variable=self.case_var,
            bg="#ffffff",
            font=("Arial", 7),
            command=self.search_text
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            search_frame,
            text="◀",
            command=self.search_previous,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 7),
            width=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=1)
        
        tk.Button(
            search_frame,
            text="▶",
            command=self.search_next,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 7),
            width=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=1)
        
        self.match_count_label = tk.Label(
            search_frame,
            text="",
            bg="#ffffff",
            font=("Arial", 7),
            fg="#7f8c8d"
        )
        self.match_count_label.pack(side=tk.LEFT, padx=3)
        
        self.logs_text = scrolledtext.ScrolledText(
            logs_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            state=tk.DISABLED
        )
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.logs_text.tag_config("search_highlight", background="#ffff00", foreground="#000000")
        self.logs_text.tag_config("current_match", background="#ff8800", foreground="#000000")
        self.logs_text.tag_config("servo_cmd", foreground="#00ff00")
        self.logs_text.tag_config("servo_error", foreground="#ff4444")
        
        # Command input frame
        cmd_frame = tk.Frame(parent, bg="#ecf0f1", relief=tk.RAISED, bd=2)
        cmd_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            cmd_frame,
            text="Send Command:",
            bg="#ecf0f1",
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.cmd_entry = tk.Entry(cmd_frame, font=("Arial", 9), width=40)
        self.cmd_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        self.cmd_entry.bind("<Return>", lambda e: self.send_command())
        
        tk.Button(
            cmd_frame,
            text="Send",
            command=self.send_command,
            bg="#3498db",
            fg="white",
            font=("Arial", 9, "bold"),
            width=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            cmd_frame,
            text="Ctrl+C",
            command=self.send_interrupt,
            bg="#e67e22",
            fg="white",
            font=("Arial", 8, "bold"),
            width=7,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            cmd_frame,
            text="Clear",
            command=self.clear_logs,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 9),
            width=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Bind Ctrl+C globally
        self.root.bind_all("<Control-c>", lambda e: self.send_interrupt())
        self.root.bind_all("<Control-C>", lambda e: self.send_interrupt())
        
    def create_servo_panel(self, parent):
        """Create the servo control panel"""
        # Servo control header
        servo_header = tk.Frame(parent, bg="#34495e", relief=tk.RAISED, bd=2)
        servo_header.pack(fill=tk.X, pady=5)
        
        tk.Label(
            servo_header,
            text="Servo Control",
            bg="#34495e",
            fg="white",
            font=("Arial", 12, "bold")
        ).pack(pady=8)
        
        # Servo connection frame
        servo_conn_frame = tk.Frame(parent, bg="#ecf0f1", relief=tk.RAISED, bd=2)
        servo_conn_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Label(servo_conn_frame, text="Port:", bg="#ecf0f1", font=("Arial", 8)).grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        tk.Entry(servo_conn_frame, textvariable=self.servo_port_var, width=12, font=("Arial", 8)).grid(row=0, column=1, padx=2, pady=2)
        
        tk.Label(servo_conn_frame, text="Baud:", bg="#ecf0f1", font=("Arial", 8)).grid(row=0, column=2, padx=2, pady=2, sticky=tk.W)
        tk.Entry(servo_conn_frame, textvariable=self.servo_baud_var, width=10, font=("Arial", 8)).grid(row=0, column=3, padx=2, pady=2)
        
        self.servo_conn_button = tk.Button(
            servo_conn_frame,
            text="Connect Servos",
            command=self.toggle_servo_connection,
            bg="#27ae60",
            fg="white",
            font=("Arial", 8, "bold"),
            cursor="hand2"
        )
        self.servo_conn_button.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=tk.EW)
        
        self.servo_status_label = tk.Label(
            servo_conn_frame,
            text="● Disconnected",
            bg="#ecf0f1",
            fg="#e74c3c",
            font=("Arial", 8, "bold")
        )
        self.servo_status_label.grid(row=2, column=0, columnspan=4, pady=2)
        
        # Quick control buttons
        quick_frame = tk.LabelFrame(parent, text="Quick Actions", bg="#ecf0f1", font=("Arial", 9, "bold"))
        quick_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Button(
            quick_frame,
            text="Move to Neutral",
            command=self.move_to_neutral,
            bg="#3498db",
            fg="white",
            font=("Arial", 9),
            cursor="hand2"
        ).pack(fill=tk.X, padx=5, pady=3)
        
        tk.Button(
            quick_frame,
            text="Test Motor 1",
            command=self.test_motor_1,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 9),
            cursor="hand2"
        ).pack(fill=tk.X, padx=5, pady=3)
        
        tk.Button(
            quick_frame,
            text="Test All Motors",
            command=self.test_all_motors,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 9),
            cursor="hand2"
        ).pack(fill=tk.X, padx=5, pady=3)
        
        # Individual motor control
        motor_frame = tk.LabelFrame(parent, text="Individual Motor Control", bg="#ecf0f1", font=("Arial", 9, "bold"))
        motor_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Motor ID selection
        id_frame = tk.Frame(motor_frame, bg="#ecf0f1")
        id_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(id_frame, text="Motor ID:", bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        self.motor_id_var = tk.StringVar(value="1")
        motor_id_spin = tk.Spinbox(id_frame, from_=1, to=12, textvariable=self.motor_id_var, width=5, font=("Arial", 9))
        motor_id_spin.pack(side=tk.LEFT, padx=2)
        
        # Position control
        pos_frame = tk.Frame(motor_frame, bg="#ecf0f1")
        pos_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(pos_frame, text="Position (deg):", bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        self.position_var = tk.StringVar(value="150")
        tk.Entry(pos_frame, textvariable=self.position_var, width=8, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        # Velocity control
        vel_frame = tk.Frame(motor_frame, bg="#ecf0f1")
        vel_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(vel_frame, text="Velocity (RPM):", bg="#ecf0f1", font=("Arial", 8)).pack(side=tk.LEFT, padx=2)
        self.velocity_var = tk.StringVar(value="30")
        tk.Entry(vel_frame, textvariable=self.velocity_var, width=8, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        # Move button
        tk.Button(
            motor_frame,
            text="Move Motor",
            command=self.move_single_motor,
            bg="#e67e22",
            fg="white",
            font=("Arial", 9, "bold"),
            cursor="hand2"
        ).pack(fill=tk.X, padx=5, pady=5)
        
        # Preset positions
        preset_frame = tk.LabelFrame(parent, text="Preset Positions", bg="#ecf0f1", font=("Arial", 9, "bold"))
        preset_frame.pack(fill=tk.X, pady=5, padx=5)
        
        presets = [
            ("90°", [90] * 12),
            ("150°", [150] * 12),
            ("180°", [180] * 12),
            ("210°", [210] * 12),
        ]
        
        for name, positions in presets:
            btn = tk.Button(
                preset_frame,
                text=name,
                command=lambda p=positions: self.send_all_servos(p),
                bg="#16a085",
                fg="white",
                font=("Arial", 8),
                cursor="hand2"
            )
            btn.pack(fill=tk.X, padx=5, pady=2)
        
    # Logs methods
    def log_message(self, message, color="#d4d4d4", tag=""):
        """Add a message to the logs display"""
        self.logs_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        tag_name = tag if tag else "log"
        self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n", tag_name)
        if tag_name not in ["servo_cmd", "servo_error"]:
            self.logs_text.tag_config(tag_name, foreground=color)
        self.logs_text.see(tk.END)
        self.logs_text.config(state=tk.DISABLED)
        
    def clear_logs(self):
        """Clear the logs display"""
        self.logs_text.config(state=tk.NORMAL)
        self.logs_text.delete(1.0, tk.END)
        self.logs_text.config(state=tk.DISABLED)
        self.clear_search()
        
    def clear_search(self):
        """Clear search highlights"""
        self.search_entry.delete(0, tk.END)
        self.search_matches = []
        self.current_match_index = -1
        self.match_count_label.config(text="")
        self.remove_search_highlights()
        
    def remove_search_highlights(self):
        """Remove all search highlights"""
        self.logs_text.config(state=tk.NORMAL)
        self.logs_text.tag_remove("search_highlight", 1.0, tk.END)
        self.logs_text.tag_remove("current_match", 1.0, tk.END)
        self.logs_text.config(state=tk.DISABLED)
        
    def search_text(self):
        """Search for text in logs"""
        search_term = self.search_entry.get()
        self.case_sensitive = self.case_var.get()
        
        self.remove_search_highlights()
        self.search_matches = []
        self.current_match_index = -1
        
        if not search_term:
            self.match_count_label.config(text="")
            return
            
        self.logs_text.config(state=tk.NORMAL)
        
        start_pos = 1.0
        nocase = 0 if self.case_sensitive else 1
        
        while True:
            pos = self.logs_text.search(search_term, start_pos, tk.END, nocase=nocase)
            if not pos:
                break
            end_pos = f"{pos}+{len(search_term)}c"
            self.search_matches.append((pos, end_pos))
            self.logs_text.tag_add("search_highlight", pos, end_pos)
            start_pos = end_pos
            
        match_count = len(self.search_matches)
        if match_count > 0:
            self.match_count_label.config(text=f"{match_count} match{'es' if match_count != 1 else ''}")
            self.current_match_index = 0
            self.highlight_current_match()
        else:
            self.match_count_label.config(text="No matches")
            
        self.logs_text.config(state=tk.DISABLED)
        
    def highlight_current_match(self):
        """Highlight current match"""
        if not self.search_matches or self.current_match_index < 0:
            return
        self.logs_text.config(state=tk.NORMAL)
        self.logs_text.tag_remove("current_match", 1.0, tk.END)
        if 0 <= self.current_match_index < len(self.search_matches):
            start, end = self.search_matches[self.current_match_index]
            self.logs_text.tag_add("current_match", start, end)
            self.logs_text.see(start)
        self.logs_text.config(state=tk.DISABLED)
        
    def search_next(self):
        """Navigate to next match"""
        if not self.search_matches:
            self.search_text()
            return
        if self.current_match_index < len(self.search_matches) - 1:
            self.current_match_index += 1
        else:
            self.current_match_index = 0
        self.highlight_current_match()
        
    def search_previous(self):
        """Navigate to previous match"""
        if not self.search_matches:
            self.search_text()
            return
        if self.current_match_index > 0:
            self.current_match_index -= 1
        else:
            self.current_match_index = len(self.search_matches) - 1
        self.highlight_current_match()
        
    def toggle_connection(self):
        """Toggle serial logs connection"""
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()
            
    def connect(self):
        """Connect to serial port for logs"""
        try:
            port = self.port_var.get()
            baud = int(self.baud_var.get())
            
            self.ser = serial.Serial(port, baud, timeout=0.1)
            self.is_connected = True
            self.stop_reading = False
            
            self.conn_button.config(text="Disconnect Logs", bg="#e74c3c")
            self.status_label.config(text="● Connected", fg="#27ae60")
            
            self.log_message(f"Connected to {port} at {baud} baud", "#27ae60")
            
            self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.read_thread.start()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid baud rate. Please enter a number.")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not open serial port:\n{e}")
            self.log_message(f"Connection error: {e}", "#e74c3c")
            
    def disconnect(self):
        """Disconnect from serial port"""
        self.stop_reading = True
        self.is_connected = False
        
        if self.ser and self.ser.is_open:
            self.ser.close()
            
        self.conn_button.config(text="Connect Logs", bg="#27ae60")
        self.status_label.config(text="● Disconnected", fg="#e74c3c")
        
        self.log_message("Disconnected from serial port", "#e74c3c")
        
    def read_serial(self):
        """Read from serial port"""
        while not self.stop_reading and self.is_connected:
            try:
                if self.ser and self.ser.is_open:
                    line = self.ser.readline()
                    if line:
                        try:
                            text = line.decode("utf-8", errors="ignore").strip()
                            if text:
                                self.root.after(0, self.log_message, text)
                        except:
                            pass
                else:
                    break
            except Exception as e:
                if not self.stop_reading:
                    self.root.after(0, self.log_message, f"Read error: {e}", "#e74c3c")
                time.sleep(0.1)
                
    def send_interrupt(self):
        """Send Ctrl+C interrupt"""
        if not self.is_connected or not self.ser or not self.ser.is_open:
            return
        try:
            self.ser.write(b'\x03')
            self.log_message(">>> [Ctrl+C] Interrupt signal sent", "#ff8800")
        except Exception as e:
            self.log_message(f"Interrupt send error: {e}", "#e74c3c")
    
    def send_command(self):
        """Send command to serial port"""
        if not self.is_connected or not self.ser or not self.ser.is_open:
            messagebox.showwarning("Not Connected", "Please connect to serial port first.")
            return
            
        command = self.cmd_entry.get()
        self.cmd_entry.delete(0, tk.END)
        
        try:
            if not command.endswith('\n'):
                command += '\n'
            self.ser.write(command.encode('utf-8'))
            display_cmd = command.strip() if command.strip() else "(empty)"
            self.log_message(f">>> {display_cmd}", "#3498db")
        except Exception as e:
            messagebox.showerror("Send Error", f"Could not send command:\n{e}")
            self.log_message(f"Send error: {e}", "#e74c3c")
    
    # Servo control methods
    def toggle_servo_connection(self):
        """Toggle servo controller connection"""
        if not self.servo_connected:
            self.connect_servos()
        else:
            self.disconnect_servos()
            
    def connect_servos(self):
        """Connect to servo controller"""
        try:
            port = self.servo_port_var.get()
            baud = int(self.servo_baud_var.get())
            
            self.servo_controller = RobotServoControllerUSB(port, baud)
            
            if self.servo_controller.connect(debug=False):
                self.servo_connected = True
                self.servo_conn_button.config(text="Disconnect Servos", bg="#e74c3c")
                self.servo_status_label.config(text="● Connected", fg="#27ae60")
                self.log_message(f"Servo controller connected to {port} at {baud} baud", "#00ff00", "servo_cmd")
            else:
                raise Exception("Connection failed")
                
        except ValueError:
            messagebox.showerror("Error", "Invalid baud rate. Please enter a number.")
        except Exception as e:
            messagebox.showerror("Servo Connection Error", f"Could not connect to servo controller:\n{e}")
            self.log_message(f"Servo connection error: {e}", "#ff4444", "servo_error")
            
    def disconnect_servos(self):
        """Disconnect from servo controller"""
        if self.servo_controller:
            self.servo_controller.disconnect()
            self.servo_controller = None
            
        self.servo_connected = False
        self.servo_conn_button.config(text="Connect Servos", bg="#27ae60")
        self.servo_status_label.config(text="● Disconnected", fg="#e74c3c")
        self.log_message("Servo controller disconnected", "#ff4444", "servo_error")
        
    def move_to_neutral(self):
        """Move all servos to neutral position"""
        if not self.servo_connected:
            messagebox.showwarning("Not Connected", "Please connect to servo controller first.")
            return
            
        self.log_message("Moving all servos to neutral position...", "#00ff00", "servo_cmd")
        success = self.servo_controller.move_to_neutral()
        if success:
            self.log_message("✓ Neutral position command sent successfully", "#00ff00", "servo_cmd")
        else:
            self.log_message("✗ Failed to send neutral position command", "#ff4444", "servo_error")
            
    def test_motor_1(self):
        """Test motor 1 with different positions"""
        if not self.servo_connected:
            messagebox.showwarning("Not Connected", "Please connect to servo controller first.")
            return
            
        self.log_message("Testing motor 1...", "#00ff00", "servo_cmd")
        positions = [180, 120, 150]
        for pos in positions:
            success = self.servo_controller.send_servo_positions(
                motor_ids=[1],
                motor_types=[RobotServoControllerUSB.MOTORTYPE_AX12],
                positions_degrees=[pos],
                velocities_rpm=[30.0]
            )
            if success:
                self.log_message(f"  Motor 1 moved to {pos}°", "#00ff00", "servo_cmd")
            else:
                self.log_message(f"  Failed to move motor 1 to {pos}°", "#ff4444", "servo_error")
            time.sleep(1)
            
    def test_all_motors(self):
        """Test all motors"""
        if not self.servo_connected:
            messagebox.showwarning("Not Connected", "Please connect to servo controller first.")
            return
            
        self.log_message("Testing all motors...", "#00ff00", "servo_cmd")
        positions = [180] * 12
        success = self.servo_controller.send_all_servos(positions)
        if success:
            self.log_message("✓ All motors moved to 180°", "#00ff00", "servo_cmd")
            time.sleep(2)
            self.move_to_neutral()
        else:
            self.log_message("✗ Failed to move all motors", "#ff4444", "servo_error")
            
    def move_single_motor(self):
        """Move a single motor to specified position"""
        if not self.servo_connected:
            messagebox.showwarning("Not Connected", "Please connect to servo controller first.")
            return
            
        try:
            motor_id = int(self.motor_id_var.get())
            position = float(self.position_var.get())
            velocity = float(self.velocity_var.get())
            
            if not (1 <= motor_id <= 12):
                raise ValueError("Motor ID must be between 1 and 12")
            if not (0 <= position <= 300):
                raise ValueError("Position must be between 0 and 300 degrees")
                
            self.log_message(f"Moving motor {motor_id} to {position}° at {velocity} RPM...", "#00ff00", "servo_cmd")
            success = self.servo_controller.send_servo_positions(
                motor_ids=[motor_id],
                motor_types=[RobotServoControllerUSB.MOTORTYPE_AX12],
                positions_degrees=[position],
                velocities_rpm=[velocity]
            )
            if success:
                self.log_message(f"✓ Motor {motor_id} command sent successfully", "#00ff00", "servo_cmd")
            else:
                self.log_message(f"✗ Failed to send command to motor {motor_id}", "#ff4444", "servo_error")
                
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Could not move motor:\n{e}")
            self.log_message(f"Error: {e}", "#ff4444", "servo_error")
            
    def send_all_servos(self, positions):
        """Send positions to all servos"""
        if not self.servo_connected:
            messagebox.showwarning("Not Connected", "Please connect to servo controller first.")
            return
            
        self.log_message(f"Moving all servos to preset positions: {positions[:3]}...", "#00ff00", "servo_cmd")
        success = self.servo_controller.send_all_servos(positions)
        if success:
            self.log_message("✓ All servos command sent successfully", "#00ff00", "servo_cmd")
        else:
            self.log_message("✗ Failed to send command to all servos", "#ff4444", "servo_error")


def main():
    root = tk.Tk()
    app = LS6IntegratedControl(root)
    root.mainloop()


if __name__ == "__main__":
    main()

