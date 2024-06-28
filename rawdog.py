import time
import uuid
from typing import Dict, Any, Optional, Callable, Generator, Union, List
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
        self._ai_model = None
        self._rawdog_instance = None
        self._proxies = {}  # Initialize proxies
        self._local_thread = None

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
        self._history_filepath: str = "history.txt"
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

        self._initialize_rawdog()
        self._initialize_ai_model()

    
    def _get_provider_mapping(self):
        """Returns a dictionary mapping provider names to their initialization functions."""
        getOr = lambda option, default: option if option else default

        return {
            "g4fauto": lambda: self._create_g4f_model(
                self._get_best_g4f_provider()
            ),
            "poe": lambda: webscout.POE(
                cookie=self._auth_token,
                model=getOr(self._selected_model, "Assistant"),
                proxy=bool(self._proxies),
                timeout=self._timeout,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                intro=self._initial_prompt,
                act=self._awesome_prompt_content,
            ),
            "leo": lambda: webscout.LEO(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                top_k=self._top_k,
                top_p=self._top_p,
                model=getOr(self._selected_model, "llama-2-13b-chat"),
                brave_key=getOr(self._auth_token, "qztbjzBqJueQZLFkwTTJrieu8Vw3789u"),
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "openai": lambda: webscout.OPENAI(
                api_key=self._auth_token,
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                presence_penalty=self._top_p,
                frequency_penalty=self._top_k,
                top_p=self._top_p,
                model=getOr(self._selected_model, self._selected_model),
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "auto": lambda: webscout.AUTO(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "opengpt": lambda: webscout.OPENGPT(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
                assistant_id="bca37014-6f97-4f2b-8928-81ea8d478d88"
            ),
            "thinkany": lambda: webscout.ThinkAnyAI(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "berlin4h": lambda: webscout.Berlin4h(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "chatgptuk": lambda: webscout.ChatGPTUK(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "geminiflash": lambda: webscout.GEMINIFLASH(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "geminipro": lambda: webscout.GEMINIPRO(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "yepchat": lambda: webscout.YEPCHAT(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                presence_penalty=self._top_p,
                frequency_penalty=self._top_k,
                top_p=self._top_p,
                model=getOr(self._selected_model, "Mixtral-8x7B-Instruct-v0.1"),
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "groq": lambda: webscout.GROQ(
                api_key=self._auth_token,
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                presence_penalty=self._top_p,
                frequency_penalty=self._top_k,
                top_p=self._top_p,
                model=getOr(self._selected_model, "mixtral-8x7b-32768"),
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "cohere": lambda: webscout.Cohere(
                api_key=self._auth_token,
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                top_k=self._top_k,
                top_p=self._top_p,
                model=getOr(self._selected_model, "command-r-plus"),
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "reka": lambda: webscout.REKA(
                api_key=self._auth_token,
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
                model=getOr(self._selected_model, "reka-core"),
            ),
            "deepseek": lambda: webscout.DeepSeek(
                api_key=self._auth_token,
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
                model=getOr(self._selected_model, "deepseek_chat"),
            ),
            "koboldai": lambda: webscout.KOBOLDAI(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                top_p=self._top_p,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "deepinfra": lambda: webscout.DeepInfra(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                model=getOr(self._selected_model, "Qwen/Qwen2-72B-Instruct"),
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "xjai": lambda: webscout.Xjai(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                top_p=self._top_p,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "gemini": lambda: webscout.GEMINI(
                cookie_file=self._auth_token,
                proxy=self._proxies,
                timeout=self._timeout,
            ),
            "phind": lambda: webscout.PhindSearch(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
                model=getOr(self._selected_model, "Phind Model"),
                quiet=self._suppress_output,
            ),
            "blackboxai": lambda: webscout.BLACKBOXAI(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "you": lambda: webscout.YouChat(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "perplexity": lambda: webscout.PERPLEXITY(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
                quiet=self._suppress_output,
            ),
            "basedgpt": lambda: webscout.BasedGPT(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "opengenptv2": lambda: self._create_opengenptv2_model(),
            "vtlchat": lambda: webscout.VTLchat(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            ),
            "phindv2": lambda: webscout.Phindv2(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
                model=getOr(self._selected_model, "Phind Instant"),
                quiet=self._suppress_output,
            ),
            "llama2": lambda: webscout.LLAMA2(
                is_conversation=self._conversation_enabled,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
                intro=self._initial_prompt,
                filepath=self._history_filepath,
                update_file=self._update_history_file,
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
                model=getOr(self._selected_model, "meta/meta-llama-3-70b-instruct"),
            ),
            "local": lambda: self._create_local_model(),
        }

    def _create_opengenptv2_model(self):
        """Creates a OPENGPTv2 model instance with all the tools."""
        return webscout.OPENGPTv2(
            generate_new_agents=False,
            assistant_name="webscout",
            retrieval_description=(
                "Can be used to look up information that was uploaded to this assistant.\n"
                "If the user is referencing particular files, that is often a good hint that information may be here.\n"
                "If the user asks a vague question, they are likely meaning to look up info from this retriever, "
                "and you should call it!"
            ),
            agent_system_message="You are a helpful assistant.",
            chat_retrieval_llm_type="GPT 3.5 Turbo",
            chat_retrieval_system_message="You are a helpful assistant.",
            chatbot_llm_type="GPT 3.5 Turbo",
            chatbot_system_message="You are a helpful assistant.",
            enable_action_server=True,  # Enable Action Server by Robocorp
            enable_ddg_search=True,  # Enable Duck Duck Go Search
            enable_arxiv=True,  # Enable Arxiv
            enable_press_releases=True,  # Enable Press Releases (Kay.ai)
            enable_pubmed=True,  # Enable PubMed
            enable_sec_filings=True,  # Enable SEC Filings (Kay.ai)
            enable_retrieval=True,  # Enable Retrieval
            enable_search_tavily=True,  # Enable Search (Tavily)
            enable_search_short_answer_tavily=True,  # Enable Search (short answer, Tavily)
            enable_you_com_search=True,  # Enable You.com Search
            enable_wikipedia=True,  # Enable Wikipedia
            is_public=True,
            is_conversation=self._conversation_enabled,
            max_tokens=self._max_tokens,
            timeout=self._timeout,
            intro=self._initial_prompt,
            filepath=self._history_filepath,
            update_file=self._update_history_file,
            proxies=self._proxies,
            history_offset=self._history_offset,
            act=self._awesome_prompt_content,
        )
    def _create_local_model(self):
        from webscout.Local import formats, samplers, Model
        """Creates a local Model instance."""
        # Load the GGUF model file
        if hasattr(self, 'local_model') and self.local_model is not None:
            return self.local_model
        # This section is now using llama-cpp-python
        # This is the local AI functionality
        model = Model(
            model_path="path/to/your/model.gguf",  # Replace with your model path
            context_length=2048, 
            verbose=True,  
            flash_attn=True,
        )
        self.local_model = webscout.Local.Thread(
            model=model, 
            format=formats.llama2chat,
            sampler=samplers.DefaultSampling,
            messages=[],
        )
        return self.local_model
    
    def _get_ai_model(self):
        """
        Gets the AI model based on the selected provider.
        """
        provider_mapping = self._get_provider_mapping()

        if self._selected_provider in provider_mapping:
            initializer = provider_mapping[self._selected_provider]
            self._ai_model = initializer()
        else:
            raise ValueError(f"Invalid provider: {self._selected_provider}")

        return self._ai_model


    def _get_best_g4f_provider(self) -> str:
        """Gets the best performing g4f provider."""
        test = TestProviders(quiet=self._suppress_output, timeout=self._timeout)
        return test.best if not self._ignore_working else test.auto
    
    def _create_g4f_model(self, provider: str):
        """
        Creates a g4f model instance.
        """
        if isinstance(provider, str):
            self._selected_provider = "g4fauto+" + provider
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
                proxies=self._proxies,
                history_offset=self._history_offset,
                act=self._awesome_prompt_content,
            )
        else:
            raise Exception(
                "No working g4f provider found. "
                "Consider running 'webscout gpt4free test -y' first"
            )

    def _initialize_rawdog(self):
        """Initializes Rawdog if enabled."""
        if self._rawdog_enabled:
            self._rawdog_instance: webscout.AIutel.RawDog = webscout.AIutel.RawDog(
                quiet=self._suppress_output,
                internal_exec=self._internal_script_execution_enabled,
                confirm_script=self._script_confirmation_required,
                interpreter=self._selected_interpreter,
            )

            self._initial_prompt = self._rawdog_instance.intro_prompt

    def _initialize_ai_model(self):
        """Initializes the selected AI model."""
        self._ai_model = self._get_ai_model()

    def process_query(self, query: str) -> None:
        """
        Processes a user query, enhancing it with web search results (if enabled),
        passing it to the AI model, and handling the response.
        """
        if self._web_search_enabled:
            query = self._augment_query_with_web_search(query)

        if self._selected_optimizer == "code":
            query = webscout.AIutel.Optimizers.code(query)

        try:
            if self._selected_provider == "local":
                # This is the local AI code section
                if hasattr(self, 'local_model') and self.local_model is not None:
                    response = self._local_thread.send(query)  # Send query to local thread
                else:
                    raise Exception("Local AI model is not loaded. Please load a local model first.")
            else:
                response = self._ai_model.chat(query)  # Send query to selected provider
        except webscout.exceptions.FailedToGenerateResponseError as e:
            self._console.print(Markdown(f"LLM: [red]{e}[/red]"))
            return
        except Exception as e:
            self._console.print(Markdown(f"LLM: [red]{e}[/red]"))
            return

        if self._rawdog_enabled:
            self._handle_rawdog_response(response)
        else:
            self._console.print(Markdown(f"LLM: {response}"))

    def _augment_query_with_web_search(self, query: str) -> str:
        """Performs a web search and appends the results to the query."""
        web_search_results = webscout.WEBS().text(query, max_results=3)
        if web_search_results:
            formatted_results = "\n".join(
                f"{i+1}. {result['title']} - {result['href']}\n\nBody: {result['body']}"
                for i, result in enumerate(web_search_results)
            )
            query += f"\n\n## Web Search Results are:\n\n{formatted_results}"
        return query

    def _handle_rawdog_response(self, response: str) -> None:
        """Handles AI responses, executing them as code with Rawdog if enabled."""
        try:
            is_feedback = self._rawdog_instance.main(response)
            if is_feedback and "PREVIOUS SCRIPT EXCEPTION" in is_feedback:
                self._console.print(Markdown(f"LLM: {is_feedback}"))
                error_message = is_feedback.split("PREVIOUS SCRIPT EXCEPTION:\n")[1].strip()
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
                    self._console.print(
                        Markdown(f"LLM: [red]Error while generating solution: {e}[/red]")
                    )
            else:
                self._console.print(Markdown("LLM: (Script executed successfully)"))
        except Exception as e:
            self._console.print(Markdown(f"LLM: [red]Error: {e}[/red]"))


if __name__ == "__main__":
    assistant = TaskExecutor()
    while True:
        input_query = input("Enter your query: ")
        assistant.process_query(input_query)