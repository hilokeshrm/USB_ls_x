import serial
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime

class LS6LogsReaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LS6 Logs Reader")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # Serial connection variables
        self.ser = None
        self.is_connected = False
        self.read_thread = None
        self.stop_reading = False
        
        # Default settings
        self.port_var = tk.StringVar(value="COM21")
        self.baud_var = tk.StringVar(value="57600")
        
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
            text="LS6 Serial Logs Reader",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=12)
        
        # Connection frame
        conn_frame = tk.Frame(self.root, bg="#ecf0f1", relief=tk.RAISED, bd=2)
        conn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Port configuration
        port_label = tk.Label(conn_frame, text="Port:", bg="#ecf0f1", font=("Arial", 10))
        port_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        port_entry = tk.Entry(conn_frame, textvariable=self.port_var, width=15, font=("Arial", 10))
        port_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Baud rate configuration
        baud_label = tk.Label(conn_frame, text="Baud Rate:", bg="#ecf0f1", font=("Arial", 10))
        baud_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        baud_entry = tk.Entry(conn_frame, textvariable=self.baud_var, width=15, font=("Arial", 10))
        baud_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Connect/Disconnect button
        self.conn_button = tk.Button(
            conn_frame,
            text="Connect",
            command=self.toggle_connection,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12,
            cursor="hand2"
        )
        self.conn_button.grid(row=0, column=4, padx=10, pady=5)
        
        # Status indicator
        self.status_label = tk.Label(
            conn_frame,
            text="● Disconnected",
            bg="#ecf0f1",
            fg="#e74c3c",
            font=("Arial", 10, "bold")
        )
        self.status_label.grid(row=0, column=5, padx=10, pady=5)
        
        # Logs display area
        logs_frame = tk.Frame(self.root, bg="#ffffff", relief=tk.SUNKEN, bd=2)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Logs header with search
        logs_header = tk.Frame(logs_frame, bg="#ffffff")
        logs_header.pack(fill=tk.X, padx=5, pady=5)
        
        logs_label = tk.Label(
            logs_header,
            text="Logs Output:",
            bg="#ffffff",
            font=("Arial", 10, "bold"),
            anchor=tk.W
        )
        logs_label.pack(side=tk.LEFT)
        
        # Search frame
        search_frame = tk.Frame(logs_header, bg="#ffffff")
        search_frame.pack(side=tk.RIGHT, padx=5)
        
        search_label = tk.Label(
            search_frame,
            text="Search:",
            bg="#ffffff",
            font=("Arial", 9)
        )
        search_label.pack(side=tk.LEFT, padx=2)
        
        self.search_entry = tk.Entry(
            search_frame,
            font=("Arial", 9),
            width=20
        )
        self.search_entry.pack(side=tk.LEFT, padx=2)
        self.search_entry.bind("<Return>", lambda e: self.search_text())
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_text())
        
        # Case sensitive checkbox
        self.case_var = tk.BooleanVar()
        case_check = tk.Checkbutton(
            search_frame,
            text="Case",
            variable=self.case_var,
            bg="#ffffff",
            font=("Arial", 8),
            command=self.search_text
        )
        case_check.pack(side=tk.LEFT, padx=2)
        
        # Search buttons
        prev_button = tk.Button(
            search_frame,
            text="◀",
            command=self.search_previous,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 8),
            width=3,
            cursor="hand2"
        )
        prev_button.pack(side=tk.LEFT, padx=1)
        
        next_button = tk.Button(
            search_frame,
            text="▶",
            command=self.search_next,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 8),
            width=3,
            cursor="hand2"
        )
        next_button.pack(side=tk.LEFT, padx=1)
        
        # Match count label
        self.match_count_label = tk.Label(
            search_frame,
            text="",
            bg="#ffffff",
            font=("Arial", 8),
            fg="#7f8c8d"
        )
        self.match_count_label.pack(side=tk.LEFT, padx=5)
        
        clear_search_button = tk.Button(
            search_frame,
            text="✕",
            command=self.clear_search,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 8),
            width=3,
            cursor="hand2"
        )
        clear_search_button.pack(side=tk.LEFT, padx=2)
        
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
        
        # Configure search highlight tag
        self.logs_text.tag_config("search_highlight", background="#ffff00", foreground="#000000")
        self.logs_text.tag_config("current_match", background="#ff8800", foreground="#000000")
        
        # Bind Ctrl+C globally to send interrupt
        self.root.bind_all("<Control-c>", lambda e: self.send_interrupt())
        self.root.bind_all("<Control-C>", lambda e: self.send_interrupt())
        
        # Command input frame
        cmd_frame = tk.Frame(self.root, bg="#ecf0f1", relief=tk.RAISED, bd=2)
        cmd_frame.pack(fill=tk.X, padx=10, pady=10)
        
        cmd_label = tk.Label(
            cmd_frame,
            text="Send Command:",
            bg="#ecf0f1",
            font=("Arial", 10, "bold")
        )
        cmd_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.cmd_entry = tk.Entry(
            cmd_frame,
            font=("Arial", 10),
            width=50
        )
        self.cmd_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        self.cmd_entry.bind("<Return>", lambda e: self.send_command())
        
        send_button = tk.Button(
            cmd_frame,
            text="Send",
            command=self.send_command,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            width=10,
            cursor="hand2"
        )
        send_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Ctrl+C interrupt button
        interrupt_button = tk.Button(
            cmd_frame,
            text="Ctrl+C",
            command=self.send_interrupt,
            bg="#e67e22",
            fg="white",
            font=("Arial", 9, "bold"),
            width=8,
            cursor="hand2"
        )
        interrupt_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Clear button
        clear_button = tk.Button(
            cmd_frame,
            text="Clear Logs",
            command=self.clear_logs,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10),
            width=12,
            cursor="hand2"
        )
        clear_button.pack(side=tk.LEFT, padx=5, pady=5)
        
    def log_message(self, message, color="#d4d4d4"):
        """Add a message to the logs display"""
        self.logs_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n", "log")
        self.logs_text.tag_config("log", foreground=color)
        self.logs_text.see(tk.END)
        self.logs_text.config(state=tk.DISABLED)
        
    def clear_logs(self):
        """Clear the logs display"""
        self.logs_text.config(state=tk.NORMAL)
        self.logs_text.delete(1.0, tk.END)
        self.logs_text.config(state=tk.DISABLED)
        self.clear_search()
        
    def clear_search(self):
        """Clear search highlights and reset search"""
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
        """Search for text in logs and highlight matches"""
        search_term = self.search_entry.get()
        self.case_sensitive = self.case_var.get()
        
        # Remove previous highlights
        self.remove_search_highlights()
        self.search_matches = []
        self.current_match_index = -1
        
        if not search_term:
            self.match_count_label.config(text="")
            return
            
        self.logs_text.config(state=tk.NORMAL)
        
        # Use text widget's search method
        start_pos = 1.0
        nocase = 0 if self.case_sensitive else 1
        
        while True:
            # Search for the term
            pos = self.logs_text.search(search_term, start_pos, tk.END, nocase=nocase)
            if not pos:
                break
                
            # Calculate end position
            end_pos = f"{pos}+{len(search_term)}c"
            
            self.search_matches.append((pos, end_pos))
            
            # Highlight match
            self.logs_text.tag_add("search_highlight", pos, end_pos)
            
            # Move start position for next search
            start_pos = end_pos
            
        # Update match count
        match_count = len(self.search_matches)
        if match_count > 0:
            self.match_count_label.config(text=f"{match_count} match{'es' if match_count != 1 else ''}")
            # Go to first match
            self.current_match_index = 0
            self.highlight_current_match()
        else:
            self.match_count_label.config(text="No matches")
            
        self.logs_text.config(state=tk.DISABLED)
        
    def highlight_current_match(self):
        """Highlight the current match"""
        if not self.search_matches or self.current_match_index < 0:
            return
            
        # Remove current match highlight from all
        self.logs_text.config(state=tk.NORMAL)
        self.logs_text.tag_remove("current_match", 1.0, tk.END)
        
        # Highlight current match
        if 0 <= self.current_match_index < len(self.search_matches):
            start, end = self.search_matches[self.current_match_index]
            self.logs_text.tag_add("current_match", start, end)
            self.logs_text.see(start)
            
        self.logs_text.config(state=tk.DISABLED)
        
    def search_next(self):
        """Navigate to next search match"""
        if not self.search_matches:
            self.search_text()
            return
            
        if self.current_match_index < len(self.search_matches) - 1:
            self.current_match_index += 1
        else:
            self.current_match_index = 0  # Wrap around
            
        self.highlight_current_match()
        
    def search_previous(self):
        """Navigate to previous search match"""
        if not self.search_matches:
            self.search_text()
            return
            
        if self.current_match_index > 0:
            self.current_match_index -= 1
        else:
            self.current_match_index = len(self.search_matches) - 1  # Wrap around
            
        self.highlight_current_match()
        
    def toggle_connection(self):
        """Connect or disconnect from serial port"""
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()
            
    def connect(self):
        """Connect to serial port"""
        try:
            port = self.port_var.get()
            baud = int(self.baud_var.get())
            
            self.ser = serial.Serial(port, baud, timeout=0.1)
            self.is_connected = True
            self.stop_reading = False
            
            # Update UI
            self.conn_button.config(text="Disconnect", bg="#e74c3c")
            self.status_label.config(text="● Connected", fg="#27ae60")
            
            self.log_message(f"Connected to {port} at {baud} baud", "#27ae60")
            
            # Start reading thread
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
            
        # Update UI
        self.conn_button.config(text="Connect", bg="#27ae60")
        self.status_label.config(text="● Disconnected", fg="#e74c3c")
        
        self.log_message("Disconnected from serial port", "#e74c3c")
        
    def read_serial(self):
        """Read from serial port in a separate thread"""
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
        """Send Ctrl+C interrupt signal to serial port"""
        if not self.is_connected or not self.ser or not self.ser.is_open:
            return  # Silently return if not connected
            
        try:
            # Send Ctrl+C (ASCII 0x03, interrupt character)
            interrupt_char = b'\x03'
            self.ser.write(interrupt_char)
            self.log_message(">>> [Ctrl+C] Interrupt signal sent", "#ff8800")
        except Exception as e:
            self.log_message(f"Interrupt send error: {e}", "#e74c3c")
    
    def send_command(self):
        """Send command to serial port"""
        if not self.is_connected or not self.ser or not self.ser.is_open:
            messagebox.showwarning("Not Connected", "Please connect to serial port first.")
            return
            
        command = self.cmd_entry.get()
        # Clear the entry field
        self.cmd_entry.delete(0, tk.END)
        
        try:
            # Add newline if not present (even for empty commands)
            if not command.endswith('\n'):
                command += '\n'
                
            self.ser.write(command.encode('utf-8'))
            # Display sent command (show as "(empty)" if just newline)
            display_cmd = command.strip() if command.strip() else "(empty)"
            self.log_message(f">>> {display_cmd}", "#3498db")
            
        except Exception as e:
            messagebox.showerror("Send Error", f"Could not send command:\n{e}")
            self.log_message(f"Send error: {e}", "#e74c3c")


def main():
    root = tk.Tk()
    app = LS6LogsReaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
