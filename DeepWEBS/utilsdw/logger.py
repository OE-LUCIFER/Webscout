import datetime
import functools
import inspect
import logging
import os
import shutil
import subprocess
from termcolor import colored


def add_fillers(text, filler="=", fill_side="both"):
    terminal_width = shutil.get_terminal_size().columns
    text = text.strip()
    text_width = len(text)
    if text_width >= terminal_width:
        return text

    if fill_side[0].lower() == "b":
        leading_fill_str = filler * ((terminal_width - text_width) // 2 - 1) + " "
        trailing_fill_str = " " + filler * (
            terminal_width - text_width - len(leading_fill_str) - 1
        )
    elif fill_side[0].lower() == "l":
        leading_fill_str = filler * (terminal_width - text_width - 1) + " "
        trailing_fill_str = ""
    elif fill_side[0].lower() == "r":
        leading_fill_str = ""
        trailing_fill_str = " " + filler * (terminal_width - text_width - 1)
    else:
        raise ValueError("Invalid fill_side")

    filled_str = f"{leading_fill_str}{text}{trailing_fill_str}"
    return filled_str


class OSLogger(logging.Logger):
    LOG_METHODS = {
        "err": ("error", "red"),
        "warn": ("warning", "light_red"),
        "note": ("info", "light_magenta"),
        "mesg": ("info", "light_cyan"),
        "file": ("info", "light_blue"),
        "line": ("info", "white"),
        "success": ("info", "light_green"),
        "fail": ("info", "light_red"),
        "back": ("debug", "light_cyan"),
    }
    INDENT_METHODS = [
        "indent",
        "set_indent",
        "reset_indent",
        "store_indent",
        "restore_indent",
        "log_indent",
    ]
    LEVEL_METHODS = [
        "set_level",
        "store_level",
        "restore_level",
        "quiet",
        "enter_quiet",
        "exit_quiet",
    ]
    LEVEL_NAMES = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

    def __init__(self, name=None, prefix=False):
        if not name:
            frame = inspect.stack()[1]
            module = inspect.getmodule(frame[0])
            name = module.__name__

        super().__init__(name)
        self.setLevel(logging.INFO)

        if prefix:
            formatter_prefix = "[%(asctime)s] - [%(name)s] - [%(levelname)s]\n"
        else:
            formatter_prefix = ""

        self.formatter = logging.Formatter(formatter_prefix + "%(message)s")

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(self.formatter)
        self.addHandler(stream_handler)

        self.log_indent = 0
        self.log_indents = []

        self.log_level = "info"
        self.log_levels = []

    def indent(self, indent=2):
        self.log_indent += indent

    def set_indent(self, indent=2):
        self.log_indent = indent

    def reset_indent(self):
        self.log_indent = 0

    def store_indent(self):
        self.log_indents.append(self.log_indent)

    def restore_indent(self):
        self.log_indent = self.log_indents.pop(-1)

    def set_level(self, level):
        self.log_level = level
        self.setLevel(self.LEVEL_NAMES[level])

    def store_level(self):
        self.log_levels.append(self.log_level)

    def restore_level(self):
        self.log_level = self.log_levels.pop(-1)
        self.set_level(self.log_level)

    def quiet(self):
        self.set_level("critical")

    def enter_quiet(self, quiet=False):
        if quiet:
            self.store_level()
            self.quiet()

    def exit_quiet(self, quiet=False):
        if quiet:
            self.restore_level()

    def log(
        self,
        level,
        color,
        msg,
        indent=0,
        fill=False,
        fill_side="both",
        end="\n",
        *args,
        **kwargs,
    ):
        if type(msg) == str:
            msg_str = msg
        else:
            msg_str = repr(msg)
            quotes = ["'", '"']
            if msg_str[0] in quotes and msg_str[-1] in quotes:
                msg_str = msg_str[1:-1]

        indent_str = " " * (self.log_indent + indent)
        indented_msg = "\n".join([indent_str + line for line in msg_str.split("\n")])

        if fill:
            indented_msg = add_fillers(indented_msg, fill_side=fill_side)

        handler = self.handlers[0]
        handler.terminator = end

        getattr(self, level)(colored(indented_msg, color), *args, **kwargs)

    def route_log(self, method, msg, *args, **kwargs):
        level, method = method
        functools.partial(self.log, level, method, msg)(*args, **kwargs)

    def err(self, msg: str = "", *args, **kwargs):
        self.route_log(("error", "red"), msg, *args, **kwargs)

    def warn(self, msg: str = "", *args, **kwargs):
        self.route_log(("warning", "light_red"), msg, *args, **kwargs)

    def note(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "light_magenta"), msg, *args, **kwargs)

    def mesg(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "light_cyan"), msg, *args, **kwargs)

    def file(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "light_blue"), msg, *args, **kwargs)

    def line(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "white"), msg, *args, **kwargs)

    def success(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "light_green"), msg, *args, **kwargs)

    def fail(self, msg: str = "", *args, **kwargs):
        self.route_log(("info", "light_red"), msg, *args, **kwargs)

    def back(self, msg: str = "", *args, **kwargs):
        self.route_log(("debug", "light_cyan"), msg, *args, **kwargs)


logger = OSLogger()


def shell_cmd(cmd, getoutput=False, showcmd=True, env=None):
    if showcmd:
        logger.info(colored(f"\n$ [{os.getcwd()}]", "light_blue"))
        logger.info(colored(f"  $ {cmd}\n", "light_cyan"))
    if getoutput:
        output = subprocess.getoutput(cmd, env=env)
        return output
    else:
        subprocess.run(cmd, shell=True, env=env)


class Runtimer:
    def __enter__(self):
        self.t1, _ = self.start_time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.t2, _ = self.end_time()
        self.elapsed_time(self.t2 - self.t1)

    def start_time(self):
        t1 = datetime.datetime.now()
        self.logger_time("start", t1)
        return t1, self.time2str(t1)

    def end_time(self):
        t2 = datetime.datetime.now()
        self.logger_time("end", t2)
        return t2, self.time2str(t2)

    def elapsed_time(self, dt=None):
        if dt is None:
            dt = self.t2 - self.t1
        self.logger_time("elapsed", dt)
        return dt, self.time2str(dt)

    def logger_time(self, time_type, t):
        time_types = {
            "start": "Start",
            "end": "End",
            "elapsed": "Elapsed",
        }
        time_str = add_fillers(
            colored(
                f"{time_types[time_type]} time: [ {self.time2str(t)} ]",
                "light_magenta",
            ),
            fill_side="both",
        )
        logger.line(time_str)

    # Convert time to string
    def time2str(self, t):
        datetime_str_format = "%Y-%m-%d %H:%M:%S"
        if isinstance(t, datetime.datetime):
            return t.strftime(datetime_str_format)
        elif isinstance(t, datetime.timedelta):
            hours = t.seconds // 3600
            hour_str = f"{hours} hr" if hours > 0 else ""
            minutes = (t.seconds // 60) % 60
            minute_str = f"{minutes:>2} min" if minutes > 0 else ""
            seconds = t.seconds % 60
            second_str = f"{seconds:>2} s"
            time_str = " ".join([hour_str, minute_str, second_str]).strip()
            return time_str
        else:
            return str(t)
