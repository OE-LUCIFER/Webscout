import json
import time
from typing import Iterable, Dict, Any, Generator

from os import listdir
from uuid import uuid4
from time import sleep, time
from threading import Thread
from json import loads, dumps
from random import getrandbits
from websocket import WebSocketApp
from requests import Session, get, post


from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider, AsyncProvider
from webscout import exceptions


class Perplexity(Provider):
    def __init__(
        self,
        email: str = None,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        quiet: bool = False,
    ) -> None:
        """Instantiates PERPLEXITY

        Args:
            email (str, optional): Your perplexity.ai email. Defaults to None.
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
            quiet (bool, optional): Ignore web search-results and yield final response only. Defaults to False.
        """
        self.max_tokens_to_sample = max_tokens
        self.is_conversation = is_conversation
        self.last_response = {}
        self.web_results: dict = {}
        self.quiet = quiet

        self.session: Session = Session()
        self.user_agent: dict = {
            "User-Agent": "Ask/2.9.1/2406 (iOS; iPhone; Version 17.1) isiOSOnMac/false",
            "X-Client-Name": "Perplexity-iOS",
            "X-App-ApiClient": "ios",
        }
        self.session.headers.update(self.user_agent)

        if email and ".perplexity_session" in listdir():
            self._recover_session(email)
        else:
            self._init_session_without_login()

            if email:
                self._login(email)

        self.email: str = email
        self.t: str = self._get_t()
        self.sid: str = self._get_sid()

        self.n: int = 1
        self.base: int = 420
        self.queue: list = []
        self.finished: bool = True
        self.last_uuid: str = None
        self.backend_uuid: str = (
            None  # unused because we can't yet follow-up questions
        )
        self.frontend_session_id: str = str(uuid4())

        assert self._ask_anonymous_user(), "failed to ask anonymous user"
        self.ws: WebSocketApp = self._init_websocket()
        self.ws_thread: Thread = Thread(target=self.ws.run_forever).start()
        self._auth_session()

        while not (self.ws.sock and self.ws.sock.connected):
            sleep(0.01)

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else intro or Conversation.intro
        )
        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset
        self.session.proxies = proxies

    def _recover_session(self, email: str) -> None:
        with open(".perplexity_session", "r") as f:
            perplexity_session: dict = loads(f.read())

        if email in perplexity_session:
            self.session.cookies.update(perplexity_session[email])
        else:
            self._login(email, perplexity_session)

    def _login(self, email: str, ps: dict = None) -> None:
        self.session.post(
            url="https://www.perplexity.ai/api/auth/signin-email",
            data={"email": email},
        )

        email_link: str = str(input("paste the link you received by email: "))
        self.session.get(email_link)

        if ps:
            ps[email] = self.session.cookies.get_dict()
        else:
            ps = {email: self.session.cookies.get_dict()}

        with open(".perplexity_session", "w") as f:
            f.write(dumps(ps))

    def _init_session_without_login(self) -> None:
        self.session.get(url=f"https://www.perplexity.ai/search/{str(uuid4())}")
        self.session.headers.update(self.user_agent)

    def _auth_session(self) -> None:
        self.session.get(url="https://www.perplexity.ai/api/auth/session")

    def _get_t(self) -> str:
        return format(getrandbits(32), "08x")

    def _get_sid(self) -> str:
        return loads(
            self.session.get(
                url=f"https://www.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.t}"
            ).text[1:]
        )["sid"]

    def _ask_anonymous_user(self) -> bool:
        response = self.session.post(
            url=f"https://www.perplexity.ai/socket.io/?EIO=4&transport=polling&t={self.t}&sid={self.sid}",
            data='40{"jwt":"anonymous-ask-user"}',
        ).text

        return response == "OK"

    def _start_interaction(self) -> None:
        self.finished = False

        if self.n == 9:
            self.n = 0
            self.base *= 10
        else:
            self.n += 1

        self.queue = []

    def _get_cookies_str(self) -> str:
        cookies = ""
        for key, value in self.session.cookies.get_dict().items():
            cookies += f"{key}={value}; "
        return cookies[:-2]

    def _write_file_url(self, filename: str, file_url: str) -> None:
        if ".perplexity_files_url" in listdir():
            with open(".perplexity_files_url", "r") as f:
                perplexity_files_url: dict = loads(f.read())
        else:
            perplexity_files_url: dict = {}

        perplexity_files_url[filename] = file_url

        with open(".perplexity_files_url", "w") as f:
            f.write(dumps(perplexity_files_url))

    def _init_websocket(self) -> WebSocketApp:
        def on_open(ws: WebSocketApp) -> None:
            ws.send("2probe")
            ws.send("5")

        def on_message(ws: WebSocketApp, message: str) -> None:
            if message == "2":
                ws.send("3")
            elif not self.finished:
                if message.startswith("42"):
                    message: list = loads(message[2:])
                    content: dict = message[1]
                    if "mode" in content and content["mode"] == "copilot":
                        content["copilot_answer"] = loads(content["text"])
                    elif "mode" in content:
                        content.update(loads(content["text"]))
                    content.pop("text")
                    if (
                        not ("final" in content and content["final"])
                    ) or ("status" in content and content["status"] == "completed"):
                        self.queue.append(content)
                    if message[0] == "query_answered":
                        self.last_uuid = content["uuid"]
                        self.finished = True
                elif message.startswith("43"):
                    message: dict = loads(message[3:])[0]
                    if (
                        "uuid" in message and message["uuid"] != self.last_uuid
                    ) or "uuid" not in message:
                        self.queue.append(message)
                        self.finished = True

        return WebSocketApp(
            url=f"wss://www.perplexity.ai/socket.io/?EIO=4&transport=websocket&sid={self.sid}",
            header=self.user_agent,
            cookie=self._get_cookies_str(),
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, err: print(f"websocket error: {err}"),
        )

    def _s(
        self,
        query: str,
        mode: str = "concise",
        search_focus: str = "internet",
        attachments: list[str] = [],
        language: str = "en-GB",
        in_page: str = None,
        in_domain: str = None,
    ) -> None:
        assert self.finished, "already searching"
        assert mode in ["concise", "copilot"], "invalid mode"
        assert len(attachments) <= 4, "too many attachments: max 4"
        assert (
            search_focus
            in [
                "internet",
                "scholar",
                "writing",
                "wolfram",
                "youtube",
                "reddit",
            ]
        ), "invalid search focus"

        if in_page:
            search_focus = "in_page"
        if in_domain:
            search_focus = "in_domain"

        self._start_interaction()
        ws_message: str = (
            f"{self.base + self.n}"
            + dumps(
                [
                    "perplexity_ask",
                    query,
                    {
                        "version": "2.1",
                        "source": "default",  # "ios"
                        "frontend_session_id": self.frontend_session_id,
                        "language": language,
                        "timezone": "CET",
                        "attachments": attachments,
                        "search_focus": search_focus,
                        "frontend_uuid": str(uuid4()),
                        "mode": mode,
                        # "use_inhouse_model": True
                        "in_page": in_page,
                        "in_domain": in_domain,
                    },
                ]
            )
        )

        self.ws.send(ws_message)

    def search(
        self,
        query: str,
        mode: str = "concise",
        search_focus: str = "internet",
        attachments: list[str] = [],
        language: str = "en-GB",
        timeout: float = 30,
        in_page: str = None,
        in_domain: str = None,
    ) -> Iterable[Dict]:
        self._s(query, mode, search_focus, attachments, language, in_page, in_domain)

        start_time: float = time()
        while (not self.finished) or len(self.queue) != 0:
            if timeout and time() - start_time > timeout:
                self.finished = True
                return {"error": "timeout"}
            if len(self.queue) != 0:
                yield self.queue.pop(0)

    def search_sync(
        self,
        query: str,
        mode: str = "concise",
        search_focus: str = "internet",
        attachments: list[str] = [],
        language: str = "en-GB",
        timeout: float = 30,
        in_page: str = None,
        in_domain: str = None,
    ) -> dict:
        self._s(query, mode, search_focus, attachments, language, in_page, in_domain)

        start_time: float = time()
        while not self.finished:
            if timeout and time() - start_time > timeout:
                self.finished = True
                return {"error": "timeout"}

        return self.queue.pop(-1)

    def upload(self, filename: str) -> str:
        assert self.finished, "already searching"
        assert filename.split(".")[-1] in [
            "txt",
            "pdf",
        ], "invalid file format"

        if filename.startswith("http"):
            file = get(filename).content
        else:
            with open(filename, "rb") as f:
                file = f.read()

        self._start_interaction()
        ws_message: str = (
            f"{self.base + self.n}"
            + dumps(
                [
                    "get_upload_url",
                    {
                        "version": "2.1",
                        "source": "default",
                        "content_type": "text/plain"
                        if filename.split(".")[-1] == "txt"
                        else "application/pdf",
                    },
                ]
            )
        )

        self.ws.send(ws_message)

        while not self.finished or len(self.queue) != 0:
            if len(self.queue) != 0:
                upload_data = self.queue.pop(0)

        assert not upload_data["rate_limited"], "rate limited"

        post(
            url=upload_data["url"],
            files={
                "acl": (None, upload_data["fields"]["acl"]),
                "Content-Type": (None, upload_data["fields"]["Content-Type"]),
                "key": (None, upload_data["fields"]["key"]),
                "AWSAccessKeyId": (None, upload_data["fields"]["AWSAccessKeyId"]),
                "x-amz-security-token": (
                    None,
                    upload_data["fields"]["x-amz-security-token"],
                ),
                "policy": (None, upload_data["fields"]["policy"]),
                "signature": (None, upload_data["fields"]["signature"]),
                "file": (filename, file),
            },
        )

        file_url: str = (
            upload_data["url"] + upload_data["fields"]["key"].split("$")[0] + filename
        )

        self._write_file_url(filename, file_url)

        return file_url

    def threads(self, query: str = None, limit: int = None) -> list[dict]:
        assert self.email, "not logged in"
        assert self.finished, "already searching"

        if not limit:
            limit = 20
        data: dict = {"version": "2.1", "source": "default", "limit": limit, "offset": 0}
        if query:
            data["search_term"] = query

        self._start_interaction()
        ws_message: str = f"{self.base + self.n}" + dumps(["list_ask_threads", data])

        self.ws.send(ws_message)

        while not self.finished or len(self.queue) != 0:
            if len(self.queue) != 0:
                return self.queue.pop(0)

    def list_autosuggest(self, query: str = "", search_focus: str = "internet") -> list[dict]:
        assert self.finished, "already searching"

        self._start_interaction()
        ws_message: str = (
            f"{self.base + self.n}"
            + dumps(
                [
                    "list_autosuggest",
                    query,
                    {
                        "has_attachment": False,
                        "search_focus": search_focus,
                        "source": "default",
                        "version": "2.1",
                    },
                ]
            )
        )

        self.ws.send(ws_message)

        while not self.finished or len(self.queue) != 0:
            if len(self.queue) != 0:
                return self.queue.pop(0)

    def close(self) -> None:
        self.ws.close()

        if self.email:
            with open(".perplexity_session", "r") as f:
                perplexity_session: dict = loads(f.read())

            perplexity_session[self.email] = self.session.cookies.get_dict()

            with open(".perplexity_session", "w") as f:
                f.write(dumps(perplexity_session))

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict | Generator:
        """Chat with AI

                Args:
                    prompt (str): Prompt to be send.
                    stream (bool, optional): Flag for streaming response. Defaults to False.
                    raw (bool, optional): Stream back raw response as received. Defaults to False.
                    optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
                    conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
                Returns:
                   dict : {}
                ```json
        {
            "status": "pending",
            "uuid": "3604dfcc-611f-4b7d-989d-edca2a7233c7",
            "read_write_token": null,
            "frontend_context_uuid": "f6d43119-5231-481d-b692-f52e1f52d2c6",
            "final": false,
            "backend_uuid": "a6d6ec9e-da69-4841-af74-0de0409267a8",
            "media_items": [],
            "widget_data": [],
            "knowledge_cards": [],
            "expect_search_results": "false",
            "mode": "concise",
            "search_focus": "internet",
            "gpt4": false,
            "display_model": "turbo",
            "attachments": null,
            "answer": "",
            "web_results": [],
            "chunks": [],
            "extra_web_results": []
        }
                ```
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        def for_stream():
            for response in self.search(conversation_prompt):
                yield dumps(response) if raw else response
                self.last_response.update(response)

            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )

        def for_non_stream():
            self.last_response.update(self.search_sync(conversation_prompt))
            self.conversation.update_chat_history(
                prompt, self.get_message(self.last_response)
            )
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> str | Generator:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str: Response generated
        """

        def for_stream():
            for response in self.ask(
                prompt, True, optimizer=optimizer, conversationally=conversationally
            ):
                yield self.get_message(response)

        def for_non_stream():
            return self.get_message(
                self.ask(
                    prompt,
                    False,
                    optimizer=optimizer,
                    conversationally=conversationally,
                )
            )

        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        text_str: str = response.get("answer", "")

        def update_web_results(web_results: list) -> None:
            for index, results in enumerate(web_results, start=1):
                self.web_results[str(index) + ". " + results["name"]] = dict(
                    url=results.get("url"), snippet=results.get("snippet")
                )

        if response.get("text"):
            # last chunk
            target: dict[str, Any] = json.loads(response.get("text"))
            text_str = target.get("answer")
            web_results: list[dict] = target.get("web_results")
            self.web_results.clear()
            update_web_results(web_results)

            return text_str 

        else:
            return text_str 


if __name__ == "__main__":
    perplexity = Perplexity() 
    # Stream the response
    response = perplexity.chat("What is the meaning of life?")
    for chunk in response:
        print(chunk, end="", flush=True)

    perplexity.close()