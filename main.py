import os
import sys
import pandas as pd
import random
import util
import ast
from pydantic import BaseModel, create_model, Field
from eval import get_metric_sums, get_metric_dist 

#new
import shutil
from openpyxl import load_workbook

# Togglable Options
IS_DEBUG = False # If True, additional debug statements will be printed.
IS_SKIP_DATA_PROCESS = False # If True, skip 'create_args_sheet' - Use if the program crashes after the data has been processed
TOTAL_SESSIONS = 4 # The highest numbered session in the data
IS_ANALYZE_ALL_SESSIONS = True # If True, all sessions will be analyzed. If False, only 'session_num' will be analyzed.
session_num = 'test' # The single session to analyze if 'IS_ANALYZE_ALL_SESSIONS' is False

DATA_DIR = 'data'
PROCESSING_DIR = 'processing'
RESULTS_DIR = 'results'
sys.path.append(os.getcwd())

# Nearly deprecated
TOPIC = "ranked choice voting"

# collecting arguments in a deliberation
def extract_args(path, deliberation):
    df = pd.DataFrame(pd.read_excel(path)) 
    start_col = df.columns.get_loc("All Arguments Summarized")
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
     print("Failed attempt #" + str(attempts))
     # If failed too many times, give up
     if attempts >= 5:
       print("ERROR: Failed to generate a primary topic and policies")
       return None
     # Else, try again
     print("Retrying...")
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
     print("Failed attempt #" + str(attempts))
     # If failed too many times, give up
     if attempts >= 5:
       print("ERROR: Failed to generate a primary topic and policies")
       return None
     # Else, try again
     print("Retrying...")
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
     print("Failed attempt #" + str(attempts))
     # If failed too many times, give up
     if attempts >= 5:
       print("ERROR: Failed to generate a primary topic and policies")
       return None
     # Else, try again
     print("Retrying...")
     return generate_category_variables(category_list, topic, attempts)
   # Else, success!
   print_categories(category_list, variable_list)
   variable_list.append("other")
   variable_list.append("notRelevant")
   return variable_list

# Given a list of categories and their variable shorthand,
# print them.
def print_categories(category_list, variable_list):
  for i in range(len(category_list)):
    print("Category", str(i+1) + ":", variable_list[i] + ":", category_list[i])

# Nearly deprecated
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

# Nearly deprecated
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

# Given a list of categories,
# construct a JSON class for the model to use.
def build_JSON_class(category_variables):
  print("\nBuilding JSON class for the model...")
  fields = {var: (bool, Field(default=False)) for var in category_variables}
  Categories = create_model("Categories", **fields)
  if IS_DEBUG:
    categories_instance = Categories()
    print("JSON Categories:\n" + categories_instance.model_dump_json(indent=2))
  return Categories()
  
# Given a primary topic and specific categories,
# return a prompt that the model will use to judge arguments.
def build_argument_analysis_prompt(topic, category_topics, category_variables):
  category_instructions = """"""
  for i in range(len(category_topics)):
     category_instructions += """\nReturn true for """ + category_variables[i] + """ if the argument is relevant to """ + category_topics[i] + """.\nReturn false for """ + category_variables[i] + """ otherwise.\n"""
  prompt = """You are a skilled annotator tasked with identifying the type of arguments made in a deliberation about """ + topic + """.
          Read through the given arguments presented.
          Your job is to extract the type of arguments made and load them into the JSON object containing true/false parameters.
          """ + category_instructions + """
          Return true for other if the argument discusses a category that is relevant to """ + topic + """
          but not covered by the other categories.

          Return true for notRelevant if the argument is not relevant to the discussion of """ + topic + """.

          It is possible for a single argument to have multiple true parameters, except for notRelevant.
          If an argument is not relevant, all other parameters should be false.
          You should return true for at least one parameter."""
  return prompt

# adds an LLM's topic classifications for an argument to the deliberation df
def add_results(response, df, line):
   for key in response.keys():
      df.loc[df['Order'] == line, key] = response[key]

# classifies all arguments in all deliberations based on the extracted topics
# note: most time-expensive function to call / may need to increase token size
def arg_inference(all_args_indexed, results_path, argument_analysis_prompt, categories):
  print("\nAnalyzing Session", session_num, "deliberations...")
  # looping over all deliberations
  for deliberation in all_args_indexed.keys():
    args = all_args_indexed[deliberation]
    path = os.path.join(PROCESSING_DIR, session_num, deliberation)

    # initializing df and fields
    df = pd.DataFrame(pd.read_excel(path)) 
    for key in categories.model_fields.keys():
      df[key] = False

    # loop over a deliberation's arguments
    for arg in args:
      prompt = argument_analysis_prompt
      response = util.json_llm_call(prompt, arg[0], categories)
      line = arg[1]
      add_results(response, df, line)
    new_filename = "EVALUATED" + deliberation.replace("xlsx", "csv")
    df.to_csv(os.path.join(results_path, new_filename))
    print("Created", new_filename)
  print("Finished analyzing deliberations in Session", session_num)

# Given a path for a 'results' folder,
# create that folder and a 'metrics' subfolder if needed.
def create_results_path(results_path):
  print("\nCreating Session", session_num, "results and metrics folders...")
  # Creates the required results folder if it does not already exist
  os.makedirs(results_path, exist_ok=True)

  # Creates the required metrics folder if it does not already exist
  metrics_path = os.path.join(results_path, "metrics")
  os.makedirs(metrics_path, exist_ok=True)

# Given a path for a 'processing' folder,
# create that folder if needed.
def create_processing_path(processing_path):
   print("\nCreating Session", session_num, "processing folder...")
   # Creates the required results folder if it does not already exist
   os.makedirs(processing_path, exist_ok=True)

