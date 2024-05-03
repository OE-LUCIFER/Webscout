import webscout
from webscout.AI import LLAMA2

# Optional: Provide proxy details if needed
PROXIES = {}

# Initialize LLAMA2 with desired parameters
llama2 = LLAMA2(
    is_conversation=True, # Flag for conversation mode
    max_tokens=800, # Maximum tokens in the generated text
    temperature=0.7, # Control randomness
    top_p=0.95, # Sampling threshold
    model="meta/meta-llama-3-70b-instruct", # Model name
    proxies=PROXIES, # Optional proxies
)

# Loop to continuously ask for user input and print the response
while True:
    # Ask a question and print the response
    question = input("Enter your question: ")
    response = llama2.chat(question)
    print(response)