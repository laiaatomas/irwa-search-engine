import pandas as pd
from .algorithm_functions import build_terms, create_index_tfidf, create_index_bm25, rank_products_tfidf, rank_products_bm25#, rank_products_ourscore
import dill
import os
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env

# so index is read only once
TFIDF_INDEX = None
BM25_INDEX = None

def build_tfidf_index(corpus):
    """
    Convert corpus (dict of Document objects) into a DataFrame
    and build the TF-IDF inverted index.
    """
    products = []
    for pid, doc in corpus.items():
        products.append({
            "pid": pid,
            "title": doc.title,
            "description": doc.description,
            "title_clean": build_terms(doc.title),
            "description_clean": build_terms(doc.description)
        })

    df = pd.DataFrame(products)
    num_products = len(df)

    index, tf, dfreq, idf, title_index, desc_index = create_index_tfidf(df, num_products)

    return {
        "index": index,
        "tf": tf,
        "df": dfreq,
        "idf": idf,
        "title_index": title_index,
        "desc_index": desc_index,
        "df": df
    }

def build_bm25_index(corpus):
    """
    Convert corpus (dict of Document objects) into a DataFrame
    and build the TF-IDF inverted index.
    """
    products = []
    for pid, doc in corpus.items():
        products.append({
            "pid": pid,
            "title": doc.title,
            "description": doc.description,
            "title_clean": build_terms(doc.title),
            "description_clean": build_terms(doc.description)
        })

    df = pd.DataFrame(products)
    num_products = len(df)

    index, tf, df, idf, title_index, desc_index, doc_len, L_ave = create_index_bm25(df, num_products)

    return {
        "index": index,
        "tf": tf,
        "df": df,
        "idf": idf,
        "title_index": title_index,
        "desc_index": desc_index,
        "df": df,
        "doc_len": doc_len,
        "L_ave": L_ave
    }

def search_in_corpus(algorithm, query, corpus):
    global TFIDF_INDEX
    global BM25_INDEX
    # If first call → build the TF-IDF index
    if TFIDF_INDEX is None and (algorithm=='tfidf' or algorithm=='tfidf-or'):
        print("Opening TF-IDF index...")
        full_path = os.path.realpath(__file__)
        path, filename = os.path.split(full_path)
        file_path = path + "/tfidf_index.dill"

        with open(file_path, "rb") as f:
            TFIDF_INDEX = dill.load(f)
        print("TF-IDF index opened.")
    
    elif BM25_INDEX is None and (algorithm=='bm25' or algorithm=='bm25-or'): 
        print("Opening BM25 index...")
        full_path = os.path.realpath(__file__)
        path, filename = os.path.split(full_path)
        file_path = path + "/bm25_index.dill"

        with open(file_path, "rb") as f:
            BM25_INDEX = dill.load(f)
        print("BM25 index opened.")

    index = BM25_INDEX if BM25_INDEX is not None else TFIDF_INDEX

    query = build_terms(query)  # so that stemmed terms are matched in the index

    # conjunctive query
    if algorithm == 'tfidf' or algorithm =='bm25':
        products = None  # start with None to handle first term properly

        for term in query:
            try:
                term_products = set(index["index"][term].keys())  # products containing this term (either index is fine because they have the same keys)

                if products is None:
                    products = term_products  # initialize with first term's product
                else:
                    products &= term_products  # intersection with the next term’s product

            except:
                # if a term isn't in the index, then no product contains ALL terms
                return []
        if not products:  # catches None or empty set
            return [], []
        products = list(products)

    # OR query (products that contain at least 1 term of the query)
    elif algorithm == 'tfidf-or' or algorithm == 'bm25-or':
        products = set()  # start with None to handle first term properly

        for term in query:
            try:
                term_products = set(index["index"][term].keys())  # products containing this term (either index is fine because they have the same keys)

                products |= term_products
            except:
                # if a term isn't in the index
                pass
        if not products:  # catches None or empty set
            return [], []
        products = list(products)

    if algorithm == 'tfidf' or algorithm == 'tfidf-or':
        ranked_products, product_scores = rank_products_tfidf(query, products, TFIDF_INDEX["index"], TFIDF_INDEX["idf"], TFIDF_INDEX["tf"], TFIDF_INDEX["title_index"])
    elif algorithm == 'bm25' or algorithm == 'bm25-or':
        ranked_products, product_scores = rank_products_bm25(query, products, BM25_INDEX["index"], BM25_INDEX["idf"], BM25_INDEX["tf"], BM25_INDEX["doc_len"], BM25_INDEX['L_ave'], k1=1.2, b=0.75)

    return ranked_products, product_scores
