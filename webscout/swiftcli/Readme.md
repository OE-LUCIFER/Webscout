# ⚡ SwiftCLI - Build CLI Apps at Light Speed! 

Yo fam! Meet SwiftCLI - the most lit CLI framework that lets you build beautiful command-line apps with zero stress! 🔥 

## 🚀 Quick Start

```python
from webscout import CLI

# Create your app
app = CLI(name="my-app", help="My awesome CLI app")

# Add a command
@app.command()
def greet(name: str):
    """Say hello to someone"""
    print(f"Hello {name}!")

# Run it!
app.run()
```

## 💫 Features That Hit Different

### 🎯 Command Groups

```python
@app.group()
def db():
    """Database management commands"""
    pass

@db.command()
def migrate():
    """Run database migrations"""
    print("Running migrations... 🚀")

@db.command()
def backup():
    """Backup the database"""
    print("Creating backup... 💾")
```

### 🎨 Beautiful Tables

```python
@app.command()
@table_output(headers=["ID", "Name", "Status"])
def users():
    """List all users"""
    return [
        [1, "John", "Active"],
        [2, "Jane", "Inactive"]
    ]
```

### ⚡ Progress Bars

```python
@app.command()
@progress("Processing files")
def process(files: list):
    """Process multiple files"""
    for file in files:
        # Your processing logic here
        yield f"Processing {file}..."
```

### 🔧 Command Options

```python
@app.command()
@option("--count", "-c", type=int, default=1)
@option("--format", "-f", type=str, choices=["json", "yaml"])
def export(count: int, format: str):
    """Export data with options"""
    print(f"Exporting {count} items as {format}")
```

### 🌍 Environment Variables

```python
@app.command()
@envvar("API_KEY", required=True)
def api_call(api_key: str):
    """Make API call using env var"""
    print(f"Using API key: {api_key}")
```

### ⚙️ Config Files

```python
@app.command()
@config_file("~/.myapp/config.json")
def setup(config: dict):
    """Setup using config file"""
    print(f"Using config: {config}")
```

## 🌟 Advanced Features

### 🔗 Command Chaining

```python
@app.group(chain=True)
def process():
    """Process data pipeline"""
    pass

@process.command()
def validate():
    """Validate input"""
    print("Validating... ✅")

@process.command()
def transform():
    """Transform data"""
    print("Transforming... 🔄")

# Run them in sequence:
# $ myapp process validate transform
```

### 🎮 Context Passing

```python
@app.command()
@pass_context
def status(ctx):
    """Get app status with context"""
    print(f"App: {ctx.cli.name}")
    print(f"Version: {ctx.cli.version}")
```

### 🔌 Plugin System

```python
class MyPlugin(Plugin):
    def before_command(self, command, args):
        print(f"About to run: {command}")

    def after_command(self, command, args, result):
        print(f"Finished running: {command}")

# Register your plugin
app.plugin_manager.register(MyPlugin())
```

## 🎯 Real-World Examples

### 🚀 Deployment CLI

```python
@app.group()
def deploy():
    """Deployment commands"""
    pass

@deploy.command()
@option("--env", type=str, default="dev")
@progress("Deploying")
def start(env: str):
    """Start deployment"""
    yield "Building application..."
    yield "Running tests..."
    yield f"Deploying to {env}..."
```

### 📊 Data Processing

```python
@app.command()
@option("--input", "-i", type=str, required=True)
@option("--output", "-o", type=str, required=True)
@table_output(headers=["File", "Status", "Time"])
def process(input: str, output: str):
    """Process data files"""
    # Your processing logic here
    return [
        ["data1.csv", "Success", "2s"],
        ["data2.csv", "Success", "3s"]
    ]
```

## 🎮 Pro Tips

1. **Auto Help Text**: Use docstrings for automatic help messages
   ```python
   @app.command()
   def awesome():
       """
       Does something awesome
       
       Options:
           --format: Output format (json/yaml)
       """
       pass
   ```

2. **Rich Output**: Use rich console for fancy output
   ```python
   from rich.console import Console
   console = Console()
   
   @app.command()
   def fancy():
       """Print fancy output"""
       console.print("[bold red]Error![/] Something went wrong!")
   ```

3. **Dynamic Completion**: Add shell completion
   ```python
   @app.command()
   def complete():
       """Command with completion"""
       pass
   
   @complete.completion()
   def complete_options(ctx, incomplete):
       return ["option1", "option2"]
   ```

## 🔥 Why SwiftCLI?

- ⚡ Lightning fast development
- 🎨 Beautiful output out of the box
- 🧠 Smart command organization
- 🔌 Extensible plugin system
- 💪 Type hints and validation
- 🚀 Modern Python practices

Made with 💖 by the HelpingAI team
