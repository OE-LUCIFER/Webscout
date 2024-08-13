<<<<<<< Updated upstream
from webscout import ThinkAnyAI

ai = ThinkAnyAI()

while True:
    response = ai.chat(input(">>> "))
    for chunk in response:
        print(chunk, end="", flush=True)  
=======
from webscout import ThinkAnyAI

ai = ThinkAnyAI()

while True:
    response = ai.chat(input(">>> "))
    for chunk in response:
        print(chunk, end="", flush=True)  
>>>>>>> Stashed changes
    print("\n")  