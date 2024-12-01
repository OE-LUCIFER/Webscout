"""
SwiftCLI - A powerful Python CLI framework 

A modern, feature-rich CLI framework for building awesome command-line applications.
Built with love for the Python community! 

Basic Usage:
    >>> from swiftcli import CLI
    >>> app = CLI(name="my-app", help="My awesome CLI app")
    >>> @app.command()
    ... def hello(name: str):
    ...     '''Say hello to someone'''
    ...     print(f"Hello {name}!")
    >>> app.run()

Advanced Usage:
    >>> @app.group()
    ... def db():
    ...     '''Database commands'''
    ...     pass
    >>> 
    >>> @db.command()
    ... def migrate():
    ...     '''Run database migrations'''
    ...     print("Running migrations...")

For more examples, check out the documentation!
"""

import os
import sys
import json
import inspect
from typing import Any, Dict, List, Optional, Type, Union, Callable
from functools import wraps
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme

# Console setup
console = Console()

class UsageError(Exception):
    """Raised when CLI is used incorrectly"""
    pass

class BadParameter(UsageError):
    """Raised when a parameter is invalid"""
    pass

class Context:
    """
    Context object that holds state for the CLI app.

    Attributes:
        cli (CLI): The CLI application instance.
        parent (Context): The parent context.
        command (str): The current command.
        obj (Any): The current object.
        params (Dict[str, Any]): The current parameters.
    """
    def __init__(
        self,
        cli: 'CLI',
        parent: Optional['Context'] = None,
        command: Optional[str] = None,
        obj: Any = None
    ):
        self.cli = cli
        self.parent = parent
        self.command = command
        self.obj = obj
        self.params = {}

class Plugin:
    """
    Base class for SwiftCLI plugins.

    Attributes:
        app (CLI): The CLI application instance.
        enabled (bool): Whether the plugin is enabled.
        config (Dict[str, Any]): The plugin configuration.
    """
    def __init__(self):
        self.app = None
        self.enabled = True
        self.config: Dict[str, Any] = {}
    
    def init_app(self, app):
        """Initialize plugin with CLI app instance"""
        self.app = app
    
    def before_command(self, command: str, args: List[str]) -> Optional[bool]:
        """Called before command execution"""
        pass
    
    def after_command(self, command: str, args: List[str], result: Any):
        """Called after command execution"""
        pass
    
    def on_error(self, command: str, error: Exception):
        """Called when command raises an error"""
        pass
    
    def on_help(self, command: str) -> Optional[str]:
        """Called when help is requested for a command"""
        pass
    
    def on_completion(self, command: str, incomplete: str) -> List[str]:
        """Called when shell completion is requested"""
        return []

class PluginManager:
    """
    Manages SwiftCLI plugins.

    Attributes:
        plugins (List[Plugin]): The list of plugins.
        plugin_dir (str): The plugin directory.
    """
    def __init__(self):
        self.plugins: List[Plugin] = []
        self.plugin_dir = os.path.expanduser("~/.swiftcli/plugins")
        os.makedirs(self.plugin_dir, exist_ok=True)
        sys.path.append(self.plugin_dir)
    
    def register(self, plugin: Plugin):
        """Register a new plugin"""
        self.plugins.append(plugin)
    
    def load_plugins(self):
        """Load all plugins from plugin directory"""
        for file in Path(self.plugin_dir).glob("*.py"):
            if file.name.startswith("_"):
                continue
            try:
                module = importlib.import_module(file.stem)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, Plugin) and 
                        attr is not Plugin):
                        plugin = attr()
                        self.register(plugin)
            except Exception as e:
                console.print(f"[red]Error loading plugin {file.name}: {e}[/red]")
    
    def before_command(self, command: str, args: List[str]) -> bool:
        """Run before_command hooks"""
        for plugin in self.plugins:
            if not plugin.enabled:
                continue
            try:
                result = plugin.before_command(command, args)
                if result is False:
                    return False
            except Exception as e:
                console.print(f"[red]Error in plugin {plugin.__class__.__name__}: {e}[/red]")
        return True
    
    def after_command(self, command: str, args: List[str], result: Any):
        """Run after_command hooks"""
        for plugin in self.plugins:
            if not plugin.enabled:
                continue
            try:
                plugin.after_command(command, args, result)
            except Exception as e:
                console.print(f"[red]Error in plugin {plugin.__class__.__name__}: {e}[/red]")
    
    def on_error(self, command: str, error: Exception):
        """Run error hooks"""
        for plugin in self.plugins:
            if not plugin.enabled:
                continue
            try:
                plugin.on_error(command, error)
            except Exception as e:
                console.print(f"[red]Error in plugin {plugin.__class__.__name__}: {e}[/red]")

