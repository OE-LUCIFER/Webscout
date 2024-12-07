import sys
import os
from webscout.Litlogger import LitLogger, LogFormat, ColorScheme
from webscout.scout import Scout, Tag
from textwrap import fill
import re
import six
import html
import json
from typing import Union, Dict, Any, Optional, List
import functools

# Initialize Litlogger
logger = LitLogger(
    name="MarkdownLite", 
    format=LogFormat.DETAILED,
    color_scheme=ColorScheme.OCEAN
)

# Decorator for error handling and logging
def markdown_conversion_error_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Markdown conversion error: {e}", exc_info=True)
            raise
    return wrapper

# Constants and configuration
MARKDOWN_CONVERSION_OPTIONS = {
    'SEMANTIC_CONVERSION': True,
    'PRESERVE_METADATA': True,
    'SMART_LISTS': True,
    'LINK_REWRITING': None,
    'CUSTOM_ANALYZERS': [],
    'STRUCTURED_OUTPUT': True,
    'DEBUG_MODE': False
}

# Existing utility functions
def chomp(text):
    """
    Strip leading/trailing spaces while preserving prefix/suffix spaces.
    
    Args:
        text (str): Input text to process
    
    Returns:
        tuple: (prefix, suffix, stripped_text)
    """
    prefix = ' ' if text and text[0] == ' ' else ''
    suffix = ' ' if text and text[-1] == ' ' else ''
    text = text.strip()
    return (prefix, suffix, text)

def abstract_inline_conversion(markup_fn):
    """
    Abstract inline tag conversion with enhanced flexibility.
    
    Args:
        markup_fn (callable): Function to generate markup
    
    Returns:
        callable: Conversion implementation
    """
    def implementation(self, el, text, convert_as_inline):
        markup_prefix = markup_fn(self)
        if markup_prefix.startswith('<') and markup_prefix.endswith('>'):
            markup_suffix = '</' + markup_prefix[1:]
        else:
            markup_suffix = markup_prefix
        
        if el.find_parent(['pre', 'code', 'kbd', 'samp']):
            return text
        
        prefix, suffix, text = chomp(text)
        if not text:
            return ''
        
        return f'{prefix}{markup_prefix}{text}{markup_suffix}{suffix}'
    return implementation

