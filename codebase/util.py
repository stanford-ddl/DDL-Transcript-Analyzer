import json
from functools import lru_cache

from openai import OpenAI, APIConnectionError

@lru_cache
def load_together_client():
    together_client = None
    try:
        from codebase.api_keys import TOGETHER_API_KEY

        together_client = OpenAI(api_key=TOGETHER_API_KEY,
            base_url='https://api.together.xyz',
        )
    except ImportError:
        print("\001\033[93m\002WARNING: Unable to load Together API client (TOGETHER_API_KEY in api_keys.py not found)\001\033[0m\002")
        print("\001\033[93m\002LLM Calls will not work.  Please add a TOGETHER_API_KEY to api_keys.py before starting parts 2 and 3.\001\033[0m\002")

    return together_client

def call_llm(messages, client, model="mistralai/Mixtral-8x7B-Instruct-v0.1", max_tokens=256):
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
        max_tokens=max_tokens
    )

    return chat_completion.choices[0].message.content

# model = "meta-llama/Llama-2-70b-chat-hf"
def stream_llm_to_console(messages, client, model="mistralai/Mixtral-8x7B-Instruct-v0.1", max_tokens=256, stop=None):
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            max_tokens=max_tokens,
            stop=stop
        )

        response = ""
        for chunk in stream:
            response += chunk.choices[0].delta.content or ""
            print(chunk.choices[0].delta.content or "", end="", flush=True)

        print()
    except APIConnectionError as e:
        print("\001\033[91m\002ERROR connecting to Together API!  Please check your TOGETHER_API_KEY in api_keys.py and try again.\001\033[0m\002")
        response = None

    return response

### Student Facing API
#  Makes a call to the Together API using the given system prompt and user message.
#   system_prompt: The system prompt to send to the API.
#   message: The user message to send to the API.
#   model: The model to use for the API call.
#   max_tokens: The maximum number of tokens to generate in the response.
#  Returns the response from the API.
def simple_llm_call(system_prompt, message, model="mistralai/Mixtral-8x7B-Instruct-v0.1", max_tokens=256, stop=None):
    client = load_together_client()
    chat_completion = client.chat.completions.create(
        messages=[{
            "role": "system",
            "content": system_prompt,
        }, {
            "role": "user",
            "content": message,
        }],
        model=model,
        max_tokens=max_tokens,
        stop=stop
    )
    return chat_completion.choices[0].message.content

### Student Facing API
#  Makes a call to the Together API using the given system prompt and user message with JSON output formatting.
#   system_prompt: The system prompt to send to the API.
#   message: The user message to send to the API.
#   json_class: The class to use for the JSON output.
#   model: The model to use for the API call.
#   max_tokens: The maximum number of tokens to generate in the response.
#  Returns the response from the API as a JSON object
def json_llm_call(system_prompt, message, json_class, model="mistralai/Mixtral-8x7B-Instruct-v0.1", max_tokens=256):
    client = load_together_client()
    chat_completion = client.chat.completions.create(
        messages=[{
            "role": "system",
            "content": system_prompt,
        }, {
            "role": "user",
            "content": message,
        }],
        model=model,
        max_tokens=max_tokens,
        response_format = {
            "type": "json_object",
            "schema": json_class.model_json_schema(),
        }
    )

    return json.loads(chat_completion.choices[0].message.content)