class Group:
    """
    Command group that can contain subcommands and be chained.

    Basic Usage:
        >>> @app.group()
        ... def db():
        ...     '''Database commands'''
        ...     pass
        >>> @db.command()
        ... def migrate():
        ...     '''Run migrations'''
        ...     pass

    Advanced Usage:
        >>> @app.group(chain=True)
        ... def process():
        ...     '''Process data'''
        ...     pass
        >>> @process.command()
        ... def validate():
        ...     '''Validate data'''
        ...     pass
    """
    def __init__(
        self,
        name: str = None,
        help: str = None,
        chain: bool = False,
        invoke_without_command: bool = False
    ):
        self.name = name
        self.help = help
        self.chain = chain
        self.invoke_without_command = invoke_without_command
        self.commands = {}
    
    def command(
        self,
        name: str = None,
        help: str = None,
        aliases: List[str] = None,
        hidden: bool = False
    ):
        """Register a new command"""
        def decorator(f):
            cmd_name = name or f.__name__
            self.commands[cmd_name] = {
                'func': f,
                'help': help or f.__doc__,
                'aliases': aliases or [],
                'hidden': hidden
            }
            return f
        return decorator

    def group(self, *args, **kwargs):
        """Create a subgroup"""
        def decorator(f):
            subgroup = Group(*args, **kwargs)
            self.commands[subgroup.name] = subgroup
            return subgroup
        return decorator

    def run(self, args: List[str]):
        """Run the group command"""
        if not args or args[0] in ['-h', '--help']:
            self._print_help()
            return
        
        command_name = args[0]
        command_args = args[1:]
        
        if command_name not in self.commands:
            console.print(f"[red]Unknown command: {command_name}[/red]")
            self._print_help()
            return 1
        
        command = self.commands[command_name]
        try:
            result = command['func'](**self._parse_args(command, command_args))
            if self.chain and result is not None:
                return result
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            return 1
    
    def _parse_args(self, command: Dict, args: List[str]) -> Dict[str, Any]:
        """Parse command arguments"""
        params = {}
        func = command['func']
        sig = inspect.signature(func)
        
        # Handle options
        if hasattr(func, '_options'):
            for opt in func._options:
                # Get the destination parameter name from the longest option
                param_decls = sorted(opt['param_decls'], key=len, reverse=True)
                param_name = param_decls[0].lstrip('-').replace('-', '_')
                
                # If there's a parameter name in the signature, use that instead
                for param in sig.parameters.values():
                    if param.name in [d.lstrip('-').replace('-', '_') for d in param_decls]:
                        param_name = param.name
                        break
                
                found = False
                multiple_values = []
                
                # Check for long and short options
                i = 0
                while i < len(args):
                    if args[i] in opt['param_decls']:
                        if opt.get('is_flag', False):
                            if opt.get('multiple', False):
                                multiple_values.append(True)
                            else:
                                params[param_name] = True
                        else:
                            if i + 1 < len(args):
                                value = args[i + 1]
                                # Convert value to the correct type
                                if 'type' in opt:
                                    try:
                                        value = opt['type'](value)
                                    except ValueError:
                                        raise UsageError(f"Invalid value for {args[i]}: {value}")
                                
                                if opt.get('multiple', False):
                                    multiple_values.append(value)
                                else:
                                    params[param_name] = value
                                args.pop(i + 1)
                            else:
                                raise UsageError(f"Option {args[i]} requires a value")
                        args.pop(i)
                        found = True
                        if not opt.get('multiple', False):
                            break
                    else:
                        i += 1
                
                # Set multiple values if any
                if multiple_values:
                    params[param_name] = multiple_values
                
                # Handle required options
                if not found and opt.get('required', False):
                    raise UsageError(f"Option {opt['param_decls'][0]} is required")
                
                # Set default value if not found
                if not found and 'default' in opt:
                    params[param_name] = opt['default']
        
        # Handle arguments
        if hasattr(func, '_arguments'):
            for i, arg in enumerate(func._arguments):
                if i < len(args):
                    value = args[i]
                    # Convert value to the correct type
                    if 'type' in arg:
                        try:
                            value = arg['type'](value)
                        except ValueError:
                            raise UsageError(f"Invalid value for {arg['name']}: {value}")
                    params[arg['name']] = value
                elif arg.get('required', True):
                    raise UsageError(f"Argument {arg['name']} is required")
                elif 'default' in arg:
                    params[arg['name']] = arg['default']
        
        # Handle environment variables
        if hasattr(func, '_envvars'):
            for env in func._envvars:
                value = os.environ.get(env['name'])
                if env.get('required', False) and not value:
                    raise UsageError(f"Environment variable {env['name']} is required")
                if value:
                    # Convert value to the correct type
                    if 'type' in env:
                        try:
                            value = env['type'](value)
                        except ValueError:
                            raise UsageError(f"Invalid value for {env['name']}: {value}")
                    params[env['name'].lower()] = value
        
        return params
    
    def _print_help(self):
        """Print group help message"""
        console.print(f"\n{self.name} commands:")
        if self.help:
            console.print(f"\n{self.help}")
        
        for name, cmd in self.commands.items():
            if not cmd.get('hidden', False):
                console.print(f"  {name:20} {cmd['help'] or ''}")
        
        console.print("\nUse -h or --help with any command for more info")

