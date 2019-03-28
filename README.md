## Entity Retrieval in the Knowledge Graph with Hierarchical Entity Type and Content
update 2019.03.26 upload the revised source codes. Other cleanup work in progress.

<del> update 2018.10.26: will be released with faster indexer and simplified implementation before 2018.11.30 (I am busy with some deadlines recently...) </del> 

This repository contains resources developed within the following paper:

    Xinshi Lin, Wai Lam and Kwun Ping Lai. “Entity Retrieval in the Knowledge Graph with Hierarchical Entity Type and Content”, ICTIR 2018

## usage
0. collect data from DBpedia/Wikipedia and store them into a MongoDB database (see https://github.com/linxinshi/DBpedia-Wikipedia-Toolkit)

1. build graph representation of the Wikipedia Category System (see folder "wikipedia_category_system")

2. build index (see folder "build_index" and "build_wikipedia_index")

3. edit config.py, config_object.py  and mongo_object.py to specify parameters for retrieval models and index path etc.

4. execute command "python main.py"

5. check results in folder Retrieval_results (created by program and name it after the time executed)

*this implementation supports multi-processing, specify NUM_PROCESS in config.py. The program will split the queries into several parts and each process will handle one of them. Finally the program merges all results and output a complete one.

6. This implementation exploits a caching strategy for bigrams if use set the parameter "model" to "sdm" and "fsdm", or you enable path-aware smoothing in the Wikipedia article tree with non-zero parameters "WIKI_LAMBDA_O" and "WIKI_LAMBDA_U". First set "hitsperpage" and "NUM_PROCESS" to 1 and run the system. Terminate it after few minutes. Then login to the mongoDB console to create index for the automatically created collections INDEX_NAME_{tf,cf}_{cache,mapping_prob_cache}. And then run the system until it ends. Then the system will automatically cache all bigrams occur in the query across the indices.

## requirements
Python 3.4+

NLTK, Gensim, Pymongo

NetworkX <= 1.11

PyLucene 6.x 

(This implementation works on both Windows and Linux. If you have PyLucene install issues on Windows, please refer to http://lxsay.com/archives/365)

## comments
Most parameters are specified in config.py and config_object.py. The normalized factor for path-aware smoothing is specified in the line 159 of lib_model/fsdm_models.py

The parameters "WIKI_LAMBDA_T", "WIKI_LAMBDA_O" and "WIKI_LAMBDA_U" are recommended to set to 1,0,0 to speed up the retrieval. This setting is already able to reproduce most results reported in the paper that incorporates the Wikipedia information.

I do not like wasting time on tuning parameters to achieve "superior performance to the state-of-the-art models" (typically I spend less than an hour on tuning my work). The ranking system will output much better results if you carefully tune it.

## contact
Xinshi Lin (xslin(at)se.cuhk.edu.hk)

## license
Creative Commons

If you use this implementation or thoughts discussed in this paper for your research, please consider citing it.