# this function takes in text from a deliberation and determines if it contains arguments
def check_arguments(text):
    system_prompt = "Determine if the following text contains arguments. Respond ONLY with 'yes' or 'no'. Do not provide an explanation, do not capitalize Yes or No, do not put any punctuation, only respond 'yes' or 'no'."
    response = util.simple_llm_call(system_prompt, text)
    # if invalid response, try again
    if response not in ['yes', 'no']:
        # print("bad output")
        response = util.simple_llm_call(system_prompt, text)
    # print(text + "----->" + response)
    return response.strip().lower() == 'yes'

# this function duplicates the input spreadsheet in destination folder, and creates and populates contians args column
def create_args_sheet(file_path, destination_folder):
    df = pd.read_excel(file_path)
    file_name = os.path.basename(file_path)
    duplicated_file_path = os.path.join(destination_folder, file_name)

    print("Creating argument columns for", file_name + "...")

    # Duplicate the file to the destination folder with the new name
    shutil.copy(file_path, duplicated_file_path)

    # Load the duplicated file with openpyxl to add columns
    wb = load_workbook(duplicated_file_path)
    ws = None
    if 'proposal' in wb.sheetnames:
       wb.remove(wb['proposal'])
    elif 'proposal ' in wb.sheetnames:
       wb.remove(wb['proposal '])
    for sheet in wb.sheetnames:
       ws = wb[sheet]

    # Add the new columns
    ws.cell(row=1, column=4, value="Has Arguments")
    ws.cell(row=1, column=5, value="All Arguments Summarized")
    ws.cell(row=1, column=6, value="Order")

    # Iterate over the rows and populate the "has arguments" column
    for row in range(2, ws.max_row + 1):
        text = ws.cell(row=row, column=3).value
        if text is not None:  # Check if the cell is not empty
            has_arguments = check_arguments(text)
            ws.cell(row=row, column=4, value="yes" if has_arguments else "no")
        else:
            ws.cell(row=row, column=4, value="no")
        # Construct the "Order" column
        ws.cell(row=row, column=6, value=row-1)

    # Iterate over the rows again to populate the "all arguments summarized" column
    for row in range(2, ws.max_row + 1):
        has_arguments = ws.cell(row=row, column=4).value
        if has_arguments == "yes":
            text = ws.cell(row=row, column=3).value
            # summarized_text = util.simple_llm_call("Summarize the following text in a numbered list. For example, the text input ' thank you. so the last thing was that if there's ten candidates and you only pick your top two, then your and they don't get it, your vote doesn't count it all. so the best thing to do is you got to rank all 10, but again, not enough data on the subject to make predictions. and i think mike use' should be summarized as '1. If you only pick your top two candidates out of ten, your vote doesn't count if they don't win. 2. The best approach is to rank all ten candidates. 3. There is not enough data available to make predictions on the subject.' Follow this formatting exactly.", text)
            summarized_text = util.simple_llm_call("Summarize the following text in a numbered list.  Follow the output format '1. argument 1 \n 2. argument 2 \n' etcetera. Every argument MUST be on a different line. There could be one or more arguments.", text)
            ws.cell(row=row, column=5).value = summarized_text
            print("+++++++++" + text)
            print("==========" + summarized_text)

    # Save the modified duplicated file
    wb.save(duplicated_file_path)

def main():
    print("Entering main() of Session", session_num)

    # keys = deliberation ids, values = (argument, index in deliberation)
    all_args_indexed = {}
    all_args = []

    # looping over all deliberations and collecting 1) the arguments presented and 2) the index of each argument in that deliberation
    data_path = os.path.join(DATA_DIR, session_num)
    processing_path = os.path.join(PROCESSING_DIR, session_num)
    create_processing_path(processing_path)
    for deliberation in os.listdir(data_path):
      path = os.path.join(data_path, deliberation)
      if path.endswith('xlsx'):
        if not IS_SKIP_DATA_PROCESS: create_args_sheet(path, processing_path)
        new_path = os.path.join(processing_path, deliberation)
        formatted_args = extract_args(new_path, deliberation)
        all_args_indexed.update(formatted_args)
        all_args += all_args_indexed[deliberation]

    # sampling 50 arguments for topic extraction
    sampled_args = random.sample(all_args, 50)
    topics = extract_topics(sampled_args)

    # Generate primary topic, policies, and categories
    category_topics = generate_categories(sampled_args, topics[0]) if topics else print("ERROR: Cannot generate categories: No topic")
    category_variables = generate_category_variables(category_topics, topics[0]) if category_topics else print("ERROR: Cannot generate variable shorthand for categories: No category topics")
    categories = build_JSON_class(category_variables) if category_variables else print("ERROR: Cannot build JSON class: No category variables")

    # running inference
    # replace with correct path for results
    results_path = os.path.join(RESULTS_DIR, session_num)
    create_results_path(results_path)
    argument_analysis_prompt = build_argument_analysis_prompt(topics[0], category_topics, category_variables) if categories else print("ERROR: Cannot generate API prompt: No JSON class")
    arg_inference(all_args_indexed, results_path, argument_analysis_prompt, categories)
    delibs = [os.path.join(results_path, csv) for csv in os.listdir(results_path) if csv.endswith(".csv")]

    # running post-evaluation
    cumulative_df = get_metric_sums(delibs, category_variables[0])
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
        if session_num == '1' or session_num == '2': # Skip 1 - 1 is analyzed
           continue
        main()
    # Else, analyze only Session number 'session_num'.
    else: main()
    print("Program Finished")
