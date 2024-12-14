from webscout import Genspark
genspark = Genspark()
resp = genspark.chat("tell me about Abhay koul, HelpingAI", stream=True)
for chunk in resp:
    print(chunk, end='', flush=True)