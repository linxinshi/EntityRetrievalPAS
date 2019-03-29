# -*- coding: utf-8 -*-
# mcl_clustering.mcl()
# average mentioned entity score  otherwise will be dominated by keyword matching case

from multiprocessing import Process,Manager
import os, time, sys, argparse, datetime, gzip
import networkx
#from franges import drange

from query_object import Query_Object
from entity_object import Entity_Object
from mongo_object import Mongo_Object
from structure_object import Structure_Object
from lucene_object import Lucene_Object
from lib_model.fsdm_models import *
from config import *
from config_object import *

def read_query(queries,conf_paras):
    src = open(QUERY_FILEPATH,'r',encoding='utf-8')
    cnt=0
    for line in src:
        cnt+=1
        list = line.strip().split('\t')
        queries.append((list[0],'',list[1])) # query_id, clusterd query, raw query
    src.close()
    
def computeScore(queryObj,entityObj,structure,lucene_handler,conf_paras):
    mongoObj,entityScore=structure.mongoObj,structure.entityScore
    lucene_obj=lucene_handler['first_pass']
    title=entityObj.title
    if title in entityScore:
       return entityScore[title]
  
    # compute score_text   
    if IS_SAS_USED==True and entityObj.categories is not None:
       score_text=fsdm_sas(queryObj,entityObj,structure,lucene_handler,conf_paras.param_server,mongoObj)
       if score_text in [0.0,NEGATIVE_INFINITY]:
          score_text=fsdmSim(queryObj,entityObj,lucene_obj,conf_paras.param_server)
          
    elif MODEL_NAME in ['lm','sdm','mlm','fsdm']:
       score_text=fsdmSim(queryObj,entityObj,lucene_obj,conf_paras.param_server)
    elif MODEL_NAME=='bm25f':
           from lib_model.basic_models import bm25fSim
           score_text=bm25fSim(queryObj,entityObj,lucene_obj,conf_paras.param_server)
       
    score=score_text
    score_wiki=0.0
    has_wiki=False
    if IS_WIKI_DOC_TREE_USED==True:
       has_wiki=True
       
       
       if entityObj.wiki_doc_tree is not None: 
          #entityObj.wiki_doc_tree.traverse(1)
          
          score_wiki=scoreWikiTree(queryObj,entityObj.wiki_doc_tree,lucene_handler['wiki'],entityObj.wiki_doc_tree.used_content_field,conf_paras.param_server)
          if score_wiki==NEGATIVE_INFINITY:
              has_wiki=False
          #print ('score_wiki=',(score_wiki))
       
       '''
       if entityObj.wiki_doc_tree is not None:  
           list_str_node=[]
           entityObj.wiki_doc_tree.getSubTreePathContentByDepth(2,list_str_node)
           list_section=[List_Term_Object(item,False,' ',mongoObj) for item in list_str_node]
           #list_section=[List_Term_Object(item,False,' ',mongoObj) for item in entityObj.wiki_doc_tree.getSubTreeContentByDepth(2)]
           has_wiki=True
           try:
              score_wiki=max([lmSim(queryObj.ngrams[1],section_obj,entityObj.wiki_doc_tree.used_content_field,w2vmodel,lucene_handler['wiki']) for section_obj in list_section])
              #print ('yes score=%f'%(score_wiki))
           except Exception as e:
              #print ('oh')
              has_wiki=False
       '''
    if has_wiki==True:
       score=0.85*score_text+0.15*score_wiki
    entityScore[title]=score
    return score

def createGraph(queryObj,lucene_handler,structure,conf_paras):
    lucene_obj=lucene_handler['first_pass']
    mongoObj=structure.mongoObj
    entityScore,entityObjects=structure.entityScore,structure.entityObjects
    candidates=[]
    cnt=0   
    for entity in structure.currentEntity:
        entityScore[entity] = computeScore(queryObj,entityObjects[entity],structure,lucene_handler,conf_paras)
        candidates.append((entityScore[entity],cnt,entity))
        cnt+=1
    return candidates

def getEntiyObject(title,structure,lucene_obj):
       entityObjects=structure.entityObjects
       if title in entityObj:
          return entityObjects[title]
          
       d_pair=lucene_obj.findDoc(title,'title',True)
       if d_pair[0] is None:
           return None
           
       entityObj=Entity_Object()
       entityObj.updateFromIndex(d_pair,structure.mongoObj,lucene_obj)
       entityObjects[title]=entityObj   
       return entityObj
       
def createEntityObject(d_pair,structure,lucene_obj):
    #d_pair:(document,docid)
    d=d_pair[0]
    title=d.get('title')

    entityObjects=structure.entityObjects
    if title not in entityObjects:
       entityObj=Entity_Object()
       entityObj.updateFromIndex(d_pair,structure.mongoObj,lucene_obj)
       entityObjects[title]=entityObj
    structure.currentEntity.add(title)
    return entityObjects[title]
             
