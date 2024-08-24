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