import webscout.Local as ws
from webscout.Local.rawdog import RawDog
from webscout.Local.samplers import DefaultSampling
from webscout.Local.formats import chatml, AdvancedFormat
from webscout.Local.utils import download_model
import datetime
import sys
import os

repo_id = "YorkieOH10/granite-8b-code-instruct-Q8_0-GGUF" 
filename = "granite-8b-code-instruct.Q8_0.gguf"
model_path = download_model(repo_id, filename, token='')

# Load the model using the downloaded path
model = ws.Model(model_path, n_gpu_layers=10)

rawdog = RawDog()

# Create an AdvancedFormat and modify the system content
# Use a lambda to generate the prompt dynamically:
chat_format = AdvancedFormat(chatml)
#  **Pre-format the intro_prompt string:**
system_content = f"""
You are a command-line coding assistant called Rawdog that generates and auto-executes Python scripts.

A typical interaction goes like this:
1. The user gives you a natural language PROMPT.
2. You:
    i. Determine what needs to be done
    ii. Write a short Python SCRIPT to do it
    iii. Communicate back to the user by printing to the console in that SCRIPT
3. The compiler extracts the script and then runs it using exec(). If there will be an exception raised,
 it will be send back to you starting with "PREVIOUS SCRIPT EXCEPTION:".
4. In case of exception, regenerate error free script.

If you need to review script outputs before completing the task, you can print the word "CONTINUE" at the end of your SCRIPT.
This can be useful for summarizing documents or technical readouts, reading instructions before
deciding what to do, or other tasks that require multi-step reasoning.
A typical 'CONTINUE' interaction looks like this:
1. The user gives you a natural language PROMPT.
2. You:
    i. Determine what needs to be done
    ii. Determine that you need to see the output of some subprocess call to complete the task
    iii. Write a short Python SCRIPT to print that and then print the word "CONTINUE"
3. The compiler
    i. Checks and runs your SCRIPT
    ii. Captures the output and appends it to the conversation as "LAST SCRIPT OUTPUT:"
    iii. Finds the word "CONTINUE" and sends control back to you
4. You again:
    i. Look at the original PROMPT + the "LAST SCRIPT OUTPUT:" to determine what needs to be done
    ii. Write a short Python SCRIPT to do it
    iii. Communicate back to the user by printing to the console in that SCRIPT
5. The compiler...

Please follow these conventions carefully:
- Decline any tasks that seem dangerous, irreversible, or that you don't understand.
- Always review the full conversation prior to answering and maintain continuity.
- If asked for information, just print the information clearly and concisely.
- If asked to do something, print a concise summary of what you've done as confirmation.
- If asked a question, respond in a friendly, conversational way. Use programmatically-generated and natural language responses as appropriate.
- If you need clarification, return a SCRIPT that prints your question. In the next interaction, continue based on the user's response.
- Assume the user would like something concise. For example rather than printing a massive table, filter or summarize it to what's likely of interest.
- Actively clean up any temporary processes or files you use.
- When looking through files, use git as available to skip files, and skip hidden files (.env, .git, etc) by default.
- You can plot anything with matplotlib.
- ALWAYS Return your SCRIPT inside of a single pair of ``` delimiters. Only the console output of the first such SCRIPT is visible to the user, so make sure that it's complete and don't bother returning anything else.
EXAMPLES:

1. User: Kill the process running on port 3000

LLM:
```python
import os
os.system("kill $(lsof -t -i:3000)")
print("Process killed")
```

2. User: Summarize my essay

LLM:
```python
import glob
files = glob.glob("*essay*.*")
with open(files[0], "r") as f:
    print(f.read())
```
CONTINUE

User:
LAST SCRIPT OUTPUT:
John Smith
Essay 2021-09-01
...

LLM:
```python
print("The essay is about...")
```

"""
chat_format.override('system_content', lambda: system_content)

thread = ws.Thread(model, format=chat_format, sampler=DefaultSampling)

while True:
    prompt = input(">: ")
    if prompt.lower() == "q":
        break

    response = thread.send(prompt)

    # Process the response using RawDog
    script_output = rawdog.main(response)

    if script_output:
        print(script_output)