import random
import numpy as np

from myapp.search.objects import Document, ResultItem
from myapp.search.algorithms import search_in_corpus

def dummy_search(corpus: dict, search_id, num_results=20):
    """
    Just a demo method, that returns random <num_results> documents from the corpus
    :param corpus: the documents corpus
    :param search_id: the search id
    :param num_results: number of documents to return
    :return: a list of random documents from the corpus
    """
    res = []
    doc_ids = list(corpus.keys())
    docs_to_return = np.random.choice(doc_ids, size=num_results, replace=False)
    for doc_id in docs_to_return:
        doc = corpus[doc_id]
        res.append(Document(pid=doc.pid, title=doc.title, description=doc.description,
                            url="doc_details?pid={}&search_id={}&param2=2".format(doc.pid, search_id), ranking=random.random()))
    return res

def algorithm_search(algorithm, search_query, search_id, corpus):

    ranked_pids, scores = search_in_corpus(algorithm, search_query, corpus)
    results = []
    for pid, score in scores:
        doc = corpus[pid]

        results.append(ResultItem(
            pid=doc.pid,
            title=doc.title,
            description=doc.description,
            url=f"doc_details?pid={doc.pid}&search_id={search_id}",
            ranking=float(score),  
            selling_price=doc.selling_price,
            discount=doc.discount,
            average_rating=doc.average_rating,
            product_url=doc.url
        ))

    return results


class SearchEngine:
    """Class that implements the search engine logic"""

    def search(self, algorithm, search_query, search_id, corpus):
        print("Search query:", search_query)

        results = []
        ### You should implement your search logic here:
        results = algorithm_search(algorithm, search_query, search_id, corpus)

        # results = search_in_corpus(search_query)
        return results
