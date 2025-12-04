from myapp.search.load_corpus import load_corpus
from myapp.search.algorithms import build_tfidf_index, build_bm25_index
import os
import dill
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env

def main():
    file_path = os.getenv("DATA_FILE_PATH")
    corpus = load_corpus(file_path)

    tfidf_index = build_tfidf_index(corpus)
    bm25_index = build_bm25_index(corpus)

    full_path = os.path.realpath(__file__)
    save_path, filename = os.path.split(full_path)

    save_path_tfidf = os.path.join(save_path, "tfidf_index.dill")
    save_path_bm25 = os.path.join(save_path, "bm25_index.dill")

    # Save to disk
    with open(save_path_tfidf, "wb") as f:
        dill.dump(tfidf_index, f)
    print("TF-IDF index precomputed and saved to tfidf_index.dill")

    with open(save_path_bm25, "wb") as f:
        dill.dump(bm25_index, f)
    print("BM25 index precomputed and saved to bm25_index.dill")

if __name__ == '__main__':
    main()