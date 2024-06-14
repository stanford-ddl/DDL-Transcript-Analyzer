import os
import sys
import pandas as pd

RESULTS_DIR = 'results'
sys.path.append(os.getcwd())

if __name__ == '__main__':
    for deliberation in os.listdir(os.path.join(RESULTS_DIR,'1')):
        path = os.path.join(RESULTS_DIR, '1', deliberation)
        if path.endswith('csv'):
            deliberation_new_name = deliberation.replace("EVALUATED", "")
            os.rename(path, os.path.join(RESULTS_DIR, '1', deliberation_new_name))