def handle_process(id_process,queries,RES_STORE_PATH,conf_paras):
    starttime=datetime.datetime.now()
    
    structure=Structure_Object(conf_paras,id_process)
    lucene_handler={}
    lucene_handler['first_pass']=Lucene_Object(LUCENE_INDEX_DIR,'BM25',False,True,structure.mongoObj)
    
    if IS_WIKI_DOC_TREE_USED==True:
       lucene_handler['wiki']=Lucene_Object(LUCENE_INDEX_WIKI_DIR,'BM25',True,True,structure.mongoObj)
    if IS_SAS_USED==True:
       lucene_handler['category_corpus']=Lucene_Object(LUCENE_INDEX_CATEGORY_CORPUS,'BM25',True,True,structure.mongoObj)
    
    RESULT_FILENAME=os.path.join(RES_STORE_PATH,'pylucene_%d.runs'%(id_process))
    rec_result=open(RESULT_FILENAME,'w',encoding='utf-8')
    
    # search
    candidates=[]    
    
    for i in range(len(queries)):
        lucene_obj=lucene_handler['first_pass']
        # build query object for computeScore
        queryObj=Query_Object(queries[i],structure,lucene_handler)
        querystr=queryObj.querystr   # no stemming may encourter zero candidates if field contents are stemmed
        docs=lucene_obj.retrieve(querystr,USED_CONTENT_FIELD,hitsPerPage)
        
        # initialize duplicate remover and score record
        structure.clear()
        del candidates[:]
        
        # find candidate results after the first pass
        # d_pair:(document,docid)
        for d_pair in docs:
            d=d_pair[0]
            if d is None:
               continue
            uri,title=d['uri'],d['title']
            if title in structure.currentEntity:
               continue    
            obj=createEntityObject(d_pair,structure,lucene_obj)  
        
        candidates=createGraph(queryObj,lucene_handler,structure,conf_paras)
        print ('id_process=%d\t %d/%d\t query=%s  len_docs=%d'%(id_process,i+1,len(queries),queryObj.querystr,len(docs)))
            
        # output results from priority queue larger score first
        candidates.sort(key=lambda pair:pair[0],reverse=True)
        
        for rank in range(min(1000,len(candidates))):
            item=candidates[rank]
            title='<dbpedia:%s>' %(item[2])
            res_line="%s\t%s\t%s\t%d\t%f\t%s\n" %(queryObj.qid,'Q0',title,rank+1,item[0],'mazda6')
            rec_result.writelines(res_line)
    interval=(datetime.datetime.now() - starttime).seconds
    print ('id_process=%d   running time=%s' %(id_process,str(interval)))

    rec_result.close()
       
def main(conf_paras):  
    starttime_total=datetime.datetime.now()
    parser = argparse.ArgumentParser()
    parser.add_argument("-comment", help="comment for configuration", default='')
    args = parser.parse_args()
    
    # generate folder to store results
    if (len(args.comment.strip()))>0:
       comment='-'.join(args.comment.split(' '))
       RES_STORE_PATH=os.path.join(str(datetime.datetime.now()).replace(':','-').replace(' ','-')[:-7]+'-'+comment)
    else:
       RES_STORE_PATH=str(datetime.datetime.now()).replace(':','-').replace(' ','-')[:-7]   
    
    RES_STORE_PATH=os.path.join('Retrieval_result',RES_STORE_PATH)
       
    print ('store_path=%s'%(RES_STORE_PATH))
    os.mkdir(RES_STORE_PATH)
  
    print ('begin backup code files')
    if SYSTEM_FLAG=='Windows':
       cmd1='robocopy /njh /njs /ndl /nc /ns /nfl %s %s *.py'%(r'%cd%',RES_STORE_PATH)
       cmd2='robocopy /njh /njs /ndl /nc /ns /nfl %s %s *.txt'%(r'%cd%',RES_STORE_PATH)
    else:
       cmd1='cp py3_ca/*.py %s'%(RES_STORE_PATH)
       cmd2='cp py3_ca/*.txt %s'%(RES_STORE_PATH)
    os.system(cmd1)
    os.system(cmd2)
    # read queries
    queries=[]
    read_query(queries,conf_paras)
    cnt_query=len(queries)
   
   # begin multiprocessing
    process_list=[]
    num_workers=NUM_PROCESS
    delta=cnt_query//num_workers  
    if cnt_query%num_workers!=0:  # +1 important
       delta=delta+1
    
    for i in range(num_workers):
        left=i*delta
        right=(i+1)*delta
        if right>cnt_query:
           right=cnt_query
         
        p = Process(target=handle_process, args=(i,queries[left:right],RES_STORE_PATH,conf_paras))
        p.daemon = True
        process_list.append(p)

    if IS_SAS_USED==True and TAXONOMY=='Wikipedia':
       delay=20
    elif IS_SAS_USED==True and TAXONOMY=='DBpedia':
       delay=5
    else:
       delay=3
    for i in range(len(process_list)):
        process_list[i].start()
        print ("sleep %d seconds to enable next process"%(delay))
        time.sleep(delay)

    for i in range(len(process_list)):
        process_list[i].join()
    
    print ('begin to merge results')
    dict_merged={}
    list_allResult={}
    list_name=['pylucene']
       
    list_ext=['runs']
    for name in list_name:
        list_allResult[name]=[]
    
    for i in range(num_workers):
        for j in range(len(list_name)):
            name=list_name[j]
            filename=os.path.join(RES_STORE_PATH,name)+'_%s.%s'%(str(i),list_ext[j])
            with open(filename,'r',encoding='utf-8') as f_tmp:
                 list_allResult[name].extend(f_tmp.readlines())
            os.remove(filename)    

    list_allResult['pylucene'].sort(key=lambda item:item.split('\t')[0],reverse=False)
    for j in range(len(list_name)):
        name=list_name[j]
        filename=os.path.join(RES_STORE_PATH,name)+'_all_mp.'+list_ext[j]
        if name!='report_lucene':
           with open(filename,'w',encoding='utf-8') as f:
                f.writelines(list_allResult[name])
        else:
           with gzip.open(filename+'.gz','wb') as f:
                f.writelines([line.encode('utf-8') for line in list_allResult[name]])           
             
    print ('total running time='+str((datetime.datetime.now() - starttime_total).seconds))

    
if __name__ == '__main__':
   # implement CA here
   conf_paras=Config_Object()
   main(conf_paras)
