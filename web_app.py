import os
from json import JSONEncoder

import httpagentparser  # for getting the user agent as json
from flask import Flask, render_template, session
from flask import request

from myapp.analytics.analytics_data import AnalyticsData, ClickedDoc
from myapp.search.load_corpus import load_corpus
from myapp.search.objects import Document, StatsDocument, ResultItem
from myapp.search.search_engine import SearchEngine
from myapp.search.build_index import main
from myapp.generation.rag import RAGGenerator
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env

import uuid
import geoip2.database


geo_reader = geoip2.database.Reader('geo2ip/GeoLite2-City.mmdb') # for ips

TFIDF_PATH = "myapp/search/tfidf_index.dill"
BM25_PATH = "myapp/search/bm25_index.dill"

# execute code to create index and store in search/ as .dill only if they don't exist already
if not (os.path.exists(TFIDF_PATH) and os.path.exists(BM25_PATH)):
    print("Indexes not found. Building index...")
    main()
    print("Indexes built!")
else:
    print("Indexes already exist. Skipping build.")

# *** for using method to_json in objects ***
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)
_default.default = JSONEncoder().default
JSONEncoder.default = _default
# end lines ***for using method to_json in objects ***


# instantiate the Flask application
app = Flask(__name__)

# random 'secret_key' is used for persisting data in secure cookie
app.secret_key = os.getenv("SECRET_KEY")
# open browser dev tool to see the cookies
app.session_cookie_name = os.getenv("SESSION_COOKIE_NAME")
# instantiate our search engine
search_engine = SearchEngine()
# instantiate our in memory persistence
analytics_data = AnalyticsData()
# instantiate RAG generator
rag_generator = RAGGenerator()

# load documents corpus into memory.
full_path = os.path.realpath(__file__)
path, filename = os.path.split(full_path)
file_path = path + "/" + os.getenv("DATA_FILE_PATH")
corpus = load_corpus(file_path)
# Log first element of corpus to verify it loaded correctly:
#print("\nCorpus is loaded... \n First element:\n", list(corpus.values())[0])


# Home URL "/"
@app.route('/')
def index():

    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())


    # call to analytics_data log request
    analytics_data.log_request(session_id=session['session_id'], path=request.path, method=request.method)

    print("starting home url /...")

    # flask server creates a session by persisting a cookie in the user's browser.
    # the 'session' object keeps data between multiple requests. Example:
    session['some_var'] = "Some value that is kept in session"

    user_agent = request.headers.get('User-Agent')
    print("Raw user browser:", user_agent)

    user_ip = request.remote_addr
    agent = httpagentparser.detect(user_agent)

    print("Remote IP: {} - JSON user browser {}".format(user_ip, agent))
    print(session)

    # as ip is localhost here, we define "176.107.185.203" as demonstration
    user_ip_demonstration = "176.107.185.203"
    try:
        response = geo_reader.city(user_ip_demonstration)
        country = response.country.name
        city = response.city.name
    except Exception:
        country = None
        city = None

    # call to analytics_data.create_session() to store session in sessions table
    session_id = session['session_id']
    analytics_data.create_session(session_id=session_id, user_agent=user_agent, user_ip=user_ip_demonstration, agent=agent, ip_country=country, ip_city=city)

    return render_template('index.html', page_title="Welcome")


