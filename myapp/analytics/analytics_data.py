import json
import random
import altair as alt
import pandas as pd
import time
from datetime import datetime
from collections import Counter


class AnalyticsData:
    """
    An in memory persistence object.
    Declare more variables to hold analytics tables.
    """
    # Example of statistics table
    # fact_clicks is a dictionary with the click counters: key = doc id | value = click counter
    fact_clicks = dict([])

    ### Please add your custom tables here:
    
    # -------------------------
    # Session table
    # -------------------------
    # key = session_id, value = session info
    sessions = {} 

    # -------------------------
    # Clicks Table
    # -------------------------
    # each row is a dict
    clicks = [] 

    # -------------------------
    # Requests Table
    # -------------------------
    # each row is a dict
    requests = [] 



    def create_session(self, session_id, user_agent, user_ip, agent, ip_country, ip_city):
        self.sessions[session_id] = {
            "session_id": session_id,
            "user_agent": user_agent,
            "browser": agent.get("browser", {}).get("name"),
            "platform": agent.get("platform", {}).get("name"),
            "is_bot": "Bot" if agent.get("bot") else "Not bot",
            "os": agent.get("os", {}).get("name"),
            "date": datetime.now().date(),
            "time_of_day": datetime.now().time(),
            "ip_address": user_ip,
            "ip_country": ip_country,
            "ip_city": ip_city,
            "start_time": time.time() # to compute session duration
        }


    # add entry to clicks table
    def log_click(self, session_id, search_id, query, doc_id, results, algorithm, rank = None):
        self.clicks.append({
            "session_id": session_id,
            "search_id": search_id,
            "query": query,
            "nterms_query": len(query.split()),
            "doc_id": doc_id,
            "rank": rank,
            "timestamp": time.time(),
            "date": datetime.now().date(),
            "time_of_day": datetime.now().time(),
            "dwell_time": None,  # can be updated later
            "top20_results": results, # pids of top 20 results (order in statement)
            "algorithm": algorithm
        })
  

    # add entry in requests table
    def log_request(self, session_id, path, method):
        self.requests.append({
            "session_id": session_id,
            "path": path,
            "method": method,
            "timestamp": time.time(),
            "date": datetime.now().date(),
            "time_of_day": datetime.now().time()
        })


    def update_dwell_time(self, doc_id):
        for click in self.clicks:
            if click["doc_id"] == doc_id:
                click["dwell_time"] = time.time() - click["timestamp"]
                break


    def save_query_terms(self, terms: str) -> int:
        print(self)
        return random.randint(0, 100000)
    
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
   
    def plot_query_frequency(self):
        df = pd.DataFrame(self.clicks)
        df_grouped = df.groupby(['search_id', 'query']).size().reset_index(name='Query frequency')

        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='query',
            y='Query frequency'
        ).properties(
            title='Number of searched queries'
        )
        return chart.to_html()
    
    def distribution_rank_clicked_docs(self):
        df = pd.DataFrame(self.clicks)
        df_grouped = df.groupby(['rank']).size().reset_index(name='Number of clicks')
        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='rank',
            y='Number of clicks'
        ).properties(
            title='Rank click distribution'
        )
        return chart.to_html()
    
    def plot_hourly_usage_distribution(self):
        df = pd.DataFrame(self.requests)
        df['hour'] = df['time_of_day'].apply(lambda x: x.hour)
        df_grouped = df.groupby(['hour']).size().reset_index(name='Number of requests')
        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='hour',
            y='Number of requests'
        ).properties(
            title='Hourly usage distribution'
        )
        return chart.to_html()
    
    def plot_browser_distribution(self):
        data = [row for session_id, row in self.sessions.items()]
        df = pd.DataFrame(data)
        df_grouped = df.groupby('browser').size().reset_index(name='Number of sessions')
        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='browser',
            y='Number of sessions'
        ).properties(
            title='Number of sessions by browser'
        )
        return chart.to_html()
    
    def plot_os_distribution(self):
        data = [row for session_id, row in self.sessions.items()]
        df = pd.DataFrame(data)
        df_grouped = df.groupby('os').size().reset_index(name='Number of sessions')
        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='os',
            y='Number of sessions'
        ).properties(
            title='Number of sessions by OS'
        )
        return chart.to_html()
    
    def plot_platform_distribution(self):
        data = [row for session_id, row in self.sessions.items()]
        df = pd.DataFrame(data)
        df_grouped = df.groupby('platform').size().reset_index(name='Number of sessions')
        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='platform',
            y='Number of sessions'
        ).properties(
            title='Number of sessions by Platform'
        )
        return chart.to_html()
    
    def plot_bot_distribution(self):
        data = [row for session_id, row in self.sessions.items()]
        df = pd.DataFrame(data)
        df_grouped = df.groupby('is_bot').size().reset_index(name='Number of sessions')
        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='is_bot',
            y='Number of sessions'
        ).properties(
            title='Number sessions per bot type'
        )
        return chart.to_html()
    
    def plot_ip_country_distribution(self):
        data = [row for session_id, row in self.sessions.items()]
        df = pd.DataFrame(data)
        df_grouped = df.groupby('ip_country').size().reset_index(name='Number of sessions')
        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='ip_country',
            y='Number of sessions'
        ).properties(
            title='Number sessions per country'
        )
        return chart.to_html()
        
    def plot_ip_city_distribution(self):
        data = [row for session_id, row in self.sessions.items()]
        df = pd.DataFrame(data)
        df_grouped = df.groupby('ip_city').size().reset_index(name='Number of sessions')
        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='ip_city',
            y='Number of sessions'
        ).properties(
            title='Number sessions per city'
        )
        return chart.to_html()
    
    def get_term_frequencies(self):
        terms = []
        df = pd.DataFrame(self.clicks)
        search_ids = df['search_id'].unique()

        for sid in search_ids:
            query = df[df['search_id']==sid]['query'].iloc[0]
            terms.extend(query.split())

        freq = Counter(terms)
        top10_freq = freq.most_common(10)
        return top10_freq
    
    def plot_average_dwell_time_by_rank(self):
        df = pd.DataFrame(self.clicks)
        df_grouped = df.groupby('rank')['dwell_time'].mean().reset_index(name='Average dwell time')
        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='rank',
            y='Average dwell time'
        ).properties(
            title='Average dwell time by rank'
        )
        return chart.to_html()

    def plot_requests_by_method(self):
        df = pd.DataFrame(self.requests)
        df_grouped = df.groupby('method').size().reset_index(name='Number of requests')
        chart = alt.Chart(df_grouped).mark_bar().encode(
            x='method',
            y='Number of requests'
        ).properties(
            title='Requests type distribution'
        )
        return chart.to_html()
    
    def get_average_session_duration(self):
        data = [row for session_id, row in self.sessions.items()]
        df = pd.DataFrame(data)
        df['session_duration'] = df['start_time'].apply(lambda x: time.time() - x)
        return df['session_duration'].mean()

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
