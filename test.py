from webscout.LLM import LLM

def chat(model_name, system_message="You are Jarvis"):
    AI = LLM(model_name, system_message)
    AI.chat()

if __name__ == "__main__":
    model_name = "mistralai/Mistral-7B-Instruct-v0.1" # name of the model you wish to use It supports ALL text generation models on deepinfra.com.
    chat(model_name)