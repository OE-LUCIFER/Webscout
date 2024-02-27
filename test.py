from webscout.AI import youChat

# Instantiate the youchat class
youChat = youChat()

while True:
    # Ask the user for a prompt
    prompt = input("💡 Enter a prompt (or type 'exit' to quit): ")
    
    # Exit condition
    if prompt.lower() == 'exit':
        break
    
    # Generate a completion based on the prompt
    try:
        completion = youChat.create(prompt)
        print("💬:", completion)
    except Exception as e:
        print("⚠️ An error occurred:", e)
