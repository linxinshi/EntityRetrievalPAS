from config import *
from math import log,log10
def lmSim(query_terms,entityObj,field,w2vmodel,lucene_obj,mongoObj=None):
    totalSim=0.0
    term_freq=entityObj.term_freq
    len_C_f = lucene_obj.get_coll_length(field)
    mu=lucene_obj.get_avg_len(field)

    for i in range(len(query_terms)):
        qt=query_terms[i]
        localSim=0.0
        # compute p(t|De)
        if qt in term_freq:
           localSim=term_freq[qt]
        len_d_f = entityObj.length
        tf_t_d_f = localSim
        tf_t_C_f = lucene_obj.get_coll_termfreq(qt, field)   
        p_t_d=get_dirichlet_prob(tf_t_d_f, float(len_d_f), float(tf_t_C_f), float(len_C_f), mu)
        # compute f(p(t1|De),p(t2|De)...) 
        if p_t_d>0.0:
           totalSim+=log(p_t_d)
    return totalSim
       
def bm25fSim(queryObj,entityObj,lucene_obj,param_server=None):
    len_C_f={}
    mu={}
    for f in LIST_F:
        len_C_f[f]=lucene_obj.get_coll_length(f)
        mu[f]=lucene_obj.get_avg_len(f)
        
    N=lucene_obj.get_doc_count('stemmed_catchall')    
    k1=2.44
    b=0.25
    boost=1
    
    totalSim=0.0
    for term in queryObj.ngrams[1]:
          df_t=lucene_obj.get_doc_freq(term,'stemmed_catchall')
          idf_t=log10((N-df_t+0.5)/(df_t+0.5))
          weight_t_d=0.0
          
          for f in LIST_F:
                len_d_f = entityObj.lengths[f]
                tf_t_d_f = entityObj.term_freqs[f].get(term,0)
                tf_t_C_f = lucene_obj.get_coll_termfreq(term, f)
            
                # compute f(p(t1|De),p(t2|De)...) 
                weight_t_d+=((tf_t_d_f*boost)/(1-b+b*(len_d_f/mu[f])))
          totalSim+=(idf_t*(weight_t_d/(k1+weight_t_d)))    
    return totalSim