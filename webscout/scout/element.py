"""
Scout Element Module - Advanced HTML Element Representation
"""

import re
from typing import Optional, List, Dict, Union, Any, Callable, Iterable

class NavigableString(str):
    """
    A string that knows its place in the document tree.
    Mimics BeautifulSoup's NavigableString for better compatibility.
    """
    def __new__(cls, text: str):
        """
        Create a new NavigableString instance.
        
        Args:
            text (str): String content
        """
        return str.__new__(cls, text)
    
    def __init__(self, text: str):
        """
        Initialize a navigable string.
        
        Args:
            text (str): String content
        """
        self.parent = None
    
    def __repr__(self):
        """String representation."""
        return f"NavigableString({super().__repr__()})"
    
    def __add__(self, other):
        """
        Allow concatenation of NavigableString with other strings.
        
        Args:
            other (str): String to concatenate
        
        Returns:
            str: Concatenated string
        """
        return str(self) + str(other)
    
    def strip(self, chars=None):
        """
        Strip whitespace or specified characters.
        
        Args:
            chars (str, optional): Characters to strip
        
        Returns:
            str: Stripped string
        """
        return NavigableString(super().strip(chars))

class Tag:
    """
    Represents an HTML tag with advanced traversal and manipulation capabilities.
    Enhanced to closely mimic BeautifulSoup's Tag class.
    """
    def __init__(self, name: str, attrs: Dict[str, str] = None):
        """
        Initialize a Tag with name and attributes.
        
        Args:
            name (str): Tag name
            attrs (dict, optional): Tag attributes
        """
        self.name = name
        self.attrs = attrs or {}
        self.contents = []
        self.parent = None
        self.string = None  # For single string content
    
    def __str__(self):
        """String representation of the tag."""
        return self.decode_contents()
    
    def __repr__(self):
        """Detailed representation of the tag."""
        return f"<{self.name} {self.attrs}>"
    
    def __call__(self, *args, **kwargs):
        """
        Allows calling find_all directly on the tag.
        Mimics BeautifulSoup's behavior.
        """
        return self.find_all(*args, **kwargs)
    
    def __contains__(self, item):
        """
        Check if an item is in the tag's contents.
        
        Args:
            item: Item to search for
        
        Returns:
            bool: True if item is in contents, False otherwise
        """
        return item in self.contents
    
    def __getitem__(self, key):
        """
        Get an attribute value using dictionary-like access.
        
        Args:
            key (str): Attribute name
        
        Returns:
            Any: Attribute value
        """
        return self.attrs[key]
    
    def __iter__(self):
        """
        Iterate through tag's contents.
        
        Returns:
            Iterator: Contents of the tag
        """
        return iter(self.contents)
    
    def __eq__(self, other):
        """
        Compare tags based on name and attributes.
        
        Args:
            other (Tag): Tag to compare
        
        Returns:
            bool: True if tags are equivalent
        """
        if not isinstance(other, Tag):
            return False
        return (
            self.name == other.name and 
            self.attrs == other.attrs and 
            str(self) == str(other)
        )
    
    def __hash__(self):
        """
        Generate a hash for the tag.
        
        Returns:
            int: Hash value
        """
        return hash((self.name, frozenset(self.attrs.items()), str(self)))
    
    def find(self, name=None, attrs={}, recursive=True, text=None, **kwargs) -> Optional['Tag']:
        """
        Find the first matching child element.
        Enhanced with more flexible matching.
        
        Args:
            name (str, optional): Tag name to search for
            attrs (dict, optional): Attributes to match
            recursive (bool, optional): Search recursively
            text (str, optional): Text content to match
        
        Returns:
            Tag or None: First matching element
        """
        results = self.find_all(name, attrs, recursive, text, limit=1, **kwargs)
        return results[0] if results else None
    
    def find_all(self, name=None, attrs={}, recursive=True, text=None, limit=None, **kwargs) -> List['Tag']:
        """
        Find all matching child elements.
        Enhanced with more flexible matching and BeautifulSoup-like features.
        
        Args:
            name (str, optional): Tag name to search for
            attrs (dict, optional): Attributes to match
            recursive (bool, optional): Search recursively
            text (str, optional): Text content to match
            limit (int, optional): Maximum number of results
        
        Returns:
            List[Tag]: List of matching elements
        """
        results = []
        
        def _match(tag):
            # Check tag name with case-insensitive and regex support
            if name:
                if isinstance(name, str):
                    if tag.name.lower() != name.lower():
                        return False
                elif isinstance(name, re.Pattern):
                    if not name.search(tag.name):
                        return False
            
            # Check attributes with more flexible matching
            for k, v in attrs.items():
                # Handle special attribute matching
                if k == 'class':
                    tag_classes = tag.get('class', [])
                    if isinstance(v, str) and v not in tag_classes:
                        return False
                    elif isinstance(v, list) and not all(cls in tag_classes for cls in v):
                        return False
                elif k == 'id':
                    if tag.get('id') != v:
                        return False
                else:
                    # Regex or exact match for other attributes
                    tag_attr = tag.attrs.get(k)
                    if isinstance(v, re.Pattern):
                        if not v.search(str(tag_attr)):
                            return False
                    elif tag_attr != v:
                        return False
            
            # Check text content
            if text:
                tag_text = tag.get_text(strip=True)
                if isinstance(text, str) and text.lower() not in tag_text.lower():
                    return False
                elif isinstance(text, re.Pattern) and not text.search(tag_text):
                    return False
            
            return True
        
        def _search(element):
            if _match(element):
                results.append(element)
                if limit and len(results) == limit:
                    return
            
            if recursive:
                for child in element.contents:
                    if isinstance(child, Tag):
                        _search(child)
        
        _search(self)
        return results
    
    def select(self, selector: str) -> List['Tag']:
        """
        Select elements using CSS selector.
        Enhanced to support more complex selectors.
        
        Args:
            selector (str): CSS selector string
        
        Returns:
            List[Tag]: List of matching elements
        """
        # More advanced CSS selector parsing
        # This is a simplified implementation and might need more robust parsing
        parts = re.split(r'\s+', selector.strip())
        results = []
        
        def _match_selector(tag, selector_part):
            # Support more complex selectors
            if selector_part.startswith('.'):
                # Class selector
                return selector_part[1:] in tag.get('class', [])
            elif selector_part.startswith('#'):
                # ID selector
                return tag.get('id') == selector_part[1:]
            elif '[' in selector_part and ']' in selector_part:
                # Attribute selector
                attr_match = re.match(r'(\w+)\[([^=]+)(?:=(.+))?\]', selector_part)
                if attr_match:
                    tag_name, attr, value = attr_match.groups()
                    if tag_name and tag.name != tag_name:
                        return False
                    if value:
                        return tag.get(attr) == value.strip("'\"")
                    return attr in tag.attrs
            else:
                # Tag selector
                return tag.name == selector_part
        
        def _recursive_select(element, selector_parts):
            if not selector_parts:
                results.append(element)
                return
            
            current_selector = selector_parts[0]
            remaining_selectors = selector_parts[1:]
            
            if _match_selector(element, current_selector):
                if not remaining_selectors:
                    results.append(element)
                else:
                    for child in element.contents:
                        if isinstance(child, Tag):
                            _recursive_select(child, remaining_selectors)
        
        for child in self.contents:
            if isinstance(child, Tag):
                _recursive_select(child, parts)
        
        return results
    
    def select_one(self, selector: str) -> Optional['Tag']:
        """
        Select the first element matching the CSS selector.
        
        Args:
            selector (str): CSS selector string
        
        Returns:
            Tag or None: First matching element
        """
        results = self.select(selector)
        return results[0] if results else None
    
    def get_text(self, separator=' ', strip=False, types=None) -> str:
        """
        Extract text from the tag and its descendants.
        Enhanced to support more flexible text extraction.
        
        Args:
            separator (str, optional): Text separator
            strip (bool, optional): Strip whitespace
            types (list, optional): Types of content to extract
        
        Returns:
            str: Extracted text
        """
        texts = []
        for content in self.contents:
            # Support filtering by content type
            if types is None or type(content) in types:
                if isinstance(content, NavigableString):
                    texts.append(str(content))
                elif isinstance(content, Tag):
                    texts.append(content.get_text(separator, strip))
        
        text = separator.join(texts)
        text = re.sub(r'\n\n+', '\n', text) # Replace multiple newlines with single newlines
        return text.strip() if strip else text
    
    def find_text(self, pattern: Union[str, re.Pattern], **kwargs) -> Optional[str]:
        """
        Find the first text matching a pattern.
        
        Args:
            pattern (str or re.Pattern): Pattern to match
            **kwargs: Additional arguments for get_text()
        
        Returns:
            str or None: First matching text
        """
        text = self.get_text(**kwargs)
        
        if isinstance(pattern, str):
            return pattern if pattern in text else None
        elif isinstance(pattern, re.Pattern):
            match = pattern.search(text)
            return match.group(0) if match else None
    
    def replace_text(self, old: Union[str, re.Pattern], new: str, **kwargs) -> str:
        """
        Replace text matching a pattern.
        
        Args:
            old (str or re.Pattern): Pattern to replace
            new (str): Replacement text
            **kwargs: Additional arguments for get_text()
        
        Returns:
            str: Modified text
        """
        text = self.get_text(**kwargs)
        
        if isinstance(old, str):
            return text.replace(old, new)
        elif isinstance(old, re.Pattern):
            return old.sub(new, text)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get an attribute value.
        
        Args:
            key (str): Attribute name
            default (Any, optional): Default value if attribute not found
        
        Returns:
            Any: Attribute value or default
        """
        return self.attrs.get(key, default)
    
    def decompose(self) -> None:
        """Remove the tag and its contents from the document."""
        if self.parent:
            self.parent.contents.remove(self)
    
    def extract(self) -> 'Tag':
        """
        Remove the tag from the document and return it.
        
        Returns:
            Tag: Extracted tag
        """
        self.decompose()
        return self
    
    def clear(self) -> None:
        """Remove all contents of the tag."""
        self.contents.clear()
    
    def replace_with(self, new_tag: 'Tag') -> None:
        """
        Replace this tag with another tag.
        
        Args:
            new_tag (Tag): Tag to replace the current tag
        """
        if self.parent:
            index = self.parent.contents.index(self)
            self.parent.contents[index] = new_tag
            new_tag.parent = self.parent
    
    def decode_contents(self, eventual_encoding='utf-8') -> str:
        """
        Decode the contents of the tag to a string.
        
        Args:
            eventual_encoding (str, optional): Encoding to use
        
        Returns:
            str: Decoded contents
        """
        return ''.join(str(content) for content in self.contents)
    
    def prettify(self, formatter='minimal') -> str:
        """
        Return a nicely formatted representation of the tag.
        
        Args:
            formatter (str, optional): Formatting style
        
        Returns:
            str: Prettified tag representation
        """
        def _prettify(tag, indent=0):
            result = ' ' * indent + f'<{tag.name}'
            for k, v in tag.attrs.items():
                result += f' {k}="{v}"'
            result += '>\n'
            
            for content in tag.contents:
                if isinstance(content, Tag):
                    result += _prettify(content, indent + 2)
                else:
                    result += ' ' * (indent + 2) + str(content) + '\n'
            
            result += ' ' * indent + f'</{tag.name}>\n'
            return result
        
        return _prettify(self)