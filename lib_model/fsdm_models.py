from math import log
from copy import deepcopy
from config import *
from list_term_object import List_Term_Object
from lib_model.lib_funcs import get_mapping_prob,get_dirichlet_prob

def fsdmSim(queryObj,entityObj,lucene_obj,param_server,w2vmodel=None,fields=LIST_F):
    len_C_f={}
    mu={}
    for field in fields:
        len_C_f[field]=lucene_obj.get_coll_length(field)
        mu[field]=param_server.get('mu_%s'%(field),lucene_obj.get_avg_len(field))
        
    ft=fo=fu=0.0
    LAMBDA_T=param_server.get('LAMBDA_T',0.0)
    LAMBDA_O=param_server.get('LAMBDA_O',0.0)
    LAMBDA_U=param_server.get('LAMBDA_U',0.0)
    
    #print (LAMBDA_T,LAMBDA_O,LAMBDA_U)
    
    # w is a dict of weights for each field
    # compute ft
    F=fields
    if LAMBDA_T>0:
       for t in queryObj.ngrams[1]:
           w=get_mapping_prob(t,lucene_obj,ordered=True,slop=0,is_bigram=False,params=param_server,fields=F)
           ft_temp=0.0
           for field in w:
               tf=entityObj.term_freqs[field].get(t,0)
               cf=lucene_obj.get_coll_termfreq(t, field)            
               ptd=get_dirichlet_prob(tf,entityObj.lengths[field],cf,len_C_f[field],mu[field])
               if ptd>0:
                  ft_temp+=ptd*w[field]
           if ft_temp>0:
              ft+=log(ft_temp)
    # compute fo
    if LAMBDA_O>0:
       for bigram in queryObj.ngrams[2]:
           w=get_mapping_prob(bigram,lucene_obj,ordered=True,slop=0,is_bigram=True,params=param_server,fields=F)
           fo_temp=0.0
           for field in w:
               tf,cf=lucene_obj.get_coll_bigram_freq(bigram,field,True,0,entityObj.title)
               ptd=get_dirichlet_prob(tf,entityObj.lengths[field],cf,len_C_f[field],mu[field])
               if ptd>0:
                  fo_temp+=ptd*w[field]
           if fo_temp>0:
              fo+=log(fo_temp)
    # compute fu
    if LAMBDA_U>0:
       for bigram in queryObj.ngrams[2]:
           w=get_mapping_prob(bigram,lucene_obj,ordered=False,slop=6,is_bigram=True,params=param_server,fields=F)
           fu_temp=0.0
           for field in w:
               tf,cf=lucene_obj.get_coll_bigram_freq(bigram,field,False,6,entityObj.title)
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

    
def fsdm_sas(queryObj,entityObj,structure,lucene_handler,param_server,mongoObj=None):
    if len(entityObj.categories)==0:
       return NEGATIVE_INFINITY
    D=structure.cat_dag
    lucene_cat=lucene_handler['category_corpus']
    lucene_doc=lucene_handler['first_pass']
    
    len_d_f=entityObj.lengths
    mu_d={}
    len_C_f={}
    for f in LIST_F:
        len_C_f[f]=lucene_doc.get_coll_length(f)
        mu_d[f]=lucene_doc.get_avg_len(f)
        
    LAMBDA_T=param_server.get('LAMBDA_T',0.0)
    LAMBDA_O=param_server.get('LAMBDA_O',0.0)
    LAMBDA_U=param_server.get('LAMBDA_U',0.0)
    ALPHA_SAS=param_server.get('ALPHA_SAS')
    TOP_PATH_NUM_PER_CAT=param_server.get('TOP_PATH_NUM_PER_CAT')
    LIMIT_SAS_PATH_LENGTH=param_server.get('LIMIT_SAS_PATH_LENGTH')
    TOP_CATEGORY_NUM=param_server.get('TOP_CATEGORY_NUM')
    
    # prepare field weights
    w={} # (term,ordered)={field:field_weight}
    for t in queryObj.ngrams[1]:
          w[(t,True)]=get_mapping_prob(t,lucene_doc)
    if LAMBDA_O>0 or LAMBDA_U>0:
       for bigram in queryObj.ngrams[2]:
           w[(bigram,True)]=get_mapping_prob(bigram,lucene_doc,ordered=True,slop=0,is_bigram=True)
           w[(bigram,False)]=get_mapping_prob(bigram,lucene_doc,ordered=False,slop=6,is_bigram=True)
    
    sum_ptc={}    
    for f in LIST_F:
        sum_ptc[('T',f)]=[0.0 for x in queryObj.ngrams[1]]
        sum_ptc[('O',f)]=[0.0 for x in queryObj.ngrams[2]]
        sum_ptc[('U',f)]=[0.0 for x in queryObj.ngrams[2]]
        
    def smooth_path(cat,alpha_t):
        nonlocal D,curPath,sum_ptc,sum_nominator,cnt_path
        nonlocal max_score_p_cat,max_score
        nonlocal lucene_cat,lucene_doc
        
        if cnt_path>TOP_PATH_NUM_PER_CAT:
           return
        # maintain useful temporary variables
        # current node is cat
        cat_corpus,docID=lucene_cat.findDoc(cat,'category',True)
        if cat_corpus is not None:
           # maintain
           cnt_doc_corpus=int(cat_corpus['num_articles'])
           for f in LIST_F:
               # get category corpus
               term_freq_c_f=lucene_cat.get_term_freq(docID,f)
               len_c_f=sum(term_freq_c_f.values())
               mu_c_f=len_c_f/cnt_doc_corpus if cnt_doc_corpus>0 else 0.0
               sum_nominator[f]+=(alpha_t*mu_c_f)       
               # maintain individual query terms
               for j in range(len(queryObj.ngrams[1])):
                   t=queryObj.ngrams[1][j]
                   cf_c=term_freq_c_f.get(t,0.0)     
                   ptc_f=cf_c/len_c_f if len_c_f>0 else -1    
                   if ptc_f>-1:  
                      sum_ptc[('T',f)][j]+=(alpha_t*ptc_f*mu_c_f) 
               # maintain ordered bigrams
               
               if LAMBDA_O>0:
                  for j in range(len(queryObj.ngrams[2])):
                      bigram=queryObj.ngrams[2][j]

                      cf_c,cf_cc=lucene_cat.get_coll_bigram_freq(bigram,f,True,0,cat,field_id='category')
                      ptc_f=cf_c/len_c_f if len_c_f>0 else -1
                      if ptc_f>-1:
                         sum_ptc[('O',f)][j]+=(alpha_t*ptc_f*mu_c_f)
               # maintain unordered bigrams
               if LAMBDA_U>0:
                  for j in range(len(queryObj.ngrams[2])):
                      bigram=queryObj.ngrams[2][j]
                      cf_c,cf_cc=lucene_cat.get_coll_bigram_freq(bigram,f,False,6,cat,field_id='category')
                      ptc_f=cf_c/len_c_f if len_c_f>0 else -1
                      if ptc_f>-1:
                         sum_ptc[('U',f)][j]+=(alpha_t*ptc_f*mu_c_f)                       

        # the following is end condition
        bak_sum_nominator=deepcopy(sum_nominator)
        bak_sum_ptc=deepcopy(sum_ptc)
        if len(curPath)==LIMIT_SAS_PATH_LENGTH or len(D[cat])==0:
           # compute score
           cnt_path+=1      
           #cof=(1-ALPHA_SAS)/(ALPHA_SAS-alpha_t*ALPHA_SAS)
           cof=0.003
           score_p=0.0
           # for individual query terms
           ft_p=0.0
           for j in range(len(queryObj.ngrams[1])):
               t=queryObj.ngrams[1][j]
               ptd=0.0
               for f in LIST_F:
                   tf_d_f = entityObj.term_freqs[f].get(t,0.0)
                   cf_f = lucene_doc.get_coll_termfreq(t, f)
                   ptc_f = cf_f/len_C_f[f] if len_C_f[f]>0 else 0.0
                   Dt = mu_d[f]*ptc_f+cof*sum_ptc[('T',f)][j]
                   Nt = mu_d[f]+cof*sum_nominator[f]
                   ptd_f=(tf_d_f+Dt)/(len_d_f[f]+Nt) if len_d_f[f]+Nt>0 else 0.0
                   weight=w[(t,True)][f]
                   ptd+=(weight*ptd_f)
               if ptd>0:
                  ft_p+=log(ptd)
                  
           f_p={(True,0):0.0,(False,6):0.0}
           for ordered,slop in f_p:
              if ordered==True and LAMBDA_O==0:
                 continue
              if ordered==False and LAMBDA_U==0:
                 continue
              for j in range(len(queryObj.ngrams[2])):
                  b=queryObj.ngrams[2][j]
                  ptd=0.0
                  for f in w[(b,ordered)]:
                      tf_d_f,cf_f=lucene_doc.get_coll_bigram_freq(b,f,ordered,slop,entityObj.title)
                      ptc_f=cf_f/len_C_f[f] if len_C_f[f]>0 else 0.0
                      Dt=mu_d[f]*ptc_f+cof*sum_ptc[('O',f)][j]
                      Nt=mu_d[f]+cof*sum_nominator[f]
                      ptd_f=(tf_d_f+Dt)/(len_d_f[f]+Nt) if len_d_f[f]+Nt>0 else 0.0
                      ptd+=w[(b,ordered)][f]*ptd_f
                  if ptd>0:
                     f_p[(ordered,slop)]+=log(ptd)*w[(b,ordered)][f]                 
           # end computing feature function
           score_p=LAMBDA_T*ft_p+LAMBDA_O*f_p[(True,0)]+LAMBDA_U*f_p[(False,6)]
           if score_p>max_score_p_cat:
              max_score_p_cat=score_p
           return
                                  
        cnt=0
        for child in iter(D[cat]):
            cnt+=1
            if cnt>TOP_CATEGORY_NUM:
               break
            if child in D:
               curPath.append(child)
               smooth_path(child,alpha_t*ALPHA_SAS)
               curPath.pop()
               sum_ptc=deepcopy(bak_sum_ptc)
               sum_nominator=deepcopy(bak_sum_nominator)
               
    # end of function smooth_path
    max_score=NEGATIVE_INFINITY
    curPath=[]
    for cat in entityObj.categories[:TOP_CATEGORY_NUM]:
        if cat not in D:
           continue
                
        sum_nominator={f:0.0 for f in LIST_F}
        bak_sum_ptc=deepcopy(sum_ptc)
        max_score_p_cat=NEGATIVE_INFINITY     
        cnt_path=0
        curPath.append(cat)
        smooth_path(cat,ALPHA_SAS)
        sum_ptc=deepcopy(bak_sum_ptc)
        del curPath[:]
        
        if max_score_p_cat>max_score:
           max_score=max_score_p_cat
    return max_score

    
