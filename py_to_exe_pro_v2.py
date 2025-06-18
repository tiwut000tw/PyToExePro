import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import sys
import webbrowser
import os

# --- Constants ---
APP_NAME = "Py-to-EXE-Pro"
APP_VERSION = "1.1" # Version updated
WINDOW_SIZE = "700x780"
PYINSTALLER_CHECK_STAGES = {
    "Building": 10,
    "checking": 20,
    "Analyzing": 40,
    "Building": 60,
    "Assembling": 80,
    "Completed": 100,
}

class PyToExeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(WINDOW_SIZE)
        self.resizable(False, False)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # --- Class Variables ---
        self.script_path = ctk.StringVar()
        self.icon_path = ctk.StringVar()
        self.output_type = ctk.StringVar(value="onefile")
        self.console_type = ctk.StringVar(value="windowed")
        self.output_dir = ""

        # --- Main Frame ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.create_widgets()
        # Run the check in a thread to keep UI responsive
        threading.Thread(target=self.check_system_startup, daemon=True).start()

    def create_widgets(self):
        # ... (The UI creation is the same as before, so I'll shorten it for brevity)
        # --- Title ---
        title_label = ctk.CTkLabel(self.main_frame, text=APP_NAME, font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(10, 20))

        # --- 1. Dependencies Section ---
        dep_frame = ctk.CTkFrame(self.main_frame)
        dep_frame.pack(fill="x", padx=20, pady=10)

        self.dep_button = ctk.CTkButton(dep_frame, text="Check Dependencies", command=self.show_install_instructions)
        self.dep_button.pack(side="left", padx=10, pady=10)
        self.dep_status_label = ctk.CTkLabel(dep_frame, text="Checking system...", text_color="orange")
        self.dep_status_label.pack(side="left", padx=10, pady=10)

        # --- 2. Script Selection Section ---
        script_frame = ctk.CTkFrame(self.main_frame)
        script_frame.pack(fill="x", padx=20, pady=10)
        script_label = ctk.CTkLabel(script_frame, text="Python Script (.py):")
        script_label.pack(side="left", padx=10, pady=10)
        script_entry = ctk.CTkEntry(script_frame, textvariable=self.script_path, width=300)
        script_entry.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        script_button = ctk.CTkButton(script_frame, text="Browse...", command=self.select_script)
        script_button.pack(side="left", padx=10, pady=10)

        # --- 3. Options Section ---
        options_frame = ctk.CTkFrame(self.main_frame)
        options_frame.pack(fill="x", padx=20, pady=10)
        output_type_label = ctk.CTkLabel(options_frame, text="Output Type:")
        output_type_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        one_file_radio = ctk.CTkRadioButton(options_frame, text="One-File (.exe)", variable=self.output_type, value="onefile")
        one_file_radio.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        one_dir_radio = ctk.CTkRadioButton(options_frame, text="One-Directory (Folder)", variable=self.output_type, value="onedir")
        one_dir_radio.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        console_type_label = ctk.CTkLabel(options_frame, text="Console:")
        console_type_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        windowed_radio = ctk.CTkRadioButton(options_frame, text="Windowless (for GUI)", variable=self.console_type, value="windowed")
        windowed_radio.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        console_radio = ctk.CTkRadioButton(options_frame, text="Show Console Window", variable=self.console_type, value="console")
        console_radio.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        
        # Icon
        icon_frame = ctk.CTkFrame(self.main_frame)
        icon_frame.pack(fill="x", padx=20, pady=10)
        icon_label = ctk.CTkLabel(icon_frame, text="Icon File (.ico):")
        icon_label.pack(side="left", padx=10, pady=10)
        icon_entry = ctk.CTkEntry(icon_frame, textvariable=self.icon_path, width=250)
        icon_entry.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        icon_browse_button = ctk.CTkButton(icon_frame, text="Browse...", command=self.select_icon)
        icon_browse_button.pack(side="left", padx=10, pady=10)
        icon_clear_button = ctk.CTkButton(icon_frame, text="Clear", width=50, command=lambda: self.icon_path.set(""))
        icon_clear_button.pack(side="left", padx=10, pady=10)

        # --- 4. Build Section ---
        build_frame = ctk.CTkFrame(self.main_frame)
        build_frame.pack(fill="x", padx=20, pady=10)
        self.build_button = ctk.CTkButton(build_frame, text="BUILD .EXE", font=ctk.CTkFont(size=14, weight="bold"), state="disabled", command=self.build_thread)
        self.build_button.pack(side="left", padx=10, pady=10, ipady=5)
        self.open_folder_button = ctk.CTkButton(build_frame, text="Open Output Folder", state="disabled", command=self.open_output_folder)
        self.open_folder_button.pack(side="right", padx=10, pady=10)
        
        # --- 5. Progress & Log Section ---
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.progress_bar = ctk.CTkProgressBar(log_frame, orientation="horizontal")
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=(10, 5))
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", wrap="word", font=("Courier New", 10))
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=(5, 10))

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")
        self.update_idletasks()

    def update_progress(self, line):
        for stage, value in PYINSTALLER_CHECK_STAGES.items():
            if stage in line:
                self.progress_bar.set(value / 100)
                break
        self.update_idletasks()

    def select_script(self):
        path = filedialog.askopenfilename(title="Select a Python Script", filetypes=[("Python Files", "*.py *.pyw")])
        if path: self.script_path.set(path)

    def select_icon(self):
        path = filedialog.askopenfilename(title="Select an Icon", filetypes=[("Icon Files", "*.ico")])
        if path: self.icon_path.set(path)

    def open_output_folder(self):
        if self.output_dir and os.path.isdir(self.output_dir):
            webbrowser.open(os.path.realpath(self.output_dir))
        else:
            self.log("ERROR: Output directory not found or not set.")

    # --- MAJOR CORRECTION HERE ---
    def check_system_startup(self):
        """Checks for PyInstaller in the system PATH."""
        self.log("--- System Check ---")
        self.log("Checking for PyInstaller...")
        
        try:
            # We try to run pyinstaller directly. This works if it's in the PATH.
            # CREATE_NO_WINDOW prevents a console flash.
            subprocess.run(['pyinstaller', '--version'], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log("SUCCESS: PyInstaller found in system PATH.")
            self.dep_status_label.configure(text="Ready to build!", text_color="green")
            self.build_button.configure(state="normal")
            self.dep_button.configure(state="disabled", text="Dependencies OK")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("ERROR: PyInstaller not found in your system's PATH.")
            self.log("Please install it by running 'pip install pyinstaller' in your terminal.")
            self.dep_status_label.configure(text="PyInstaller not found!", text_color="red")
            self.dep_button.configure(state="normal", text="Show Install Instructions")
            self.build_button.configure(state="disabled")

    def show_install_instructions(self):
        """Shows a helpful message box to the user."""
        messagebox.showinfo(
            "PyInstaller Not Found",
            "To build an EXE, PyInstaller must be installed and accessible.\n\n"
            "1. Open a Command Prompt (CMD) or PowerShell.\n"
            "2. Type the following command and press Enter:\n\n"
            "pip install pyinstaller\n\n"
            "After installation, please restart this application."
        )

    def build_thread(self):
        thread = threading.Thread(target=self.build_exe, daemon=True)
        thread.start()

    def build_exe(self):
        script = self.script_path.get()
        if not script or not os.path.exists(script):
            self.log("ERROR: Please select a valid Python script first.")
            return

        self.build_button.configure(state="disabled", text="BUILDING...")
        self.open_folder_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.log("\n--- Starting Build Process ---")

        command = ['pyinstaller', '--noconfirm', '--clean']
        if self.output_type.get() == "onefile": command.append('--onefile')
        if self.console_type.get() == "windowed": command.append('--windowed')
        icon = self.icon_path.get()
        if icon and os.path.exists(icon): command.extend(['--icon', icon])
        command.append(script)
        
        self.log(f"Running command: {' '.join(command)}")
        
        try:
            # CREATE_NO_WINDOW is crucial here for a clean GUI experience
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None: break
                if output:
                    clean_output = output.strip()
                    self.log(clean_output)
                    self.update_progress(clean_output)
            
            if process.returncode == 0:
                self.log("\n--- BUILD SUCCESSFUL ---")
                self.progress_bar.set(1)
                self.output_dir = os.path.join(os.path.dirname(script), "dist")
                self.log(f"Executable created in: {self.output_dir}")
                self.open_folder_button.configure(state="normal")
            else:
                self.log(f"\n--- BUILD FAILED (Code: {process.returncode}) ---")
                self.progress_bar.configure(progress_color="red")
        except FileNotFoundError:
            self.log("ERROR: 'pyinstaller' command not found. Your PATH might have changed. Please restart.")
        except Exception as e:
            self.log(f"An unexpected error occurred: {e}")
        finally:
            self.build_button.configure(state="normal", text="BUILD .EXE")


# --- ESSENTIAL GUARD FOR PACKAGED APPS ---
if __name__ == "__main__":
    # On Windows, multiprocessing/subprocesses can cause issues.
    # This check is not strictly needed with the new code but is best practice.
    # from multiprocessing import freeze_support
    # freeze_support() 

    app = PyToExeApp()
    app.mainloop()