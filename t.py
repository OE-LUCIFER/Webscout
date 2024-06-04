from webscout import DeepSeek
from rich import print

ai = DeepSeek(
    is_conversation=True,
    api_key='',
    max_tokens=800,
    timeout=30,
    intro=None,
    filepath=None,
    update_file=True,
    proxies={},
    history_offset=10250,
    act=None,
    model="deepseek_chat"
)

# Start an infinite loop for continuous interaction
while True:
    # Define a prompt to send to the AI
    prompt = input("Enter your prompt: ")
    
    # Check if the user wants to exit the loop
    if prompt.lower() == "exit":
        break
    
    # Use the 'chat' method to send the prompt and receive a response
    r = ai.chat(prompt)
    print(r)