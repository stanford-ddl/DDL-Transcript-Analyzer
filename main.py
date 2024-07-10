import os
import sys

from codebase.clean import clean_input_data
from codebase.process import process_cleaned_data
from codebase.analyze import analyze_processed_data
from codebase.config import IS_DEBUG, TOTAL_SESSIONS, IS_ANALYZE_ALL_SESSIONS, session_num, DATA_DIR, RESULTS_DIR, PROCESSING_DIR

sys.path.append(os.getcwd())

# READ THIS - VERY IMPORTANT
# To change the Togglable Options that affect how the code runs,
# see config.py
# VERY IMPORTANT - READ THIS

def main():
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

# Code starts here
if __name__ == '__main__':
    print("\nProgram Started")
    # If all sessions should be analyzed
    if IS_ANALYZE_ALL_SESSIONS:
      # Iterate through all sessions from 1 through TOTAL_SESSIONS
      for session in range(TOTAL_SESSIONS):
        session_num = str(session + 1)
        main()
    # Else, analyze only Session number 'session_num'.
    else: main()
    print("Program Finished\n")
