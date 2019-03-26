## Entity Retrieval in the Knowledge Graph with Hierarchical Entity Type and Content
update 2019.03.26 upload the revised source codes. Cleanup work in progress.

<del> update 2018.10.26: will be released with faster indexer and simplified implementation before 2018.11.30 (I am busy with some deadlines recently...) </del> 

This repository contains resources developed within the following paper:

    Xinshi Lin, Wai Lam and Kwun Ping Lai. “Entity Retrieval in the Knowledge Graph with Hierarchical Entity Type and Content”, ICTIR 2018

## usage
0. collect data from DBpedia/Wikipedia and store them into a MongoDB database (see https://github.com/linxinshi/DBpedia-Wikipedia-Toolkit)

1. build graph representation of the Wikipedia Category System (see folder "wikipedia_category_system")

2. build index (see folder "build_index")

3. edit config.py, config_object.py  and mongo_object.py to specify parameters for retrieval models and index path etc.

4. execute command "python main.py"

5. check results in folder Retrieval_results (created by program and name it after the time executed)

*this implementation supports multi-processing, specify NUM_PROCESS in config.py. The program will split the queries into several parts and each process will handle one of them. Finally the program merges all results and output a complete one.

## requirements
Python 3.4+

NLTK, Gensim

NetworkX <= 1.11

PyLucene 6.x 

(if you have PyLucene install issues on Windows, please refer to http://lxsay.com/archives/365)
