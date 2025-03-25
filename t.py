from webscout import autocoder_utiles
from webscout import autocoder
from webscout import FreeAIChat

ai = FreeAIChat(model="o3-mini-high", timeout=5000, system_prompt=autocoder_utiles.get_intro_prompt())
agent = autocoder.AutoCoder(ai_instance=ai)
while True:
    response = ai.chat(input("> "))
    resp = agent.main(response=response)
    if resp:
        print(resp)
