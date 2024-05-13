import sys

from .model    import Model, assert_model_is_loaded, _SupportsWriteAndFlush
from .utils    import RESET_ALL, cls, print_verbose, truncate
from .samplers import SamplerSettings, DefaultSampling
from typing    import Optional, Literal, Union

from .formats import blank as formats_blank


class Thread:
    """
    Provide functionality to facilitate easy interactions with a Model

    This is just a brief overview of .Thread.
    To see a full description of each method and its parameters,
    call help(Thread), or see the relevant docstring.

    The following methods are available:
    - `.add_message()` - Add a message to `Thread.messages`
    - `.as_string()` - Return this thread's complete message history as a string
    - `.create_message()` - Create a message using the format of this thread
    - `.inference_str_from_messages()` - Using the list of messages, return a string suitable for inference
    - `.interact()` - Start an interactive, terminal-based chat session
    - `.len_messages()` - Get the total length of all messages in tokens
    - `.print_stats()` - Print stats about the context usage in this thread
    - `.reset()` - Clear the list of messages
    - `.send()` - Send a message in this thread

    The following attributes are available:
    - `.format` - The format being used for messages in this thread
    - `.messages` - The list of messages in this thread
    - `.model` - The `.Model` instance used by this thread
    - `.sampler` - The SamplerSettings object used in this thread
    """

    def __init__(
        self,
        model: Model,
        format: dict[str, Union[str, list]],
        sampler: SamplerSettings = DefaultSampling
    ):
        """
        Given a Model and a format, construct a Thread instance.

        model: The Model to use for text generation
        format: The format specifying how messages should be structured (see .formats)

        The following parameter is optional:
        - sampler: The SamplerSettings object used to control text generation
        """
        
        assert isinstance(model, Model), \
            "Thread: model should be an " + \
            f"instance of webscout.Model, not {type(model)}"
        
        assert_model_is_loaded(model)

        assert isinstance(format, dict), \
            f"Thread: format should be dict, not {type(format)}"
        
        if any(k not in format.keys() for k in formats_blank.keys()):
            raise KeyError(
                "Thread: format is missing one or more required keys, see " + \
                "webscout.formats.blank for an example"
            )

        assert isinstance(format['stops'], list), \
            "Thread: format['stops'] should be list, not " + \
            f"{type(format['stops'])}"
        
        assert all(
            hasattr(sampler, attr) for attr in [
                'max_len_tokens',
                'temp',
                'top_p',
                'min_p',
                'frequency_penalty',
                'presence_penalty',
                'repeat_penalty',
                'top_k'
            ]
        ), 'Thread: sampler is missing one or more required attributes'
        
        self.model: Model = model
        self.format: dict[str, Union[str, list]] = format
        self.messages: list[dict[str, str]] = [
            self.create_message("system", self.format['system_content'])
        ]
        self.sampler: SamplerSettings = sampler

        if self.model.verbose:
            print_verbose("new Thread instance with the following attributes:")
            print_verbose(f"model                     == {self.model}")
            print_verbose(f"format['system_prefix']   == {truncate(repr(self.format['system_prefix']))}")
            print_verbose(f"format['system_content']  == {truncate(repr(self.format['system_content']))}")
            print_verbose(f"format['system_postfix']  == {truncate(repr(self.format['system_postfix']))}")
            print_verbose(f"format['user_prefix']     == {truncate(repr(self.format['user_prefix']))}")
            print_verbose(f"format['user_content']    == {truncate(repr(self.format['user_content']))}")
            print_verbose(f"format['user_postfix']    == {truncate(repr(self.format['user_postfix']))}")
            print_verbose(f"format['bot_prefix']      == {truncate(repr(self.format['bot_prefix']))}")
            print_verbose(f"format['bot_content']     == {truncate(repr(self.format['bot_content']))}")
            print_verbose(f"format['bot_postfix']     == {truncate(repr(self.format['bot_postfix']))}")
            print_verbose(f"format['stops']           == {truncate(repr(self.format['stops']))}")
            print_verbose(f"sampler.temp              == {self.sampler.temp}")
            print_verbose(f"sampler.top_p             == {self.sampler.top_p}")
            print_verbose(f"sampler.min_p             == {self.sampler.min_p}")
            print_verbose(f"sampler.frequency_penalty == {self.sampler.frequency_penalty}")
            print_verbose(f"sampler.presence_penalty  == {self.sampler.presence_penalty}")
            print_verbose(f"sampler.repeat_penalty    == {self.sampler.repeat_penalty}")
            print_verbose(f"sampler.top_k             == {self.sampler.top_k}")
    

    def __repr__(self) -> str:
        repr_str = f"Thread({repr(self.model)}, {repr(self.format)}, "
        repr_str += f"{repr(self.sampler)})"
        # system message is created from format, so not represented
        if len(self.messages) <= 1:
            return repr_str
        else:
            for msg in self.messages:
                if msg['role'] == 'user':
                    repr_str += "\nThread.add_message('user', " + repr(msg['content']) + ')'
                elif msg['role'] == 'bot':
                    repr_str += "\nThread.add_message('bot', " + repr(msg['content']) + ')'
            return repr_str
    
    def __str__(self) -> str:
        return self.as_string()
    
    def __len__(self) -> int:
        """
        `len(Thread)` returns the length of the Thread in tokens

        To get the number of messages in the Thread, use `len(Thread.messages)`
        """
        return self.len_messages()

    def create_message(
        self,
        role: Literal['system', 'user', 'bot'],
        content: str
    ) -> dict[str, str]:
        """
        Create a message using the format of this Thread
        """

        assert role.lower() in ['system', 'user', 'bot'], \
            f"create_message: role should be 'system', 'user', or 'bot', not '{role.lower()}'"

        assert isinstance(content, str), \
            f"create_message: content should be str, not {type(content)}"

        if role.lower() == 'system':
            return {
                "role": "system",
                "prefix": self.format['system_prefix'],
                "content": content,
                "postfix": self.format['system_postfix']
            }
        
        elif role.lower() == 'user':
            return {
                "role": "user",
                "prefix": self.format['user_prefix'],
                "content": content,
                "postfix": self.format['user_postfix']
            }
        
        elif role.lower() == 'bot':
            return {
                "role": "bot",
                "prefix": self.format['bot_prefix'],
                "content": content,
                "postfix": self.format['bot_postfix']
            }
    
    def len_messages(self) -> int:
        """
        Return the total length of all messages in this thread, in tokens.
        
        Equivalent to `len(Thread)`."""

        return self.model.get_length(self.as_string())

    def add_message(
        self,
        role: Literal['system', 'user', 'bot'],
        content: str
    ) -> None:
        """
        Create a message and append it to `Thread.messages`.

        `Thread.add_message(...)` is a shorthand for
        `Thread.messages.append(Thread.create_message(...))`
        """
        self.messages.append(
            self.create_message(
                role=role,
                content=content
            )
        )

    def inference_str_from_messages(self) -> str:
        """
        Using the list of messages, construct a string suitable for inference,
        respecting the format and context length of this thread.
        """

        messages = self.messages

        context_len_budget = self.model.context_length
        if len(messages) > 0:
            sys_msg = messages[0]
            sys_msg_str = (
                sys_msg['prefix'] + sys_msg['content'] + sys_msg['postfix']
            )
            context_len_budget -= self.model.get_length(sys_msg_str)
        else:
            sys_msg_str = ''

        inf_str = ''

        # Start at most recent message and work backwards up the history
        # excluding system message. Once we exceed thread
        # max_context_length, break without including that message
        for message in reversed(messages[1:]):
            context_len_budget -= self.model.get_length(
                message['prefix'] + message['content'] + message['postfix']
            )

            if context_len_budget <= 0:
                break

            msg_str = (
                message['prefix'] + message['content'] + message['postfix']
            )
            
            inf_str = msg_str + inf_str

        inf_str = sys_msg_str + inf_str
        inf_str += self.format['bot_prefix']

        return inf_str


    def send(self, prompt: str) -> str:
        """
        Send a message in this thread. This adds your message and the bot's
        response to the list of messages.

        Returns a string containing the response to your message.
        """

        self.add_message("user", prompt)
        output = self.model.generate(
            self.inference_str_from_messages(),
            stops=self.format['stops'],
            sampler=self.sampler
        )
        self.add_message("bot", output)

        return output
    

    def _interactive_update_sampler(self) -> None:
        """Interactively update the sampler settings used in this Thread"""
        print()
        try:
            new_max_len_tokens = input(f'max_len_tokens: {self.sampler.max_len_tokens} -> ')
            new_temp = input(f'temp: {self.sampler.temp} -> ')
            new_top_p = input(f'top_p: {self.sampler.top_p} -> ')
            new_min_p = input(f'min_p: {self.sampler.min_p} -> ')
            new_frequency_penalty = input(f'frequency_penalty: {self.sampler.frequency_penalty} -> ')
            new_presence_penalty = input(f'presence_penalty: {self.sampler.presence_penalty} -> ')
            new_repeat_penalty = input(f'repeat_penalty: {self.sampler.repeat_penalty} -> ')
            new_top_k = input(f'top_k: {self.sampler.top_k} -> ')
        
        except KeyboardInterrupt:
            print('\nwebscout: sampler settings not updated\n')
            return
        print()

        try:
            self.sampler.max_len_tokens = int(new_max_len_tokens)
        except ValueError:
            pass
        else:
            print('webscout: max_len_tokens updated')
        
        try:
            self.sampler.temp = float(new_temp)
        except ValueError:
            pass
        else:
            print('webscout: temp updated')
        
        try:
            self.sampler.top_p = float(new_top_p)
        except ValueError:
            pass
        else:
            print('webscout: top_p updated')

        try:
            self.sampler.min_p = float(new_min_p)
        except ValueError:
            pass
        else:
            print('webscout: min_p updated')

        try:
            self.sampler.frequency_penalty = float(new_frequency_penalty)
        except ValueError:
            pass
        else:
            print('webscout: frequency_penalty updated')
        
        try:
            self.sampler.presence_penalty = float(new_presence_penalty)
        except ValueError:
            pass
        else:
            print('webscout: presence_penalty updated')
        
        try:
            self.sampler.repeat_penalty = float(new_repeat_penalty)
        except ValueError:
            pass
        else:
            print('webscout: repeat_penalty updated')
        
        try:
            self.sampler.top_k = int(new_top_k)
        except ValueError:
            pass
        else:
            print('webscout: top_k updated')
        print()
                

    def _interactive_input(
        self,
        prompt: str,
        _dim_style: str,
        _user_style: str,
        _bot_style: str
    ) -> tuple:
        """
        Recive input from the user, while handling multi-line input
        and commands
        """
        full_user_input = '' # may become multiline
        
        while True:
            user_input = input(prompt)
            
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
                    print(f'\n[no command]\n')

                elif command.lower() in ['reset', 'restart']:
                    self.reset()
                    print(f'\n[thread reset]\n')

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
                    old_len = len(self.messages)
                    del self.messages[-1]
                    assert len(self.messages) == (old_len - 1)
                    print('[removed last message]\n')

                elif command.lower() in ['last', 'repeat']:
                    last_msg = self.messages[-1]
                    if last_msg['role'] == 'user':
                        print(f"\n{_user_style}{last_msg['content']}{RESET_ALL}\n")
                    elif last_msg['role'] == 'bot':
                        print(f"\n{_bot_style}{last_msg['content']}{RESET_ALL}\n")
                
                elif command.lower() in ['inf', 'inference', 'inf_str']:
                    print(f'\n"""{self.inference_str_from_messages()}"""\n')
                
                elif command.lower() in ['reroll', 're-roll', 're', 'swipe']:
                    old_len = len(self.messages)
                    del self.messages[-1]
                    assert len(self.messages) == (old_len - 1)
                    return '', None
                
                elif command.lower() in ['exit', 'quit']:
                    print(RESET_ALL)
                    return None, None
                
                elif command.lower() in ['help', '/?', '?']:
                    print()
                    print('reset / restart     -- Reset the thread to its original state')
                    print('clear / cls         -- Clear the terminal')
                    print('context / ctx       -- Get the context usage in tokens')
                    print('print_stats / stats -- Get the context usage stats')
                    print('sampler / settings  -- Update the sampler settings')
                    print('string / str        -- Print the message history as a string')
                    print('repr / save         -- Print the representation of the thread')
                    print('remove / delete     -- Remove the last message')
                    print('last / repeat       -- Repeat the last message')
                    print('inference / inf     -- Print the inference string')
                    print('reroll / swipe      -- Regenerate the last message')
                    print('exit / quit         -- Exit the interactive chat (can also use ^C)')
                    print('help / ?            -- Show this screen')
                    print()
                    print("TIP: type < at the prompt and press ENTER to prefix the bot's next message.")
                    print('     for example, type "Sure!" to bypass refusals')
                    print()

                else:
                    print(f'\n[unknown command]\n')
            
            elif user_input == '<': # the next bot message will start with...

                print()
                try:
                    next_message_start = input(f'{_dim_style}  < ')

                except KeyboardInterrupt:
                    print(f'{RESET_ALL}\n')
                    continue

                else:
                    print()
                    return '', next_message_start
            
            elif user_input.endswith('<'):

                print()

                msg = user_input.removesuffix('<')
                self.add_message("user", msg)
                
                try:
                    next_message_start = input(f'{_dim_style}  < ')

                except KeyboardInterrupt:
                    print(f'{RESET_ALL}\n')
                    continue

                else:
                    print()
                    return '', next_message_start

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
        Start an interactive chat session using this Thread.

        While text is being generated, press `^C` to interrupt the bot.
        Then you have the option to press `ENTER` to re-roll, or to simply type
        another message.

        At the prompt, press `^C` to end the chat session.

        Type `!` and press `ENTER` to enter a basic command prompt. For a list
        of  commands, type `help` at this prompt.
        
        Type `<` and press `ENTER` to prefix the bot's next message, for
        example with `Sure!`.

        The following parameters are optional:
        - color: Whether to use colored text to differentiate user / bot
        - header: Header text to print at the start of the interaction
        - stream: Whether to stream text as it is generated
        """
        print()

        # fresh import of color codes in case `color` param has changed
        from .utils import USER_STYLE, BOT_STYLE, DIM_STYLE, SPECIAL_STYLE

        # disable color codes if explicitly disabled by `color` param
        if not color:
            USER_STYLE = ''
            BOT_STYLE = ''
            DIM_STYLE = ''
            SPECIAL_STYLE = ''
        
        if header is not None:
            print(f"{SPECIAL_STYLE}{header}{RESET_ALL}\n")
        
        while True:

            prompt = f"{RESET_ALL}  > {USER_STYLE}"
            
            try:
                user_prompt, next_message_start = self._interactive_input(
                    prompt,
                    DIM_STYLE,
                    USER_STYLE,
                    BOT_STYLE
                )
            except KeyboardInterrupt:
                print(f"{RESET_ALL}\n")
                return
            
            # got 'exit' or 'quit' command
            if user_prompt is None and next_message_start is None:
                break
            
            if next_message_start is not None:
                try:
                    if stream:
                        print(f"{BOT_STYLE}{next_message_start}", end='', flush=True)
                        output = next_message_start + self.model.stream_print(
                            self.inference_str_from_messages() + next_message_start,
                            stops=self.format['stops'],
                            sampler=self.sampler,
                            end=''
                        )
                    else:
                        print(f"{BOT_STYLE}", end='', flush=True)
                        output = next_message_start + self.model.generate(
                            self.inference_str_from_messages() + next_message_start,
                            stops=self.format['stops'],
                            sampler=self.sampler
                        )
                        print(output, end='', flush=True)
                except KeyboardInterrupt:
                    print(f"{DIM_STYLE} [message not added to history; press ENTER to re-roll]\n")
                    continue
                else:
                    self.add_message("bot", output)
            else:
                print(BOT_STYLE)
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
                    print(f"{DIM_STYLE} [message not added to history; press ENTER to re-roll]\n")
                    continue
                else:
                    self.add_message("bot", output)

            if output.endswith("\n\n"):
                print(RESET_ALL, end = '', flush=True)
            elif output.endswith("\n"):
                print(RESET_ALL)
            else:
                print(f"{RESET_ALL}\n")


    def reset(self) -> None:
        """
        Clear the list of messages, which resets the thread to its original
        state
        """
        self.messages: list[dict[str, str]] = [
            self.create_message("system", self.format['system_content'])
        ]
    
    
    def as_string(self) -> str:
        """Return this thread's message history as a string"""
        ret = ''
        for msg in self.messages:
            ret += msg['prefix']
            ret += msg['content']
            ret += msg['postfix']
        return ret

    
    def print_stats(
        self,
        end: str = '\n',
        file: _SupportsWriteAndFlush = sys.stdout,
        flush: bool = True
    ) -> None:
        """Print stats about the context usage in this thread"""
        thread_len_tokens = self.len_messages()
        max_ctx_len = self.model.context_length
        context_used_percentage = round((thread_len_tokens/max_ctx_len)*100)
        print(f"{thread_len_tokens} / {max_ctx_len} tokens", file=file, flush=flush)
        print(f"{context_used_percentage}% of context used", file=file, flush=flush)
        print(f"{len(self.messages)} messages", end=end, file=file, flush=flush)
        if not flush:
            file.flush()