import os
import sys
import pandas as pd

RESULTS_DIR = 'results'
sys.path.append(os.getcwd())

# collecting the sums of metrics (argument topics) from all deliberations
def get_metric_sums(delibs):
  cumulative_df = pd.DataFrame()
  for delib in delibs:
    if delib.endswith(".csv"):
      df = pd.read_csv(delib)
      start_metric_col = df.columns.get_loc("comparisonToCurrentSystem")
      metric_cols = df.columns[start_metric_col:]
      df_metrics = df[metric_cols]
      df_metric_sums = df_metrics.sum(axis=0).to_frame().T
      df_metric_sums["deliberation"] = delib.replace("results/", "")
      df_metric_sums = df_metric_sums.set_index("deliberation")
      cumulative_df = pd.concat([cumulative_df, df_metric_sums])
  return cumulative_df

# normalizing the metric sums to get a distribution
def get_metric_dist(cumulative_df):
  row_sums = cumulative_df.sum(axis=1)
  normalized_df = cumulative_df.div(row_sums, axis=0)
  cumulative_df.to_csv("metric_sums.csv")
  normalized_df.to_csv("metric_sums_normalized.csv")