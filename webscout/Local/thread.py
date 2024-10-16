import sys
import time
from typing import Optional, Literal, Union, Generator, Tuple, TextIO
import uuid  

from .model import Model, assert_model_is_loaded, _SupportsWriteAndFlush
from .utils import RESET_ALL, cls, print_verbose, truncate
from .samplers import SamplerSettings, DefaultSampling
from .formats import AdvancedFormat, blank as formats_blank


class Message(dict):
    """
    Represents a single message within a Thread.

    Inherits from `dict` and provides additional functionality:

    - `as_string()`: Returns the full message string.

    Typical message keys:
    - `role`: The speaker's role ('system', 'user', 'bot').
    - `prefix`: Text prefixing the content.
    - `content`: The message content.
    - `suffix`: Text suffixing the content.
    """

    def __repr__(self) -> str:
        return (
            f"Message(["
            f"('role', {repr(self['role'])}), "
            f"('prefix', {repr(self['prefix'])}), "
            f"('content', {repr(self['content'])}), "
            f"('suffix', {repr(self['suffix'])})])"
        )

    def as_string(self) -> str:
        """Returns the full message string."""
        try:
            return self['prefix'] + self['content'] + self['suffix']
        except KeyError as e:
            e.add_note(
                "Message.as_string(): Missing 'prefix', 'content', or 'suffix' "
                "attribute. This is unexpected."
            )
            raise e


