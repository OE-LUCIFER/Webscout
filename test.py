from webscout import OLLAMA
ollama_provider = OLLAMA(model="qwen2:0.5b")
response = ollama_provider.chat("What is the meaning of life?")
print(response)
