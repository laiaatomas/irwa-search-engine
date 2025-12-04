import math
import string
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import re
import numpy as np
from collections import defaultdict
import collections
from numpy import linalg as la

def build_terms(text):

    #check that the text is a string
    if not isinstance(text, str):
        return []

    #keep only any word character or spaces (remove special characters and numbers) (includes removing punctuation marks)
    text = re.sub(r'[^a-z\s]', '', text.lower()) 

    #tokenize text to a list of tokens
    tokens = text.split()

    #remove stop words
    stop_words = set(stopwords.words('english'))
    text = [word for word in tokens if word not in stop_words and len(word) > 2] #keep only words of length 3 minimum

    #apply stemming
    stemmer = PorterStemmer()
    text=[stemmer.stem(word) for word in text]

    return text


def create_index_tfidf(products_df, num_products):
    """
    Implement the inverted index and compute tf, df and idf

    Argument:
    lines -- collection of Wikipedia articles
    num_documents -- total number of documents

    Returns:
    index - the inverted index (implemented through a Python dictionary) containing terms as keys and the corresponding
    list of document these keys appears in (and the positions) as values.
    tf - normalized term frequency for each term in each document
    df - number of documents each term appear in
    idf - inverse document frequency of each term
    """

    index = defaultdict(lambda: defaultdict(lambda: 0))
    tf = defaultdict(list)  #term frequencies of terms in documents (documents in the same order as in the main index)
    df = defaultdict(int)  #document frequencies of terms in the corpus
    title_index = defaultdict(str)
    desc_index = defaultdict(str)
    idf = defaultdict(float)

    for _, line in products_df.iterrows():

        pid = line['pid']
        terms = line['title_clean'] + line['description_clean']

        title = line['title']
        desc = line['description']
        title_index[pid] = title  ## we do not need to apply get terms to title because it used only to print titles and not in the index
        desc_index[pid] = desc

        current_product_terms = defaultdict(lambda: 0)
        for term in terms:
            current_product_terms[term] += 1
            index[term][pid] += 1


        # normalize term frequencies
        # Compute the denominator to normalize term frequencies (formula 2 above)
        # norm is the same for all terms of a document.
        norm = 0
        for freq in current_product_terms.values():
            # posting will contain the list of positions for current term in current document.
            # posting ==> [current_doc, [list of positions]]
            # you can use it to infer the frequency of current term.
            norm += freq ** 2
        norm = math.sqrt(norm)

        #calculate the tf(dividing the term frequency by the above computed norm) and df weights
        for term, freq in current_product_terms.items():
            # append the tf for current term (tf = term frequency in current doc/norm)
            tf[term].append(np.round(freq / norm, 4)) ## SEE formula (1) above
            #increment the document frequency of current term (number of documents containing the current term)
            df[term] += 1 # increment DF for current term


    # Compute IDF following the formula (3) above. HINT: use np.log
    # Note: It is computed later after we know the df.
    for term in df:
        idf[term] = np.round(np.log(float(num_products / df[term])), 4)


    return index, tf, df, idf, title_index, desc_index


def rank_products_tfidf(terms, pids, index, idf, tf, title_index):
    """
    Perform the ranking of the results of a search based on the tf-idf weights

    Argument:
    terms -- list of query terms
    pids -- list of products, to rank, matching the query
    index -- inverted index data structure
    idf -- inverted document frequencies
    tf -- term frequencies
    title_index -- mapping between page id and page title

    Returns:
    Print the list of ranked product
    """

    # I'm interested only on the element of the productVector corresponding to the query terms
    # The remaining elements would become 0 when multiplied to the query_vector
    products_vectors = defaultdict(lambda: [0] * len(terms)) # I call doc_vectors[k] for a nonexistent key k, the key-value pair (k,[0]*len(terms)) will be automatically added to the dictionary
    query_vector = [0] * len(terms)

    # compute the norm for the query tf
    query_terms_count = collections.Counter(terms)  # get the frequency of each term in the query.
    query_norm = la.norm(list(query_terms_count.values()))

    for termIndex, term in enumerate(terms):  #termIndex is the index of the term in the query
        if term not in index:
            continue

        ## Compute tf*idf(normalize TF as done with products)
        query_vector[termIndex] = query_terms_count[term] / query_norm * idf[term]

        # Generate product_vectors for matching products
        for pid_index, pid in enumerate(index[term].keys()):
            # Example of pid_index, pid
            # 0 JEAFNHERP6UHRQKH
            # 1 JEAFNHERJGTGQ4GP

            #tf[term][0] will contain the tf of the term "term" in the product JEAFNHERP6UHRQKH 
            if pid in pids:
                products_vectors[pid][termIndex] = tf[term][pid_index] * idf[term]  

    # Calculate the score of each product
    # compute the cosine similarity between queyVector and each productVector:

    products_scores = [[product, np.dot(curProdVec, query_vector)] for product, curProdVec in products_vectors.items()]
    products_scores.sort(reverse=True)
    result_products = [x[1] for x in products_scores]
    #print product titles instead if product id's
    #result_products=[ title_index[x] for x in result_products ]
    if len(result_products) == 0:
        print("No results found, try again")
        # query = input()
        # products = search_tf_idf(query, index)
    #print ('\n'.join(result_products), '\n')
    return result_products, products_scores