class Thread:
    """
    Facilitates easy interactions with a Model.

    Methods:
    - `add_message()`: Appends a message to the thread's messages.
    - `as_string()`: Returns the complete message history as a string.
    - `create_message()`: Creates a message using the thread's format.
    - `inference_str_from_messages()`: Generates an inference-ready string from messages.
    - `interact()`: Starts an interactive chat session.
    - `len_messages()`: Gets the total token length of all messages.
    - `print_stats()`: Prints context usage statistics.
    - `reset()`: Clears the message history.
    - `send()`: Sends a message and receives a response.
    - `warmup()`: Warms up the model by running a simple generation.

    Attributes:
    - `format`: The message format (see `webscout.AIutel.formats`).
    - `messages`: The list of messages in the thread.
    - `model`: The associated `webscout.AIutel.model.Model` instance.
    - `sampler`: The `webscout.AIutel.samplers.SamplerSettings` for text generation.
    - `tools`: A list of tools available for function calling.
    - `uuid`: A unique identifier for the thread (UUID object).
    """

    def __init__(
        self,
        model: Model,
        format: Union[dict, AdvancedFormat],
        sampler: SamplerSettings = DefaultSampling,
        messages: Optional[list[Message]] = None,
    ):
        """
        Initializes a Thread instance.

        Args:
            model: The Model instance for text generation.
            format: The message format (see `webscout.AIutel.formats`).
            sampler: Sampler settings for controlling generation.
            messages: Initial list of messages (optional).
        """
        assert isinstance(model, Model), \
            f"Thread: model should be a webscout.AIutel.model.Model, not {type(model)}"
        assert_model_is_loaded(model)

        assert isinstance(format, (dict, AdvancedFormat)), \
            f"Thread: format should be dict or AdvancedFormat, not {type(format)}"
        
        if any(k not in format.keys() for k in formats_blank.keys()):
            raise KeyError(
                "Thread: format is missing one or more required keys, see "
                "webscout.AIutel.formats.blank for an example"
            )

        assert isinstance(format['stops'], list), \
            f"Thread: format['stops'] should be list, not {type(format['stops'])}"
        
        assert all(
            hasattr(sampler, attr) for attr in [
                'max_len_tokens', 'temp', 'top_p', 'min_p',
                'frequency_penalty', 'presence_penalty', 'repeat_penalty',
                'top_k'
            ]
        ), 'Thread: sampler is missing one or more required attributes'

        self._messages: Optional[list[Message]] = messages
        if self._messages is not None:
            if not all(isinstance(msg, Message) for msg in self._messages):
                raise TypeError(
                    "Thread: one or more messages provided to __init__() is "
                    "not an instance of webscout.AIutel.thread.Message"
                )

        self.model = model
        self.format = format
        self.messages: list[Message] = [
            self.create_message("system", self.format['system_prompt'])
        ] if self._messages is None else self._messages
        self.sampler = sampler
        self.tools = []
        self.uuid = uuid.uuid4()  # Generate a UUID for the thread

        if self.model.verbose:
            print_verbose("New Thread instance with attributes:")
            print_verbose(f"model                     == {self.model}")
            print_verbose(f"format['system_prefix']   == {truncate(repr(self.format['system_prefix']))}")
            print_verbose(f"format['system_prompt']  == {truncate(repr(self.format['system_prompt']))}")
            print_verbose(f"format['system_suffix']   == {truncate(repr(self.format['system_suffix']))}")
            print_verbose(f"format['user_prefix']     == {truncate(repr(self.format['user_prefix']))}")
            # print_verbose(f"format['user_content']    == {truncate(repr(self.format['user_content']))}")
            print_verbose(f"format['user_suffix']     == {truncate(repr(self.format['user_suffix']))}")
            print_verbose(f"format['bot_prefix']      == {truncate(repr(self.format['bot_prefix']))}")
            # print_verbose(f"format['bot_content']     == {truncate(repr(self.format['bot_content']))}")
            print_verbose(f"format['bot_suffix']      == {truncate(repr(self.format['bot_suffix']))}")
            print_verbose(f"format['stops']           == {truncate(repr(self.format['stops']))}")
            print_verbose(f"sampler.temp              == {self.sampler.temp}")
            print_verbose(f"sampler.top_p             == {self.sampler.top_p}")
            print_verbose(f"sampler.min_p             == {self.sampler.min_p}")
            print_verbose(f"sampler.frequency_penalty == {self.sampler.frequency_penalty}")
            print_verbose(f"sampler.presence_penalty  == {self.sampler.presence_penalty}")
            print_verbose(f"sampler.repeat_penalty    == {self.sampler.repeat_penalty}")
            print_verbose(f"sampler.top_k             == {self.sampler.top_k}")

    def add_tool(self, tool: dict) -> None:
        """
        Adds a tool to the Thread for function calling.

        Args:
            tool (dict): A dictionary describing the tool, containing
                         'function' with 'name', 'description', and 'execute' keys.
        """
        self.tools.append(tool)
        self.model.register_tool(tool['function']['name'], tool['function']['execute'])
        self.messages[0]['content'] += f"\nYou have access to the following tool:\n{tool['function']['description']}"

    def __repr__(self) -> str:
        return (
            f"Thread({repr(self.model)}, {repr(self.format)}, "
            f"{repr(self.sampler)}, {repr(self.messages)})"
        )

    def __str__(self) -> str:
        return self.as_string()

    def __len__(self) -> int:
        """Returns the total token length of all messages."""
        return self.len_messages()

    def create_message(self, role: Literal['system', 'user', 'bot'], content: str) -> Message:
        """Constructs a message using the thread's format."""
        assert role.lower() in ['system', 'user', 'bot'], \
            f"Thread.create_message(): role should be 'system', 'user', or 'bot', not '{role.lower()}'"
        assert isinstance(content, str), \
            f"Thread.create_message(): content should be str, not {type(content)}"

        message_data = {
            'system': {
                'role': 'system',
                'prefix': self.format['system_prefix'],
                'content': content,
                'suffix': self.format['system_suffix']
            },
            'user': {
                'role': 'user',
                'prefix': self.format['user_prefix'],
                'content': content,
                'suffix': self.format['user_suffix']
            },
            'bot': {
                'role': 'bot',
                'prefix': self.format['bot_prefix'],
                'content': content,
                'suffix': self.format['bot_suffix']
            }
        }

        return Message(message_data[role.lower()])

    def len_messages(self) -> int:
        """Returns the total length of all messages in tokens."""
        return self.model.get_length(self.as_string())

    def add_message(self, role: Literal['system', 'user', 'bot'], content: str) -> None:
        """Appends a message to the thread's messages."""
        self.messages.append(self.create_message(role, content))

    def inference_str_from_messages(self) -> str:
        """Constructs an inference-ready string from messages."""
        inf_str = ''
        sys_msg_str = ''
        sys_msg_flag = False
        context_len_budget = self.model.context_length

        if len(self.messages) >= 1 and self.messages[0]['role'] == 'system':
            sys_msg_flag = True
            sys_msg = self.messages[0]
            sys_msg_str = sys_msg.as_string()
            context_len_budget -= self.model.get_length(sys_msg_str)

        iterator = reversed(self.messages[1:]) if sys_msg_flag else reversed(self.messages)

        for message in iterator:
            msg_str = message.as_string()
            context_len_budget -= self.model.get_length(msg_str)
            if context_len_budget <= 0:
                break
            inf_str = msg_str + inf_str

        inf_str = sys_msg_str + inf_str if sys_msg_flag else inf_str
        inf_str += self.format['bot_prefix']

        return inf_str

    def send(self, prompt: str) -> str:
        """Sends a message and receives a response."""
        self.add_message("user", prompt)
        output = self.model.generate(
            self.inference_str_from_messages(),
            stops=self.format['stops'],
            sampler=self.sampler
        )
        self.add_message("bot", output)
        return output

    def _interactive_update_sampler(self) -> None:
        """Interactively updates sampler settings."""
        print()
        try:
            for param_name in SamplerSettings.param_types:
                current_value = getattr(self.sampler, param_name)
                new_value = input(f'{param_name}: {current_value} -> ')
                try:
                    if new_value.lower() == 'none':
                        setattr(self.sampler, param_name, None)
                    elif param_name in ('top_k', 'max_len_tokens'):
                        setattr(self.sampler, param_name, int(new_value))
                    else:
                        setattr(self.sampler, param_name, float(new_value))
                    print(f'webscout.AIutel: {param_name} updated')
                except ValueError:
                    print(f'webscout.AIutel: {param_name} not updated (invalid input)')
            print()
        except KeyboardInterrupt:
            print('\nwebscout.AIutel: Sampler settings not updated\n')

    def _interactive_input(
        self,
        prompt: str,
        _dim_style: str,
        _user_style: str,
        _bot_style: str,
        _special_style: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Receives input from the user, handling multi-line input and commands."""
        full_user_input = ''
        
        while True:
            try:
                user_input = input(prompt)
            except KeyboardInterrupt:
                print(f"{RESET_ALL}\n")
                return None, None

            if user_input.endswith('\\'):
                full_user_input += user_input[:-1] + '\n'
            elif user_input == '!':
                print()
                try:
                    command = input(f'{RESET_ALL}  ! {_dim_style}')
                except KeyboardInterrupt:
                    print('\n')
                    continue

                if command == '':
                    print('\n[No command]\n')
                elif command.lower() in ['reset', 'restart']:
                    self.reset()
                    print('\n[Thread reset]\n')
                elif command.lower() in ['cls', 'clear']:
                    cls()
                    print()
                elif command.lower() in ['ctx', 'context']:
                    print(f"\n{self.len_messages()}\n")
                elif command.lower() in ['stats', 'print_stats']:
                    print()
                    self.print_stats()
                    print()
                elif command.lower() in ['sampler', 'samplers', 'settings']:
                    self._interactive_update_sampler()
                elif command.lower() in ['str', 'string', 'as_string']:
                    print(f"\n{self.as_string()}\n")
                elif command.lower() in ['repr', 'save', 'backup']:
                    print(f"\n{repr(self)}\n")
                elif command.lower() in ['remove', 'rem', 'delete', 'del']:
                    print()
                    if len(self.messages) > 1:  # Prevent deleting the system message
                        old_len = len(self.messages)
                        del self.messages[-1]
                        assert len(self.messages) == (old_len - 1)
                        print('[Removed last message]\n')
                    else:
                        print('[Cannot remove system message]\n')
                elif command.lower() in ['last', 'repeat']:
                    if len(self.messages) > 1:
                        last_msg = self.messages[-1]
                        if last_msg['role'] == 'user':
                            print(f"\n{_user_style}{last_msg['content']}{RESET_ALL}\n")
                        elif last_msg['role'] == 'bot':
                            print(f"\n{_bot_style}{last_msg['content']}{RESET_ALL}\n")
                    else:
                        print("\n[No previous message]\n")
                elif command.lower() in ['inf', 'inference', 'inf_str']:
                    print(f'\n"""{self.inference_str_from_messages()}"""\n')
                elif command.lower() in ['reroll', 're-roll', 're', 'swipe']:
                    if len(self.messages) > 1:
                        old_len = len(self.messages)
                        del self.messages[-1]
                        assert len(self.messages) == (old_len - 1)
                        return '', None
                    else:
                        print("\n[Cannot reroll system message]\n")
                elif command.lower() in ['exit', 'quit']:
                    print(RESET_ALL)
                    return None, None
                elif command.lower() in ['help', '/?', '?']:
                    print(
                        "\n"
                        "reset | restart     -- Reset the thread to its original state\n"
                        "clear | cls         -- Clear the terminal\n"
                        "context | ctx       -- Get the context usage in tokens\n"
                        "print_stats | stats -- Get the context usage stats\n"
                        "sampler | settings  -- Update the sampler settings\n"
                        "string | str        -- Print the message history as a string\n"
                        "repr | save         -- Print the representation of the thread\n"
                        "remove | delete     -- Remove the last message\n"
                        "last | repeat       -- Repeat the last message\n"
                        "inference | inf     -- Print the inference string\n"
                        "reroll | swipe      -- Regenerate the last message\n"
                        "exit | quit         -- Exit the interactive chat (can also use ^C)\n"
                        "help | ?            -- Show this screen\n"
                        "\n"
                        "TIP: Type '<' at the prompt and press ENTER to prefix the bot's next message.\n"
                        "     For example, type 'Sure!' to bypass refusals\n"
                        "\n"
                        "TIP: Type '!!' at the prompt and press ENTER to insert a system message\n"
                        "\n"
                    )
                else:
                    print('\n[Unknown command]\n')
            elif user_input == '<':
                print()
                try:
                    next_message_start = input(f'{RESET_ALL}  < {_dim_style}')
                except KeyboardInterrupt:
                    print(f'{RESET_ALL}\n')
                    continue
                else:
                    print()
                    return '', next_message_start
            elif user_input == '!!':
                print()
                try:
                    next_sys_msg = input(f'{RESET_ALL} !! {_special_style}')
                except KeyboardInterrupt:
                    print(f'{RESET_ALL}\n')
                    continue
                else:
                    print()
                    return next_sys_msg, '-1'
            else:
                full_user_input += user_input
                return full_user_input, None

    def interact(
        self,
        color: bool = True,
        header: Optional[str] = None,
        stream: bool = True
    ) -> None:
        """
        Starts an interactive chat session.

        Allows for real-time interaction with the model, including
        interrupting generation, regenerating responses, and using
        commands.

        Args:
            color (bool, optional): Whether to use colored output. Defaults to True.
            header (Optional[str], optional): Header text to display. Defaults to None.
            stream (bool, optional): Whether to stream the response. Defaults to True.
        """
        print()
        from .utils import SPECIAL_STYLE, USER_STYLE, BOT_STYLE, DIM_STYLE
        if not color:
            SPECIAL_STYLE = USER_STYLE = BOT_STYLE = DIM_STYLE = ''
        
        if header is not None:
            print(f"{SPECIAL_STYLE}{header}{RESET_ALL}\n")

        while True:
            prompt = f"{RESET_ALL}  > {USER_STYLE}"
            try:
                user_prompt, next_message_start = self._interactive_input(
                    prompt, DIM_STYLE, USER_STYLE, BOT_STYLE, SPECIAL_STYLE
                )
            except KeyboardInterrupt:
                print(f"{RESET_ALL}\n")
                return
            
            if user_prompt is None and next_message_start is None:
                break

            if next_message_start == '-1':
                self.add_message('system', user_prompt)
                continue

            if next_message_start is not None:
                try:
                    print(f"{BOT_STYLE}{next_message_start}", end='', flush=True)
                    if stream:
                        output = next_message_start + self.model.stream_print(
                            self.inference_str_from_messages() + next_message_start,
                            stops=self.format['stops'],
                            sampler=self.sampler,
                            end=''
                        )
                    else:
                        output = next_message_start + self.model.generate(
                            self.inference_str_from_messages() + next_message_start,
                            stops=self.format['stops'],
                            sampler=self.sampler
                        )
                        print(output, end='', flush=True)
                except KeyboardInterrupt:
                    print(
                        f"{DIM_STYLE} [Message not added to history; "
                        "press ENTER to re-roll]\n"
                    )
                    continue
                else:
                    self.add_message("bot", output)
            else:
                print(BOT_STYLE, end='')
                if user_prompt != "":
                    self.add_message("user", user_prompt)
                try:
                    if stream:
                        output = self.model.stream_print(
                            self.inference_str_from_messages(),
                            stops=self.format['stops'],
                            sampler=self.sampler,
                            end=''
                        )
                    else:
                        output = self.model.generate(
                            self.inference_str_from_messages(),
                            stops=self.format['stops'],
                            sampler=self.sampler
                        )
                        print(output, end='', flush=True)
                except KeyboardInterrupt:
                    print(
                        f"{DIM_STYLE} [Message not added to history; "
                        "press ENTER to re-roll]\n"
                    )
                    continue
                else:
                    self.add_message("bot", output)

            if output.endswith("\n\n"):
                print(RESET_ALL, end='', flush=True)
            elif output.endswith("\n"):
                print(RESET_ALL)
            else:
                print(f"{RESET_ALL}\n")

    def reset(self) -> None:
        """Clears the message history, resetting the thread to its initial state."""
        self.messages: list[Message] = [
            self.create_message("system", self.format['system_prompt'])
        ] if self._messages is None else self._messages

    def as_string(self) -> str:
        """Returns the thread's message history as a string."""
        return ''.join(msg.as_string() for msg in self.messages)

    def print_stats(
        self,
        end: str = '\n',
        file: TextIO = sys.stdout,
        flush: bool = True
    ) -> None:
        """Prints context usage statistics."""
        thread_len_tokens = self.len_messages()
        max_ctx_len = self.model.context_length
        context_used_percentage = round((thread_len_tokens / max_ctx_len) * 100)
        print(
            f"{thread_len_tokens} / {max_ctx_len} tokens "
            f"({context_used_percentage}% of context used), "
            f"{len(self.messages)} messages",
            end=end, file=file, flush=flush
        )
        if not flush:
            file.flush()

    def warmup(self):
        """
        Warms up the model by running a simple generation.
        """
        if self.model.verbose:
            print_verbose("Warming up the model...")
        self.model.generate("This is a warm-up prompt.")