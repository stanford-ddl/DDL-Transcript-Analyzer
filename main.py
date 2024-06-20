import os
import sys
import pandas as pd
import random
import util
import ast
from pydantic import BaseModel, Field
from eval import get_metric_sums, get_metric_dist 

DATA_DIR = 'data'
RESULTS_DIR = 'results'
TOTAL_SESSIONS = 4
session_num = '1'
sys.path.append(os.getcwd())

TOPIC = "ranked choice voting"

# collecting arguments in a deliberation
def extract_args(path, deliberation):
    df = pd.DataFrame(pd.read_excel(path)) 
    start_col = df.columns.get_loc("(Beta) For proposal: Implement RCV as an alternative method both to elected officials and representatives at all levels")
    cols = df.columns[start_col:]

    # filtering out debugging columns
    filter_cols = [col for col in cols if col.find("debugging") == -1]
    relevant_args_df = df.dropna(subset=filter_cols, how='all')

    # list of Fileread's summarized arguments and their indexed order
    arguments = list((relevant_args_df["All Arguments Summarized"], relevant_args_df["Order"]))
    arguments = [(x, y) for x, y in zip(arguments[0], arguments[1]) if str(x) != 'nan']
    return concat_args(arguments, deliberation)

# cleaning arguments
def concat_args(arguments, deliberation):
  cleaned_args = {deliberation: []}
  for arg in arguments:
    args = arg[0].split("\n")
    joined = " ".join([arg[3:] for arg in args])
    cleaned_args[deliberation].append((joined, arg[1]))
  return cleaned_args

# extracts 7 argument topics from a sample of arguments on topic
def extract_topics(sampled_args):
   prompt = """This is a list of arguments presented in a deliberation about """ + TOPIC + """. Your job is to summarize
   these arguments into 7 distinct topics regarding """ + TOPIC + """ in a Python list of strings, with each string being a topic.
   Every string MUST start with 'Ranked choice voting is' followed by a brief summary of the topic.
   Do NOT number the list or indent in your response, and do NOT include apostrophes.
   Do NOT include anything in the list other than the topics themselves. Your response is ONLY the list of topics.
   Once again, the Python list you return should contain exactly 7 strings. This is an example of what you should return:
   ['Ranked choice voting is fair', 'Ranked choice voting is complicated', 'Ranked choice voting is pointless'...]
   The topics in the list should be somewhat distinct from each other.
   You should not have broad topics, such as the advantages and disadvantages of """ + TOPIC + """. Rather,
   you should instead find nuanced groups of arguments that may be present on either side of the discussion."""
   response = util.simple_llm_call(prompt, sampled_args)
   topic_list = ast.literal_eval(response.strip())
   if len(topic_list) != 7 or type(topic_list) != list:
     return "The response you provided is not in the correct format. Please provide a list of 7 strings."
   return topic_list

# JSON class for extraction
class TopicClassifier(BaseModel):
  comparisonToCurrentSystem: bool = Field(default=False)
  votingDecisions: bool = Field(default=False)
  partyRepresentation: bool = Field(default=False)
  voterTurnout: bool = Field(default=False)
  strategicVoting: bool = Field(default=False)
  moderateCandidates: bool = Field(default=False)
  moneyInPolitics: bool = Field(default=False)
  other: bool = Field(default=False)
  notRelevant: bool = Field(default=False)

