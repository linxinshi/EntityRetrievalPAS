## Entity Retrieval in the Knowledge Graph with Hierarchical Entity Type and Content
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

6. This implementation exploits a caching strategy for bigrams if use set the parameter "model" to "sdm" and "fsdm", or you enable path-aware smoothing in the Wikipedia article tree with non-zero parameters "WIKI_LAMBDA_O" and "WIKI_LAMBDA_U". First set "hitsperpage" and "NUM_PROCESS" to 1 and run the system. Terminate it after few minutes. Then login to the MongoDB console to create index for the automatically created collections INDEX_NAME_{tf,cf}_{cache,mapping_prob_cache}. And then run the system until it ends. Then the system will automatically cache all bigrams occur in the query across the indices.

## requirements
Python 3.4+

NLTK, Gensim, Pymongo

NetworkX <= 1.11

PyLucene 6.x 

(This implementation works on both Windows and Linux. If you have PyLucene install issues on Windows, please refer to http://lxsay.com/archives/365)

## comments
Most parameters are specified in config.py and config_object.py. The normalized factor for path-aware smoothing is specified in the line 159 of lib_model/fsdm_models.py

The parameters "WIKI_LAMBDA_T", "WIKI_LAMBDA_O" and "WIKI_LAMBDA_U" are recommended to set to 1,0,0 to speed up the retrieval. This setting is already able to reproduce most results reported in the paper that incorporates the Wikipedia information.

The parameter "NUMBER_TOP_K_PARENT" in wikipedia_category_system/create_category_corpus.py and "TOP_CATEGORY_NUM" in config_object.py matter the retrieval performance as well as other parameters for retrieval models.

There are less improvements brought by this framework using the DBpedia ontology (instance_types.ttl) because the DBpedia ontology is a small tree-like strcture and each entity is assigned with only one or two types. The effect of similar context sharing by entities with the same type is little. If you want answers found through graph topologies instead of text information, consider some completely graph-based "entity search" or "relevance search" methods.

The ranking system will output better results than those reported in the paper if you adjust it carefully.

## contact
Xinshi Lin (xslin(at)se.cuhk.edu.hk)

## license
Beer-ware or Snack-ware license

If you use this implementation or thoughts discussed in this paper for your research, please consider citing it.
