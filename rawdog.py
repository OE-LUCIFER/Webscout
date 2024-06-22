import time
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style
import webscout
import webscout.AIutel
import g4f
from webscout.g4f import *
from webscout.async_providers import mapper as async_provider_map

class TaskExecutor:
    """
    Manages an interactive chat session, handling user input, AI responses, 
    and optional features like web search, code execution, and text-to-speech.
    """

    def __init__(self) -> None:
        """Initializes the conversational assistant with default settings."""
        self._console: Console = Console()

        # Session configuration
        self._selected_provider: str = "phind"
        self._selected_model: str = "Phind Model"
        self._conversation_enabled: bool = True
        self._max_tokens: int = 600
        self._temperature: float = 0.2
        self._top_k: int = -1
        self._top_p: float = 0.999
        self._timeout: int = 30
        self._auth_token: str = None  # API key, if required
        self._chat_completion_enabled: bool = True  # g4fauto
        self._ignore_working: bool = False  # Ignore working status of providers
        self._proxy_path: str = None  # Path to proxy configuration

        # History Management
        self._history_filepath: str = None
        self._update_history_file: bool = True
        self._history_offset: int = 10250

        # Prompt Engineering
        self._initial_prompt: str = None
        self._awesome_prompt_content: str = None 

        # Optional Features
        self._web_search_enabled: bool = False  # Enable web search
        self._rawdog_enabled: bool = True
        self._internal_script_execution_enabled: bool = True
        self._script_confirmation_required: bool = False
        self._selected_interpreter: str = "python"
        self._selected_optimizer: str = "code"
        self._suppress_output: bool = False  # Suppress verbose output

        # AI provider mapping
        self._ai_provider_mapping: Dict[str, Any] = {
            "phind": webscout.PhindSearch,
            "opengpt": webscout.OPENGPT,
            "koboldai": webscout.KOBOLDAI,
            "blackboxai": webscout.BLACKBOXAI,
            "llama2": webscout.LLAMA2,
            "yepchat": webscout.YEPCHAT,
            "leo": webscout.LEO,
            "groq": webscout.GROQ,
            "openai": webscout.OPENAI,
            "perplexity": webscout.PERPLEXITY,
            "you": webscout.YouChat,
            "xjai": webscout.Xjai,
            "cohere": webscout.Cohere,
            "reka": webscout.REKA,
            "thinkany": webscout.ThinkAnyAI,
            "gemini": webscout.GEMINI, 
            "berlin4h": webscout.Berlin4h,
            "chatgptuk": webscout.ChatGPTUK,
            "poe": webscout.POE,
            "basedgpt": webscout.BasedGPT,
            "deepseek": webscout.DeepSeek,
            "deepinfra": webscout.DeepInfra,
            "opengenptv2": webscout.OPENGPTv2
        }

        # Initialize Rawdog if enabled
        if self._rawdog_enabled:
            self._rawdog_instance: webscout.AIutel.RawDog = webscout.AIutel.RawDog(
                quiet=self._suppress_output,
                internal_exec=self._internal_script_execution_enabled,
                confirm_script=self._script_confirmation_required,
                interpreter=self._selected_interpreter,
            )

            self._initial_prompt = self._rawdog_instance.intro_prompt

        # Initialize the selected AI model 
        self._ai_model = self._get_ai_model()

    def _get_ai_model(self):
        """
        Determines the appropriate AI model based on the selected provider, 
        including automatic provider selection and g4fauto support.
        """
        if self._selected_provider == "g4fauto":
            # Automatically select the best provider from g4f
            test = TestProviders(quiet=self._suppress_output, timeout=self._timeout)
            g4fauto = test.best if not self._ignore_working else test.auto
            if isinstance(g4fauto, str):
                self._selected_provider = "g4fauto+" + g4fauto
                self._ai_model = self._create_g4f_model(g4fauto)
            else:
                raise Exception(
                    "No working g4f provider found. "
                    "Consider running 'webscout.webai gpt4free test -y' first"
                )
        else:
            # Use the specified provider
            self._ai_model = self._ai_provider_mapping[self._selected_provider](
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies={},  # Load proxies from config if needed
                history_offset=self._history_offset,
                act=self._awesome_prompt_content, 
                model=self._selected_model,
                quiet=self._suppress_output,
                # auth=self._auth_token,  # Pass API key if required
            )
        return self._ai_model

    def _create_g4f_model(self, provider: str):
        """
        Creates a g4f model instance using the provided provider and webscout.WEBS for web search.
        """
        return webscout.g4f.GPT4FREE(
            provider=provider,
            auth=self._auth_token,
            max_tokens=self._max_tokens,
            chat_completion=self._chat_completion_enabled,
            ignore_working=self._ignore_working,
            timeout=self._timeout,
            intro=self._initial_prompt,
            filepath=self._history_filepath,
            update_file=self._update_history_file,
            proxies={},  # Load proxies from config if needed
            history_offset=self._history_offset,
            act=self._awesome_prompt_content, 
        )

    def process_query(self, query: str) -> None:
        """
        Processes a user query, potentially enhancing it with web search results, 
        passing it to the AI model, and handling the response.

        Args:
            query: The user's text input.

        Returns:
            None
        """
        if self._web_search_enabled:
            query = self._augment_query_with_web_search(query)

        # Apply code optimization if configured
        if self._selected_optimizer == "code":
            query = webscout.AIutel.Optimizers.code(query)

        try:
            response: str = self._ai_model.chat(query)
        except webscout.exceptions.FailedToGenerateResponseError as e:
            self._console.print(Markdown(f"LLM: [red]{e}[/red]"))
            return

        # Handle Rawdog responses if enabled
        if self._rawdog_enabled:
            self._handle_rawdog_response(response)
        else:
            self._console.print(Markdown(f"LLM: {response}"))

    def _augment_query_with_web_search(self, query: str) -> str:
        """Performs a web search and appends the results to the query.

        Args:
            query: The user's text input.

        Returns:
            str: The augmented query with web search results.
        """
        web_search_results = webscout.WEBS().text(query, max_results=3)
        if web_search_results:
            formatted_results = "\n".join(
                f"{i+1}. {result['title']} - {result['href']}\n\nBody: {result['body']}"
                for i, result in enumerate(web_search_results)
            )
            query += f"\n\n## Web Search Results are:\n\n{formatted_results}"
        return query

    def _handle_rawdog_response(self, response: str) -> None:
        """Handles AI responses, potentially executing them as code with Rawdog.

        Args:
            response: The AI model's response.

        Returns:
            None
        """
        try:
            is_feedback = self._rawdog_instance.main(response)
            if is_feedback and "PREVIOUS SCRIPT EXCEPTION" in is_feedback:
                self._console.print(Markdown(f"LLM: {is_feedback}"))
                error_message = is_feedback.split("PREVIOUS SCRIPT EXCEPTION:\n")[1].strip()
                # Generate a solution for the error and execute it
                error_solution_query = (
                    f"The following code was executed and resulted in an error:\n\n"
                    f"{response}\n\n"
                    f"Error: {error_message}\n\n"
                    f"Please provide a solution to fix this error in the code and execute it."
                )
                try:
                    new_response = self._ai_model.chat(error_solution_query)
                    self._handle_rawdog_response(new_response)
                except webscout.exceptions.FailedToGenerateResponseError as e:
                    self._console.print(Markdown(f"LLM: [red]Error while generating solution: {e}[/red]"))
            else:
                self._console.print(Markdown("LLM: (Script executed successfully)"))
        except Exception as e:
            self._console.print(Markdown(f"LLM: [red]Error: {e}[/red]"))


    async def process_async_query(self, query: str) -> None:
        """
        Asynchronously processes a user query, potentially enhancing it with web search results, 
        passing it to the AI model, and handling the response.

        Args:
            query: The user's text input.

        Returns:
            None
        """
        if self._web_search_enabled:
            query = self._augment_query_with_web_search(query)

        # Apply code optimization if configured
        if self._selected_optimizer == "code":
            query = webscout.AIutel.Optimizers.code(query)

        async_model = self._get_async_ai_model()

        try:
            async for response in async_model.chat(query, stream=True):
                self._console.print(Markdown(f"LLM: {response}"), end="")
        except webscout.exceptions.FailedToGenerateResponseError as e:
            self._console.print(Markdown(f"LLM: [red]{e}[/red]"))
            return

        # Handle Rawdog responses if enabled
        if self._rawdog_enabled:
            self._handle_rawdog_response(response)
        else:
            self._console.print(Markdown(f"LLM: {response}"))

    def _get_async_ai_model(self):
        """
        Determines the appropriate asynchronous AI model based on the selected provider.
        """
        if self._selected_provider == "g4fauto":
            # Automatically select the best provider from g4f
            test = TestProviders(quiet=self._suppress_output, timeout=self._timeout)
            g4fauto = test.best if not self._ignore_working else test.auto
            if isinstance(g4fauto, str):
                self._selected_provider = "g4fauto+" + g4fauto
                self._ai_model = self._create_async_g4f_model(g4fauto)
            else:
                raise Exception(
                    "No working g4f provider found. "
                    "Consider running 'webscout gpt4free test -y' first"
                )
        else:
            # Use the specified provider
            if self._selected_provider in async_provider_map:
                self._ai_model = async_provider_map[self._selected_provider](
                    is_conversation=self._conversation_enabled,
                    max_tokens=self._max_tokens,
                    timeout=self._timeout,
                    intro=self._initial_prompt,
                    filepath=self._history_filepath,
                    update_file=self._update_history_file,
                    proxies={},  # Load proxies from config if needed
                    history_offset=self._history_offset,
                    act=self._awesome_prompt_content, 
                    model=self._selected_model,
                    quiet=self._suppress_output,
                    auth=self._auth_token,  # Pass API key if required
                )
            else:
                raise Exception(
                    f"Asynchronous provider '{self._selected_provider}' is not yet supported"
                )
        return self._ai_model

    def _create_async_g4f_model(self, provider: str):
        """
        Creates an asynchronous g4f model instance using the provided provider and webscout.WEBS for web search.
        """
        return webscout.g4f.AsyncGPT4FREE(
            provider=provider,
            auth=self._auth_token,
            max_tokens=self._max_tokens,
            chat_completion=self._chat_completion_enabled,
            ignore_working=self._ignore_working,
            timeout=self._timeout,
            intro=self._initial_prompt,
            filepath=self._history_filepath,
            update_file=self._update_history_file,
            proxies={},  # Load proxies from config if needed
            history_offset=self._history_offset,
            act=self._awesome_prompt_content,
        )

if __name__ == "__main__":
    assistant = TaskExecutor()
    while True:
        input_query = input("Enter your query: ")
        assistant.process_query(input_query)
