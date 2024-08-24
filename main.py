import os
import sys
import tkinter as tk
from tkinter import ttk
import sys
import time
import threading

from codebase import config
from codebase.config import is_debug, TOTAL_SESSIONS, IS_ANALYZE_ALL_SESSIONS, session_num, DATA_DIR, RESULTS_DIR, PROCESSING_DIR
from codebase.clean import clean_input_data
from codebase.process import process_cleaned_data
from codebase.analyze import analyze_processed_data

sys.path.append(os.getcwd())

# READ THIS - VERY IMPORTANT
# To change the Togglable Options that affect how the code runs,
# see config.py
# VERY IMPORTANT - READ THIS

# Run current session_num
def run_session():
    print("Started working with Session", config.session_num)

    # Clean the input data
    data_path = os.path.join(DATA_DIR, config.session_num)
    clean_input_data(data_path)

    # Process the cleaned data (search the text for arguments)
    all_args_indexed = {} # keys = deliberation ids, values = (argument, index in deliberation)
    all_args = []
    process_cleaned_data(data_path, all_args_indexed, all_args)

    # Analyze the processed data (compare arguments to generated policies)
    analyze_processed_data(all_args_indexed, all_args)
    
    print("\nFinished working with Session", config.session_num)

# Run all selected sessions
def main(*selected_sessions):
    print("\nProgram Started")
    for session in selected_sessions:
        config.session_num = session
        run_session()
    print("Program Finished\n")

# Display Console/Terminal output on GUI Progress Bar Screen
class RedirectOutput:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

# GUI Progress Bar Screen
def progress_bar(root, session_vars, debug_var, restart_var, current_frame):
    current_frame.destroy()
    root.title("Progress Bar")
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(2, weight=1)
    frame.rowconfigure(3, weight=1)

    num_transcripts = 10 # TODO: Calculate number of transcripts based on 'data' folder

    selected_sessions = [f"{i+1}" for i, var in enumerate(session_vars) if var.get() == 1]
    config.is_debug = debug_var.get() == 1
    hard_restart = restart_var.get() == 1
    
    # Text above the Phase Progress Bar
    phases = ["Cleaning", "Processing", "Analyzing"]
    for i, phase in enumerate(phases):
        phase_progress_text = tk.Label(frame, text=phase)
        phase_progress_text.grid(row=0, column=i)
    
    # Phase Progress Bar
    phase_progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
    phase_progress_bar.grid(row=1, column=0, columnspan=3, pady=5, padx=10, sticky='ew')

    # Transcript Progress Bar
    transcript_progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
    transcript_progress_bar.grid(row=2, column=1, pady=5, padx=10, sticky='ew')

    # Text to the right of the Transcript Progress Bar
    transcript_progress_text = tk.Label(frame, text=f"0/{num_transcripts}")
    transcript_progress_text.grid(row=2, column=2, padx=10, sticky='w')

    # Console/Terminal Output Textbox
    text = tk.Text(frame, wrap='word', state='normal')
    text.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

    sys.stdout = RedirectOutput(text)

    phase_progress_bar['value'] = 0
    phase_progress_bar['maximum'] = 100
    transcript_progress_bar['value'] = 0
    transcript_progress_bar['maximum'] = 100

    threading.Thread(target=main, args=(selected_sessions), daemon=True).start()

# Clear the GUI and restart the program
def restart_program(root, current_frame):
    current_frame.destroy()
    main_menu(root)

# GUI HelpBox with instructions
class HelpBox:
    def __init__(self, parent, text):
        self.parent = parent
        self.text = text
        self.tooltip = None

    def show_tooltip(self, event):
        if self.tooltip:
            return
        x = event.x_root + 10
        y = event.y_root + 10
        self.tooltip = tk.Toplevel(self.parent)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="light yellow", relief="solid", borderwidth=3, padx=10, pady=5)
        label.pack(expand=True)

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

