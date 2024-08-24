import os
import sys
import tkinter as tk
from tkinter import ttk
import sys
import time
import threading

from codebase.clean import clean_input_data
from codebase.process import process_cleaned_data
from codebase.analyze import analyze_processed_data
from codebase.config import IS_DEBUG, TOTAL_SESSIONS, IS_ANALYZE_ALL_SESSIONS, session_num, DATA_DIR, RESULTS_DIR, PROCESSING_DIR

sys.path.append(os.getcwd())

# READ THIS - VERY IMPORTANT
# To change the Togglable Options that affect how the code runs,
# see config.py
# VERY IMPORTANT - READ THIS

def run_session():
    print("Started working with Session", session_num)

    # Clean the input data
    data_path = os.path.join(DATA_DIR, session_num)
    clean_input_data(data_path)

    # Process the cleaned data (search the text for arguments)
    all_args_indexed = {} # keys = deliberation ids, values = (argument, index in deliberation)
    all_args = []
    process_cleaned_data(data_path, all_args_indexed, all_args)

    # Analyze the processed data (compare arguments to generated policies)
    analyze_processed_data(all_args_indexed, all_args)
    
    print("\nFinished working with Session", session_num)

def main():
    print("\nProgram Started")
    # If all sessions should be analyzed
    if IS_ANALYZE_ALL_SESSIONS:
      # Iterate through all sessions from 1 through TOTAL_SESSIONS
      for session in range(TOTAL_SESSIONS):
        session_num = str(session + 1)
        run_session()
    # Else, analyze only Session number 'session_num'.
    else: run_session()
    print("Program Finished\n")

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