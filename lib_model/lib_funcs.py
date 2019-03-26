from config import *

def get_dirichlet_prob(tf_t_d, len_d, tf_t_C, len_C, mu):
    """
    Computes Dirichlet-smoothed probability
    P(t|theta_d) = [tf(t, d) + mu P(t|C)] / [|d| + mu]

    :param tf_t_d: tf(t,d)
    :param len_d: |d|
    :param tf_t_C: tf(t,C)
    :param len_C: |C| = \sum_{d \in C} |d|
    :param mu: \mu
    :return:
    """
    if mu == 0:  # i.e. field does not have any content in the collection
       return 0
    else:
       p_t_C = tf_t_C / len_C if len_C > 0.0 else 0.0
       return (tf_t_d + mu * p_t_C) / (len_d + mu)

def get_mapping_prob(t,lucene_obj,ordered=True,slop=0,**kwargs):
    """
    Computes PRMS field mapping probability.
        p(f|t) = P(t|f)P(f) / sum_f'(P(t|C_{f'_c})P(f'))

    :param t: str
    :param coll_termfreq_fields: {field: freq, ...}
    :return Dictionary {field: prms_prob, ...}
    """
    is_bigram=kwargs.get('is_bigram',False)
    is_cached=kwargs.get('is_cached',True)
    params=kwargs.get('params',None)
    fields=kwargs.get('fields',None)
    if MODEL_NAME=='fsdm_elr':
       assert fields is not None    
    if fields is None:
       fields=LIST_F
       
    if len(fields)==1:
       # for sdm, lm
       return {fields[0]:1.0}
    if MODEL_NAME in ['mlm']:
       return {field:1/len(LIST_F) for field in LIST_F}
       
    #find cache
    if is_cached==True:
        item=lucene_obj.get_mapping_prob_cached(t,ordered,slop)
        if item is not None:
           return item['weights']
          
    coll_termfreq_fields={}
    
    for f in fields:
        if is_bigram==False:
           coll_termfreq_fields[f]=lucene_obj.get_coll_termfreq(t, f)
        else:
           flag=is_cached
           coll_termfreq_fields[f]=lucene_obj.get_coll_bigram_freq(t,f,ordered,slop,'NONE',is_cached=flag)[1]

    total_field_freq=lucene_obj.get_total_field_freq(fields)
    # calculates numerators for all fields: P(t|f)P(f)
    numerators = {}
    for f in fields:
        p_t_f = coll_termfreq_fields[f] / lucene_obj.get_coll_length(f)
        p_f = lucene_obj.get_doc_count(f) / total_field_freq
        p_f_t = p_t_f * p_f
        if p_f_t > 0:
           numerators[f] = p_f_t
        else:
           numerators[f]=0

    # calculates denominator: sum_f'(P(t|C_{f'_c})P(f'))
    denominator = sum(numerators.values())

    mapping_probs = {}
    if denominator > 0:  # if the term is present in the collection
       for f in numerators:
           mapping_probs[f] = numerators[f] / denominator
    if is_cached==True:       
       lucene_obj.insert_mapping_prob_cached(t,ordered,slop,mapping_probs)
    return mapping_probs