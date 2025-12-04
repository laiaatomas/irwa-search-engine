# IRWA FINAL PROJECT
This repository contains the final project for the Information Retrieval and Web Analysis course.
This final project focuses on building a search and retrieval system for an e-commerce fashion products dataset. 

### Dataset Availability :warning:
The dataset used in this project cannot be shared publicly. If you want to run the project, please contact me to obtain the dataset.

## Project Part 1 Overview
The goal of the first part is to preprocess product data, perform exploratory data analysis (EDA), and prepare the dataset for the next parts for efficient retrieval based on user queries.

## Project Part 2 Overview
The goal of the second part is to build an inverted index for the fashion products dataset, implement the TF-IDF algorithm, rank the products accordingly based on custom queries, and finally implement and test different evaluation metrics.

## Project Part 3 Overview
The goal of the third part is to implement and test different ranking methods: TF-IDF and cosine similarity, bm25, some new score, and word2vec. The ranking is done on the queries created in part 2 (defined by term-frequency and relevance). Doc2Vec is also implemented in this part as a bonus point.

## Installation
1. Clone the repository:  
   ```bash
   git clone https://github.com/laiaatomas/IRWA_FinalProject
   cd IRWA_FinalProject

2. Create a virtual environment:
   ```bash
    python -m venv .venv

3. Activate the environment:
   ```bash
    .venv\Scripts\activate

4. Install dependencies:
   ```bash
    pip install -r requirements.txt

## Usage
After obtaining the dataset:

Run project_part1.ipynb\
&nbsp;- Preprocessing and EDA.

Run project_part2.ipynb\
&nbsp;- Inverted index, TF-IDF, query selection, ranking and evaluations.

Run project_part3.ipynb\
&nbsp;- TF-IDF, BM25, custom scoring, Word2Vec and Doc2Vec.

Find additional information in the report.