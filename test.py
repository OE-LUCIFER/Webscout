from webscout.AI import OPENGPT

opengpt = OPENGPT(is_conversation=True, max_tokens=8000, timeout=30)
# This example sends a simple greeting and prints the response
prompt = "tell me about india"
response_str = opengpt.chat(prompt)
print(response_str)