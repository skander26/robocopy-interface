import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import sys
import os

# Set the appearance mode to dark and use the blue color theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ToolTip:
    """
    A simple ToolTip class to display hover text for Tkinter/CustomTkinter widgets.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            tw, text=self.text, background="#2b2b2b", foreground="white", 
            relief="solid", borderwidth=1, justify="left", 
            padx=5, pady=5, font=("Segoe UI", 10)
        )
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class RobocopyGUI(ctk.CTk):
    """
    A comprehensive, modern Graphical User Interface (GUI) wrapper
    for the Windows robocopy utility using CustomTkinter.
    """
    def __init__(self):
        super().__init__()

        self.title("Robocopy Modern GUI")
        self.geometry("900x750")
        self.minsize(800, 700)

        self.process = None
        self.is_running = False

        self._build_ui()

    def _build_ui(self):
        """Constructs the user interface components."""
        # Main layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # The terminal output will expand

        # 1. Path Selection Frame
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(1, weight=1)

        # Source
        ctk.CTkLabel(self.path_frame, text="Source:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.source_var = ctk.StringVar()
        self.source_entry = ctk.CTkEntry(
            self.path_frame, 
            textvariable=self.source_var, 
            placeholder_text="Select or type source directory..."
        )
        self.source_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.source_btn = ctk.CTkButton(self.path_frame, text="Browse", command=self._browse_source)
        self.source_btn.grid(row=0, column=2, padx=10, pady=10)

        # Destination
        ctk.CTkLabel(self.path_frame, text="Destination:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.dest_var = ctk.StringVar()
        self.dest_entry = ctk.CTkEntry(
            self.path_frame, 
            textvariable=self.dest_var, 
            placeholder_text="Select or type destination directory..."
        )
        self.dest_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        self.dest_btn = ctk.CTkButton(self.path_frame, text="Browse", command=self._browse_dest)
        self.dest_btn.grid(row=1, column=2, padx=10, pady=10)

        # 2. Options Frame (Toggles and Advanced)
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.options_frame.grid_columnconfigure((0, 1), weight=1)

        # Toggles
        self.toggles_frame = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.toggles_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        ctk.CTkLabel(
            self.toggles_frame, 
            text="Core Options", 
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # /MIR
        mir_info = ctk.CTkLabel(self.toggles_frame, text="ℹ️", cursor="hand2")
        mir_info.grid(row=1, column=0, sticky="w", padx=(0, 5))
        ToolTip(mir_info, "Mirrors a directory tree.\nCopies all subdirectories and deletes files in the\ndestination that no longer exist in the source.")
        
        self.mir_var = ctk.BooleanVar(value=False)
        self.mir_check = ctk.CTkCheckBox(self.toggles_frame, text="/MIR (Mirror mode)", variable=self.mir_var)
        self.mir_check.grid(row=1, column=1, sticky="w", pady=5)
        
        self.mir_warning = ctk.CTkLabel(
            self.toggles_frame, 
            text="WARNING: Deletes extra files in destination!", 
            text_color="#ff4444", 
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.mir_warning.grid(row=1, column=2, sticky="w", padx=10, pady=5)

        # /E
        e_info = ctk.CTkLabel(self.toggles_frame, text="ℹ️", cursor="hand2")
        e_info.grid(row=2, column=0, sticky="w", padx=(0, 5))
        ToolTip(e_info, "Copies all subdirectories, including empty ones.")

        self.e_var = ctk.BooleanVar(value=True)
        self.e_check = ctk.CTkCheckBox(
            self.toggles_frame, 
            text="/E (Copy subdirs, including empty)", 
            variable=self.e_var
        )
        self.e_check.grid(row=2, column=1, sticky="w", pady=5)

        # /Z
        z_info = ctk.CTkLabel(self.toggles_frame, text="ℹ️", cursor="hand2")
        z_info.grid(row=3, column=0, sticky="w", padx=(0, 5))
        ToolTip(z_info, "Copies files in restartable mode.\nUseful for large files or unstable network connections.")

        self.z_var = ctk.BooleanVar(value=True)
        self.z_check = ctk.CTkCheckBox(self.toggles_frame, text="/Z (Restartable mode)", variable=self.z_var)
        self.z_check.grid(row=3, column=1, sticky="w", pady=5)

        # /L
        l_info = ctk.CTkLabel(self.toggles_frame, text="ℹ️", cursor="hand2")
        l_info.grid(row=4, column=0, sticky="w", padx=(0, 5))
        ToolTip(l_info, "List only. Simulates the copy process without\nactually copying, deleting, or moving any files.")

        self.l_var = ctk.BooleanVar(value=False)
        self.l_check = ctk.CTkCheckBox(self.toggles_frame, text="/L (List only / Dry run)", variable=self.l_var)
        self.l_check.grid(row=4, column=1, sticky="w", pady=5)

        # Advanced Parameters
        self.adv_frame = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.adv_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nw")

        ctk.CTkLabel(
            self.adv_frame, 
            text="Advanced Parameters", 
            font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # /MT
        mt_info = ctk.CTkLabel(self.adv_frame, text="ℹ️", cursor="hand2")
        mt_info.grid(row=1, column=0, sticky="w", padx=(0, 5))
        ToolTip(mt_info, "Multithreading. Creates multi-threaded copies\n(default is 8, max is 128). Improves performance.")

        ctk.CTkLabel(self.adv_frame, text="/MT: (Threads)").grid(row=1, column=1, sticky="w", pady=5)
        self.mt_var = ctk.StringVar(value="8")
        self.mt_entry = ctk.CTkEntry(self.adv_frame, textvariable=self.mt_var, width=60)
        self.mt_entry.grid(row=1, column=2, sticky="w", padx=10, pady=5)

        # /R
        r_info = ctk.CTkLabel(self.adv_frame, text="ℹ️", cursor="hand2")
        r_info.grid(row=2, column=0, sticky="w", padx=(0, 5))
        ToolTip(r_info, "Number of retries on failed copies.\n(default is 1 million). Setting this lower saves time on errors.")

        ctk.CTkLabel(self.adv_frame, text="/R: (Retries)").grid(row=2, column=1, sticky="w", pady=5)
        self.r_var = ctk.StringVar(value="5")
        self.r_entry = ctk.CTkEntry(self.adv_frame, textvariable=self.r_var, width=60)
        self.r_entry.grid(row=2, column=2, sticky="w", padx=10, pady=5)

        # /W
        w_info = ctk.CTkLabel(self.adv_frame, text="ℹ️", cursor="hand2")
        w_info.grid(row=3, column=0, sticky="w", padx=(0, 5))
        ToolTip(w_info, "Wait time between retries in seconds.\n(default is 30 seconds).")

        ctk.CTkLabel(self.adv_frame, text="/W: (Wait time sec)").grid(row=3, column=1, sticky="w", pady=5)
        self.w_var = ctk.StringVar(value="5")
        self.w_entry = ctk.CTkEntry(self.adv_frame, textvariable=self.w_var, width=60)
        self.w_entry.grid(row=3, column=2, sticky="w", padx=10, pady=5)

        # 3. Execution Controls Frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.controls_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.generate_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Generate Command", 
            command=self._generate_command, 
            fg_color="gray", 
            hover_color="darkgray"
        )
        self.generate_btn.grid(row=0, column=0, padx=10, pady=10)

        self.start_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Start Copy", 
            command=self._start_copy, 
            fg_color="#2b8a3e", 
            hover_color="#237032"
        )
        self.start_btn.grid(row=0, column=1, padx=10, pady=10)

        self.stop_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Cancel/Stop", 
            command=self._stop_copy, 
            fg_color="#c92a2a", 
            hover_color="#a61e1e", 
            state="disabled"
        )
        self.stop_btn.grid(row=0, column=2, padx=10, pady=10)

        # 4. Live Terminal Output
        self.terminal_frame = ctk.CTkFrame(self)
        self.terminal_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.terminal_frame.grid_columnconfigure(0, weight=1)
        self.terminal_frame.grid_rowconfigure(0, weight=1)

        self.terminal_text = ctk.CTkTextbox(
            self.terminal_frame, 
            font=ctk.CTkFont(family="Consolas", size=12), 
            state="disabled", 
            wrap="none"
        )
        self.terminal_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def _browse_source(self):
        """Opens a directory dialog for selecting the source directory."""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_var.set(os.path.normpath(directory))

    def _browse_dest(self):
        """Opens a directory dialog for selecting the destination directory."""
        directory = filedialog.askdirectory(title="Select Destination Directory")
        if directory:
            self.dest_var.set(os.path.normpath(directory))

    def _append_to_terminal(self, text):
        """
        Appends text to the terminal text box in a thread-safe manner.
        
        Args:
            text (str): The string to append to the text box.
        """
        self.terminal_text.configure(state="normal")
        self.terminal_text.insert("end", text)
        self.terminal_text.see("end")
        self.terminal_text.configure(state="disabled")

    def _clear_terminal(self):
        """Clears all text from the terminal text box."""
        self.terminal_text.configure(state="normal")
        self.terminal_text.delete("1.0", "end")
        self.terminal_text.configure(state="disabled")

    def _build_command(self):
        """
        Builds the robocopy command list based on current UI inputs.
        
        Returns:
            list: A list of strings representing the robocopy command and its arguments,
                  or None if validation fails.
        """
        source = self.source_var.get().strip()
        dest = self.dest_var.get().strip()

        if not source or not dest:
            messagebox.showerror("Error", "Source and Destination paths are required.")
            return None

        # Base command
        cmd = ["robocopy", source, dest]

        # Toggles
        if self.mir_var.get():
            cmd.append("/MIR")
        if self.e_var.get():
            cmd.append("/E")
        if self.z_var.get():
            cmd.append("/Z")
        if self.l_var.get():
            cmd.append("/L")

        # Advanced
        mt = self.mt_var.get().strip()
        if mt.isdigit():
            cmd.append(f"/MT:{mt}")
            
        r = self.r_var.get().strip()
        if r.isdigit():
            cmd.append(f"/R:{r}")
            
        w = self.w_var.get().strip()
        if w.isdigit():
            cmd.append(f"/W:{w}")

        # Add /NP to avoid spamming the log with progress percentages
        cmd.append("/NP")
        # Add /BYTES to output exact sizes instead of auto-formatting for easier parsing
        cmd.append("/BYTES")
        
        return cmd

    def _generate_command(self):
        """Generates and previews the robocopy command in the terminal."""
        cmd = self._build_command()
        if cmd:
            self._clear_terminal()
            command_str = " ".join([f'"{x}"' if ' ' in x and not x.startswith('/') else x for x in cmd])
            self._append_to_terminal(f"Generated Command:\n{command_str}\n\n")

    def _start_copy(self):
        """Initiates the robocopy process in a separate background thread."""
        if self.is_running:
            return

        cmd = self._build_command()
        if not cmd:
            return

        self._clear_terminal()
        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.generate_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # Start the background thread for executing the command
        self.thread = threading.Thread(target=self._run_robocopy, args=(cmd,), daemon=True)
        self.thread.start()

    def _run_robocopy(self, cmd):
        """
        Executes the robocopy command and reads its output in real-time.
        This method must be run in a separate thread to prevent GUI freezing.
        
        Args:
            cmd (list): The list of arguments representing the command.
        """
        try:
            command_str = " ".join([f'"{x}"' if ' ' in x and not x.startswith('/') else x for x in cmd])
            self.after(0, self._append_to_terminal, f"Executing: {command_str}\n{'-'*50}\n")
            
            # Use CREATE_NO_WINDOW to hide the console window popup on Windows
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=creationflags
            )

            # Read stdout line by line
            # Windows command line typically uses cp437, cp850, or cp1252.
            # We try decoding with utf-8 first, then fallback to cp1252.
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                
                try:
                    decoded_line = line.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_line = line.decode('cp1252', errors='replace')
                    
                # Send the update back to the main GUI thread safely
                self.after(0, self._append_to_terminal, decoded_line)

            self.process.wait()
            
            # Print exit code information
            exit_code = self.process.returncode
            self.after(0, self._append_to_terminal, f"\n{'-'*50}\nProcess finished with exit code {exit_code}\n")

        except Exception as e:
            self.after(0, self._append_to_terminal, f"\nError occurred: {str(e)}\n")
        finally:
            self.after(0, self._reset_ui_state)

    def _stop_copy(self):
        """Terminates the running robocopy subprocess cleanly."""
        if self.process and self.process.poll() is None:
            self._append_to_terminal("\n[!] Cancelling process...\n")
            self.process.terminate()
            
    def _reset_ui_state(self):
        """Resets the UI buttons and flags after execution completes or stops."""
        self.is_running = False
        self.process = None
        self.start_btn.configure(state="normal")
        self.generate_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")


if __name__ == "__main__":
    app = RobocopyGUI()
    app.mainloop()
