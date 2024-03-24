from webscout.AI import BLACKBOXAI
from rich import print

ai = BLACKBOXAI(
    is_conversation=True,
    max_tokens=800,
    timeout=30,
    intro=None,
    filepath=None,
    update_file=True,
    proxies={},
    history_offset=10250,
    act=None,
    model=None # You can specify a model if needed
)

# Define a prompt to send to the AI
prompt = "Tell me about india"

# Use the 'ask' method to send the prompt and receive a response
response = ai.ask(prompt)

# Extract the text from the response
response_text = ai.get_message(response)

# Print the response text
print(response_text)