class CLI:
    """
    The main CLI application class that handles all command registration and execution.

    Basic Usage:
        >>> from swiftcli import CLI
        >>> app = CLI("myapp")
        >>> @app.command()
        ... def greet(name: str):
        ...     print(f"Hello {name}!")
        >>> app.run()

    Advanced Usage:
        >>> app = CLI("myapp", version="1.0.0")
        >>> @app.group()
        ... def config():
        ...     '''Manage configuration'''
        ...     pass
        >>> @config.command()
        ... def set(key: str, value: str):
        ...     '''Set config value'''
        ...     print(f"Setting {key}={value}")
    """
    def __init__(
        self,
        name: str = None,
        help: str = None,
        version: str = None,
        chain: bool = False
    ):
        self.name = name
        self.help = help
        self.version = version
        self.chain = chain
        self.commands = {}
        self.groups = {}
        self.plugin_manager = PluginManager()
    
    def command(
        self,
        name: str = None,
        help: str = None,
        aliases: List[str] = None,
        hidden: bool = False
    ):
        """
        Decorator to register a new command.

        Basic Usage:
            >>> @app.command()
            ... def hello(name: str):
            ...     '''Say hello'''
            ...     print(f"Hello {name}!")

        Advanced Usage:
            >>> @app.command(name="greet", aliases=["hi", "hey"])
            ... def hello(name: str):
            ...     '''Greet someone'''
            ...     print(f"Hello {name}!")
        """
        def decorator(f):
            cmd_name = name or f.__name__
            self.commands[cmd_name] = {
                'func': f,
                'help': help or f.__doc__,
                'aliases': aliases or [],
                'hidden': hidden
            }
            return f
        return decorator
    
    def group(
        self,
        name: str = None,
        help: str = None,
        chain: bool = False,
        **kwargs
    ):
        """Create a command group"""
        def decorator(f):
            if hasattr(f, '_group'):
                group_info = f._group
                group = Group(
                    name=group_info['name'],
                    help=group_info['help'],
                    chain=group_info['chain'],
                    invoke_without_command=group_info['invoke_without_command']
                )
            else:
                group = Group(
                    name=name or f.__name__,
                    help=help or f.__doc__,
                    chain=chain
                )
            self.groups[group.name] = group
            return group
        return decorator
    
    def run(self, args: List[str] = None):
        """Run the CLI application"""
        args = args or sys.argv[1:]
        
        if not args or args[0] in ['-h', '--help']:
            self._print_help()
            return
        
        if args[0] in ['-v', '--version'] and self.version:
            console.print(self.version)
            return
        
        command_name = args[0]
        command_args = args[1:]
        
        # Check if it's a group command
        if command_name in self.groups:
            group = self.groups[command_name]
            if len(command_args) == 0:
                if not group.invoke_without_command:
                    group._print_help()
                    return
            else:
                return group.run(command_args)
        
        # Regular command
        if command_name not in self.commands:
            console.print(f"[red]Unknown command: {command_name}[/red]")
            self._print_help()
            return 1
        
        command = self.commands[command_name]
        try:
            ctx = Context(self, command=command_name)
            result = command['func'](**self._parse_args(command, command_args))
            
            if self.chain and result is not None:
                return result
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            return 1
    
    def _parse_args(self, command: Dict, args: List[str]) -> Dict[str, Any]:
        """Parse command arguments"""
        params = {}
        func = command['func']
        sig = inspect.signature(func)
        
        # Handle options
        if hasattr(func, '_options'):
            for opt in func._options:
                # Get the destination parameter name from the longest option
                param_decls = sorted(opt['param_decls'], key=len, reverse=True)
                param_name = param_decls[0].lstrip('-').replace('-', '_')
                
                # If there's a parameter name in the signature, use that instead
                for param in sig.parameters.values():
                    if param.name in [d.lstrip('-').replace('-', '_') for d in param_decls]:
                        param_name = param.name
                        break
                
                found = False
                multiple_values = []
                
                # Check for long and short options
                i = 0
                while i < len(args):
                    if args[i] in opt['param_decls']:
                        if opt.get('is_flag', False):
                            if opt.get('multiple', False):
                                multiple_values.append(True)
                            else:
                                params[param_name] = True
                        else:
                            if i + 1 < len(args):
                                value = args[i + 1]
                                # Convert value to the correct type
                                if 'type' in opt:
                                    try:
                                        value = opt['type'](value)
                                    except ValueError:
                                        raise UsageError(f"Invalid value for {args[i]}: {value}")
                                
                                if opt.get('multiple', False):
                                    multiple_values.append(value)
                                else:
                                    params[param_name] = value
                                args.pop(i + 1)
                            else:
                                raise UsageError(f"Option {args[i]} requires a value")
                        args.pop(i)
                        found = True
                        if not opt.get('multiple', False):
                            break
                    else:
                        i += 1
                
                # Set multiple values if any
                if multiple_values:
                    params[param_name] = multiple_values
                
                # Handle required options
                if not found and opt.get('required', False):
                    raise UsageError(f"Option {opt['param_decls'][0]} is required")
                
                # Set default value if not found
                if not found and 'default' in opt:
                    params[param_name] = opt['default']
        
        # Handle arguments
        if hasattr(func, '_arguments'):
            for i, arg in enumerate(func._arguments):
                if i < len(args):
                    value = args[i]
                    # Convert value to the correct type
                    if 'type' in arg:
                        try:
                            value = arg['type'](value)
                        except ValueError:
                            raise UsageError(f"Invalid value for {arg['name']}: {value}")
                    params[arg['name']] = value
                elif arg.get('required', True):
                    raise UsageError(f"Argument {arg['name']} is required")
                elif 'default' in arg:
                    params[arg['name']] = arg['default']
        
        # Handle environment variables
        if hasattr(func, '_envvars'):
            for env in func._envvars:
                value = os.environ.get(env['name'])
                if env.get('required', False) and not value:
                    raise UsageError(f"Environment variable {env['name']} is required")
                if value:
                    # Convert value to the correct type
                    if 'type' in env:
                        try:
                            value = env['type'](value)
                        except ValueError:
                            raise UsageError(f"Invalid value for {env['name']}: {value}")
                    params[env['name'].lower()] = value
        
        return params
    
    def _print_help(self):
        """Print main help message"""
        console.print(f"\n{self.name or 'CLI Application'}")
        if self.help:
            console.print(f"\n{self.help}")
        
        console.print("\nCommands:")
        for name, cmd in self.commands.items():
            if not cmd.get('hidden', False):
                console.print(f"  {name:20} {cmd['help'] or ''}")
        
        for name, group in self.groups.items():
            console.print(f"\n{name} commands:")
            for cmd_name, cmd in group.commands.items():
                if not cmd.get('hidden', False):
                    console.print(f"  {name} {cmd_name:20} {cmd['help'] or ''}")
        
        console.print("\nUse -h or --help with any command for more info")

