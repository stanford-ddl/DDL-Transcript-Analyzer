This project is part of an ongoing initiative within the Deliberative Democracy Lab at Stanford to extract, evaluate, and quantify the unique arguments presented in a deliberation.

Current work has focused on ranked-choice voting (RCV) deliberations. The code written so far does the following:
- Collects all arguments (only those identified and summarized by the Fileread system) across RCV deliberations
- Condenses the RCV arguments, using a sample of arguments, into distinct argument topics by prompting LLM
- Runs LLM evaluation on all arguments for which topics are present
- Accumulates counts and distributions for topics across deliberations

Future work should likely involve the following:
- Run sanity checks on the model's evaluation of arguments 
- Adapt and scale the code for other types of deliberations

The data folder contains the deliberation transcripts that we evaluated the current methods on in an initial round of testing. The results for this can be found in results/eval1. 

Access to LLMs is currently provided by a together.ai key. This may need to be replaced in the future if credits get used up.