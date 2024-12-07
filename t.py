
from webscout import Meta
Meta = Meta()
ai = Meta.chat("hi")
for chunk in ai:
    print(chunk, end="", flush=True)
