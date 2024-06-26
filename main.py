import os
import sys
import pandas as pd
import random
import util
import ast
from pydantic import BaseModel, Field
from eval import get_metric_sums, get_metric_dist 

# Togglable Options
IS_DEBUG = False # If True, additional debug statements will be printed.
TOTAL_SESSIONS = 4 # The highest numbered session in the data
IS_ANALYZE_ALL_SESSIONS = True # If True, all sessions will be analyzed. If False, only 'session_num' will be analyzed.
session_num = '1' # The single session to analyze if 'IS_ANALYZE_ALL_SESSIONS' is False

DATA_DIR = 'data'
RESULTS_DIR = 'results'
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

# Given a subset of arguments,
# return a list of topics that most arguments deliberate on.
def extract_topics(sampled_args, attempts = 0):
   NUM_TOPICS = '7'
   if attempts == 0: print("\nGenerating", NUM_TOPICS, "topics from Session", session_num + "...")

   prompt = """This is a list of arguments presented in a deliberation. Your job is to identify the single, primary topic deliberated on and write
   """ + NUM_TOPICS + """ distinct policies regarding the primary topic in a Python list of strings, with each string being a policy.
   The first string in the list is the primary topic, and every other string is a policy.
   It should be possible to define every argument initially provided as being an argument "for" or "against" at least one of the policies you generate.
   The exceptions to this are the very small number of arguments that are unrelated to the primary topic and all policies.
   Here is an example of what you might return if the primary topic was 'Ranked choice voting':
   ["Ranked choice voting", "Implement ranked choice voting as an alternative method both to elected officials and representatives at all levels", "Use proportional representatives to elect elected officials"...]
   The policies in the list should be somewhat distinct from each other.
   You should NOT have broad policies, such as the advantages and disadvantages of the primary topic. Rather,
   you should instead find nuanced groups of arguments that may be present on either side of the discussion.
   Every policy should be a feasable, actionable change. Here is an example of what a policy should NOT be:
   "Limit the influence of political parties in elections" This policy is BAD because it is too vague and not actionable;
   this BAD policy could not feasibly be turned into a law.
   The following non-case-sensitive words are BANNED and should NOT be included in your response:
   "and", "but", "or", "by", "Promote", "Encourage", "Ensure", "Explore", "Maintain".
   This program will CRASH if your response fails to conform to these guidelines.
   Other code ran for several hours before you were given this task.
   If this program crashes, we will need to restart which takes several hours.
   Please take your time and ensure ALL of these instructions are followed.
   Do NOT write "Primary topic:" in your response.
   Do NOT number the list.
   Do NOT indent in your response.
   Do NOT include a newline character in your response.
   Do NOT include anything in the list other than the primary topic and the policies themselves.
   Your response is ONLY a single list of the primary topic and the policies.
   Once again, your response is ONLY a single list.
   Your response is ONLY one line.
   The Python list you return should contain EXACTLY """ + str(int(NUM_TOPICS)+1) + """ strings.
   Thank you!"""
   response = util.simple_llm_call(prompt, sampled_args)
   if IS_DEBUG: print("\n(DEBUG) Raw response:", response + "\n")
   topic_list = ast.literal_eval(response.strip())
   # If invalid response, try again
   if len(topic_list) != (int(NUM_TOPICS) + 1) or type(topic_list) != list:
     attempts += 1
     print("Failed attempt #" + attempts + ".")
     # If failed too many times, give up
     if attempts >= 5:
       print("Giving up :(")
       return None
     # Else, try again
     return extract_topics(sampled_args, attempts)
   # Else, success!
   print_topics(topic_list)
   return topic_list

# Given a list of topics,
# print them.
def print_topics(topic_list):
  print("Primary Topic:", topic_list[0])
  for i in range(1, len(topic_list)):
    print("Policy", str(i) + ":", topic_list[i])

