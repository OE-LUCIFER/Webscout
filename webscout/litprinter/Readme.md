# 🖨️ LitPrinter - The Most Lit Console Printer Ever! 

Yo fam! Meet LitPrinter - your new bestie for making your console output look absolutely fire! 🔥 Built different with all the drip you need to make your terminal pop!

## 🚀 Quick Start

```python
from webscout import printer

# Basic printing with style
printer.print("Wassup World!", color="blue", bold=True)
printer.success("We got a W! 🏆")
printer.warning("Heads up fam! ⚠️")
printer.error("Oof, that ain't it chief! ❌")
```

## 💫 Features That Hit Different

### 🎨 Styled Text

```python
# Colors & styles
printer.print("Glow up!", color="cyan", bold=True)
printer.print("Subtle flex", italic=True, dim=True)
printer.print("Important stuff", bg_color="red", underline=True)
```

### 📦 Fancy Boxes

```python
# Box it up with style
printer.print("VIP Message", border=True, rounded_corners=True)
printer.print("ALERT!", border=True, border_color="red", double_border=True)
```

### 🎬 Animations

```python
# Make it move!
printer.print("Loading...", animate=True, animation_type="typing")
printer.print("Processing", animate=True, animation_speed=0.1)
```

### 📊 Data Visualization

```python
# Show data with drip
data = {
    "status": "vibing",
    "energy": "100%",
    "mood": "lit"
}

# Pretty JSON
printer.print(data, as_json=True)

# Tree view
printer.print(data, as_tree=True)

# Table format
headers = ["Metric", "Value"]
rows = [["Hype Level", "Maximum"]]
printer.print([headers, rows], as_table=True)
```

### 💻 Code Blocks

```python
code = '''
def stay_lit():
    return "Always keeping it 💯"
'''
printer.print(code, as_code=True, language="python")
```

### 📝 Markdown Support

```python
markdown = """
# Big Moves
- Level 1: Start the grind
- Level 2: Keep pushing
- Level 3: **Achieve greatness**
"""
printer.print(markdown, markdown=True)
```

## 🎯 Real Examples

### Progress Tracking

```python
from webscout import printer

def download_files():
    with printer.progress_bar(total=100) as progress:
        for i in range(100):
            # Do work here
            progress.update(i + 1)
            
def process_data():
    with printer.spinner("Processing your data... "):
        # Do work here
        pass
```

### Status Updates

```python
# Keep the squad updated
printer.status("Connecting to server...")
printer.success("We're in! 🎯")

# Show warnings with style
printer.warning("CPU getting spicy! 🌶️")

# Error handling with flair
try:
    raise Exception("Connection lost")
except Exception as e:
    printer.error(f"We hit a snag: {e} 😤")
```

### Data Reports

```python
# Print structured data
stats = {
    "users_online": 1000,
    "server_status": "vibing",
    "uptime": "99.9%"
}

printer.print("Server Stats 📊", style="bold")
printer.json(stats)  # Pretty JSON output

# Or as a table
headers = ["Metric", "Value"]
rows = [[k, v] for k, v in stats.items()]
printer.table(headers, rows)
```

## 🌟 Why LitPrinter?

- 🎨 Makes your console look absolutely fire
- 💪 Easy to use, hard to mess up
- 🚀 Packed with features but light on resources
- 🔥 Perfect for CLI apps that need that extra drip
- 💯 Built by devs who know what's good

## 🎮 Pro Tips

1. **Style Combos**: Mix and match styles for maximum impact
   ```python
   printer.print("IMPORTANT", color="red", bold=True, blink=True)
   ```

2. **Smart Layouts**: Use center and width for clean alignment
   ```python
   printer.print("Centered Text", center=True, width=50)
   ```

3. **Interactive Updates**: Keep your users in the loop
   ```python
   with printer.spinner("Working on it..."):
       # Your code here
       pass
   ```

Made with 💖 by the HelpingAI team