@app.route('/search', methods=['POST', 'GET'])
def search_form_post():

    # call to analytics_data log request
    analytics_data.log_request(session_id=session['session_id'], path=request.path, method=request.method)

    if request.method == 'POST':
        search_query = request.form['search-query']
        search_algorithm = request.form['search-algorithm']

        session['last_search_query'] = search_query
        session['last_search_algorithm'] = search_algorithm
        search_id = analytics_data.save_query_terms(search_query)

        results = search_engine.search(search_algorithm, search_query, search_id, corpus)

        # generate RAG response based on user query and retrieved results
        rag_response = rag_generator.generate_response(search_query, results)
        print("RAG response:", rag_response)

        found_count = len(results)

        session['last_result_pids'] = [doc.pid for doc in results[:20]] # just the top bc session would get too large
        session['last_scores'] = [doc.ranking for doc in results[:20]] 
        session['last_rag'] = rag_response
        session['last_search_id'] = search_id
        session['last_found_count'] = found_count

    else: # from doc_details
        if 'last_search_query' in session:
            search_query = session['last_search_query']
            #search_id = analytics_data.save_query_terms(search_query)
            rag_response = session['last_rag']
            found_count = session['last_found_count']
            
            pids = session['last_result_pids']
            scores = session['last_scores']
            results = []

            for pid, score in zip(pids, scores):
                doc = corpus[pid]
                results.append(ResultItem(
                    pid=doc.pid,
                    title=doc.title,
                    description=doc.description,
                    url=f"doc_details?pid={doc.pid}&search_id={session['last_search_id']}",
                    ranking=score,
                    selling_price =doc.selling_price,
                    discount=doc.discount,
                    average_rating=doc.average_rating,
                    product_url = doc.url
                ))

    # after user comes back from doc_details:
    # call update dwell time. not sure how to handle click_id TODO
    if 'last_clicked_doc_id' in session:
        analytics_data.update_dwell_time(session['last_clicked_doc_id'])

    return render_template('results.html', results_list=results, page_title="Results", found_counter=found_count, rag_response=rag_response)


@app.route('/doc_details', methods=['GET'])
def doc_details():
    """
    Show document details page
    ### Replace with your custom logic ###
    """
    # call to analytics_data log request
    analytics_data.log_request(session_id=session['session_id'], path=request.path, method=request.method)

    # getting request parameters:
    # user = request.args.get('user')
    print("doc details session: ")
    print(session)

    res = session["some_var"]
    #print("recovered var from session:", res)

    # get the query string parameters from request
    clicked_doc_id = request.args["pid"]
    print("click in id={}".format(clicked_doc_id))

    session['last_clicked_doc_id'] = clicked_doc_id

    # store data in statistics table 1
    if clicked_doc_id in analytics_data.fact_clicks.keys():
        analytics_data.fact_clicks[clicked_doc_id] += 1
    else:
        analytics_data.fact_clicks[clicked_doc_id] = 1 # first entry

    # print("fact_clicks count for id={} is {}".format(clicked_doc_id, analytics_data.fact_clicks[clicked_doc_id]))
    # print(analytics_data.fact_clicks)

    # call to analytics_data log click document
    analytics_data.log_click(
        session_id=session['session_id'], 
        search_id=request.args['search_id'], 
        query=session['last_search_query'],
        doc_id=clicked_doc_id,
        results=session['last_result_pids'],
        algorithm=session['last_search_algorithm'],
        rank=request.args['rank']
    )

    doc = corpus.get(clicked_doc_id)
    if doc is None:
        return "Document not found", 404
    
    return render_template('doc_details.html', doc=doc)


