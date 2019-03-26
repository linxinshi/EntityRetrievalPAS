from math import log
from copy import deepcopy
from config import *
from list_term_object import List_Term_Object
from lib_model.lib_funcs import get_mapping_prob,get_dirichlet_prob

def get_topn_fields(concept,fields,lucene_obj,**kwargs):
    from heapq import heappush, heappop
    heap=[]
    cnt=0
    is_bigram=kwargs.get('is_bigram',False)
    if is_bigram:
       slop=kwargs['slop']
       ordered=kwargs['ordered']
       title=kwargs['title']
    for field in fields:
        # notice: include catchall field
        if is_bigram==False:
           cf=lucene_obj.get_coll_termfreq(concept, field)
           tup=(cf,field)
        else:
           tf,cf=lucene_obj.get_coll_bigram_freq(concept,field,ordered,slop,title,is_cached=True)
           tup=(cf,tf,field)
           
        if cnt<NUM_TOP_FIELD:
           heappush(heap,tup)
           cnt+=1
        elif cf>heap[0][0]:
           heappush(heap,tup)
           heappop(heap)
           
    return heap
    
def fsdmSim_elr(queryObj,entityObj,lucene_obj,param_server,w2vmodel=None):
    # an reimplementation of EntityLinking-ELR project
    # fields are dynamic subject to different query terms and phrases
    len_C_f={}
    mu={}
    for field in entityObj.fields:
        len_C_f[field]=lucene_obj.get_coll_length(field)
        mu[field]=lucene_obj.get_avg_len(field)
           
    ft=fo=fu=0.0
    LAMBDA_T=param_server.get('LAMBDA_T',0.0)
    LAMBDA_O=param_server.get('LAMBDA_O',0.0)
    LAMBDA_U=param_server.get('LAMBDA_U',0.0)
    
    #print (LAMBDA_T,LAMBDA_O,LAMBDA_U)
    
    # w is a dict of weights for each field
    # compute ft
    print ('###############')
    for t in queryObj.ngrams[1]:
        fields_info=get_topn_fields(t,entityObj.fields,lucene_obj)
        w=get_mapping_prob(t,lucene_obj,ordered=True,slop=0,is_cached=False,fields=[item[1] for item in fields_info])
        print (t)
        print (w)
        ft_temp=0.0
        for cf,field in fields_info:
            tf=entityObj.term_freqs[field].get(t,0)           
            ptd=get_dirichlet_prob(tf,entityObj.lengths[field],cf,len_C_f[field],mu[field])
            if ptd>0:
               ft_temp+=ptd*w[field]
        if ft_temp>0:
           ft+=log(ft_temp)
    # compute fo
    if LAMBDA_O>0:
       for bigram in queryObj.ngrams[2]:
           fields_info=get_topn_fields(bigram,entityObj.fields,lucene_obj,is_bigram=True,ordered=True,slop=0,title=entityObj.title)
           #print (bigram)
           #print (fields_info)
           # item[2] is field name for bigram!    
           w=get_mapping_prob(bigram,lucene_obj,ordered=True,slop=0,is_bigram=True,is_cached=False,fields=[item[2] for item in fields_info])
           print (bigram)
           print (w)
           fo_temp=0.0
           for cf,tf,field in fields_info:
               # notice: need to modify to set cache
               ptd=get_dirichlet_prob(tf,entityObj.lengths[field],cf,len_C_f[field],mu[field])
               if ptd>0:
                  fo_temp+=ptd*w[field]
           if fo_temp>0:
              fo+=log(fo_temp)
    # compute fu
    if LAMBDA_U>0:
       for bigram in queryObj.ngrams[2]:
           fields_info=get_topn_fields(bigram,entityObj.fields,lucene_obj,is_bigram=True,ordered=False,slop=6,title=entityObj.title)
           # item[2] is field name for bigram!  
           w=get_mapping_prob(bigram,lucene_obj,ordered=False,slop=6,is_bigram=True,is_cached=False,fields=[item[2] for item in fields_info])
           #print (w) 
           fu_temp=0.0
           for cf,tf,field in fields_info:
               ptd=get_dirichlet_prob(tf,entityObj.lengths[field],cf,len_C_f[field],mu[field])
               if ptd>0:
                  fu_temp+=ptd*w[field]
           if fu_temp>0:
              fu+=log(fu_temp)
    '''
    if queryObj.contents_obj.length>1:
       ft/=queryObj.contents_obj.length
       fo/=(queryObj.contents_obj.length-1)
       fu/=(queryObj.contents_obj.length-1)
    '''
    score=LAMBDA_T*ft+LAMBDA_O*fo+LAMBDA_U*fu
    return score 