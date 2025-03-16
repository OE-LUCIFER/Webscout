# -*- coding: utf-8 -*-

import os
import json
import requests
from typing import Optional, Dict, Union
from rich.console import Console
from rich.table import Table
from datetime import datetime

console = Console()

class AwesomePrompts:
    """The most awesome prompts manager you'll ever see fr fr! 🔥"""
    
    def __init__(
        self,
        repo_url: str = "https://raw.githubusercontent.com/OE-LUCIFER/prompts/main/prompt.json",
        local_path: Optional[str] = None,
        auto_update: bool = True
    ):
        """Initialize them Awesome Prompts with style! 💫

        Args:
            repo_url (str): URL to fetch prompts from
            local_path (str, optional): Where to save them prompts locally
            auto_update (bool): Auto update prompts on init. Defaults to True
        """
        self.repo_url = repo_url
        self.local_path = local_path or os.path.join(
            os.path.expanduser("~"),
            ".webscout",
            "awesome-prompts.json"
        )
        self._cache: Dict[Union[str, int], str] = {}
        self._last_update: Optional[datetime] = None
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.local_path), exist_ok=True)
        
        # Load those prompts on init if auto_update is True
        if auto_update:
            self.update_prompts_from_online()
    
    def _load_prompts(self) -> Dict[Union[str, int], str]:
        """Load prompts from the local file fr fr! 📂"""
        try:
            if os.path.exists(self.local_path):
                with open(self.local_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            console.print(f"[red]❌ Error loading prompts: {str(e)}[/red]")
            return {}
    
    def _save_prompts(self, prompts: Dict[Union[str, int], str]) -> None:
        """Save them prompts with style! 💾"""
        try:
            with open(self.local_path, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, indent=4, ensure_ascii=False)
            self._cache = prompts
            console.print("[green]✨ Prompts saved successfully![/green]")
        except Exception as e:
            console.print(f"[red]❌ Error saving prompts: {str(e)}[/red]")
    
    def update_prompts_from_online(self, force: bool = False) -> bool:
        """Update prompts from the repo! 🚀

        Args:
            force (bool): Force update even if recently updated

        Returns:
            bool: True if update successful
        """
        try:
            # Check if we need to update
            if not force and self._last_update and \
               (datetime.now() - self._last_update).total_seconds() < 3600:
                console.print("[yellow]⚡ Prompts are already up to date![/yellow]")
                return True
                
            console.print("[cyan]🔄 Updating prompts...[/cyan]")
            response = requests.get(self.repo_url, timeout=10)
            response.raise_for_status()
            
            # Merge new prompts with existing ones
            new_prompts = response.json()
            existing_prompts = self._load_prompts()
            merged_prompts = {**existing_prompts, **new_prompts}
            
            # Create a new dictionary for numeric indices
            indexed_prompts = merged_prompts.copy()
            
            # Add indices for numeric access
            for i, (key, value) in enumerate(list(merged_prompts.items())):
                if isinstance(key, str):
                    indexed_prompts[i] = value
            
            self._save_prompts(indexed_prompts)
            self._last_update = datetime.now()
            
            console.print("[green]✨ Prompts updated successfully![/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error updating prompts: {str(e)}[/red]")
            return False
    
    def get_act(
        self,
        key: Union[str, int],
        default: Optional[str] = None,
        case_insensitive: bool = True
    ) -> Optional[str]:
        """Get that perfect prompt! 🎯

        Args:
            key: Prompt name or index
            default: Default value if not found
            case_insensitive: Match case exactly?

        Returns:
            str: The prompt or default value
        """
        prompts = self._cache or self._load_prompts()
        
        # Try direct access first
        if key in prompts:
            return prompts[key]
            
        # Try case-insensitive search for string keys
        if isinstance(key, str) and case_insensitive:
            key_lower = key.lower()
            for k, v in prompts.items():
                if isinstance(k, str) and k.lower() == key_lower:
                    return v
        
        return default
    
    def add_prompt(self, name: str, prompt: str) -> bool:
        """Add a new prompt to the collection! ✨

        Args:
            name: Name of the prompt
            prompt: The prompt text

        Returns:
            bool: Success status
        """
        if not name or not prompt:
            console.print("[red]❌ Name and prompt cannot be empty![/red]")
            return False
            
        prompts = self._cache or self._load_prompts()
        prompts[name] = prompt
        self._save_prompts(prompts)
        return True
    
    def delete_prompt(
        self,
        name: Union[str, int],
        case_insensitive: bool = True,
        raise_not_found: bool = False
    ) -> bool:
        """Delete a prompt from the collection! 🗑️

        Args:
            name: Name or index of prompt to delete
            case_insensitive: Match case exactly?
            raise_not_found: Raise error if prompt not found?

        Returns:
            bool: Success status
        """
        prompts = self._cache or self._load_prompts()
        
        # Handle direct key match
        if name in prompts:
            del prompts[name]
            self._save_prompts(prompts)
            return True
            
        # Handle case-insensitive match
        if isinstance(name, str) and case_insensitive:
            name_lower = name.lower()
            for k in list(prompts.keys()):
                if isinstance(k, str) and k.lower() == name_lower:
                    del prompts[k]
                    self._save_prompts(prompts)
                    return True
        
        if raise_not_found:
            raise KeyError(f"Prompt '{name}' not found!")
        console.print(f"[yellow]⚠️ Prompt '{name}' not found![/yellow]")
        return False
    
    @property
    def all_acts(self) -> Dict[Union[str, int], str]:
        """All them awesome prompts mapped with style! 📚

        Returns:
            dict: All prompts with their indices
        """
        prompts = self._cache or self._load_prompts()
        if not prompts:
            self.update_prompts_from_online()
            prompts = self._load_prompts()
            
        # Create a new dictionary for the result
        result = prompts.copy()
        
        # Add numeric indices to the copy
        for i, (key, value) in enumerate(list(prompts.items())):
            if isinstance(key, str):
                result[i] = value
                
        return result
    
    def show_acts(self, search: Optional[str] = None) -> None:
        """Show all them awesome prompts with style! 📋

        Args:
            search: Optional search term to filter prompts
        """
        prompts = self.all_acts
        
        # Create a fire table! 🔥
        table = Table(
            title="🚀 Awesome Prompts Collection",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Index", style="cyan", justify="right")
        table.add_column("Name", style="green")
        table.add_column("Preview", style="yellow")
        
        for i, (key, value) in enumerate(prompts.items()):
            if isinstance(key, int):
                continue  # Skip numeric keys as they're duplicates
                
            # Filter by search term if provided
            if search and search.lower() not in key.lower() and \
               search.lower() not in value.lower():
                continue
                
            preview = value[:50] + "..." if len(value) > 50 else value
            table.add_row(str(i), str(key), preview)
        
        console.print(table)
    
    def get_random_act(self) -> Optional[str]:
        """Get a random prompt for that surprise factor! 🎲"""
        import random
        prompts = self.all_acts
        string_keys = [k for k in prompts.keys() if isinstance(k, str)]
        if not string_keys:
            return None
        return prompts[random.choice(string_keys)]

if __name__ == "__main__":
    # Quick demo of the features! 🚀
    prompts = AwesomePrompts()
    prompts.update_prompts_from_online()
    prompts.show_acts()
    
    # Add a test prompt
    prompts.add_prompt("test_prompt", "This is a test prompt! 🔥")
    
    # Show the new prompt
    print("\nTest Prompt:", prompts.get_act("test_prompt"))
    
    # Clean up
    prompts.delete_prompt("test_prompt")
