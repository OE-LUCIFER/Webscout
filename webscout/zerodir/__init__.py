"""
ZeroDir: A zero-dependency app directories management library

Provides cross-platform directory management for application data, 
configuration, and cache without external dependencies.
"""

import os
import sys
import json
import platform
import tempfile
import shutil
import hashlib
import time
import datetime

class ZeroDirs:
    def __init__(self, app_name, app_author=None):
        """
        Initialize ZeroDirs with application details
        
        :param app_name: Name of the application
        :param app_author: Author/Company name (optional)
        """
        self.app_name = app_name
        self.app_author = app_author or os.getlogin()
        self._init_dirs()

    def _init_dirs(self):
        """Initialize application directories"""
        self.user_data_dir = self._get_user_data_dir()
        self.user_config_dir = self._get_user_config_dir()
        self.user_cache_dir = self._get_user_cache_dir()
        self.user_log_dir = self._get_user_log_dir()
        self.temp_dir = self._get_temp_dir()

        # Create directories if they don't exist
        for directory in [
            self.user_data_dir, 
            self.user_config_dir, 
            self.user_cache_dir, 
            self.user_log_dir,
            self.temp_dir
        ]:
            os.makedirs(directory, exist_ok=True)

    def _get_user_data_dir(self):
        """Get user data directory"""
        system = platform.system().lower()
        if system == 'windows':
            base = os.path.expandvars('%LOCALAPPDATA%')
            return os.path.join(base, self.app_author, self.app_name)
        elif system == 'darwin':  # macOS
            return os.path.expanduser(f'~/Library/Application Support/{self.app_name}')
        else:  # Linux and other Unix-like
            xdg_data_home = os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')
            return os.path.join(xdg_data_home, self.app_name)

    def _get_user_config_dir(self):
        """Get user configuration directory"""
        system = platform.system().lower()
        if system == 'windows':
            base = os.path.expandvars('%APPDATA%')
            return os.path.join(base, self.app_author, self.app_name)
        elif system == 'darwin':  # macOS
            return os.path.expanduser(f'~/Library/Preferences/{self.app_name}')
        else:  # Linux and other Unix-like
            xdg_config_home = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
            return os.path.join(xdg_config_home, self.app_name)

    def _get_user_cache_dir(self):
        """Get user cache directory"""
        system = platform.system().lower()
        if system == 'windows':
            base = os.path.expandvars('%LOCALAPPDATA%')
            return os.path.join(base, self.app_author, self.app_name, 'Cache')
        elif system == 'darwin':  # macOS
            return os.path.expanduser(f'~/Library/Caches/{self.app_name}')
        else:  # Linux and other Unix-like
            xdg_cache_home = os.environ.get('XDG_CACHE_HOME') or os.path.expanduser('~/.cache')
            return os.path.join(xdg_cache_home, self.app_name)

    def _get_user_log_dir(self):
        """Get user log directory"""
        system = platform.system().lower()
        if system == 'windows':
            base = os.path.expandvars('%LOCALAPPDATA%')
            return os.path.join(base, self.app_author, self.app_name, 'Logs')
        elif system == 'darwin':  # macOS
            return os.path.expanduser(f'~/Library/Logs/{self.app_name}')
        else:  # Linux and other Unix-like
            xdg_data_home = os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')
            return os.path.join(xdg_data_home, self.app_name, 'logs')

    def _get_temp_dir(self):
        """Get temporary directory for the application"""
        return os.path.join(tempfile.gettempdir(), f'{self.app_name}_temp')

    def save_config(self, config_data, filename='config.json'):
        """
        Save configuration data to config directory
        
        :param config_data: Dictionary of configuration data
        :param filename: Name of the config file (default: config.json)
        :return: Path to saved config file
        """
        config_path = os.path.join(self.user_config_dir, filename)
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
        return config_path

    def load_config(self, filename='config.json'):
        """
        Load configuration data from config directory
        
        :param filename: Name of the config file (default: config.json)
        :return: Dictionary of configuration data or None if file doesn't exist
        """
        config_path = os.path.join(self.user_config_dir, filename)
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return None

    def cache_file(self, content, filename=None, extension=None):
        """
        Cache a file with optional naming and extension
        
        :param content: File content or bytes
        :param filename: Optional custom filename
        :param extension: Optional file extension
        :return: Path to cached file
        """
        if not filename:
            # Generate a hash-based filename if not provided
            content_hash = hashlib.md5(str(content).encode()).hexdigest()
            filename = f'{content_hash}{extension or ""}'
        
        cache_path = os.path.join(self.user_cache_dir, filename)
        
        # Write content to file
        with open(cache_path, 'wb' if isinstance(content, bytes) else 'w') as f:
            f.write(content)
        
        return cache_path

    def clear_cache(self, max_age_days=30):
        """
        Clear cache directory, optionally removing files older than max_age_days
        
        :param max_age_days: Maximum age of files to keep (default: 30 days)
        :return: Number of files deleted
        """
        current_time = time.time()
        
        deleted_count = 0
        for filename in os.listdir(self.user_cache_dir):
            filepath = os.path.join(self.user_cache_dir, filename)
            
            # Check file age
            file_age_days = (current_time - os.path.getctime(filepath)) / (24 * 3600)
            
            if file_age_days > max_age_days:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception:
                    pass
        
        return deleted_count

    def log(self, message, filename='app.log', level='INFO'):
        """
        Log a message to the log directory
        
        :param message: Log message
        :param filename: Log filename (default: app.log)
        :param level: Log level (default: INFO)
        """
        log_path = os.path.join(self.user_log_dir, filename)
        
        with open(log_path, 'a') as log_file:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_file.write(f'[{level}] {timestamp}: {message}\n')

def user_data_dir(app_name, app_author=None):
    """
    Quick function to get user data directory
    
    :param app_name: Name of the application
    :param app_author: Author/Company name (optional)
    :return: Path to user data directory
    """
    return ZeroDirs(app_name, app_author).user_data_dir

def user_config_dir(app_name, app_author=None):
    """
    Quick function to get user config directory
    
    :param app_name: Name of the application
    :param app_author: Author/Company name (optional)
    :return: Path to user config directory
    """
    return ZeroDirs(app_name, app_author).user_config_dir

def user_cache_dir(app_name, app_author=None):
    """
    Quick function to get user cache directory
    
    :param app_name: Name of the application
    :param app_author: Author/Company name (optional)
    :return: Path to user cache directory
    """
    return ZeroDirs(app_name, app_author).user_cache_dir

def user_log_dir(app_name, app_author=None):
    """
    Quick function to get user log directory
    
    :param app_name: Name of the application
    :param app_author: Author/Company name (optional)
    :return: Path to user log directory
    """
    return ZeroDirs(app_name, app_author).user_log_dir