@app.route('/stats', methods=['GET'])
def stats():
    """
    Show simple statistics example. ### Replace with yourdashboard ###
    :return:
    """
    # call to analytics_data log request
    analytics_data.log_request(session_id=session['session_id'], path=request.path, method=request.method)

    docs = []
    for doc_id in analytics_data.fact_clicks:
        row: Document = corpus[doc_id]
        count = analytics_data.fact_clicks[doc_id]
        doc = StatsDocument(pid=row.pid, title=row.title, description=row.description, url=row.url, count=count)
        docs.append(doc)
    
    # simulate sort by ranking
    docs.sort(key=lambda doc: doc.count, reverse=True)
    num_req = len(analytics_data.requests)

    avg_rank = 0
    avg_dwell_time = 0
    dwell_count = 0
    for row in analytics_data.clicks:
        avg_rank += int(row['rank'])
        if row['dwell_time'] is not None:
                avg_dwell_time += row['dwell_time']
                dwell_count += 1    
    avg_rank /= len(analytics_data.clicks)
    if dwell_count != 0:
        avg_dwell_time /= dwell_count
    total_clicks = len(analytics_data.clicks)

    unique_docs = []
    for row in analytics_data.clicks:
        if row['doc_id'] not in unique_docs:
            unique_docs.append(row['doc_id'])
    
    unique_queries = []
    avg_num_terms = 0
    total_searches = []
    for row in analytics_data.clicks:
        avg_num_terms += row['nterms_query']
        if row['query'] not in unique_queries:
            unique_queries.append(row['query'])
        if row['search_id'] not in total_searches:
            total_searches.append(row['search_id'])
    avg_num_terms /= len(analytics_data.clicks)

    avg_session_duration = analytics_data.get_average_session_duration()

    return render_template('stats.html', clicks_data=docs, num_requests=num_req, avg_rank=round(avg_rank, 2), total_clicks=total_clicks, unique_docs=len(unique_docs), unique_queries=len(unique_queries), avg_num_terms=round(avg_num_terms,2), top_10_q_terms=analytics_data.get_term_frequencies(), avg_dwell_time=round(avg_dwell_time,2), avg_session_duration=round(avg_session_duration, 2), num_searches=len(total_searches))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    # call to analytics_data log request
    analytics_data.log_request(session_id=session['session_id'], path=request.path, method=request.method)

    visited_docs = []
    for doc_id in analytics_data.fact_clicks.keys():
        d: Document = corpus[doc_id]
        doc = ClickedDoc(doc_id, d.description, analytics_data.fact_clicks[doc_id])
        visited_docs.append(doc)

    # simulate sort by ranking
    visited_docs.sort(key=lambda doc: doc.counter, reverse=True)

    for doc in visited_docs: print(doc)
    return render_template('dashboard.html', visited_docs=visited_docs)


# New route added for generating an examples of basic Altair plot (used for dashboard)
@app.route('/plot_number_of_views', methods=['GET'])
def plot_number_of_views():
    return analytics_data.plot_number_of_views()

@app.route('/plot_query_frequency', methods=['GET'])
def plot_query_frequency():

    return analytics_data.plot_query_frequency()

@app.route('/distribution_rank_clicked_docs', methods=['GET'])
def distribution_rank_clicked_docs():

    return analytics_data.distribution_rank_clicked_docs()

@app.route('/plot_hourly_usage_distribution', methods=['GET'])
def plot_hourly_usage_distribution():

    return analytics_data.plot_hourly_usage_distribution()

@app.route('/plot_browser_distribution', methods=['GET'])
def plot_browser_distribution():

    return analytics_data.plot_browser_distribution()

@app.route('/plot_os_distribution', methods=['GET'])
def plot_os_distribution():

    return analytics_data.plot_os_distribution()

@app.route('/plot_platform_distribution', methods=['GET'])
def plot_platform_distribution():

    return analytics_data.plot_platform_distribution()

@app.route('/plot_bot_distribution', methods=['GET'])
def plot_bot_distribution():

    return analytics_data.plot_bot_distribution()

@app.route('/plot_average_dwell_time_by_rank', methods=['GET'])
def plot_average_dwell_time_by_rank():

    return analytics_data.plot_average_dwell_time_by_rank()

@app.route('/plot_requests_by_method', methods=['GET'])
def plot_requests_by_method():

    return analytics_data.plot_requests_by_method()

@app.route('/plot_ip_city_distribution', methods=['GET'])
def plot_ip_city_distribution():

    return analytics_data.plot_ip_city_distribution()

@app.route('/plot_ip_country_distribution', methods=['GET'])
def plot_ip_country_distribution():

    return analytics_data.plot_ip_country_distribution()

if __name__ == "__main__":
    app.run(port=8088, host="0.0.0.0", threaded=False, debug=os.getenv("DEBUG"))
