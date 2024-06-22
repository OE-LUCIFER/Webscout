from webscout import OPENGPTv2

# Initialize the bot with all specified settings
bot = OPENGPTv2(
    generate_new_agents=True,  # Set to True to generate new IDs, False to load from file
    assistant_name="My Custom Assistant",
    retrieval_description="Helpful information from my files.",
    agent_system_message="",
    enable_action_server=False,  # Assuming you want to disable Action Server by Robocorp
    enable_ddg_search=False,  # Enable DuckDuckGo search tool
    enable_arxiv=False,  # Assuming you want to disable Arxiv
    enable_press_releases=False,  # Assuming you want to disable Press Releases (Kay.ai)
    enable_pubmed=False,  # Assuming you want to disable PubMed
    enable_sec_filings=False,  # Assuming you want to disable SEC Filings (Kay.ai)
    enable_retrieval=False,  # Assuming you want to disable Retrieval
    enable_search_tavily=False,  # Assuming you want to disable Search (Tavily)
    enable_search_short_answer_tavily=False,  # Assuming you want to disable Search (short answer, Tavily)
    enable_you_com_search=True,  # Assuming you want to disable You.com Search
    enable_wikipedia=False,  # Enable Wikipedia tool
    is_public=True,
    is_conversation=True,
    max_tokens=800,
    timeout=40,
    filepath="opengpt_conversation_history.txt",
    update_file=True,
    history_offset=10250,
    act=None,
)

# Example interaction loop
while True:
    prompt = input("You: ")
    if prompt.strip().lower() == 'exit':
        break
    response = bot.chat(prompt)
    print(response)
