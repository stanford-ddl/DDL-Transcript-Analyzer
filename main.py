import os
import shutil
import sys
import tkinter as tk
from tkinter import ttk
import sys
import threading

from codebase import config
from codebase.config import TOTAL_SESSIONS, IS_ANALYZE_ALL_SESSIONS, DATA_DIR, RESULTS_DIR, PROCESSING_DIR
from codebase.clean import clean_input_data
from codebase.process import process_cleaned_data
from codebase.analyze import analyze_processed_data

sys.path.append(os.getcwd())

# READ THIS - VERY IMPORTANT
# To change the Togglable Options that affect how the code runs,
# see config.py
# VERY IMPORTANT - READ THIS

# Increase the phase progress bar and reset the transcript progress bar
def advance_GUI_to_next_phase(phase_progress_bar, transcript_progress_bar, transcript_progress_text, num_transcripts):
    phase_progress_bar['value'] += 100 / 3
    transcript_progress_bar['value'] = 0
    transcript_progress_text.config(text=f"0/{num_transcripts}")

# Given a directory,
# return the number of deliberations in it.
def get_num_deliberations(data_path):
    num_transcripts = 0
    for deliberation in os.listdir(data_path):
      path = os.path.join(data_path, deliberation)
      if path.endswith('xlsx') or path.endswith('csv') or path.endswith('numbers'):
          num_transcripts += 1
    return num_transcripts

# Run current session_num
def run_session(phase_progress_bar, transcript_progress_bar, transcript_progress_text):
    print("Started working with Session", config.session_num)

    # Clean the input data
    data_path = os.path.join(DATA_DIR, config.session_num)
    num_transcripts = get_num_deliberations(data_path)
    advance_GUI_to_next_phase(phase_progress_bar, transcript_progress_bar, transcript_progress_text, num_transcripts)

    # Clean the input data
    clean_input_data(data_path, transcript_progress_bar, transcript_progress_text, num_transcripts)

    # Transcript Cleaning -> Argument Identification
    advance_GUI_to_next_phase(phase_progress_bar, transcript_progress_bar, transcript_progress_text, num_transcripts)

    # Process the cleaned data (search the text for arguments)
    all_args_indexed = {} # keys = deliberation ids, values = (argument, index in deliberation)
    all_args = []
    process_cleaned_data(data_path, all_args_indexed, all_args)

    # Argument Identification -> Argument Analysis
    advance_GUI_to_next_phase(phase_progress_bar, transcript_progress_bar, transcript_progress_text, num_transcripts)

    # Analyze the processed data (compare arguments to generated policies)
    analyze_processed_data(all_args_indexed, all_args)

    # Delete this sessions processing path so it does not interfere with future sessions
    delete_processing_path(config.session_num)
    
    print("\nFinished working with Session", config.session_num)

# Run all selected sessions
def main(selected_sessions, phase_progress_bar, transcript_progress_bar, transcript_progress_text):
    print("Program Started")
    for session in selected_sessions:
        config.session_num = session
        phase_progress_bar['value'] = 0
        transcript_progress_bar['value'] = 0
        transcript_progress_text.config(text="0")
        run_session(phase_progress_bar, transcript_progress_bar, transcript_progress_text)
    print("Program Finished", end="")

# Display Console/Terminal output on GUI Progress Bar Screen
class RedirectOutput:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

# Given a session,
# delete its processing folder (if it exists)
def delete_processing_path(session):
    processing_path = os.path.join(PROCESSING_DIR, session)
    if os.path.exists(processing_path): shutil.rmtree(processing_path)

# Given a session,
# delete its results folder (if it exists)
def delete_results_path(session):
    results_path = os.path.join(RESULTS_DIR, session)
    if os.path.exists(results_path): shutil.rmtree(results_path)

# Given a session,
# delete its processing and results folders (if they exist)
def hard_restart(session):
    print("Performing a hard restart on Session", session + "...", end=" ")
    delete_processing_path(session)
    delete_results_path(session)
    print("Done")