def create_index_bm25(products_df, num_products):
    """
    Implement the inverted index and compute tf, df and idf

    Argument:
    lines -- collection of Wikipedia articles
    num_documents -- total number of documents

    Returns:
    index - the inverted index (implemented through a Python dictionary) containing terms as keys and the corresponding
    list of document these keys appears in (and the positions) as values.
    tf - normalized term frequency for each term in each document
    df - number of documents each term appear in
    idf - inverse document frequency of each term
    """

    index = defaultdict(lambda: defaultdict(lambda: 0))
    tf = defaultdict(dict)  # term raw frequencies: tf[term][pid] = freq
    df = defaultdict(int)  # document frequencies of terms in the corpus
    title_index = defaultdict(str)
    desc_index = defaultdict(str)
    idf = defaultdict(float)
    doc_len = defaultdict(float) # dict of pid and document length

    for _, line in products_df.iterrows():

        pid = line['pid']
        terms = line['title_clean'] + line['description_clean']

        title = line['title']
        desc = line['description']
        title_index[pid] = title  ## we do not need to apply get terms to title because it used only to print titles and not in the index
        desc_index[pid] = desc

        doc_len[pid] = len(terms) # (product length after removing stopwords)

        current_product_terms = defaultdict(lambda: 0)
        for term in terms:
            current_product_terms[term] += 1
            index[term][pid] += 1

        # term raw frequencies 
        for term, freq in current_product_terms.items():
            tf[term][pid] = freq 
            #increment the document frequency of current term (number of documents containing the current term)
            df[term] += 1 # increment DF for current term


    # Compute IDF 
    for term in df:
        idf[term] = np.round(np.log(float(num_products / df[term])), 4)

    L_ave = 0
    for pid in doc_len.keys():
        L_ave += doc_len[pid]
    L_ave /= len(doc_len)

    return index, tf, df, idf, title_index, desc_index, doc_len, L_ave


def rank_products_bm25(terms, pids, index, idf, tf, doc_len, L_ave, k1, b):
    """
    Perform the ranking of the results of a search based on the tf-idf weights

    Argument:
    terms -- list of query terms
    pids -- list of products, to rank, matching the query
    index -- inverted index data structure
    idf -- inverted document frequencies
    tf -- term raw frequencies for a given product
    doc_len -- dictionary of product id: length of title + description
    L_ave -- average length of all products

    Returns:
    Print the list of ranked product
    """

    rsv_product = defaultdict(float)
    
    for pid in pids:
        for termIndex, term in enumerate(terms):  #termIndex is the index of the term in the query
            if term not in index:
                continue
            
            tf_ij = tf[term].get(pid, 0)  # <-- SAFE TF lookup

            if tf_ij == 0:
                continue  # term not in this product → skip

            # Calculate the score of each product
            # sum for term in query: idf * formula
            numerator = (k1 + 1) * tf_ij
            denominator = k1 * ((1 - b) + b *(doc_len[pid]/L_ave)) + tf_ij
            rsv_product[pid] += idf[term] * numerator / denominator
    
    sorted_rsv = sorted(rsv_product.items(), key=lambda x: x[1], reverse=True)

    result_products = [x[0] for x in sorted_rsv]
    #products_scores = [x[1] for x in sorted_rsv]
    if len(sorted_rsv) == 0:
        print("No results found, try again")

    return result_products, sorted_rsv