def scoreWikiTree(queryObj,T_obj,lucene_wiki,field,param_server):
    curPath=[]
    bestPath=[]
    maxScore=NEGATIVE_INFINITY
    T=T_obj.T
    mu=lucene_wiki.get_avg_len(field)
    len_C = lucene_wiki.get_coll_length(field)
    LIMIT_D_PATH_LENGTH=param_server.get('LIMIT_D_PATH_LENGTH')
    ALPHA_D=param_server.get('ALPHA_D')
    LAMBDA_T=param_server.get('WIKI_LAMBDA_T')
    LAMBDA_O=param_server.get('WIKI_LAMBDA_O')
    LAMBDA_U=param_server.get('WIKI_LAMBDA_U')
  
    def scorePath(v,sum_w_len,len_path):
        # v:node sum_w_tf:sum of weighted tf, sum_w_len:sum of weighted doc len
        nonlocal T_obj,T,lucene_wiki,queryObj
        nonlocal field,maxScore
        nonlocal curPath,bestPath,sum_w_tf_ug,sum_w_tf_ob,sum_w_tf_ub

        content=' '.join(T[v][field])
        T[v]['list_term_object']=List_Term_Object(content,True,' ',None,is_bigram_used=True)
        lto=T[v]['list_term_object']
        bak_ug=sum_w_tf_ug[:]
        bak_ob=sum_w_tf_ob[:]
        bak_ub=sum_w_tf_ub[:]
        for i in range(len(queryObj.ngrams[1])):
            term=queryObj.ngrams[1][i]
            tf=lto.term_freq.get(term,0)
            sum_w_tf_ug[i]=sum_w_tf_ug[i]*ALPHA_D+tf
        
        if LAMBDA_O>0:
            for i in range(len(queryObj.ngrams[2])):
                bigram=queryObj.ngrams[2][i]
                tf=lto.bigram_freq.get(bigram,0)
                sum_w_tf_ob[i]=sum_w_tf_ob[i]*ALPHA_D+tf
        if LAMBDA_U>0:
            for i in range(len(queryObj.ngrams[2])):
                bigram=queryObj.ngrams[2][i]
                term1,term2=bigram.split()
                assert len(term1)>0 and len(term2)>0
                p2=tf=0
                # can be optimized with suffix array
                for p1 in range(len(queryObj.ngrams[1])):
                    if queryObj.ngrams[1][p1] not in [term1,term2]:
                       continue
                    for p2 in range(p1+1,len(queryObj.ngrams[1])):
                        if p2-p1-1>6:
                           break
                        elif queryObj.ngrams[1][p2] in [term1,term2]:
                             tf+=1                           
                sum_w_tf_ub[i]=sum_w_tf_ub[i]*ALPHA_D+tf  
         
        if len(T[v]['child'])>0 and len_path<LIMIT_D_PATH_LENGTH:
              for c in T[v]['child']:
                  curPath.append(T[c]['label'])
                  scorePath(c,sum_w_len*ALPHA_D+lto.length,len_path+1)
                  curPath.pop()
                  sum_w_tf_ug=bak_ug[:]
                  sum_w_tf_ob=bak_ob[:]
                  sum_w_tf_ub=bak_ub[:]
        else:
               #scorePath(-1,sum_w_len*ALPHA_D+lto.length,len_path+1)
               score_T=score_U=score_O=0.0
               for i in range(len(queryObj.ngrams[1])):
                   term=queryObj.ngrams[1][i]
                   cf=lucene_wiki.get_coll_termfreq(term,field)
                   prob_i=get_dirichlet_prob(sum_w_tf_ug[i], sum_w_len, cf, len_C, mu)
                   if prob_i>0:
                      score_T+=log(prob_i)
                      
               if LAMBDA_O>0:
                   for i in range(len(queryObj.ngrams[2])):
                       bigram=queryObj.ngrams[2][i]
                       cf=lucene_wiki.get_coll_bigram_freq(bigram,field,True,0,T_obj.title,field_id='title')[1]
                       prob_i=get_dirichlet_prob(sum_w_tf_ob[i], sum_w_len, cf, len_C, mu)
                       if prob_i>0:
                          score_O+=log(prob_i)     
               if LAMBDA_U>0:                      
                   for i in range(len(queryObj.ngrams[2])):
                       bigram=queryObj.ngrams[2][i]
                       cf=lucene_wiki.get_coll_bigram_freq(bigram,field,False,6,T_obj.title,field_id='title')[1]
                       prob_i=get_dirichlet_prob(sum_w_tf_ub[i], sum_w_len, cf, len_C, mu)
                       if prob_i>0:
                          score_U+=log(prob_i)   
               
               score=LAMBDA_T*score_T+LAMBDA_O*score_O+LAMBDA_U*score_U
               if score==0:
                  score=NEGATIVE_INFINITY           
               if score>maxScore:
                  maxScore=score
                  bestPath=curPath[:]
              
    # ----------------------------------------------------    
    for v in T[1]['child']:  
        #print ('traverse '+T[v]['label'])    
        sum_w_tf_ug=[0.0 for x in queryObj.ngrams[1]]
        sum_w_tf_ob=[0.0 for x in queryObj.ngrams[2]]
        sum_w_tf_ub=[0.0 for x in queryObj.ngrams[2]]    
        curPath.append(T[v]['label'])
        scorePath(v,0.0,1)
        curPath.pop()
    return maxScore
 
