from webscout import WEBS as w
R = w().chat("hello", model='claude-3-haiku') # GPT-3.5 Turbo, mixtral-8x7b, llama-3-70b, claude-3-haiku
print(R)