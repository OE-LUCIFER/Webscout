from webscout import ChatGPTUK
# Create an instance of the PERPLEXITY class
ai = ChatGPTUK(
    is_conversation=True,
    max_tokens=800,
    timeout=30,
    intro=None,
    filepath=None,
    update_file=True,
    proxies={},
    history_offset=10250,
    act=None,
)

# Example usage:
prompt = "Explain the concept of recursion in simple terms."
response = ai.chat(prompt)
print(response)