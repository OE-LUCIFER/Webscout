import concurrent.futures
import re
from pathlib import Path
from pprint import pprint
from bs4 import BeautifulSoup
from tiktoken import get_encoding as tiktoken_get_encoding
from DeepWEBS.utilsdw.logger import logger
from markdownify import markdownify
from DeepWEBS.networks.network_configs import IGNORE_TAGS, IGNORE_CLASSES
from termcolor import colored


class WebpageContentExtractor:
    def __init__(self):
        self.tokenizer = tiktoken_get_encoding("cl100k_base")

    def count_tokens(self, text):
        tokens = self.tokenizer.encode(text)
        token_count = len(tokens)
        return token_count

    def html_to_markdown(self, html_str, ignore_links=True):
        if ignore_links:
            markdown_str = markdownify(html_str, strip="a")
        else:
            markdown_str = markdownify(html_str)
        markdown_str = re.sub(r"\n{3,}", "\n\n", markdown_str)

        self.markdown_token_count = self.count_tokens(markdown_str)
        logger.mesg(f'- Tokens: {colored(self.markdown_token_count,"light_green")}')

        self.markdown_str = markdown_str

        return self.markdown_str

    def remove_elements_from_html(self, html_str):
        soup = BeautifulSoup(html_str, "html.parser")
        ignore_classes_with_parentheses = [f"({word})" for word in IGNORE_CLASSES]
        ignore_classes_pattern = f'{"|".join(ignore_classes_with_parentheses)}'
        removed_element_counts = 0
        for element in soup.find_all():
            class_str = ""
            id_str = ""
            try:
                class_attr = element.get("class", [])
                if class_attr:
                    class_str = " ".join(list(class_attr))
                if id_str:
                    class_str = f"{class_str} {id_str}"
            except:
                pass

            try:
                id_str = element.get("id", "")
            except:
                pass

            if (
                (not element.text.strip())
                or (element.name in IGNORE_TAGS)
                or (re.search(ignore_classes_pattern, class_str, flags=re.IGNORECASE))
                or (re.search(ignore_classes_pattern, id_str, flags=re.IGNORECASE))
            ):
                element.decompose()
                removed_element_counts += 1

        logger.mesg(
            f"- Elements: "
            f'{colored(len(soup.find_all()),"light_green")} / {colored(removed_element_counts,"light_red")}'
        )

        html_str = str(soup)
        self.html_str = html_str

        return self.html_str

    def extract(self, html_path):
        logger.note(f"Extracting content from: {html_path}")

        if not Path(html_path).exists():
            logger.warn(f"File not found: {html_path}")
            return ""

        encodings = ["utf-8", "latin-1"]
        for encoding in encodings:
            try:
                with open(html_path, "r", encoding=encoding, errors="ignore") as rf:
                    html_str = rf.read()
                break
            except UnicodeDecodeError:
                pass
        else:
            logger.warn(f"No matching encodings: {html_path}")
            return ""

        html_str = self.remove_elements_from_html(html_str)
        markdown_str = self.html_to_markdown(html_str)
        return markdown_str


class BatchWebpageContentExtractor:
    def __init__(self) -> None:
        self.html_path_and_extracted_content_list = []
        self.done_count = 0

    def extract_single_html(self, html_path):
        webpage_content_extractor = WebpageContentExtractor()
        extracted_content = webpage_content_extractor.extract(html_path)
        self.html_path_and_extracted_content_list.append(
            {"html_path": html_path, "extracted_content": extracted_content}
        )
        self.done_count += 1
        logger.success(
            f"> [{self.done_count}/{self.total_count}] Extracted: {html_path}"
        )

    def extract(self, html_paths):
        self.html_path = html_paths
        self.total_count = len(self.html_path)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.extract_single_html, html_path)
                for html_path in self.html_path
            ]
            for idx, future in enumerate(concurrent.futures.as_completed(futures)):
                result = future.result()

        return self.html_path_and_extracted_content_list


if __name__ == "__main__":
    html_root = Path(__file__).parents[1] / "files" / "urls" / "python tutorials"
    html_paths = [
        html_root / html_filename
        for html_filename in [
            "docs.python.org_zh-cn_3_tutorial_interpreter.html",
            "stackoverflow.com_questions_295135_turn-a-string-into-a-valid-filename.html",
            "www.liaoxuefeng.com_wiki_1016959663602400_1017495723838528.html",
        ]
    ]
    batch_webpage_content_extractor = BatchWebpageContentExtractor()
    html_path_and_extracted_content_list = batch_webpage_content_extractor.extract(
        html_paths
    )
    # pprint(html_path_and_extracted_content_list)
