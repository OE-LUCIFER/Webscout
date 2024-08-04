from webscout import RUBIKSAI
ai = RUBIKSAI(model="gpt-4o-mini")
response = ai.chat(input(">>> "))
for chunk in response:
    print(chunk, end="", flush=True)