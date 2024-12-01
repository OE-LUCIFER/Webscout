# 📝 LitLogger - The Most Fire Logger You'll Ever Use! 

Yo fam! Meet LitLogger - your new logging bestie that's built different! 🔥 With smart level detection, fire color schemes, and emoji support, your logs never looked this good!

## 🚀 Quick Start

```python
from webscout import LitLogger, LogFormat, ColorScheme

# Create your logger with style
logger = LitLogger(
    name="MyApp",
    format=LogFormat.MODERN_EMOJI,
    color_scheme=ColorScheme.CYBERPUNK
)

# Start logging with swag
logger.info("App started! 🚀")
logger.success("Mission accomplished! 💯")
logger.warning("CPU getting spicy! 🌶️")
logger.error("Houston, we got a problem! 🔧")
```

## 💫 Features That Hit Different

### 🎨 Fire Color Schemes

```python
# Cyberpunk vibes
logger = LitLogger(color_scheme=ColorScheme.CYBERPUNK)

# Ocean feels
logger = LitLogger(color_scheme=ColorScheme.OCEAN)

# Matrix mode
logger = LitLogger(color_scheme=ColorScheme.MATRIX)

# Aurora lights
logger = LitLogger(color_scheme=ColorScheme.AURORA)

# Sunset mood
logger = LitLogger(color_scheme=ColorScheme.SUNSET)
```

### 📝 Lit Log Formats

```python
# Modern with emojis
logger = LitLogger(format=LogFormat.MODERN_EMOJI)
# Output: 🚀 [2024-01-20 15:30:45] INFO Server started!

# Clean and minimal
logger = LitLogger(format=LogFormat.MODERN_CLEAN)
# Output: 2024-01-20 15:30:45 INFO Server started

# Boxed style
logger = LitLogger(format=LogFormat.BOXED)
# Output: ╭─────────────────────╮
#        │ [2024-01-20 15:30:45]
#        │ INFO - MyApp
#        │ Server started!
#        ╰─────────────────────╯

# Japanese style
logger = LitLogger(format=LogFormat.MODERN_BRACKET)
# Output: 【2024-01-20 15:30:45】「INFO」Server started
```

### 🧠 Smart Level Detection

```python
# Auto-detects appropriate log level
logger.auto("Starting server...")  # INFO
logger.auto("CPU usage at 95%")   # WARNING
logger.auto("404: Not Found")     # ERROR
logger.auto("x = calculate(y)")   # DEBUG

# With context
logger.auto("Memory usage: 90%", memory=90)  # WARNING
logger.auto("Response time: 1500ms", latency=1500)  # WARNING
```

### 🎯 Log Levels

```python
# All the levels you need
logger.trace("Entering function...")
logger.debug("x = 42")
logger.info("Server started")
logger.success("Task completed")
logger.warning("Running low on memory")
logger.error("Failed to connect")
logger.critical("System crash!")
```

## 🌟 Real-World Examples

### API Server Logging

```python
logger = LitLogger(name="APIServer", format=LogFormat.MODERN_EMOJI)

def handle_request():
    logger.info("Received new request 📥")
    try:
        # Process request
        logger.success("Request processed successfully ✨")
    except Exception as e:
        logger.error(f"Request failed: {e} 💀")
```

### Performance Monitoring

```python
logger = LitLogger(name="Monitor", color_scheme=ColorScheme.MATRIX)

def monitor_system():
    metrics = get_system_metrics()
    logger.auto(
        f"CPU: {metrics['cpu']}%, Memory: {metrics['memory']}%",
        cpu=metrics['cpu'],
        memory=metrics['memory']
    )
```

### Development Debugging

```python
logger = LitLogger(name="Debug", format=LogFormat.DETAILED)

def complex_calculation(x, y):
    logger.debug(f"Input: x={x}, y={y}")
    result = x * y
    logger.debug(f"Result: {result}")
    return result
```

## 🎮 Pro Tips

1. **Custom Color Schemes**: Create your own vibe
   ```python
   my_scheme = {
       "trace": (128, 128, 255),  # Your colors
       "debug": (255, 0, 255),
       "info": (0, 255, 255)
   }
   logger = LitLogger(color_scheme=my_scheme)
   ```

2. **Log to File**: Keep records with style
   ```python
   logger = LitLogger(
       name="MyApp",
       log_path="logs/app.log",
       console_output=True  # Both file and console
   )
   ```

3. **Smart Context**: Let the logger decide
   ```python
   # Automatically chooses log level based on content
   logger.auto("Database connection failed")  # ERROR
   logger.auto("Cache hit ratio: 95%")       # INFO
   ```

## 🔥 Why LitLogger?

- 🎨 Beautiful, colorful output
- 🧠 Smart level detection
- 📱 Multiple output formats
- 🌈 Customizable color schemes
- 💪 Easy to use, hard to mess up
- ⚡ Fast and lightweight

Made with 💖 by the HelpingAI team
