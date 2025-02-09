import os
import sys
import json
import base64

from httpx import stream


from .utils import (
    InferenceLock,
    print_verbose,
    SPECIAL_STYLE,
    assert_type,
    ERROR_STYLE,
    USER_STYLE,
    BOT_STYLE,
    RESET_ALL,
)

from .thread import Thread
from cryptography import x509
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta, UTC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from flask import Flask, render_template, request, Response
from cryptography.hazmat.primitives.serialization import Encoding

# Color codes for console output
YELLOW = SPECIAL_STYLE
GREEN = USER_STYLE
RED = ERROR_STYLE
RESET = RESET_ALL
BLUE = BOT_STYLE

# Warning message for WebUI security
WARNING = f"""{RED}
################################################################################
{RESET}

                          PLEASE KEEP IN MIND

        The webscout.Local WebUI is not guaranteed to be secure.

             It is not intended to be exposed to the internet.

     If you expose the WebUI to the internet, you do so at your own risk.

                          YOU HAVE BEEN WARNED!

{RED}
################################################################################
{RESET}"""

# SSL certificate generation warning
SSL_CERT_FIRST_TIME_WARNING = (
    f"{YELLOW}You have just generated a new self-signed SSL certificate and "
    f"key. Your browser will probably warn you about an untrusted "
    f"certificate. This is expected, and you may safely proceed to the WebUI. "
    f"Subsequent WebUI sessions will reuse this SSL certificate.{RESET}"
)

# Constants
ASSETS_FOLDER = os.path.join(os.path.dirname(__file__), "assets")
MAX_LENGTH_INPUT = 100_000  # Maximum input length (characters)


