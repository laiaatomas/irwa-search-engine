import json
import random
import altair as alt
import pandas as pd
from collections import defaultdict

class AnalyticsData:
    """
    An in memory persistence object.
    Declare more variables to hold analytics tables.
    """
    # 1. For HTTPS 
    # Example of statistics table
    # fact_clicks is a dictionary with the click counters: key = doc id | value = click counter
    fact_clicks = dict([])

    http_requests = defaultdict(list) # : Dict[str, List[Dict]]
    sessions = {} # : Dict[str, Dict] 

    # 2. For queries
    query_counter = 0
    fact_queries = {} # dict where key: query_id, value: [terms, number terms, # order??]

    # 3. For results (documents): query_id -> [ClickedDoc]
    fact_doc_clicks = defaultdict(list)

    ### Please add your custom tables here:

    def save_query_terms(self, terms: str) -> int:
        self.query_counter += 1  
        self.fact_queries[self.query_counter] = [terms, len(terms)]        
        print(self)
        return random.randint(0, 100000)
    
    def click_document(self, doc_id, query_id, rank):
        self.fact_clicks[doc_id] += 1
        doc = ClickedDoc(doc_id=doc_id, description='', counter=self.fact_clicks[doc_id])
        self.fact_doc_clicks[query_id].append(doc)

    def plot_number_of_views(self):
        # Prepare data
        data = [{'Document ID': doc_id, 'Number of Views': count} for doc_id, count in self.fact_clicks.items()]
        df = pd.DataFrame(data)
        # Create Altair chart
        chart = alt.Chart(df).mark_bar().encode(
            x='Document ID',
            y='Number of Views'
        ).properties(
            title='Number of Views per Document'
        )
        # Render the chart to HTML
        return chart.to_html()


class ClickedDoc:
    def __init__(self, doc_id, description, counter):
        self.doc_id = doc_id
        self.description = description
        self.counter = counter

    def to_json(self):
        return self.__dict__

    def __str__(self):
        """
        Print the object content as a JSON string
        """
        return json.dumps(self)
