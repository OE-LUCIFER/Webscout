from webscout.webai import Main

def use_rawdog_with_webai(prompt):
    """
    Wrap the webscout default method in a try-except block to catch any unhandled
    exceptions and print a helpful message.
    """
    try:
        webai_bot = Main(
            max_tokens=500, 
            provider="phind",
            temperature=0.7,  
            top_k=40,          
            top_p=0.95,        
            model="Phind Model",  # Replace with your desired model
            auth=None,       # Replace with your auth key/value (if needed)
            timeout=30,
            disable_conversation=True,
            filepath=None,
            update_file=True,
            intro=None,
            rawdog=True,
            history_offset=10250,
            awesome_prompt=None,
            proxy_path=None,
            quiet=True
        )
        webai_response = webai_bot.default(prompt) 
    except Exception as e:
        print("Unexpected error:", e)


if __name__ == "__main__":
    user_prompt = input("Enter your prompt: ")
    use_rawdog_with_webai(user_prompt)