def generate_self_signed_ssl_cert() -> None:
    """Generates a self-signed SSL certificate and key."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Certificate details
    name = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "XY"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "DUMMY_STATE"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "DUMMY_LOCALITY"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EZLLAMA LLC"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )

    # Certificate builder
    builder = x509.CertificateBuilder(
        subject_name=name,
        issuer_name=name,
        public_key=public_key,
        serial_number=x509.random_serial_number(),
        not_valid_before=datetime.now(tz=UTC),
        not_valid_after=datetime.now(tz=UTC) + timedelta(days=36500),
    )
    builder = builder.add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost")]),
        critical=False,
    )

    # Sign and save the certificate and key
    certificate = builder.sign(private_key=private_key, algorithm=hashes.SHA256())
    with open(f"{ASSETS_FOLDER}/key.pem", "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    with open(f"{ASSETS_FOLDER}/cert.pem", "wb") as f:
        f.write(certificate.public_bytes(Encoding.PEM))


def check_for_ssl_cert() -> bool:
    """Checks if SSL certificate and key exist."""
    return all(
        os.path.exists(f"{ASSETS_FOLDER}/{file}.pem") for file in ["cert", "key"]
    )


def newline() -> None:
    """Prints a newline to stderr."""
    print("", end="\n", file=sys.stderr, flush=True)


def encode(text: str) -> str:
    """Encodes a string to base64."""
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def decode(text: str) -> str:
    """Decodes a base64 encoded string."""
    return base64.b64decode(text).decode("utf-8")


def assert_max_length(text: str) -> None:
    """Asserts that the length of the text is within the allowed limit."""
    if len(text) > MAX_LENGTH_INPUT:
        raise AssertionError(
            f"Input text exceeds maximum length of {MAX_LENGTH_INPUT} characters."
        )


def _print_inference_string(text: str) -> None:
    """Prints the inference string to stderr."""
    print(
        f"{'#' * 80}\n{YELLOW}'''{RESET}{text}{YELLOW}'''{RESET}\n{'#' * 80}",
        file=sys.stderr,
        flush=True,
    )


class WebUI:
    """
    Represents the webscout.Local WebUI server.
    """

    def __init__(self, thread: Thread):
        """
        Initializes the WebUI instance.

        Args:
            thread (Thread): The Thread instance to use for the WebUI.
        """
        assert_type(thread, Thread, "thread", "WebUI")
        self.thread = thread
        self.lock = InferenceLock()
        self._cancel_flag = False

        self.app = Flask(
            __name__,
            static_folder=ASSETS_FOLDER,
            template_folder=ASSETS_FOLDER,
            static_url_path="",
        )

        self._log_host = None
        self._log_port = None

    def log(self, text: str) -> None:
        """Logs a message to the console."""
        if self._log_host is None or self._log_port is None:
            print_verbose(text)
        else:
            print(
                f"webscout.Local: WebUI @ "
                f"{YELLOW}{self._log_host}{RESET}:"
                f"{YELLOW}{self._log_port}{RESET}: {text}",
                file=sys.stderr,
                flush=True,
            )

    def _get_context_string(self) -> str:
        """Returns a string representing the current context usage."""
        thread_len_tokens = self.thread.len_messages()
        max_ctx_len = self.thread.model.context_length
        return f"{thread_len_tokens} / {max_ctx_len} tokens used"

    def start(self, host: str, port: int = 8080, ssl: bool = False) -> None:
        """
        Starts the WebUI server.

        Args:
            host (str): The hostname or IP address to bind the server to.
            port (int, optional): The port to listen on. Defaults to 8080.
            ssl (bool, optional): Whether to use SSL. Defaults to False.
        """
        print(WARNING, file=sys.stderr, flush=True)

        assert_type(host, str, "host", "WebUI.start")
        assert_type(port, int, "port", "WebUI.start")

        self._log_host = host
        self._log_port = port

        self.log("Starting WebUI instance:")
        self.log(f"   thread.uuid == {self.thread.uuid}")
        self.log(f"   host        == {host}")
        self.log(f"   port        == {port}")
        self.log(f"   ssl (HTTPS) == {ssl}")

        if ssl:
            if not check_for_ssl_cert():
                self.log("Generating self-signed SSL certificate...")
                generate_self_signed_ssl_cert()
                print_verbose(SSL_CERT_FIRST_TIME_WARNING)
            else:
                self.log("Reusing previously generated SSL certificate.")

        # Flask route definitions
        @self.app.route("/")
        def home():
            return render_template("index.html")

        @self.app.route("/convo", methods=["GET"])
        def convo():
            msgs_dict = {
                i: {encode(msg["role"]): encode(msg["content"])}
                for i, msg in enumerate(self.thread.messages)
            }
            json_convo = json.dumps(msgs_dict)
            return json_convo, 200, {"ContentType": "application/json"}

        @self.app.route("/cancel", methods=["POST"])
        def cancel():
            newline()
            self.log("Hit cancel endpoint - flag is set.")
            self._cancel_flag = True
            return "", 200

        @self.app.route("/submit", methods=["POST"])
        def submit():
            self.log("Hit submit endpoint.")
            prompt = decode(request.data)
            assert_max_length(prompt)

            if not prompt:
                self.log("Empty prompt submitted. Ignoring.")
                return "", 200

            # Pass the stream variable to the generate function
            def generate(stream=stream):
                with self.lock:
                    self.thread.add_message("user", prompt)
                    print(f"{GREEN}{prompt}{RESET}", file=sys.stderr)
                    inf_str = self.thread.inference_str_from_messages()
                    _print_inference_string(inf_str)

                    if stream:
                        token_generator = self.thread.model.stream(
                            inf_str,
                            stops=self.thread.format["stops"],
                            sampler=self.thread.sampler,
                        )
                        response = ""
                        for token in token_generator:
                            if self._cancel_flag:
                                print(file=sys.stderr)
                                self.log("Canceling generation from /submit.")
                                self._cancel_flag = False
                                return "", 418  # I'm a teapot

                            tok_text = token["choices"][0]["text"]
                            response += tok_text
                            print(
                                f"{BLUE}{tok_text}{RESET}",
                                end="",
                                flush=True,
                                file=sys.stderr,
                            )
                            yield encode(tok_text) + "\n"
                    else:
                        response = self.thread.model.generate(
                            inf_str,
                            stops=self.thread.format["stops"],
                            sampler=self.thread.sampler,
                        )
                        # Simulate streaming by yielding chunks of the content
                        chunk_size = self.stream_chunk_size
                        for i in range(0, len(response), chunk_size):
                            chunk = response[i : i + chunk_size]
                            yield encode(chunk) + "\n"

                    self._cancel_flag = False
                    newline()
                    self.thread.add_message("bot", response)

            return Response(generate(), mimetype="text/plain")

        @self.app.route("/reset", methods=["POST"])
        def reset():
            self.thread.reset()
            self.log("Thread reset.")
            return "", 200

        @self.app.route("/get_context_string", methods=["GET"])
        def get_context_string():
            return (
                json.dumps({"text": encode(self._get_context_string())}),
                200,
                {"ContentType": "application/json"},
            )

        @self.app.route("/remove", methods=["POST"])
        def remove():
            if len(self.thread.messages) > 1:  # Prevent deleting the system message
                self.thread.messages.pop(-1)
                self.log("Removed last message.")
                return "", 200
            else:
                self.log("No previous message to remove.")
                return "", 418  # I'm a teapot

        @self.app.route("/trigger", methods=["POST"])
        def trigger():
            self.log("Hit trigger endpoint.")
            prompt = decode(request.data)
            assert_max_length(prompt)

            if prompt:
                self.log(f"Trigger with prompt: {prompt!r}")
            else:
                self.log("Trigger without prompt.")

            # Pass stream to the generate function
            def generate(stream=stream):
                with self.lock:
                    inf_str = self.thread.inference_str_from_messages() + prompt
                    _print_inference_string(inf_str)

                    if stream:
                        token_generator = self.thread.model.stream(
                            inf_str,
                            stops=self.thread.format["stops"],
                            sampler=self.thread.sampler,
                        )
                        response = ""
                        for token in token_generator:
                            if self._cancel_flag:
                                print(file=sys.stderr)
                                self.log("Canceling generation from /trigger.")
                                self._cancel_flag = False
                                return "", 418  # I'm a teapot

                            tok_text = token["choices"][0]["text"]
                            response += tok_text
                            print(f"{BLUE}{tok_text}{RESET}", end="", flush=True)
                            yield encode(tok_text) + "\n"
                    else:
                        response = self.thread.model.generate(
                            inf_str,
                            stops=self.thread.format["stops"],
                            sampler=self.thread.sampler,
                        )
                        # Simulate streaming by yielding chunks of the content
                        chunk_size = self.stream_chunk_size
                        for i in range(0, len(response), chunk_size):
                            chunk = response[i : i + chunk_size]
                            yield encode(chunk) + "\n"

                    self._cancel_flag = False
                    print("", file=sys.stderr)
                    self.thread.add_message("bot", prompt + response)

            return Response(generate(), mimetype="text/plain")

        @self.app.route("/summarize", methods=["GET"])
        def summarize():
            with self.lock:
                summary = self.thread.summarize()
            self.log(f"Generated summary: {BLUE}{summary!r}{RESET}")
            return encode(summary), 200, {"ContentType": "text/plain"}

        if not self.thread.model.is_loaded():
            self.log("Loading model...")
            self.thread.model.load()
        else:
            self.log("Model is already loaded.")

        self.log("Warming up thread...")
        self.thread.warmup()

        self.log("Running Flask app...")
        try:
            self.app.run(
                host=host,
                port=port,
                ssl_context=(
                    (f"{ASSETS_FOLDER}/cert.pem", f"{ASSETS_FOLDER}/key.pem")
                    if ssl
                    else None
                ),
            )
        except Exception as exc:
            newline()
            self.log(f"{RED}Exception in Flask: {exc}{RESET}")
            raise exc
        else:
            newline()
            self._log_host = None
            self._log_port = None