def command(
    name: str = None,
    help: str = None,
    aliases: List[str] = None,
    hidden: bool = False
):
    """
    Decorator to register a new command.

    Basic Usage:
        >>> @app.command()
        ... def hello(name: str):
        ...     '''Say hello'''
        ...     print(f"Hello {name}!")

    Advanced Usage:
        >>> @app.command(name="greet", aliases=["hi", "hey"])
        ... def hello(name: str):
        ...     '''Greet someone'''
        ...     print(f"Hello {name}!")
    """
    def decorator(f: Callable) -> Callable:
        f._command = {
            'name': name or f.__name__,
            'help': help or f.__doc__,
            'aliases': aliases or [],
            'hidden': hidden
        }
        return f
    return decorator

def option(*param_decls, **attrs):
    """
    Decorator to add an option to a command.

    Basic Usage:
        >>> @app.command()
        ... @option("--count", type=int, default=1)
        ... def repeat(count: int, message: str):
        ...     '''Repeat a message'''
        ...     for _ in range(count):
        ...         print(message)

    Advanced Usage:
        >>> @app.command()
        ... @option("--format", "-f", type=click.Choice(["json", "yaml"]))
        ... def export(format: str):
        ...     '''Export data'''
        ...     print(f"Exporting as {format}")
    """
    def decorator(f: Callable) -> Callable:
        if not hasattr(f, '_options'):
            f._options = []
        
        # Set default values
        attrs.setdefault('type', str)
        attrs.setdefault('required', False)
        attrs.setdefault('default', None)
        attrs.setdefault('help', None)
        attrs.setdefault('is_flag', False)
        attrs.setdefault('multiple', False)
        attrs.setdefault('count', False)
        attrs.setdefault('prompt', False)
        attrs.setdefault('hide_input', False)
        attrs.setdefault('confirmation_prompt', False)
        attrs.setdefault('choices', None)
        attrs.setdefault('callback', None)
        attrs.setdefault('show_default', True)
        attrs.setdefault('hidden', False)
        
        f._options.append({
            'param_decls': param_decls,
            **attrs
        })
        return f
    return decorator

