import os
import logging
from typing import Optional
from .Litlogger import LitLogger, LogFormat, ColorScheme

# Create a logger instance for this module
logger = LitLogger(
    name="Conversation",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.CYBERPUNK
)

class Conversation:
    """Handles prompt generation based on history and maintains chat context.
    
    This class is responsible for managing chat conversations, including:
    - Maintaining chat history
    - Loading/saving conversations from/to files
    - Generating prompts based on context
    - Managing token limits and history pruning
    
    Examples:
        >>> chat = Conversation(max_tokens=500)
        >>> chat.add_message("user", "Hello!")
        >>> chat.add_message("llm", "Hi there!")
        >>> prompt = chat.gen_complete_prompt("What's up?")
    """

    intro = (
        "You're a Large Language Model for chatting with people. "
        "Assume role of the LLM and give your response."
    )

    def __init__(
        self,
        status: bool = True,
        max_tokens: int = 600,
        filepath: Optional[str] = None,
        update_file: bool = True,
    ):
        """Initialize a new Conversation manager.

        Args:
            status (bool): Flag to control history tracking. Defaults to True.
            max_tokens (int): Maximum tokens for completion response. Defaults to 600.
            filepath (str, optional): Path to save/load conversation history. Defaults to None.
            update_file (bool): Whether to append new messages to file. Defaults to True.

        Examples:
            >>> chat = Conversation(max_tokens=500)
            >>> chat = Conversation(filepath="chat_history.txt")
        """
        self.status = status
        self.max_tokens_to_sample = max_tokens
        self.chat_history = ""  # Initialize as empty string
        self.history_format = "\nUser : %(user)s\nLLM :%(llm)s"
        self.file = filepath
        self.update_file = update_file
        self.history_offset = 10250
        self.prompt_allowance = 10
        
        if filepath:
            self.load_conversation(filepath, False)

    def load_conversation(self, filepath: str, exists: bool = True) -> None:
        """Load conversation history from a text file.

        Args:
            filepath (str): Path to the history file
            exists (bool): Flag for file availability. Defaults to True.

        Raises:
            AssertionError: If filepath is not str or file doesn't exist
        """
        assert isinstance(
            filepath, str
        ), f"Filepath needs to be of str datatype not {type(filepath)}"
        assert (
            os.path.isfile(filepath) if exists else True
        ), f"File '{filepath}' does not exist"

        if not os.path.isfile(filepath):
            logging.debug(f"Creating new chat-history file - '{filepath}'")
            with open(filepath, "w", encoding="utf-8") as fh:
                fh.write(self.intro)
        else:
            logging.debug(f"Loading conversation from '{filepath}'")
            with open(filepath, encoding="utf-8") as fh:
                file_contents = fh.readlines()
                if file_contents:
                    self.intro = file_contents[0]  # First line is intro
                    self.chat_history = "\n".join(file_contents[1:])
    
    def __trim_chat_history(self, chat_history: str, intro: str) -> str:
        """Keep the chat history fresh by trimming it when it gets too long! 

        This method makes sure we don't exceed our token limits by:
        - Calculating total length (intro + history)
        - Trimming older messages if needed
        - Keeping the convo smooth and within limits

        Args:
            chat_history (str): The current chat history to trim
            intro (str): The conversation's intro/system prompt

        Returns:
            str: The trimmed chat history, ready to use! 

        Examples:
            >>> chat = Conversation(max_tokens=500)
            >>> trimmed = chat._Conversation__trim_chat_history("Hello! Hi!", "Intro")
        """
        len_of_intro = len(intro)
        len_of_chat_history = len(chat_history)
        total = self.max_tokens_to_sample + len_of_intro + len_of_chat_history

        if total > self.history_offset:
            truncate_at = (total - self.history_offset) + self.prompt_allowance
            trimmed_chat_history = chat_history[truncate_at:]
            return "... " + trimmed_chat_history
        return chat_history

    def gen_complete_prompt(self, prompt: str, intro: Optional[str] = None) -> str:
        """Generate a complete prompt that's ready to go! 

        This method:
        - Combines the intro, history, and new prompt
        - Trims history if needed
        - Keeps everything organized and flowing

        Args:
            prompt (str): Your message to add to the chat
            intro (str, optional): Custom intro to use. Default: None (uses class intro)

        Returns:
            str: The complete conversation prompt, ready for the LLM! 

        Examples:
            >>> chat = Conversation()
            >>> prompt = chat.gen_complete_prompt("What's good?")
        """
        if not self.status:
            return prompt

        intro = intro or self.intro or (
            "You're a Large Language Model for chatting with people. "
            "Assume role of the LLM and give your response."
        )
        
        incomplete_chat_history = self.chat_history + self.history_format % {
            "user": prompt,
            "llm": ""
        }
        complete_prompt = intro + self.__trim_chat_history(incomplete_chat_history, intro)
        # logger.info(f"Generated prompt: {complete_prompt}")
        return complete_prompt

    def update_chat_history(
        self, prompt: str, response: str, force: bool = False
    ) -> None:
        """Keep the conversation flowing by updating the chat history! 

        This method:
        - Adds new messages to the history
        - Updates the file if needed
        - Keeps everything organized

        Args:
            prompt (str): Your message to add
            response (str): The LLM's response
            force (bool): Force update even if history is off. Default: False

        Examples:
            >>> chat = Conversation()
            >>> chat.update_chat_history("Hi!", "Hello there!")
        """
        if not self.status and not force:
            return

        new_history = self.history_format % {"user": prompt, "llm": response}
        
        if self.file and self.update_file:
            # Create file if it doesn't exist
            if not os.path.exists(self.file):
                with open(self.file, "w", encoding="utf-8") as fh:
                    fh.write(self.intro + "\n")
            
            # Append new history
            with open(self.file, "a", encoding="utf-8") as fh:
                fh.write(new_history)
        
        self.chat_history += new_history
        # logger.info(f"Chat history updated with prompt: {prompt}")

    def add_message(self, role: str, content: str) -> None:
        """Add a new message to the chat - simple and clean! 

        This method:
        - Validates the message role
        - Adds the message to history
        - Updates file if needed

        Args:
            role (str): Who's sending? ('user', 'llm', 'tool', or 'reasoning')
            content (str): What's the message?

        Examples:
            >>> chat = Conversation()
            >>> chat.add_message("user", "Hey there!")
            >>> chat.add_message("llm", "Hi! How can I help?")
        """
        if not self.validate_message(role, content):
            raise ValueError("Invalid message role or content")

        role_formats = {
            "user": "User",
            "llm": "LLM",
            "tool": "Tool",
            "reasoning": "Reasoning"
        }

        if role in role_formats:
            self.chat_history += f"\n{role_formats[role]} : {content}"
        else:
            logger.warning(f"Unknown role '{role}' for message: {content}")

    #     # Enhanced logging for message addition
    #     logger.info(f"Added message from {role}: {content}")
    #     logging.info(f"Message added: {role}: {content}")

    # def validate_message(self, role: str, content: str) -> bool:
    #     """Validate the message role and content."""
    #     valid_roles = {'user', 'llm', 'tool', 'reasoning'}
    #     if role not in valid_roles:
    #         logger.error(f"Invalid role: {role}")
    #         return False
    #     if not content:
    #         logger.error("Content cannot be empty.")
    #         return False
    #     return True


