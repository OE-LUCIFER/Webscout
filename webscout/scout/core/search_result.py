"""
Scout Search Result Module
"""

from typing import List, Union, Callable, Any, Dict, Iterator
from ..element import Tag
from .text_analyzer import ScoutTextAnalyzer


class ScoutSearchResult:
    """
    Represents a search result with advanced querying capabilities.
    Enhanced with more intelligent filtering and processing.
    """
    def __init__(self, results: List[Tag]):
        """
        Initialize a search result collection.
        
        Args:
            results (List[Tag]): List of matching tags
        """
        self._results = results
    
    def __len__(self) -> int:
        return len(self._results)
    
    def __iter__(self) -> Iterator[Tag]:
        return iter(self._results)
    
    def __getitem__(self, index: Union[int, slice]) -> Union[Tag, List[Tag]]:
        return self._results[index]
    
    def texts(self, separator=' ', strip=True) -> List[str]:
        """
        Extract texts from all results.
        
        Args:
            separator (str, optional): Text separator
            strip (bool, optional): Strip whitespace
        
        Returns:
            List[str]: List of extracted texts
        """
        return [tag.get_text(separator, strip) for tag in self._results]
    
    def attrs(self, attr_name: str) -> List[Any]:
        """
        Extract a specific attribute from all results.
        
        Args:
            attr_name (str): Attribute name to extract
        
        Returns:
            List[Any]: List of attribute values
        """
        return [tag.get(attr_name) for tag in self._results]
    
    def filter(self, predicate: Callable[[Tag], bool]) -> 'ScoutSearchResult':
        """
        Filter results using a predicate function.
        
        Args:
            predicate (Callable[[Tag], bool]): Filtering function
        
        Returns:
            ScoutSearchResult: Filtered search results
        """
        return ScoutSearchResult([tag for tag in self._results if predicate(tag)])
    
    def map(self, transform: Callable[[Tag], Any]) -> List[Any]:
        """
        Transform results using a mapping function.
        
        Args:
            transform (Callable[[Tag], Any]): Transformation function
        
        Returns:
            List[Any]: Transformed results
        """
        return [transform(tag) for tag in self._results]
    
    def analyze_text(self) -> Dict[str, Any]:
        """
        Perform text analysis on search results.
        
        Returns:
            Dict[str, Any]: Text analysis results
        """
        texts = self.texts(strip=True)
        full_text = ' '.join(texts)
        
        return {
            'total_results': len(self._results),
            'word_count': ScoutTextAnalyzer.count_words(full_text),
            'entities': ScoutTextAnalyzer.extract_entities(full_text)
        }