def argument(name: str, **attrs):
    """Argument decorator"""
    def decorator(f: Callable) -> Callable:
        if not hasattr(f, '_arguments'):
            f._arguments = []
        f._arguments.append({
            'name': name,
            **attrs
        })
        return f
    return decorator

def group(
    name: str = None,
    help: str = None,
    chain: bool = False,
    invoke_without_command: bool = False
):
    """Group decorator"""
    def decorator(f: Callable) -> Callable:
        f._group = {
            'name': name or f.__name__,
            'help': help or f.__doc__,
            'chain': chain,
            'invoke_without_command': invoke_without_command
        }
        return f
    return decorator

def pass_context(f: Callable) -> Callable:
    """Pass context decorator"""
    f._pass_context = True
    return f

def envvar(name: str, help: str = None, required: bool = False):
    """Environment variable decorator"""
    def decorator(f: Callable) -> Callable:
        if not hasattr(f, '_envvars'):
            f._envvars = []
        f._envvars.append({
            'name': name,
            'help': help,
            'required': required
        })
        return f
    return decorator

def config_file(path: str = None, auto_create: bool = True):
    """Configuration file decorator"""
    def decorator(f: Callable) -> Callable:
        f._config = {
            'path': path,
            'auto_create': auto_create
        }
        return f
    return decorator

def table_output(headers: List[str], style: str = None):
    """Table output decorator"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if result:
                table = Table(show_header=True, header_style="bold blue")
                for header in headers:
                    table.add_column(header)
                for row in result:
                    table.add_row(*[str(cell) for cell in row])
                console.print(table)
            return result
        return wrapper
    return decorator

def progress(description: str = None):
    """Progress decorator"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task(description or f.__name__, total=None)
                result = f(*args, **kwargs)
                progress.update(task, completed=True)
                return result
        return wrapper
    return decorator