# GUI Icon of a circle with an 'i' inside it
def create_info_icon(parent, row, column, text):
    canvas = tk.Canvas(parent, width=20, height=20)
    canvas.grid(row=row, column=column, padx=10, pady=10)
    
    # Draw the icon
    canvas.create_oval(4, 4, 20, 20, outline="black", fill="white", tags="info")
    canvas.create_text(13, 12, text="i", fill="black", tags="info")

    # Create the HelpBox
    help_box = HelpBox(canvas, text)
    
    # Bind hover events
    canvas.tag_bind("info", "<Enter>", help_box.show_tooltip)
    canvas.tag_bind("info", "<Leave>", help_box.hide_tooltip)

# GUI Session Selection and Options Menu
def session_selection(root, current_frame):
    current_frame.destroy()
    root.title("Options")
    frame = tk.Frame(root)
    frame.pack(expand=True, padx=20, pady=20)

    session_count = 4  #TODO: GRAB FROM DATA FOLDER

    # Instructions Text
    instructions_text = tk.Label(frame, text="Please hover over the info icons below:")
    instructions_text.grid(row=0, column=0, columnspan=3, pady=10, sticky='ew')

    # Session Selection Info Icon
    create_info_icon(frame, 1, 0, "Please select the sessions you want to run.\n\nTo add or remove sessions, please load your data into\n\"ddl-deliberation-args/data/{session_num}\"\nwith {session_num} being replaced by the\nappropriate session number for your data.")
    
    # Options Info Icon
    create_info_icon(frame, 1, 2, "Additionally, you may toggle the following options:\n\nDebug Mode: Debug statements will be shown.\nUse if the program is outputting odd results\n\nHard Restart: Normally, the program will resume where it\nleft off if you must restart due to an error.\nHowever, this option will make the program delete all previous\nprogress and complete reanalyze the selected sessions.")

    # Session Checkboxes
    session_vars = [tk.IntVar(value=1) for _ in range(session_count)]
    for i in range(session_count):
        tk.Checkbutton(frame, text=f"Session {i+1}", variable=session_vars[i]).grid(row=i+2, column=0, sticky='w', pady=2)
    
    # Debug Mode Checkbox
    debug_var = tk.IntVar(value=0)
    tk.Checkbutton(frame, text="Debug Mode", variable=debug_var).grid(row=2, column=2, sticky='w', pady=2)

    # Hard Restart Checkbox
    restart_var = tk.IntVar(value=0)
    tk.Checkbutton(frame, text="Hard Restart", variable=restart_var).grid(row=3, column=2, sticky='w', pady=2)

    button_row = max(4, session_count + 2)

    # Back Button
    back_button = tk.Button(frame, text="Back", command=lambda: restart_program(root, frame))
    back_button.grid(row=button_row, column=0, pady=20, sticky='w')

    # Start Button
    start_button = tk.Button(frame, text="Start", command=lambda: progress_bar(root, session_vars, debug_var, restart_var, frame))
    start_button.grid(row=button_row, column=2, pady=20, sticky='e')

    # Increase window size if needed
    new_height = max(300, 200 + session_count * 28)
    root.minsize(500, new_height)

# GUI Main Menu
def main_menu(root):
    root.title("Stanford DDL Transcript Analyzer")
    frame = tk.Frame(root)
    frame.pack(expand=True)

    # Logo
    logo_text = tk.Label(frame, text="LOGO", font=("Arial", 24))
    logo_text.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
    
    # Instructions Text
    instructions_text = tk.Label(frame, text="Welcome to the Stanford DDL Transcript Analyzer!\n\nThis program will generate an argument\nanalysis when given raw transcripts.\n\nPlease select an option below.", font=("Arial", 14))
    instructions_text.grid(row=1, column=0, columnspan=2, padx=20, pady=20)

    # Exit Button
    exit_button = tk.Button(frame, text="Exit", command=root.destroy)
    exit_button.grid(row=2, column=0, pady=20, padx=20)
    
    # Start Button
    start_button = tk.Button(frame, text="Start", command=lambda: session_selection(root, frame))
    start_button.grid(row=2, column=1, pady=20, padx=20)

# Code starts here
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("500x312")
    root.minsize(500, 312)
    root.eval('tk::PlaceWindow . center')

    main_menu(root)

    root.mainloop()