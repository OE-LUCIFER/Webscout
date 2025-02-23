import json
import re
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union

class MessageFormatter:
    """Utility class for formatting log messages."""
    
    @staticmethod
    def format_exception(exc_info: tuple) -> str:
        """
        Format exception information into a readable string.
        
        Args:
            exc_info: Tuple of (type, value, traceback)
            
        Returns:
            Formatted exception string
        """
        return "".join(traceback.format_exception(*exc_info))

    @staticmethod
    def format_dict(data: Dict[str, Any], indent: int = 2) -> str:
        """
        Format dictionary into pretty-printed string.
        
        Args:
            data: Dictionary to format
            indent: Number of spaces for indentation
            
        Returns:
            Formatted string representation
        """
        return json.dumps(data, indent=indent, default=str, ensure_ascii=False)

    @staticmethod
    def format_object(obj: Any) -> str:
        """
        Format any object into a string representation.
        
        Args:
            obj: Object to format
            
        Returns:
            String representation of object
        """
        if hasattr(obj, "to_dict"):
            return MessageFormatter.format_dict(obj.to_dict())
        if hasattr(obj, "__dict__"):
            return MessageFormatter.format_dict(obj.__dict__)
        return str(obj)

    @staticmethod
    def truncate(message: str, max_length: int = 1000, suffix: str = "...") -> str:
        """
        Truncate message to maximum length.
        
        Args:
            message: Message to truncate
            max_length: Maximum length
            suffix: String to append when truncated
            
        Returns:
            Truncated message
        """
        if len(message) <= max_length:
            return message
        return message[:max_length - len(suffix)] + suffix

    @staticmethod
    def mask_sensitive(message: str, patterns: Dict[str, str]) -> str:
        """
        Mask sensitive information in message.
        
        Args:
            message: Message to process
            patterns: Dictionary of {pattern: mask}
            
        Returns:
            Message with sensitive info masked
        """
        result = message
        for pattern, mask in patterns.items():
            result = re.sub(pattern, mask, result)
        return result

    @staticmethod
    def format_context(context: Dict[str, Any]) -> str:
        """
        Format context dictionary into readable string.
        
        Args:
            context: Context dictionary
            
        Returns:
            Formatted context string
        """
        parts = []
        for key, value in sorted(context.items()):
            formatted_value = (
                MessageFormatter.format_object(value)
                if isinstance(value, (dict, list, tuple))
                else str(value)
            )
            parts.append(f"{key}={formatted_value}")
        return " ".join(parts)

    @staticmethod
    def format_metrics(metrics: Dict[str, Union[int, float]]) -> str:
        """
        Format performance metrics into readable string.
        
        Args:
            metrics: Dictionary of metric names and values
            
        Returns:
            Formatted metrics string
        """
        parts = []
        for key, value in sorted(metrics.items()):
            if isinstance(value, float):
                formatted = f"{value:.3f}"
            else:
                formatted = str(value)
            parts.append(f"{key}={formatted}")
        return " ".join(parts)

    @staticmethod
    def format_timestamp(
        timestamp: Optional[datetime] = None,
        format: str = "%Y-%m-%d %H:%M:%S.%f"
    ) -> str:
        """
        Format timestamp into string.
        
        Args:
            timestamp: Datetime object (uses current time if None)
            format: strftime format string
            
        Returns:
            Formatted timestamp string
        """
        if timestamp is None:
            timestamp = datetime.now()
        return timestamp.strftime(format)

    @classmethod
    def format_message(
        cls,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Union[int, float]]] = None,
        max_length: Optional[int] = None,
        mask_patterns: Optional[Dict[str, str]] = None,
        timestamp_format: Optional[str] = None
    ) -> str:
        """
        Format complete log message with all options.
        
        Args:
            message: Base message
            context: Optional context dictionary
            metrics: Optional performance metrics
            max_length: Optional maximum length
            mask_patterns: Optional sensitive data patterns
            timestamp_format: Optional timestamp format
            
        Returns:
            Formatted complete message
        """
        parts = []
        
        # Add timestamp
        if timestamp_format:
            parts.append(cls.format_timestamp(format=timestamp_format))
            
        # Add main message
        parts.append(message)
        
        # Add context if present
        if context:
            parts.append(cls.format_context(context))
            
        # Add metrics if present
        if metrics:
            parts.append(cls.format_metrics(metrics))
            
        # Join all parts
        result = " ".join(parts)
        
        # Apply masking if needed
        if mask_patterns:
            result = cls.mask_sensitive(result, mask_patterns)
            
        # Apply length limit if needed
        if max_length:
            result = cls.truncate(result, max_length)
            
        return result