# system prompt for the topic evaluation task based on current extracted topics for ranked choice voting
EVAL_PROMPT = """You are a skilled annotator tasked with identifying the type of arguments made in a deliberation about """ + TOPIC + """.
        Read through the given arguments presented.
        Your job is to extract the type of arguments made and load them into the JSON object containing true/false parameters.

        Return true for comparisonToCurrentSystem if the argument compares ranked choice voting to the current system.
        For example, 'Ranked choice voting is more equitable than the current system that only allows for two dominant parties to win'.
        Return false for comparisonToCurrentSystem otherwise.
        
        Return true for votingDecisions if the argument discusses the impact of ranked choice voting on voting decisions.
        For example, 'Ranked choice voting will allow voters to vote for their preferred candidate without fear of wasting their vote'.
        Return false for votingDecisions otherwise.
        
        Return true for partyRepresentation if the argument discusses how ranked choice voting may impact party representation.
        For example, 'Ranked choice voting will allow for more third-party candidates to win elections'.
        Return false for partyRepresentation otherwise.
        
        Return true for voterTurnout if the argument discusses how ranked choice voting may impact voter turnout.
        For example, 'Ranked choice voting will increase voter turnout and encourage more people to engage in elections.
        Return false for voterTurnout otherwise.
        
        Return true for strategicVoting if the argument discusses how ranked choice voting may impact strategic voting.
        For example, 'Ranked choice voting will prevent people from voting for a candidate they don't like to avoid a worse outcome'.
        Return false for strategicVoting otherwise.
        
        Return true for moderateCandidates if the argument discusses how ranked choice voting may impact moderate candidates.
        For example, 'Ranked choice voting will allow moderate candidates to win elections'. 
        Return false for moderateCandidates otherwise.
        
        Return true for moneyInPolitics if the argument discusses how ranked choice voting may impact money in politics.
        For example, 'Ranked choice voting will reduce the influence of money in politics'.
        Return false for moneyInPolitics otherwise.
        
        Return true for other if the argument discusses a topic not covered by the other parameters.
        For example, 'Ranked choice voting will make voting too complicated.'
        
        Return true for notRelevant if the argument is not relevant to the discussion of ranked choice voting.
        For example, 'I have a dog and two kids.'
        
        It is possible for a single argument to have multiple true parameters, except for notRelevant.
        If an argument is not relevant, all other parameters should be false.
        You should return true for at least one parameter.
        """

# adds an LLM's topic classifications for an argument to the deliberation df
def add_results(response, df, line):
   for key in response.keys():
      df.loc[df['Order'] == line, key] = response[key]

# classifies all arguments in all deliberations based on the 7 extracted topics
# note: most time-expensive function to call / may need to increase token size
def arg_inference(all_args_indexed, results_path):
  print("Started analyzing deliberations in Session", session_num)
  # looping over all deliberations
  for deliberation in all_args_indexed.keys():
    args = all_args_indexed[deliberation]
    path = os.path.join(DATA_DIR, session_num, deliberation)

    # initializing df and fields
    df = pd.DataFrame(pd.read_excel(path)) 
    for key in TopicClassifier.model_fields.keys():
      df[key] = False

    # loop over a deliberation's arguments
    for arg in args:
      topic_class = TopicClassifier
      prompt = EVAL_PROMPT
      response = util.json_llm_call(prompt, arg[0], topic_class)
      line = arg[1]
      add_results(response, df, line)
    new_filename = "EVALUATED" + deliberation.replace("xlsx", "csv")
    df.to_csv(os.path.join(results_path, new_filename))
    print("Created", new_filename)
  print("Finished analyzing deliberations in Session", session_num)

def create_results_path(results_path):
  print("Creating results and metrics folders for Session", session_num)
  # Creates the required results folder if it does not already exist
  os.makedirs(results_path, exist_ok=True)

  # Creates the required metrics folder if it does not already exist
  metrics_path = os.path.join(results_path, "metrics")
  os.makedirs(metrics_path, exist_ok=True)

def main():
    print("Entering main() of Session", session_num)

    # keys = deliberation ids, values = (argument, index in deliberation)
    all_args_indexed = {}
    all_args = []

    # looping over all deliberations and collecting 1) the arguments presented and 2) the index of each argument in that deliberation
    data_path = os.path.join(DATA_DIR, session_num)
    for deliberation in os.listdir(data_path):
      path = os.path.join(data_path, deliberation)
      if path.endswith('xlsx'):
        formatted_args = extract_args(path, deliberation)
        all_args_indexed.update(formatted_args)
        all_args += all_args_indexed[deliberation]

    # sampling 50 arguments for topic extraction
    sampled_args = random.sample(all_args, 50)
    # uncomment line below to run topic extraction
    # topics = extract_topics(sampled_args)

    # running inference
    # replace with correct path for results
    results_path = os.path.join(RESULTS_DIR, session_num)
    create_results_path(results_path)
    arg_inference(all_args_indexed, results_path)
    delibs = [os.path.join(results_path, csv) for csv in os.listdir(results_path) if csv.endswith(".csv")]

    # running post-evaluation
    cumulative_df = get_metric_sums(delibs)
    get_metric_dist(cumulative_df, results_path)
    print("Exiting main() of Session", session_num)

# Code starts here
if __name__ == '__main__':
    print("Program Started")
    # Iterate through all sessions from 1 through TOTAL_SESSIONS
    for current_session in range(TOTAL_SESSIONS):
      session_num = str(current_session + 1)
       # Temporary since Sessions 1, 2, and 3 for RCV has already been completed
      if session_num == '1' or session_num == '2' or session_num == '3':
        print("Skipping Session", session_num)
        continue
      main()
    print("Program Finished")