class MarkdownConverter(object):
    class DefaultOptions:
        autolinks = True
        bullets = '*+-'  # An iterable of bullet types.
        code_language = ''
        code_language_callback = None
        convert = None
        default_title = False
        escape_asterisks = True
        escape_underscores = True
        escape_misc = False
        heading_style = 'underlined'
        keep_inline_images_in = []
        newline_style = 'spaces'
        strip = None
        strong_em_symbol = '*'
        sub_symbol = ''
        sup_symbol = ''
        wrap = False
        wrap_width = 80
        
        # New options for Scout integration
        semantic_conversion = False  # Enable semantic-aware conversion
        preserve_metadata = False  # Keep HTML metadata in markdown
        smart_lists = True  # Smart list handling
        link_rewriting = None  # Function for rewriting URLs
        custom_analyzers = []  # List of custom text analyzers
        structured_output = False  # Return structured output with metadata
        
        # Existing options
        debug_mode = False
        handle_unknown_tags = 'ignore'  # 'ignore', 'warn', 'error'
        preserve_html_comments = False
        max_depth = 100  # Prevent potential infinite recursion
        custom_tag_handlers = {}  # Allow custom tag conversion functions

    class Options(DefaultOptions):
        pass

    # Inline conversion methods
    convert_b = abstract_inline_conversion(lambda self: 2 * self.options['strong_em_symbol'])
    convert_del = abstract_inline_conversion(lambda self: '~~')
    convert_em = abstract_inline_conversion(lambda self: self.options['strong_em_symbol'])
    convert_i = convert_em
    convert_s = convert_del
    convert_strong = convert_b
    convert_sub = abstract_inline_conversion(lambda self: self.options['sub_symbol'])
    convert_sup = abstract_inline_conversion(lambda self: self.options['sup_symbol'])

    def __init__(self, **options):
        # Merge default and user-provided options
        default_options = {
            'SEMANTIC_CONVERSION': True,
            'PRESERVE_METADATA': True,
            'SMART_LISTS': True,
            'LINK_REWRITING': None,
            'CUSTOM_ANALYZERS': [],
            'STRUCTURED_OUTPUT': True,
            'DEBUG_MODE': False,
            # Add max_depth for conversion
            'max_depth': 10,
            # Inherit existing default options
            'strip': None,
            'convert': None,
            'heading_style': 'underlined',
            'newline_style': 'spaces',
            'strong_em_symbol': '*',
            'escape_asterisks': True,
            'escape_underscores': True,
            'escape_misc': False,
            'keep_inline_images_in': [],
            'sub_symbol': '',
            'sup_symbol': '',
            'wrap': False
        }
        
        # Update with user options
        default_options.update(options)
        self.options = default_options
        
        # Setup logging based on debug mode
        if self.options['DEBUG_MODE']:
            logger.setLevel(logging.DEBUG)
        
        # Initialize metadata and structure
        self._metadata = {}
        self._structure = {}
        self._semantic_info = {}

    @markdown_conversion_error_handler
    def convert(self, html):
        """
        Enhanced conversion with metadata and structure analysis.
        
        Args:
            html (str): HTML content to convert
        
        Returns:
            Union[str, Dict[str, Any]]: Markdown text or structured output
        """
        # Handle different Scout result types
        scout = html if hasattr(html, '_soup') or hasattr(html, 'name') else Scout(html, features='html.parser')
        
        # If scout is a search result, get the first result or the original scout
        if hasattr(scout, '_results') and scout._results:
            scout = scout._results[0]
        
        # Ensure we have a valid Scout object or Tag
        if not hasattr(scout, '_soup') and not hasattr(scout, 'name'):
            raise ValueError("Unable to convert input to a valid Scout object")
        
        logger.debug(f"Parsing HTML: {str(scout)[:100]}...")
        
        # Extract additional information if needed
        if self.options['PRESERVE_METADATA']:
            self._metadata = self._extract_metadata(scout)
            
        if self.options['SEMANTIC_CONVERSION']:
            self._structure = self._analyze_structure(scout)
            self._semantic_info = self._extract_semantic_info(scout)
        
        # Convert to markdown
        markdown = self.convert_soup(scout._soup if hasattr(scout, '_soup') else scout)
        
        # Return structured output if requested
        if self.options['STRUCTURED_OUTPUT']:
            return {
                'markdown': markdown,
                'metadata': self._metadata,
                'structure': self._structure,
                'semantic_info': self._semantic_info
            }
            
        return markdown

    def convert_soup(self, soup):
        """Convert Scout's internal soup object."""
        return self.process_tag(soup, convert_as_inline=False, children_only=True)

    def process_tag(self, node, convert_as_inline, children_only=False, depth=0):
        """Enhanced tag processing with semantic awareness."""
        if depth > self.options['max_depth']:
            logger.warning(f"Max recursion depth reached at tag: {node.name}")
            return ''

        # Check for custom tag handlers
        if hasattr(node, 'name') and node.name in self.options['custom_tag_handlers']:
            custom_handler = self.options['custom_tag_handlers'][node.name]
            return custom_handler(node, convert_as_inline)

        text = ''

        # markdown headings or cells can't include
        # block elements (elements w/newlines)
        isHeading = re.match(r'h[1-6]', node.name) if hasattr(node, 'name') else False
        isCell = hasattr(node, 'name') and node.name in ['td', 'th']
        convert_children_as_inline = convert_as_inline

        if not children_only and (isHeading or isCell):
            convert_children_as_inline = True

        # Remove whitespace-only textnodes
        should_remove_inside = should_remove_whitespace_inside(node)

        # Iterate through children
        for el in node.children:
            # Skip script, style, and comment-like elements
            if hasattr(el, 'name') and el.name in ['script', 'style', 'comment']:
                continue

            # Check if element is a text node that can be stripped
            if (isinstance(el, str) or 
                (hasattr(el, 'string') and el.string and str(el.string).strip() == '')):
                if should_remove_inside and (not el.previous_sibling or not el.next_sibling):
                    continue

            # Process child elements
            if isinstance(el, str):
                text += el
            elif hasattr(el, 'name'):
                text_strip = text.rstrip('\n')
                newlines_left = len(text) - len(text_strip)
                next_text = self.process_tag(el, convert_children_as_inline)
                next_text_strip = next_text.lstrip('\n')
                newlines_right = len(next_text) - len(next_text_strip)
                newlines = '\n' * max(newlines_left, newlines_right)
                text = text_strip + newlines + next_text_strip

        if not children_only and hasattr(node, 'name'):
            convert_fn = getattr(self, 'convert_%s' % node.name, None)
            if convert_fn and self.should_convert_tag(node.name):
                text = convert_fn(node, text, convert_as_inline)

        # Apply custom analyzers
        for analyzer in self.options['custom_analyzers']:
            text = analyzer(text, node)
            
        return text

    def _validate_options(self):
        """Validate and sanitize converter options."""
        if self.options['max_depth'] < 1:
            raise ValueError("max_depth must be a positive integer")
        
        if self.options['handle_unknown_tags'] not in ['ignore', 'warn', 'error']:
            raise ValueError("handle_unknown_tags must be 'ignore', 'warn', or 'error'")

    def process_text(self, el):
        text = six.text_type(el) or ''

        # normalize whitespace if we're not inside a preformatted element
        if not el.find_parent('pre'):
            if self.options['wrap']:
                text = re.sub(r'[\t ]+', ' ', text)
            else:
                text = re.sub(r'[\t \r\n]*[\r\n][\t \r\n]*', '\n', text)
                text = re.sub(r'[\t ]+', ' ', text)

        # escape special characters if we're not inside a preformatted or code element
        if not el.find_parent(['pre', 'code', 'kbd', 'samp']):
            text = self.escape(text)

        # remove leading whitespace at the start or just after a
        # block-level element; remove traliing whitespace at the end
        # or just before a block-level element.
        if (should_remove_whitespace_outside(el.previous_sibling)
                or (should_remove_whitespace_inside(el.parent)
                    and not el.previous_sibling)):
            text = text.lstrip()
        if (should_remove_whitespace_outside(el.next_sibling)
                or (should_remove_whitespace_inside(el.parent)
                    and not el.next_sibling)):
            text = text.rstrip()

        return text

    def __getattr__(self, attr):
        # Handle headings
        m = re.match(r'convert_h(\d+)', attr)
        if m:
            n = int(m.group(1))

            def convert_tag(el, text, convert_as_inline):
                return self._convert_hn(n, el, text, convert_as_inline)

            convert_tag.__name__ = 'convert_h%s' % n
            setattr(self, convert_tag.__name__, convert_tag)
            return convert_tag

        raise AttributeError(attr)

    def should_convert_tag(self, tag):
        tag = tag.lower()
        strip = self.options['strip']
        convert = self.options['convert']
        if strip is not None:
            return tag not in strip
        elif convert is not None:
            return tag in convert
        else:
            return True

    def escape(self, text):
        if not text:
            return ''
        if self.options['escape_misc']:
            text = re.sub(r'([\\&<`[>~=+|])', r'\\\1', text)
            # A sequence of one or more consecutive '-', preceded and
            # followed by whitespace or start/end of fragment, might
            # be confused with an underline of a header, or with a
            # list marker.
            text = re.sub(r'(\s|^)(-+(?:\s|$))', r'\1\\\2', text)
            # A sequence of up to six consecutive '#', preceded and
            # followed by whitespace or start/end of fragment, might
            # be confused with an ATX heading.
            text = re.sub(r'(\s|^)(#{1,6}(?:\s|$))', r'\1\\\2', text)
            # '.' or ')' preceded by up to nine digits might be
            # confused with a list item.
            text = re.sub(r'((?:\s|^)[0-9]{1,9})([.)](?:\s|$))', r'\1\\\2',
                          text)
        if self.options['escape_asterisks']:
            text = text.replace('*', r'\*')
        if self.options['escape_underscores']:
            text = text.replace('_', r'\_')
        return text

    def indent(self, text, columns):
        return re.sub(r'^', ' ' * columns, text, flags=re.MULTILINE) if text else ''

    def underline(self, text, pad_char):
        text = (text or '').rstrip()
        return '\n\n%s\n%s\n\n' % (text, pad_char * len(text)) if text else ''

    def convert_a(self, el, text, convert_as_inline):
        """Enhanced link conversion with URL rewriting."""
        if self.options['link_rewriting'] and callable(self.options['link_rewriting']):
            href = el.get('href')
            if href:
                href = self.options['link_rewriting'](href)
                el['href'] = href
                
        prefix, suffix, text = chomp(text)
        if not text:
            return ''
        href = el.get('href')
        title = el.get('title')
        # For the replacement see #29: text nodes underscores are escaped
        if (self.options['autolinks']
                and text.replace(r'\_', '_') == href
                and not title
                and not self.options['default_title']):
            # Shortcut syntax
            return '<%s>' % href
        if self.options['default_title'] and not title:
            title = href
        title_part = ' "%s"' % title.replace('"', r'\"') if title else ''
        return '%s[%s](%s%s)%s' % (prefix, text, href, title_part, suffix) if href else text

    def convert_blockquote(self, el, text, convert_as_inline):

        if convert_as_inline:
            return ' ' + text.strip() + ' '

        return '\n' + (re.sub(r'^', '> ', text.strip(), flags=re.MULTILINE) + '\n\n') if text else ''

    def convert_br(self, el, text, convert_as_inline):
        if convert_as_inline:
            return ""

        if self.options['newline_style'].lower() == 'backslash':
            return '\\\n'
        else:
            return '  \n'

    def convert_code(self, el, text, convert_as_inline):
        if el.parent.name == 'pre':
            return text
        converter = abstract_inline_conversion(lambda self: '`')
        return converter(self, el, text, convert_as_inline)

    def convert_kbd(self, el, text, convert_as_inline):
        return self.convert_code(el, text, convert_as_inline)

    def _convert_hn(self, n, el, text, convert_as_inline):
        """ Method name prefixed with _ to prevent <hn> to call this """
        if convert_as_inline:
            return text

        # prevent MemoryErrors in case of very large n
        n = max(1, min(6, n))

        style = self.options['heading_style'].lower()
        text = text.strip()
        if style == 'underlined' and n <= 2:
            line = '=' if n == 1 else '-'
            return self.underline(text, line)
        text = re.sub(r'[\t ]+', ' ', text)
        hashes = '#' * n
        if style == 'atx_closed':
            return '\n%s %s %s\n\n' % (hashes, text, hashes)
        return '\n%s %s\n\n' % (hashes, text)

    def convert_hr(self, el, text, convert_as_inline):
        return '\n\n---\n\n'

    def convert_img(self, el, text, convert_as_inline):
        alt = el.attrs.get('alt', None) or ''
        src = el.attrs.get('src', None) or ''
        title = el.attrs.get('title', None) or ''
        title_part = ' "%s"' % title.replace('"', r'\"') if title else ''
        if (convert_as_inline
                and el.parent.name not in self.options['keep_inline_images_in']):
            return alt

        return '![%s](%s%s)' % (alt, src, title_part)

    def convert_list(self, el, text, convert_as_inline):
        """Enhanced list conversion with smart handling."""
        if not self.options['smart_lists']:
            return super().convert_list(el, text, convert_as_inline)
            
        nested = False
        before_paragraph = False
        
        # Smart list processing
        list_type = el.name
        is_ordered = list_type == 'ol'
        start = el.get('start', 1) if is_ordered else None
        
        # Process list items
        items = el.find_all('li', recursive=False)
        processed_items = []
        
        for i, item in enumerate(items):
            item_text = self.process_tag(item, convert_as_inline)
            if is_ordered:
                number = start + i if start else i + 1
                processed_items.append(f"{number}. {item_text}")
            else:
                processed_items.append(f"* {item_text}")
                
        return '\n'.join(processed_items)

    def convert_ul(self, el, text, convert_as_inline):
        return self.convert_list(el, text, convert_as_inline)

    def convert_ol(self, el, text, convert_as_inline):
        return self.convert_list(el, text, convert_as_inline)

    def convert_li(self, el, text, convert_as_inline):
        parent = el.parent
        if parent is not None and parent.name == 'ol':
            if parent.get("start") and str(parent.get("start")).isnumeric():
                start = int(parent.get("start"))
            else:
                start = 1
            bullet = '%s.' % (start + parent.index(el))
        else:
            depth = -1
            while el:
                if el.name == 'ul':
                    depth += 1
                el = el.parent
            bullets = self.options['bullets']
            bullet = bullets[depth % len(bullets)]
        bullet = bullet + ' '
        text = (text or '').strip()
        text = self.indent(text, len(bullet))
        if text:
            text = bullet + text[len(bullet):]
        return '%s\n' % text

    def convert_p(self, el, text, convert_as_inline):
        if convert_as_inline:
            return ' ' + text.strip() + ' '
        if self.options['wrap']:
            # Preserve newlines (and preceding whitespace) resulting
            # from <br> tags.  Newlines in the input have already been
            # replaced by spaces.
            lines = text.split('\n')
            new_lines = []
            for line in lines:
                line = line.lstrip()
                line_no_trailing = line.rstrip()
                trailing = line[len(line_no_trailing):]
                line = fill(line,
                            width=self.options['wrap_width'],
                            break_long_words=False,
                            break_on_hyphens=False)
                new_lines.append(line + trailing)
            text = '\n'.join(new_lines)
        return '\n\n%s\n\n' % text if text else ''

    def convert_pre(self, el, text, convert_as_inline):
        if not text:
            return ''
        code_language = self.options['code_language']

        if self.options['code_language_callback']:
            code_language = self.options['code_language_callback'](el) or code_language

        return '\n```%s\n%s\n```\n' % (code_language, text)

    def convert_script(self, el, text, convert_as_inline):
        return ''

    def convert_style(self, el, text, convert_as_inline):
        return ''

    def convert_comment(self, el, text, convert_as_inline):
        """Handle comment-like elements based on configuration."""
        if self.options['preserve_html_comments']:
            return f'<!-- {text} -->'
        return ''

    def convert_details(self, el, text, convert_as_inline):
        """Convert HTML5 details and summary tags."""
        summary = el.find('summary')
        summary_text = summary.text if summary else 'Details'
        return f'\n<details>\n<summary>{summary_text}</summary>\n\n{text}\n</details>\n'

    def convert_mark(self, el, text, convert_as_inline):
        """Convert mark tag with highlighting."""
        return f'`{text}`'

    def convert_table(self, el, text, convert_as_inline):
        return '\n\n' + text + '\n'

    def convert_caption(self, el, text, convert_as_inline):
        return text + '\n'

    def convert_figcaption(self, el, text, convert_as_inline):
        return '\n\n' + text + '\n\n'

    def convert_td(self, el, text, convert_as_inline):
        colspan = 1
        if 'colspan' in el.attrs and el['colspan'].isdigit():
            colspan = int(el['colspan'])
        return ' ' + text.strip().replace("\n", " ") + ' |' * colspan

    def convert_th(self, el, text, convert_as_inline):
        colspan = 1
        if 'colspan' in el.attrs and el['colspan'].isdigit():
            colspan = int(el['colspan'])
        return ' ' + text.strip().replace("\n", " ") + ' |' * colspan

    def convert_tr(self, el, text, convert_as_inline):
        cells = el.find_all(['td', 'th'])
        is_headrow = (
            all([cell.name == 'th' for cell in cells])
            or (not el.previous_sibling and not el.parent.name == 'tbody')
            or (not el.previous_sibling and el.parent.name == 'tbody' and len(el.parent.parent.find_all(['thead'])) < 1)
        )
        overline = ''
        underline = ''
        if is_headrow and not el.previous_sibling:
            # first row and is headline: print headline underline
            full_colspan = 0
            for cell in cells:
                if 'colspan' in cell.attrs and cell['colspan'].isdigit():
                    full_colspan += int(cell["colspan"])
                else:
                    full_colspan += 1
            underline += '| ' + ' | '.join(['---'] * full_colspan) + ' |' + '\n'
        elif (not el.previous_sibling
              and (el.parent.name == 'table'
                   or (el.parent.name == 'tbody'
                       and not el.parent.previous_sibling))):
            # first row, not headline, and:
            # - the parent is table or
            # - the parent is tbody at the beginning of a table.
            # print empty headline above this row
            overline += '| ' + ' | '.join([''] * len(cells)) + ' |' + '\n'
            overline += '| ' + ' | '.join(['---'] * len(cells)) + ' |' + '\n'
        return overline + '|' + text + '\n' + underline

    def _extract_metadata(self, scout):
        """
        Extract metadata from the parsed document.
        
        Args:
            scout (Union[Scout, Tag, ScoutSearchResult]): Parsed object
        
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        metadata = {}
        try:
            # Handle ScoutSearchResult
            if hasattr(scout, '_results'):
                scout = scout._results[0] if scout._results else None
            
            if scout is None:
                return metadata

            # Find head tag
            head = scout.find('head')
            if not head and hasattr(scout, 'find_all'):
                head_list = scout.find_all('head')
                head = head_list[0] if head_list else None

            if head:
                # Extract title
                title_tag = head.find('title') or (head.find_all('title')[0] if head.find_all('title') else None)
                metadata['title'] = title_tag.get_text() if title_tag else None

                # Extract meta tags
                metadata['meta'] = {}
                meta_tags = head.find_all('meta') if hasattr(head, 'find_all') else []
                for meta in meta_tags:
                    name = meta.get('name') or meta.get('property')
                    content = meta.get('content')
                    if name and content:
                        metadata['meta'][name] = content

        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")
        
        return metadata

    def _extract_semantic_info(self, scout):
        """
        Extract semantic information from the document.
        
        Args:
            scout (Union[Scout, Tag, ScoutSearchResult]): Parsed object
        
        Returns:
            Dict[str, Any]: Semantic information
        """
        # Handle ScoutSearchResult
        if hasattr(scout, '_results'):
            scout = scout._results[0] if scout._results else None
        
        if scout is None:
            return {
                'language': 'unknown',
                'text_density': 0,
                'content_types': {}
            }

        semantic_info = {
            'language': 'unknown',
            'text_density': 0,
            'content_types': {}
        }

        try:
            # Try to find language
            html_tag = scout.find('html')
            if not html_tag and hasattr(scout, 'find_all'):
                html_tags = scout.find_all('html')
                html_tag = html_tags[0] if html_tags else None

            semantic_info['language'] = html_tag.get('lang', 'unknown') if html_tag else 'unknown'
            
            # Calculate text density
            total_text = scout.get_text() if hasattr(scout, 'get_text') else ''
            total_html = str(scout)
            semantic_info['text_density'] = len(total_text) / len(total_html) * 100 if total_html else 0

            # Analyze content types
            content_types = {}
            for tag in scout.find_all() if hasattr(scout, 'find_all') else [scout]:
                tag_type = tag.name
                content_types[tag_type] = content_types.get(tag_type, 0) + 1
            
            semantic_info['content_types'] = content_types

        except Exception as e:
            logger.warning(f"Semantic info extraction failed: {e}")
        
        return semantic_info

    def _analyze_structure(self, scout):
        """
        Analyze document structure.
        
        Args:
            scout (Scout): Parsed Scout object
        
        Returns:
            Dict[str, Any]: Document structure information
        """
        structure = {
            'headings': [
                {'level': h.name, 'text': h.get_text(strip=True)}
                for h in scout.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            ],
            'sections': [],
            'links': [
                {'href': a.get('href'), 'text': a.get_text(strip=True)}
                for a in scout.find_all('a')
            ]
        }
        return structure

    def _calculate_text_density(self, scout):
        """
        Calculate text density of the document.
        
        Args:
            scout (Scout): Parsed Scout object
        
        Returns:
            float: Text density percentage
        """
        try:
            total_text = scout.get_text()
            total_html = str(scout)
            return len(total_text) / len(total_html) * 100 if total_html else 0
        except Exception as e:
            logger.warning(f"Text density calculation failed: {e}")
            return 0

    def _analyze_content_types(self, scout):
        """
        Analyze content types in the document.
        
        Args:
            scout (Scout): Parsed Scout object
        
        Returns:
            Dict[str, int]: Content type counts
        """
        content_types = {}
        try:
            for tag in scout.find_all():
                tag_type = tag.name
                content_types[tag_type] = content_types.get(tag_type, 0) + 1
        except Exception as e:
            logger.warning(f"Content type analysis failed: {e}")
        return content_types

def markdownify(html: str, **options) -> Union[str, Dict[str, Any]]:
    """
    Convert HTML to Markdown with advanced options.
    
    Args:
        html (str): HTML content to convert
        **options: Conversion options
    
    Returns:
        Union[str, Dict[str, Any]]: Markdown text or structured output
    """
    try:
        # Use Scout's native markdown conversion
        scout = Scout(html, features='html.parser')
        
        # Handle ScoutSearchResult
        if hasattr(scout, '_results'):
            scout = scout._results[0] if scout._results else scout
        
        # Determine conversion style based on options
        heading_style = options.get('heading_style', 'ATX')
        
        # Custom markdown conversion to preserve formatting
        def convert_tag(tag):
            # Handle specific tag types
            if tag.name == 'h1':
                return f"# {tag.get_text(strip=True)}\n\n"
            elif tag.name == 'h2':
                return f"## {tag.get_text(strip=True)}\n\n"
            elif tag.name == 'h3':
                return f"### {tag.get_text(strip=True)}\n\n"
            elif tag.name == 'p':
                return f"{tag.get_text(strip=True)}\n\n"
            elif tag.name == 'strong':
                return f"**{tag.get_text(strip=True)}**"
            elif tag.name == 'em':
                return f"*{tag.get_text(strip=True)}*"
            elif tag.name == 'ul':
                return ''.join(f"* {li.get_text(strip=True)}\n" for li in tag.find_all('li'))
            elif tag.name == 'ol':
                return ''.join(f"{i+1}. {li.get_text(strip=True)}\n" for i, li in enumerate(tag.find_all('li')))
            elif tag.name == 'a':
                return f"[{tag.get_text(strip=True)}]({tag.get('href', '')})"
            return tag.get_text(strip=True)
        
        # Traverse and convert tags
        markdown_parts = []
        for tag in scout.find_all():
            if tag.name in ['h1', 'h2', 'h3', 'p', 'strong', 'em', 'ul', 'ol', 'a']:
                markdown_parts.append(convert_tag(tag))
        
        markdown = '\n'.join(markdown_parts)
        
        # If structured output is requested, include additional metadata
        if options.get('STRUCTURED_OUTPUT', False):
            # Custom metadata extraction
            metadata = {}
            try:
                head = scout.find('head') or scout.find_all('head')[0] if scout.find_all('head') else None
                if head:
                    # Extract title
                    title_tag = head.find('title') or head.find_all('title')[0] if head.find_all('title') else None
                    metadata['title'] = title_tag.get_text() if title_tag else None
                    
                    # Extract meta tags
                    metadata['meta'] = {
                        meta.get('name', meta.get('property')): meta.get('content')
                        for meta in head.find_all('meta')
                        if meta.get('name') or meta.get('property')
                    }
            except Exception as e:
                logger.warning(f"Metadata extraction failed: {e}")
            
            return {
                'markdown': markdown,
                'metadata': metadata,
                'structure': scout.analyze_page_structure(),
                'semantic_info': scout.extract_semantic_info()
            }
        
        return markdown
    except Exception as e:
        logger.error(f"Markdownify failed: {e}", exc_info=True)
        return str(e)