# Given a subset of arguments and a topic,
# return a list of categories that most arguments fall under.
def generate_categories(sampled_args, topic, attempts = 0):
   NUM_CATEGORIES = '7'
   if attempts == 0: print("\nGenerating", NUM_CATEGORIES, "categories regarding", topic + "...")
   
   prompt = """This is a list of arguments presented in a deliberation about """ + topic + """. Your job is to summarize
   these arguments into """ + NUM_CATEGORIES + """ distinct categories regarding """ + topic + """ in a Python list of strings, with each string being a category.
   The exceptions to this are the very small number of arguments that are unrelated to """ + topic + """.
   Your response will be """ + NUM_CATEGORIES + """ strings.
   The categories in the list should be somewhat distinct from each other.
   The categories should be specific to the most common arguments given to you as they relate to """ + topic + """.
   Do NOT use the words "for" or "against" in your response.
   You should not have broad categories, such as the advantages and disadvantages of """ + topic + """. Rather,
   you should instead find nuanced groups of arguments that may be present on either side of the discussion.
   This program will CRASH if your response fails to conform to these guidelines.
   Other code ran for several hours before you were given this task.
   If this program crashes, we will need to restart which takes several hours.
   Please take your time and ensure ALL of these instructions are followed.
   Do NOT number the list.
   Do NOT indent in your response.
   Do NOT include a newline character in your response.
   Do NOT include anything in the list other than the categories.
   Your response is ONLY a single list of categories.
   Once again, your response is ONLY a single list.
   Your response is ONLY one line.
   The Python list you return should contain EXACTLY """ + NUM_CATEGORIES + """ strings.
   Thank you!"""
   response = util.simple_llm_call(prompt, sampled_args)
   if IS_DEBUG: print("\n(DEBUG) Raw response:", response + "\n")
   category_list = ast.literal_eval(response.strip())
   # If invalid response, try again
   if len(category_list) != int(NUM_CATEGORIES) or type(category_list) != list:
     attempts += 1
     print("Failed attempt #" + attempts + ".")
     # If failed too many times, give up
     if attempts >= 5:
       print("Giving up :(")
       return None
     # Else, try again
     return generate_categories(sampled_args, topic, attempts)
   # Else, success!
   return category_list

# Given a list of categories,
# return a list of variables that can be used as shorthand for each category.
def generate_category_variables(category_list, topic, attempts = 0):
   NUM_VARIABLES = str(len(category_list))
   if attempts == 0: print("Generating variables for the", NUM_VARIABLES, "categories regarding", topic + "...")
   
   prompt = """This is a list of categories representing arguments made in a deliberation about """ + topic + """.
   Your job is to create variable names for each category in a Python list of strings, with each string being a variable name.
   Your response will be """ + NUM_VARIABLES + """ strings.
   The variable names should be short.
   The variable names should use camel case style.
   The variable names should encapsulate the core of the category.
   Here is an example of what you might return:
   ["VariableOne", "VariableTwo",...]
   This program will CRASH if your response fails to conform to these guidelines.
   Other code ran for several hours before you were given this task.
   If this program crashes, we will need to restart which takes several hours.
   Please take your time and ensure ALL of these instructions are followed.
   Do NOT number the list.
   Do NOT indent in your response.
   Do NOT include a newline character in your response.
   Do NOT include anything in the list other than the variable names.
   Your response is ONLY a single list of variable names.
   Once again, your response is ONLY a single list.
   Your response is ONLY one line.
   The Python list you return should contain EXACTLY """ + NUM_VARIABLES + """ strings.
   Thank you!"""
   response = util.simple_llm_call(prompt, category_list)
   if IS_DEBUG: print("\n(DEBUG) Raw response:", response + "\n")
   variable_list = ast.literal_eval(response.strip())
   # If invalid response, try again
   if len(variable_list) != int(NUM_VARIABLES) or type(variable_list) != list:
     attempts += 1
     print("Failed attempt #" + attempts + ".")
     # If failed too many times, give up
     if attempts >= 5:
       print("Giving up :(")
       return None
     # Else, try again
     return generate_category_variables(category_list, topic, attempts)
   # Else, success!
   print_categories(category_list, variable_list)
   return variable_list

# Given a list of categories and their variable shorthand,
# print them.
def print_categories(category_list, variable_list):
  for i in range(len(category_list)):
    print("Category", str(i+1) + ":", variable_list[i] + ":", category_list[i])

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

# classifies all arguments in all deliberations based on the extracted topics
# note: most time-expensive function to call / may need to increase token size
def arg_inference(all_args_indexed, results_path):
  print("\nAnalyzing Session", session_num, "deliberations...")
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

# Given a path for a 'results' folder,
# create that folder and a 'metrics' subfolder if needed
def create_results_path(results_path):
  print("Creating Session", session_num, "results and metrics folders...")
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

    # sampling 500 arguments for topic extraction
    sampled_args = random.sample(all_args, 500)
    topics = extract_topics(sampled_args)
    categories = generate_categories(sampled_args, topics[0]) if topics else print("ERROR: Cannot generate categories.")
    category_variables = generate_category_variables(categories, topics[0]) if topics and categories else print("ERROR: Cannot generate variable shorthand for categories.")

    print("\nEarly return for debugging")
    return

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
    # If all sessions should be analyzed
    if IS_ANALYZE_ALL_SESSIONS:
      # Iterate through all sessions from 1 through TOTAL_SESSIONS
      for session in range(TOTAL_SESSIONS):
        session_num = str(session + 1)
        main()
    # Else, analyze only Session number 'session_num'.
    else: main()
    print("Program Finished")
