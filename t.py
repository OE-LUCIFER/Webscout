from rich import print
from webscout import YEPCHAT
ai = YEPCHAT()
response = ai.chat(input(">>> "))
for chunk in response:
    print(chunk, end="", flush=True)