# GUI Progress Bar Screen
def progress_bar(root, sessions, session_vars, debug_var, restart_var, current_frame):
    # Grab Selected Sessions
    selected_sessions = [sessions[i] for i, var in enumerate(session_vars) if var.get() == 1]

    if not selected_sessions: return

    current_frame.destroy()
    root.title("Progress Bar")
    frame = tk.Frame(root)
    frame.pack(fill='both', expand=True)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    frame.columnconfigure(2, weight=1)
    frame.rowconfigure(3, weight=1)
    
    # Text above the Phase Progress Bar
    phases = ["Transcript Cleaning", "Argument Identification", "Argument Analysis"]
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
    transcript_progress_text = tk.Label(frame, text="0")
    transcript_progress_text.grid(row=2, column=2, padx=10, sticky='w')

    # Console/Terminal Output Textbox
    text = tk.Text(frame, wrap='word', state='normal')
    text.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

    # Display print and error statement in GUI
    sys.stdout = RedirectOutput(text)
    sys.stderr = RedirectOutput(text)

    # Set is_debug
    config.is_debug = debug_var.get() == 1

    # Hard Restart if needed
    if restart_var.get() == 1:
        for session in selected_sessions:
            hard_restart(session)

    phase_progress_bar['value'] = 0
    phase_progress_bar['maximum'] = 100
    transcript_progress_bar['value'] = 0
    transcript_progress_bar['maximum'] = 100

    threading.Thread(target=main, args=(selected_sessions, phase_progress_bar, transcript_progress_bar, transcript_progress_text), daemon=True).start()

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

# The key for sorting sessions.
# This sorts all numerical sessions (theoretically, all of them)
# followed by string sessions
def sort_sessions_key(session):
    try:
        return (0, int(session))
    except ValueError:
        return (1, session)

# GUI Session Selection and Options Menu
def session_selection(root, current_frame):
    current_frame.destroy()
    root.title("Options")
    frame = tk.Frame(root)
    frame.pack(expand=True, padx=20, pady=20)

    sessions = sorted([f.name for f in os.scandir(DATA_DIR) if f.is_dir()], key=sort_sessions_key)

    # Instructions Text
    instructions_text = tk.Label(frame, text="Please hover over the info icons below:")
    instructions_text.grid(row=0, column=0, columnspan=3, pady=10, sticky='ew')

    # Session Selection Info Icon
    create_info_icon(frame, 1, 0, "Please select the sessions you want to run.\n\nTo add or remove sessions, please load your data into\n\"ddl-deliberation-args/data/{session_num}\"\nwith {session_num} being replaced by the\nappropriate session number for your data.")
    
    # Options Info Icon
    create_info_icon(frame, 1, 2, "Additionally, you may toggle the following options:\n\nDebug Mode: Debug statements will be shown.\nUse if the program is outputting odd results\n\nHard Restart: Normally, the program will resume where it\nleft off if you must restart due to an error.\nHowever, this option will make the program delete all previous\nprogress and complete reanalyze the selected sessions.")

    # Session Checkboxes
    session_vars = [tk.IntVar(value=1) for _ in range(len(sessions))]
    for i in range(len(sessions)):
        tk.Checkbutton(frame, text=f"Session {sessions[i]}", variable=session_vars[i]).grid(row=i+2, column=0, sticky='w', pady=2)
    
    # Debug Mode Checkbox
    debug_var = tk.IntVar(value=0)
    tk.Checkbutton(frame, text="Debug Mode", variable=debug_var).grid(row=2, column=2, sticky='w', pady=2)

    # Hard Restart Checkbox
    restart_var = tk.IntVar(value=0)
    tk.Checkbutton(frame, text="Hard Restart", variable=restart_var).grid(row=3, column=2, sticky='w', pady=2)

    button_row = max(4, len(sessions) + 2)

    # Back Button
    back_button = tk.Button(frame, text="Back", command=lambda: restart_program(root, frame))
    back_button.grid(row=button_row, column=0, pady=20, sticky='w')

    # Start Button
    start_button = tk.Button(frame, text="Start", command=lambda: progress_bar(root, sessions, session_vars, debug_var, restart_var, frame))
    start_button.grid(row=button_row, column=2, pady=20, sticky='e')

    # Increase window size if needed
    new_height = max(300, 200 + len(sessions) * 28)
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