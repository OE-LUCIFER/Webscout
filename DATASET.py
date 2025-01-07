import json
import os
import csv
import random
import xml.etree.ElementTree as ET
import pyarrow as pa
import pyarrow.parquet as pq
import re
from typing import List, Dict, Any, Tuple, Union, Optional, Callable
from rich import print
from rich.console import Console
import pandas as pd
from collections import Counter
from datasets import Dataset, DatasetDict
import math
import datetime
console = Console()

def create_dataset_file(filepath: str, data: List[Dict[str, Any]]) -> None:
    """Creates or overwrites a JSON file with the given data."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except (IOError, OSError) as e:
        console.print(f"[red]Error writing to file {filepath}: {e}[/red]")

def load_dataset_file(filepath: str) -> Union[List[Dict[str, Any]], None]:
    """Loads a JSON dataset from a file."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError) as e:
        console.print(f"[red]Error loading dataset from {filepath}: {e}[/red]")
        return None

class DatasetBuilder:
    def __init__(self, filepath: str):
        """Initializes a DatasetBuilder object."""
        self.filepath = filepath
        self.dataset = load_dataset_file(self.filepath) or []

    def save_dataset(self) -> None:
        """Saves the dataset to the specified file."""
        create_dataset_file(self.filepath, self.dataset)

    def add_datapoint(self, **kwargs) -> None:
        """Adds a new data point to the dataset."""
        self.dataset.append(kwargs)
        self.save_dataset()


    def create_conversation_format(self, roles: List[str], content_keys: List[str]) -> None:
        """
        Creates a conversation format for chat-based LLMs.

        :param roles: List of roles in the conversation (e.g., ["user", "assistant", "system"])
        :param content_keys: List of keys containing the content for each role
        """
        for item in self.dataset:
            item['conversation'] = [
                {
                    "role": role,
                    "content": item.get(key, "")
                }
                for role, key in zip(roles, content_keys)
            ]
        
        self.save_dataset()
        console.print(f"[blue]Conversation format created using roles: {roles}.[/blue]")

       
    def add_datapoint_from_json(self, json_data: Union[str, Dict[str, Any]]) -> None:
        """Adds a new data point from a JSON string or dictionary."""
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError:
                console.print("[red]Error decoding JSON string. Please provide valid JSON.[/red]")
                return
        elif isinstance(json_data, dict):
            data = json_data
        else:
            console.print("[red]Invalid input. Please provide a JSON string or a dictionary.[/red]")
            return

        self.dataset.append(data)
        self.save_dataset()

    def search_dataset(self, query: str, regex: bool = False, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Searches the dataset for data points containing the query string."""
        results = []
        for item in self.dataset:
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                if any(re.search(query, str(value), flags) for value in item.values()):
                    results.append(item)
            else:
                if case_sensitive:
                    if any(query in str(value) for value in item.values()):
                        results.append(item)
                else:
                    if any(query.lower() in str(value).lower() for value in item.values()):
                        results.append(item)
        return results

    def delete_datapoint(self, index: int) -> None:
        """Deletes a data point from the dataset."""
        try:
            del self.dataset[index]
            self.save_dataset()
        except IndexError:
            console.print("[red]Invalid index.[/red]")

    def update_datapoint(self, index: int, **kwargs) -> None:
        """Updates a data point in the dataset."""
        try:
            self.dataset[index].update(kwargs)
            self.save_dataset()
        except IndexError:
            console.print("[red]Invalid index.[/red]")

    def get_statistics(self) -> Dict[str, Any]:
        """Returns statistics about the dataset."""
        if not self.dataset:
            return {"total_datapoints": 0, "unique_keys": set(), "average_keys_per_datapoint": 0}

        all_keys = [key for item in self.dataset for key in item.keys()]
        key_counts = Counter(all_keys)

        return {
            "total_datapoints": len(self.dataset),
            "unique_keys": set(all_keys),
            "average_keys_per_datapoint": sum(len(item.keys()) for item in self.dataset) / len(self.dataset),
            "most_common_keys": key_counts.most_common(5),
            "least_common_keys": key_counts.most_common()[:-6:-1]
        }

    def export_to_csv(self, filepath: str) -> None:
        """Exports the dataset to a CSV file."""
        if not self.dataset:
            console.print("[yellow]Dataset is empty. Nothing to export.[/yellow]")
            return
        try:
            df = pd.DataFrame(self.dataset)
            df.to_csv(filepath, index=False, encoding='utf-8')
        except Exception as e:
            console.print(f"[red]Error exporting to CSV: {e}[/red]")

    def export_to_parquet(self, filepath: str) -> None:
        """Exports the dataset to a Parquet file."""
        if not self.dataset:
            console.print("[yellow]Dataset is empty. Nothing to export.[/yellow]")
            return
        try:
            df = pd.DataFrame(self.dataset)
            df.to_parquet(filepath, index=False)
        except Exception as e:
            console.print(f"[red]Error exporting to Parquet: {e}[/red]")

    def export_to_xml(self, filepath: str) -> None:
        """Exports the dataset to an XML file."""
        if not self.dataset:
            console.print("[yellow]Dataset is empty. Nothing to export.[/yellow]")
            return
        try:
            root = ET.Element("dataset")
            for item in self.dataset:
                datapoint = ET.SubElement(root, "datapoint")
                for key, value in item.items():
                    ET.SubElement(datapoint, key).text = str(value)
            tree = ET.ElementTree(root)
            tree.write(filepath, encoding="utf-8", xml_declaration=True)
        except Exception as e:
            console.print(f"[red]Error exporting to XML: {e}[/red]")

    def export_to_jsonl(self, filepath: str) -> None:
        """Exports the dataset to a JSONL file."""
        if not self.dataset:
            console.print("[yellow]Dataset is empty. Nothing to export.[/yellow]")
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for item in self.dataset:
                    json.dump(item, f, ensure_ascii=False)
                    f.write('\n')
        except (IOError, OSError) as e:
            console.print(f"[red]Error exporting to JSONL: {e}[/red]")

    def export_to_excel(self, filepath: str) -> None:
        """Exports the dataset to an Excel file."""
        if not self.dataset:
            console.print("[yellow]Dataset is empty. Nothing to export.[/yellow]")
            return
        try:
            df = pd.DataFrame(self.dataset)
            df.to_excel(filepath, index=False)
        except Exception as e:
            console.print(f"[red]Error exporting to Excel: {e}[/red]")

    def export_to_sqlite(self, filepath: str, table_name: str) -> None:
        """Exports the dataset to an SQLite database."""
        if not self.dataset:
            console.print("[yellow]Dataset is empty. Nothing to export.[/yellow]")
            return
        try:
            df = pd.DataFrame(self.dataset)
            df.to_sql(table_name, f"sqlite:///{filepath}", index=False, if_exists='replace')
        except Exception as e:
            console.print(f"[red]Error exporting to SQLite: {e}[/red]")

    def modify_structure(self, old_structure: Dict[str, str], new_structure: Dict[str, str], new_filepath: Optional[str] = None) -> None:
        """
        Modifies the structure of the dataset and optionally saves it to a new file.

        :param old_structure: A dictionary mapping old column names to their positions or meanings
        :param new_structure: A dictionary mapping new column names to their corresponding old names
        :param new_filepath: Optional path to save the modified dataset (if None, updates the current file)
        """
        new_dataset = []
        for item in self.dataset:
            new_item = {}
            for new_key, old_key in new_structure.items():
                if old_key in item:
                    new_item[new_key] = item[old_key]
                else:
                    console.print(f"[yellow]Warning: '{old_key}' not found in item. Setting '{new_key}' to None.[/yellow]")
                    new_item[new_key] = None
            new_dataset.append(new_item)

        self.dataset = new_dataset

        if new_filepath:
            self.filepath = new_filepath

        self.save_dataset()
        console.print(f"[blue]Dataset structure has been modified and saved to {self.filepath}.[/blue]")

    def clean_dataset(self, columns: List[str], remove_duplicates: bool = True, fill_missing: Optional[Any] = "") -> None:
        """
        Cleans the dataset by removing duplicates and handling missing values for specified columns.

        :param columns: List of column names to be checked and cleaned
        :param remove_duplicates: Whether to remove duplicate entries
        :param fill_missing: Value to fill in for missing data (None to skip filling)
        """
        if remove_duplicates:
            self.dataset = [dict(t) for t in {tuple(d.items()) for d in self.dataset}]

        for item in self.dataset:
            for col in columns:
                if col not in item:
                    console.print(f"[yellow]Warning: Column '{col}' not found in item. Skipping.[/yellow]")
                    continue
                if fill_missing is not None and item[col] is None:
                    item[col] = fill_missing

        self.save_dataset()
        console.print(f"[blue]Dataset cleaned. Processed columns: {', '.join(columns)}[/blue]")

    def validate_structure(self, required_structure: Dict[str, type]) -> bool:
        """
        Validates the structure of the dataset against a required structure.

        :param required_structure: A dictionary mapping column names to their expected types
        :return: True if the dataset matches the required structure, False otherwise
        """
        for item in self.dataset:
            for col, expected_type in required_structure.items():
                if col not in item:
                    console.print(f"[red]Validation failed: Column '{col}' is missing.[/red]")
                    return False
                if not isinstance(item[col], expected_type):
                    console.print(f"[red]Validation failed: Column '{col}' has incorrect type. Expected {expected_type}, got {type(item[col])}.[/red]")
                    return False
        return True

    def rename_column(self, old_name: str, new_name: str) -> None:
        """
        Renames a column in the dataset.

        :param old_name: The current name of the column
        :param new_name: The new name for the column
        """
        for item in self.dataset:
            if old_name in item:
                item[new_name] = item.pop(old_name)
        self.save_dataset()
        console.print(f"[blue]Column '{old_name}' has been renamed to '{new_name}'.[/blue]")

    def add_column(self, name: str, default_value: Any = None) -> None:
        """
        Adds a new column to the dataset.

        :param name: The name of the new column
        :param default_value: The default value for the new column (optional)
        """
        for item in self.dataset:
            item[name] = default_value
        self.save_dataset()
        console.print(f"[blue]New column '{name}' has been added to the dataset.[/blue]")

    def remove_column(self, name: str) -> None:
        """
        Removes a column from the dataset.

        :param name: The name of the column to remove
        """
        for item in self.dataset:
            item.pop(name, None)
        self.save_dataset()
        console.print(f"[blue]Column '{name}' has been removed from the dataset.[/blue]")

    def apply_function_to_column(self, column: str, func: callable) -> None:
        """
        Applies a function to all values in a specified column.

        :param column: The name of the column to modify
        :param func: The function to apply to each value in the column
        """
        for item in self.dataset:
            if column in item:
                item[column] = func(item[column])
        self.save_dataset()
        console.print(f"[blue]Function applied to column '{column}'.[/blue]")

    def print_dataset(self, limit: Optional[int] = None) -> None:
        """Prints the dataset to the console, optionally limiting the number of items shown."""
        if limit:
            console.print(json.dumps(self.dataset[:limit], indent=4, ensure_ascii=False))
        else:
            console.print(json.dumps(self.dataset, indent=4, ensure_ascii=False))

    def filter_dataset(self, condition: callable) -> List[Dict[str, Any]]:
        """Filters the dataset based on a given condition."""
        return list(filter(condition, self.dataset))

    def sort_dataset(self, key: str, reverse: bool = False) -> None:
        """Sorts the dataset based on a given key."""
        self.dataset.sort(key=lambda x: x.get(key, ""), reverse=reverse)
        self.save_dataset()

    def get_unique_values(self, key: str) -> set:
        """Returns a set of unique values for a given key in the dataset."""
        return set(item.get(key) for item in self.dataset if key in item)

    def batch_update(self, condition: callable, update: Dict[str, Any]) -> None:
        """Updates multiple datapoints that meet a certain condition."""
        for item in self.dataset:
            if condition(item):
                item.update(update)
        self.save_dataset()

    def merge_datasets(self, other_dataset: List[Dict[str, Any]]) -> None:
        """Merges another dataset into the current one."""
        self.dataset.extend(other_dataset)
        self.clean_dataset(columns=list(self.dataset[0].keys()) if self.dataset else [])  # Remove potential duplicates
        self.save_dataset()

    def to_pandas(self) -> pd.DataFrame:
        """Converts the dataset to a pandas DataFrame."""
        return pd.DataFrame(self.dataset)

    def shuffle_dataset(self, seed: Optional[int] = None) -> None:
        """
        Shuffles the dataset randomly.

        :param seed: Optional seed for reproducible shuffling
        """
        if seed is not None:
            random.seed(seed)
        random.shuffle(self.dataset)
        console.print("[blue]Dataset has been shuffled.[/blue]")

    def extract_subset(self, n: int, shuffle: bool = True, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Extracts a subset of the dataset.

        :param n: Number of rows to extract
        :param shuffle: Whether to shuffle before extraction (default: True)
        :param seed: Optional seed for reproducible extraction
        :return: Extracted subset of the dataset
        """
        if shuffle:
            self.shuffle_dataset(seed)

        subset = self.dataset[:n]
        console.print(f"[blue]Extracted {len(subset)} rows from the dataset.[/blue]")
        return subset

    def save_subset(self, n: int, filepath: str, format: str = 'json', shuffle: bool = True, seed: Optional[int] = None) -> None:
        """
        Extracts a subset of the dataset and saves it to a new file.

        :param n: Number of rows to extract
        :param filepath: Path to save the extracted subset
        :param format: Format to save the subset ('json', 'csv', 'parquet', 'xml', 'jsonl', 'excel', 'sqlite')
        :param shuffle: Whether to shuffle before extraction (default: True)
        :param seed: Optional seed for reproducible extraction
        """
        subset = self.extract_subset(n, shuffle, seed)
        try:
            if format == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(subset, f, ensure_ascii=False, indent=2)
            elif format == 'csv':
                df = pd.DataFrame(subset)
                df.to_csv(filepath, index=False, encoding='utf-8')
            elif format == 'parquet':
                df = pd.DataFrame(subset)
                df.to_parquet(filepath, index=False)
            elif format == 'xml':
                root = ET.Element("dataset")
                for item in subset:
                    datapoint = ET.SubElement(root, "datapoint")
                    for key, value in item.items():
                        ET.SubElement(datapoint, key).text = str(value)
                tree = ET.ElementTree(root)
                tree.write(filepath, encoding="utf-8", xml_declaration=True)
            elif format == 'jsonl':
                with open(filepath, 'w', encoding='utf-8') as f:
                    for item in subset:
                        json.dump(item, f, ensure_ascii=False)
                        f.write('\n')
            elif format == 'excel':
                df = pd.DataFrame(subset)
                df.to_excel(filepath, index=False)
            elif format == 'sqlite':
                df = pd.DataFrame(subset)
                df.to_sql('subset', f"sqlite:///{filepath}", index=False, if_exists='replace')
            else:
                console.print(f"[red]Unsupported format: {format}[/red]")
                return
            console.print(f"[blue]Extracted subset saved to {filepath}[/blue]")
        except (IOError, OSError) as e:
            console.print(f"[red]Error writing subset to file {filepath}: {e}[/red]")

    def from_pandas(self, df: pd.DataFrame, append: bool = False) -> None:
        """Loads data from a pandas DataFrame into the dataset."""
        new_data = df.to_dict('records')
        if append:
            self.dataset.extend(new_data)
        else:
            self.dataset = new_data
        self.save_dataset()

    def create_hf_dataset(self) -> DatasetDict:
        """
        Creates a Hugging Face DatasetDict from the current dataset.

        :return: DatasetDict containing the dataset
        """
        full_dataset = Dataset.from_list(self.dataset)
        train_testvalid = full_dataset.train_test_split(test_size=0.2, seed=42)
        test_valid = train_testvalid['test'].train_test_split(test_size=0.5, seed=42)
        return DatasetDict({
            'train': train_testvalid['train'],
            'test': test_valid['test'],
            'validation': test_valid['train']
        })

    def add_chain_of_thought(self, input_key: str, output_key: str, reasoning_key: str = "reasoning") -> None:
        """
        Adds Chain of Thought reasoning to existing data points.
        
        :param input_key: Key containing the input/question
        :param output_key: Key containing the output/answer
        :param reasoning_key: Key to store the reasoning steps
        """
        for item in self.dataset:
            if input_key in item and output_key in item:
                item[reasoning_key] = f"Let's approach this step by step:\n1. Question: {item[input_key]}\n2. Analysis: {item[output_key]}"
        self.save_dataset()
        console.print(f"[green]Added Chain of Thought reasoning to {len(self.dataset)} datapoints.[/green]")

    def validate_data(self, schema: Dict[str, type], required_keys: List[str] = None) -> List[Dict[str, Any]]:
        """
        Validates the dataset against a schema and returns invalid entries.
        
        :param schema: Dictionary mapping keys to their expected types
        :param required_keys: List of keys that must be present
        :return: List of invalid data points
        """
        invalid_entries = []
        for idx, item in enumerate(self.dataset):
            if required_keys and not all(key in item for key in required_keys):
                invalid_entries.append((idx, item, "Missing required keys"))
                continue
            
            for key, expected_type in schema.items():
                if key in item and not isinstance(item[key], expected_type):
                    invalid_entries.append((idx, item, f"Invalid type for {key}"))
        return invalid_entries

    def augment_data(self, augmentation_fn: Callable[[Dict[str, Any]], List[Dict[str, Any]]], 
                    max_augmentations: int = 1) -> None:
        """
        Augments the dataset using a custom augmentation function.
        
        :param augmentation_fn: Function that takes a data point and returns a list of augmented versions
        :param max_augmentations: Maximum number of augmented versions to generate per data point
        """
        augmented_dataset = []
        for item in self.dataset:
            augmented_versions = augmentation_fn(item)[:max_augmentations]
            augmented_dataset.extend(augmented_versions)
        
        self.dataset.extend(augmented_dataset)
        self.save_dataset()
        console.print(f"[green]Added {len(augmented_dataset)} augmented datapoints.[/green]")

    def batch_process(self, batch_size: int, process_fn: Callable[[List[Dict[str, Any]]], None]) -> None:
        """
        Process the dataset in batches for better performance.
        
        :param batch_size: Size of each batch
        :param process_fn: Function to process each batch
        """
        for i in range(0, len(self.dataset), batch_size):
            batch = self.dataset[i:i + batch_size]
            process_fn(batch)

    def deduplicate(self, keys: List[str] = None) -> int:
        """
        Removes duplicate entries from the dataset.
        
        :param keys: List of keys to consider for duplication (if None, considers all keys)
        :return: Number of duplicates removed
        """
        initial_size = len(self.dataset)
        seen = set()
        unique_dataset = []

        for item in self.dataset:
            if keys:
                item_tuple = tuple((k, item[k]) for k in keys if k in item)
            else:
                item_tuple = tuple(sorted(item.items()))
            
            if item_tuple not in seen:
                seen.add(item_tuple)
                unique_dataset.append(item)

        self.dataset = unique_dataset
        self.save_dataset()
        removed = initial_size - len(self.dataset)
        console.print(f"[green]Removed {removed} duplicate entries.[/green]")
        return removed

    def add_metadata(self, metadata_fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """
        Adds metadata to each data point using a custom function.
        
        :param metadata_fn: Function that takes a data point and returns metadata to add
        """
        for item in self.dataset:
            metadata = metadata_fn(item)
            item['metadata'] = metadata
        self.save_dataset()

    def filter_dataset(self, condition_fn: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
        """
        Filters the dataset based on a condition function.
        
        :param condition_fn: Function that takes a data point and returns True/False
        :return: Filtered dataset
        """
        filtered = [item for item in self.dataset if condition_fn(item)]
        return filtered

    def to_huggingface_dataset(self) -> Dataset:
        """
        Converts the dataset to a Hugging Face Dataset format.
        
        :return: Hugging Face Dataset object
        """
        return Dataset.from_list(self.dataset)

    def split_dataset(self, train_ratio: float = 0.8, 
                     val_ratio: float = 0.1, 
                     test_ratio: float = 0.1,
                     shuffle: bool = True) -> DatasetDict:
        """
        Splits the dataset into train, validation, and test sets.
        
        :param train_ratio: Ratio of training data
        :param val_ratio: Ratio of validation data
        :param test_ratio: Ratio of test data
        :param shuffle: Whether to shuffle the data before splitting
        :return: DatasetDict containing the splits
        """
        assert math.isclose(train_ratio + val_ratio + test_ratio, 1.0), "Ratios must sum to 1"
        
        if shuffle:
            dataset_copy = self.dataset.copy()
            random.shuffle(dataset_copy)
        else:
            dataset_copy = self.dataset

        n = len(dataset_copy)
        train_size = int(n * train_ratio)
        val_size = int(n * val_ratio)

        train_data = dataset_copy[:train_size]
        val_data = dataset_copy[train_size:train_size + val_size]
        test_data = dataset_copy[train_size + val_size:]

        return DatasetDict({
            'train': Dataset.from_list(train_data),
            'validation': Dataset.from_list(val_data),
            'test': Dataset.from_list(test_data)
        })

    def split_dataset(self, output_dir: str, rows_per_file: int, file_extension: str = ".json") -> None:
        """Splits the dataset into smaller files with the specified number of rows per file."""
        if not self.dataset:
            console.print("[yellow]Dataset is empty. Nothing to split.[/yellow]")
            return

        os.makedirs(output_dir, exist_ok=True)
        num_files = math.ceil(len(self.dataset) / rows_per_file)
        for i in range(num_files):
            start_index = i * rows_per_file
            end_index = min((i + 1) * rows_per_file, len(self.dataset))
            subset = self.dataset[start_index:end_index]
            filepath = os.path.join(output_dir, f"part_{i + 1}{file_extension}")
            create_dataset_file(filepath, subset)
        console.print(f"[blue]Dataset split into {num_files} files in directory '{output_dir}'.[/blue]")

    def preprocess_text(self, text_key: str, 
                       lowercase: bool = True,
                       remove_special_chars: bool = True,
                       max_length: Optional[int] = None) -> None:
        """
        Preprocesses text data in the dataset.
        
        :param text_key: Key containing text to preprocess
        :param lowercase: Whether to convert text to lowercase
        :param remove_special_chars: Whether to remove special characters
        :param max_length: Maximum length of text (in tokens)
        """
        for item in self.dataset:
            if text_key in item:
                text = item[text_key]
                if lowercase:
                    text = text.lower()
                if remove_special_chars:
                    text = re.sub(r'[^\w\s]', '', text)
                if max_length:
                    words = text.split()[:max_length]
                    text = ' '.join(words)
                item[text_key] = text
        self.save_dataset()

    def balance_dataset(self, label_key: str, strategy: str = 'undersample') -> None:
        """
        Balances the dataset based on class distribution.
        
        :param label_key: Key containing the class labels
        :param strategy: 'undersample' or 'oversample'
        """
        label_counts = Counter(item[label_key] for item in self.dataset if label_key in item)
        if not label_counts:
            return

        if strategy == 'undersample':
            min_count = min(label_counts.values())
            balanced_dataset = []
            for label in label_counts:
                items = [item for item in self.dataset if item.get(label_key) == label]
                balanced_dataset.extend(random.sample(items, min_count))
            self.dataset = balanced_dataset
        elif strategy == 'oversample':
            max_count = max(label_counts.values())
            balanced_dataset = []
            for label in label_counts:
                items = [item for item in self.dataset if item.get(label_key) == label]
                while len(items) < max_count:
                    items.extend(random.sample(items, min(len(items), max_count - len(items))))
                balanced_dataset.extend(items)
            self.dataset = balanced_dataset
        
        self.save_dataset()

    def generate_prompt_variations(self, template_key: str, variables_key: str, num_variations: int = 3) -> None:
        """
        Generates variations of prompts using templates and variables.
        
        :param template_key: Key containing the prompt template
        :param variables_key: Key containing variables to substitute
        :param num_variations: Number of variations to generate per template
        """
        prompt_patterns = [
            "I want you to {action} {subject}",
            "Please {action} the following {subject}",
            "Could you {action} this {subject}",
            "Help me {action} the {subject}",
            "{action} the given {subject}"
        ]

        for item in self.dataset:
            if template_key in item and variables_key in item:
                template = item[template_key]
                variables = item[variables_key]
                variations = []
                
                for _ in range(num_variations):
                    pattern = random.choice(prompt_patterns)
                    variation = pattern.format(**variables)
                    variations.append(variation)
                
                item['prompt_variations'] = variations
        
        self.save_dataset()

    def add_synthetic_data(self, generator_fn: Callable[[], Dict[str, Any]], num_samples: int) -> None:
        """
        Adds synthetic data points generated by a custom function.
        
        :param generator_fn: Function that generates synthetic data points
        :param num_samples: Number of synthetic samples to generate
        """
        synthetic_data = [generator_fn() for _ in range(num_samples)]
        self.dataset.extend(synthetic_data)
        self.save_dataset()
        console.print(f"[green]Added {num_samples} synthetic data points.[/green]")

    def apply_data_augmentation_pipeline(self, text_key: str, augmentation_types: List[str]) -> None:
        """
        Applies a series of text augmentation techniques.
        
        :param text_key: Key containing text to augment
        :param augmentation_types: List of augmentation types to apply
        """
        def synonym_replacement(text: str) -> str:
            words = text.split()
            num_replacements = max(1, len(words) // 10)
            for _ in range(num_replacements):
                idx = random.randint(0, len(words) - 1)
                # Add your synonym replacement logic here
                words[idx] = f"SYNONYM({words[idx]})"
            return ' '.join(words)

        def back_translation(text: str) -> str:
            # Simulate back translation
            return f"BACKTRANSLATED({text})"

        def word_insertion(text: str) -> str:
            words = text.split()
            num_insertions = max(1, len(words) // 10)
            for _ in range(num_insertions):
                idx = random.randint(0, len(words))
                words.insert(idx, "INSERTED_WORD")
            return ' '.join(words)

        augmentation_functions = {
            'synonym': synonym_replacement,
            'backtranslation': back_translation,
            'insertion': word_insertion
        }

        augmented_dataset = []
        for item in self.dataset:
            if text_key in item:
                text = item[text_key]
                for aug_type in augmentation_types:
                    if aug_type in augmentation_functions:
                        augmented_text = augmentation_functions[aug_type](text)
                        augmented_item = item.copy()
                        augmented_item[text_key] = augmented_text
                        augmented_item['augmentation_type'] = aug_type
                        augmented_dataset.append(augmented_item)

        self.dataset.extend(augmented_dataset)
        self.save_dataset()

    def generate_few_shot_examples(self, num_shots: int = 3, shuffle: bool = True) -> List[Dict[str, Any]]:
        """
        Generates few-shot learning examples from the dataset.
        
        :param num_shots: Number of examples per task
        :param shuffle: Whether to shuffle the examples
        :return: List of few-shot examples
        """
        if shuffle:
            examples = random.sample(self.dataset, min(num_shots, len(self.dataset)))
        else:
            examples = self.dataset[:num_shots]
        
        return examples

    def add_quality_metrics(self) -> None:
        """
        Adds quality metrics to each data point.
        """
        for item in self.dataset:
            metrics = {}
            
            # Length-based metrics
            for key, value in item.items():
                if isinstance(value, str):
                    metrics[f'{key}_length'] = len(value.split())
            
            # Complexity metrics
            if 'input' in item and isinstance(item['input'], str):
                metrics['input_complexity'] = len(set(item['input'].split())) / len(item['input'].split()) if item['input'] else 0
            
            # Add more metrics as needed
            item['quality_metrics'] = metrics
        
        self.save_dataset()

    def create_training_pairs(self, input_keys: List[str], output_key: str, 
                            negative_sampling: bool = False) -> List[Dict[str, Any]]:
        """
        Creates training pairs for contrastive learning or similar tasks.
        
        :param input_keys: Keys containing input features
        :param output_key: Key containing target output
        :param negative_sampling: Whether to include negative samples
        :return: List of training pairs
        """
        pairs = []
        for i, item in enumerate(self.dataset):
            pair = {
                'input': {key: item[key] for key in input_keys if key in item},
                'output': item.get(output_key)
            }
            pairs.append(pair)
            
            if negative_sampling:
                # Add negative samples
                neg_idx = random.choice([j for j in range(len(self.dataset)) if j != i])
                neg_pair = {
                    'input': {key: item[key] for key in input_keys if key in item},
                    'output': self.dataset[neg_idx].get(output_key),
                    'is_negative': True
                }
                pairs.append(neg_pair)
        
        return pairs

    def export_for_training(self, export_format: str = 'jsonl', 
                          include_metadata: bool = True,
                          compression: bool = False) -> str:
        """
        Exports the dataset in a format suitable for AI training.
        
        :param export_format: Format to export ('jsonl', 'csv', 'parquet')
        :param include_metadata: Whether to include metadata
        :param compression: Whether to compress the output
        :return: Path to exported file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = f"training_data_{timestamp}"
        
        if export_format == 'jsonl':
            export_path += '.jsonl'
            with open(export_path, 'w', encoding='utf-8') as f:
                for item in self.dataset:
                    if not include_metadata:
                        item = {k: v for k, v in item.items() if not k.startswith('_')}
                    json.dump(item, f)
                    f.write('\n')
        elif export_format == 'csv':
            export_path += '.csv'
            df = pd.DataFrame(self.dataset)
            df.to_csv(export_path, index=False)
        elif export_format == 'parquet':
            export_path += '.parquet'
            df = pd.DataFrame(self.dataset)
            df.to_parquet(export_path, compression='snappy' if compression else None)
        
        if compression and export_format != 'parquet':
            import gzip
            with open(export_path, 'rb') as f_in:
                with gzip.open(f"{export_path}.gz", 'wb') as f_out:
                    f_out.writelines(f_in)
            export_path += '.gz'
        
        return export_path

    def merge_and_create_hf_splits(self, input_dir: str) -> DatasetDict:
        """
        Merges JSON files from the input directory and creates Hugging Face dataset splits.
        
        Args:
            input_dir: Directory containing the JSON files
        
        Returns:
            DatasetDict containing the merged datasets
        """
        # Load all JSON files
        dataset_files = {}
        for filename in os.listdir(input_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(input_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    dataset_files[filename] = json.load(f)
        
        # Create v1 split from dataset.json
        v1_data = dataset_files.get('dataset.json', [])
        v1_dataset = Dataset.from_list(v1_data)
        
        # Create v2 split from dataset2.json
        v2_data = dataset_files.get('dataset2.json', [])
        v2_dataset = Dataset.from_list(v2_data)
        
        # Create DatasetDict with both splits
        dataset_dict = DatasetDict({
            'v1': v1_dataset,
            'v2': v2_dataset
        })
        
        return dataset_dict

if __name__ == "__main__":
    # Create a dataset builder instance
    builder = DatasetBuilder(filepath="merged_dataset.json")
    
    # Merge files and create HF splits
    input_dir = "C:/Users/koula/OneDrive/Desktop/HelpingAI/done"
    dataset_dict = builder.merge_and_create_hf_splits(input_dir)
    
    # Save the splits (optional)
    dataset_dict.save_to_disk("huggingface_dataset")
    print("Dataset splits created successfully!")
