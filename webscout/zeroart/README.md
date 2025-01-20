# 🎨 ZeroArt: Zero-Dependency ASCII Art Generator

## 🚀 Overview

ZeroArt is a powerful, lightweight Python library for generating stunning ASCII art text with zero external dependencies. Transform your plain text into eye-catching, stylized art with just a few lines of code!

## ✨ Features

- **Multiple Font Styles**
  - Block Font
  - Slant Font
  - Neon Font
  - Cyber Font

- **Zero Dependencies**
  - Completely standalone library
  - No external package requirements

- **Easy to Use**
  - Simple, intuitive API
  - Minimal setup needed

- **Text Effects**
  - Rainbow coloring
  - Glitch effect
  - Text wrapping
  - Outline generation

## 🛠 Installation

No installation required! Just copy the `zeroart` directory into your project.

## 💻 Usage Examples

### Basic ASCII Art

```python
from webscout import zeroart

# Generate ASCII art
art = zeroart.figlet_format("PYTHON", font='block')
print(art)

# Directly print ASCII art
zeroart.print_figlet("CODING", font='slant')
```

### Font Styles

```python
from webscout import zeroart

# Different font styles
print(zeroart.figlet_format("AWESOME", font='block'))   # Block style
print(zeroart.figlet_format("CODING", font='slant'))    # Slant style
print(zeroart.figlet_format("NEON", font='neon'))       # Neon style
print(zeroart.figlet_format("CYBER", font='cyber'))     # Cyber style
```

### Text Effects

```python
from webscout import zeroart

# Rainbow effect
print(zeroart.rainbow("COLORFUL", font='neon'))

# Glitch effect
print(zeroart.glitch("GLITCH", font='cyber'))

# Outline effect
print(zeroart.outline("BORDER", font='block'))
```

## 🎨 Available Fonts

1. **Block Font**: Classic, bold block-style letters
2. **Slant Font**: Elegant, slanted text
3. **Neon Font**: Glowing, pixel-style art
4. **Cyber Font**: Cyberpunk-inspired rendering

## 🤝 Contributing

Contributions are welcome! 

- Fork the repository
- Create a new font
- Add text effects
- Improve existing code
