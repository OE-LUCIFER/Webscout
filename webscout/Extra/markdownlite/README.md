# Markdownlite 🚀

A powerful HTML to Markdown conversion library integrated with Scout.

## Installation

```bash
pip install webscout
```

## Basic Usage

```python
from webscout import markdownify

# Simple conversion
html_content = '<h1>Hello</h1><p>World</p>'
markdown = markdownify(html_content)
print(markdown)
```

## Advanced Features

### Structured Output
```python
# Get markdown with metadata and semantic information
result = markdownify(
    html_content, 
    STRUCTURED_OUTPUT=True
)

print(result['markdown'])      # The markdown content
print(result['metadata'])      # Document metadata
print(result['structure'])     # Page structure analysis
print(result['semantic_info']) # Semantic information
```

### Heading Styles
```python
# Customize heading style (ATX is default)
markdown = markdownify(
    html_content, 
    heading_style='ATX'  # Outputs: # Heading
)
```

## Configuration Options

- `STRUCTURED_OUTPUT`: Return detailed conversion results including:
  - `markdown`: Converted markdown text
  - `metadata`: Document metadata (title, meta tags)
  - `structure`: Page structure analysis
  - `semantic_info`: Semantic information
- `heading_style`: Markdown heading style (default: 'ATX')

## Supported HTML Elements

- Headers (h1-h6)
- Paragraphs
- Lists (ordered and unordered)
- Links
- Emphasis (bold, italic)
- And more...

## Example Output

Input HTML:
```html
<h1>Welcome</h1>
<p>This is a <strong>bold</strong> and <em>italic</em> text.</p>
<ul>
    <li>First item</li>
    <li>Second item</li>
</ul>
```

Output Markdown:
```markdown
# Welcome

This is a **bold** and *italic* text.

* First item
* Second item
```
