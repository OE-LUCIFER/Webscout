
from pydantic import BaseModel, Field
from typing import Union

from DeepWEBS.utilsdw.logger import logger
from DeepWEBS.networks.google_searcher import GoogleSearcher
from DeepWEBS.networks.webpage_fetcher import BatchWebpageFetcher
from DeepWEBS.documents.query_results_extractor import QueryResultsExtractor
from DeepWEBS.documents.webpage_content_extractor import BatchWebpageContentExtractor
from DeepWEBS.utilsdw.logger import logger
import argparse

class DeepWEBS:
    def __init__(self):
        pass

    class DeepSearch(BaseModel):
        queries: list = Field(
            default=[""],
            description="(list[str]) Queries to search",
        )
        result_num: int = Field(
            default=10,
            description="(int) Number of search results",
        )
        safe: bool = Field(
            default=False,
            description="(bool) Enable SafeSearch",
        )
        types: list = Field(
            default=["web"],
            description="(list[str]) Types of search results: `web`, `image`, `videos`, `news`",
        )
        extract_webpage: bool = Field(
            default=False,
            description="(bool) Enable extracting main text contents from webpage, will add `text` filed in each `query_result` dict",
        )
        overwrite_query_html: bool = Field(
            default=False,
            description="(bool) Overwrite HTML file of query results",
        )
        overwrite_webpage_html: bool = Field(
            default=False,
            description="(bool) Overwrite HTML files of webpages from query results",
        )

    def queries_to_search_results(self, item: DeepSearch):
        google_searcher = GoogleSearcher()
        queries_search_results = []
        for query in item.queries:
            query_results_extractor = QueryResultsExtractor()
            if not query.strip():
                continue
            try:
                query_html_path = google_searcher.search(
                    query=query,
                    result_num=item.result_num,
                    safe=item.safe,
                    overwrite=item.overwrite_query_html,
                )
            except Exception as e:
                logger.error(f"Failed to search for query '{query}': {e}")
                continue

            try:
                query_search_results = query_results_extractor.extract(query_html_path)
            except Exception as e:
                logger.error(f"Failed to extract search results for query '{query}': {e}")
                continue

            queries_search_results.append(query_search_results)
        logger.note(queries_search_results)

        if item.extract_webpage:
            queries_search_results = self.extract_webpages(
                queries_search_results,
                overwrite_webpage_html=item.overwrite_webpage_html,
            )
        return queries_search_results

    def extract_webpages(self, queries_search_results, overwrite_webpage_html=False):
        for query_idx, query_search_results in enumerate(queries_search_results):
            try:
                # Fetch webpages with urls
                batch_webpage_fetcher = BatchWebpageFetcher()
                urls = [
                    query_result["url"]
                    for query_result in query_search_results["query_results"]
                ]
                url_and_html_path_list = batch_webpage_fetcher.fetch(
                    urls,
                    overwrite=overwrite_webpage_html,
                    output_parent=query_search_results["query"],
                )
            except Exception as e:
                logger.error(f"Failed to fetch webpages for query '{query_search_results['query']}': {e}")
                continue

            # Extract webpage contents from htmls
            html_paths = [
                str(url_and_html_path["html_path"])
                for url_and_html_path in url_and_html_path_list
            ]
            batch_webpage_content_extractor = BatchWebpageContentExtractor()
            try:
                html_path_and_extracted_content_list = (
                    batch_webpage_content_extractor.extract(html_paths)
                )
            except Exception as e:
                logger.error(f"Failed to extract webpage contents for query '{query_search_results['query']}': {e}")
                continue

            # Build the map of url to extracted_content
            html_path_to_url_dict = {
                str(url_and_html_path["html_path"]): url_and_html_path["url"]
                for url_and_html_path in url_and_html_path_list
            }
            url_to_extracted_content_dict = {
                html_path_to_url_dict[
                    html_path_and_extracted_content["html_path"]
                ]: html_path_and_extracted_content["extracted_content"]
                for html_path_and_extracted_content in html_path_and_extracted_content_list
            }

            # Write extracted contents (as 'text' field) to query_search_results
            for query_result_idx, query_result in enumerate(
                query_search_results["query_results"]
            ):
                url = query_result["url"]
                extracted_content = url_to_extracted_content_dict.get(url, "")
                queries_search_results[query_idx]["query_results"][query_result_idx][
                    "text"
                ] = extracted_content

        return queries_search_results


class ArgParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(ArgParser, self).__init__(*args, **kwargs)

        self.add_argument(
            "-q",
            "--queries",
            type=str,
            nargs="+",
            required=True,
            help="Queries to search",
        )
        self.add_argument(
            "-n",
            "--result_num",
            type=int,
            default=10,
            help="Number of search results",
        )
        self.add_argument(
            "-s",
            "--safe",
            default=False,
            action="store_true",
            help="Enable SafeSearch",
        )
        self.add_argument(
            "-t",
            "--types",
            type=str,
            nargs="+",
            default=["web"],
            choices=["web", "image", "videos", "news"],
            help="Types of search results",
        )
        self.add_argument(
            "-e",
            "--extract_webpage",
            default=False,
            action="store_true",
            help="Enable extracting main text contents from webpage",
        )
        self.add_argument(
            "-o",
            "--overwrite_query_html",
            default=False,
            action="store_true",
            help="Overwrite HTML file of query results",
        )
        self.add_argument(
            "-w",
            "--overwrite_webpage_html",
            default=False,
            action="store_true",
            help="Overwrite HTML files of webpages from query results",
        )

        self.args = self.parse_args()


