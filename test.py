from webscout import GPT4ALL

# Initialize the GPT4ALL class with your model path and other optional parameters
gpt4all_instance = GPT4ALL(
    model="path/to/your/model/file", # Replace with the actual path to your model file
    is_conversation=True,
    max_tokens=800,
    temperature=0.7,
    presence_penalty=0,
    frequency_penalty=1.18,
    top_p=0.4,
    intro="Hello, how can I assist you today?", # sys
    filepath="path/to/conversation/history/file", # Optional, for conversation history
    update_file=True,
    history_offset=10250,
    act=None # Optional, for using an awesome prompt as intro
)

# Generate a response from the AI model
response = gpt4all_instance.chat(
    prompt="What is the weather like today?",
    stream=False, # Set to True if you want to stream the response
    optimizer=None, # Optional, specify an optimizer if needed
    conversationally=False # Set to True for conversationally generated responses
)

# Print the generated response
print(response)