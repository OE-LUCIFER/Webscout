from bs4 import BeautifulSoup
from pathlib import Path
from DeepWEBS.utilsdw.logger import logger


class QueryResultsExtractor:
    def __init__(self) -> None:
        self.query_results = []
        self.related_questions = []

    def load_html(self, html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        self.soup = BeautifulSoup(html, "html.parser")

    def extract_query_results(self):
        self.query = self.soup.find("textarea").text.strip()
        query_result_elements = self.soup.find_all("div", class_="g")
        for idx, result in enumerate(query_result_elements):
            site = result.find("cite").find_previous("span").text.strip()
            url = result.find("a")["href"]
            title = result.find("h3").text.strip()

            abstract_element_conditions = [
                {"data-sncf": "1"},
                {"class_": "ITZIwc"},
            ]
            for condition in abstract_element_conditions:
                abstract_element = result.find("div", condition)
                if abstract_element is not None:
                    abstract = abstract_element.text.strip()
                    break
            else:
                abstract = ""

            logger.mesg(
                f"{title}\n" f"  - {site}\n" f"  - {url}\n" f"  - {abstract}\n" f"\n"
            )
            self.query_results.append(
                {
                    "title": title,
                    "site": site,
                    "url": url,
                    "abstract": abstract,
                    "index": idx,
                    "type": "web",
                }
            )
        logger.success(f"- {len(query_result_elements)} query results")

    def extract_related_questions(self):
        related_question_elements = self.soup.find_all(
            "div", class_="related-question-pair"
        )
        for question_element in related_question_elements:
            question = question_element.find("span").text.strip()
            print(question)
            self.related_questions.append(question)
        logger.success(f"- {len(self.related_questions)} related questions")

    def extract(self, html_path):
        self.load_html(html_path)
        self.extract_query_results()
        self.extract_related_questions()
        self.search_results = {
            "query": self.query,
            "query_results": self.query_results,
            "related_questions": self.related_questions,
        }
        return self.search_results


if __name__ == "__main__":
    html_path_root = Path(__file__).parents[1] / "files"
    html_filename = "python_tutorials"
    html_path = html_path_root / f"{html_filename}.html"
    extractor = QueryResultsExtractor()
    extractor.extract(html_path)
