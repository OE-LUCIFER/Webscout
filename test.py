from webscout import MultiChatAI
ai = MultiChatAI(is_conversation=True, max_tokens=800, timeout=30, intro=None, filepath=None, update_file=True, proxies={}, history_offset=10250, act=None)
resp = ai.chat("test", stream=True)
for chunks in resp:
  print(chunks, end="", flush=True)