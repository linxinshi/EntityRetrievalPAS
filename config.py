# coding=utf-8
# global parameter
import platform,os

SYSTEM_FLAG=platform.system()

hitsPerPage = 500
NUM_PROCESS= 3  # 1~4.   each process consumes about 6GB of memory 
NEGATIVE_INFINITY=-99999999
MODEL_NAME='lm'  # lm,mlm,sdm,fsdm
DATA_VERSION = 2015
mongo_port=58903
TAXONOMY='Wikipedia'
PREPROCESS_TYPE='STEM' # LEMMA,STEM

# field setting
if MODEL_NAME=='fsdm_elr':
   USED_CONTENT_FIELD='catchall'
else:
   USED_CONTENT_FIELD='stemmed_catchall'
 
if MODEL_NAME in ['lm','sdm']:
   LIST_F=['stemmed_catchall']
elif MODEL_NAME=='mlm-tc':
   LIST_F=['stemmed_names','stemmed_catchall']
else: 
   LIST_F=['stemmed_names','stemmed_attributes','stemmed_categories','stemmed_similar_entities','stemmed_related_entities']
NO_SMOOTHING_LIST=[]


# options for variants
IS_WIKI_DOC_TREE_USED=True
IS_SAS_USED=False

# for bigram related operation
IS_BIGRAM_CACHE_USED=False
if MODEL_NAME.find('sdm')>-1:
   IS_BIGRAM_CACHE_USED=True
 
# specify index path
LUCENE_INDEX_DIR=os.path.join('mmapDirectory','dbpedia_v3_FSDM3')
LUCENE_INDEX_WIKI_DIR=os.path.join('mmapDirectory','index_wikipedia_2015')
LUCENE_INDEX_CATEGORY_CORPUS=os.path.join('mmapDirectory','category_corpus_dbpedia201510_top5_fsdm3')

#queries_all_v2.txt
#queries-v2_stopped.txt
QUERY_FILEPATH=os.path.join('query','simple_cluster','INEX_LD_v2.txt')
PATH_GROUNDTRUTH=os.path.join('qrels-v2.txt')
PATH_CATEGORY_DAG='category_dag_dbpedia_top10.pkl.gz'

