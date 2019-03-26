from math import log
from lib_model.lib_funcs import cosSim
def elrSim_his(queryObj,entityObj,lucene_obj,entityVec): 
    field='catchall'
    mu=lucene_obj.get_avg_len(field)
    len_C_f=lucene_obj.get_coll_length(field)

    num_bins=10
    interval=1.0/(num_bins-1)
    score=0.0
    d,docid=lucene_obj.findDoc(entityObj.title,'title',True)
    if d is None or docid is None:
        return 0.0
    entity_term_freq=lucene_obj.get_term_freq(docid,field)
    print (entity_term_freq)
    
    lengths=sum(entity_term_freq.values())
    lengths_Dir=lengths+mu
    # compute ft
    for t in queryObj.query_entities:
        sims={}
        pt=0.0
        tf_t_d_f=entity_term_freq.get(t,0)
        bins=[0 for x in range(num_bins)]
        bins_cf=[0 for x in range(num_bins)]
        cnt_total=0
        p_t_d_f=0.0
        
        for tq in entity_term_freq:
                if tq not in sims:
                   sim_t_tq=cosSim(t,tq)
                   sims[tq]=sim_t_tq
                else:
                   sim_t_tq=sims[tq]               
                # get term statistics
                cf_tq_f=lucene_obj.get_coll_termfreq(tq, field)                
                # classify into bins according to sim
                idx_bin=num_bins-1 if sim_t_tq==1.0 else int(sim_t_tq/interval)
                bins[idx_bin]+=entity_term_freq.get(tq,0)
                cnt_total+=entity_term_freq.get(tq,0)
                bins_cf[idx_bin]+=cf_tq_f
            # compute p_t_d_f according to the bin distribution
            assert cnt_total==sum(bins)
            cof=0.85
            sum_p_t_B=0.0
            prod_cof=1.0
            for idx_bin in range(num_bins-1,-1,-1):
                prod_cof*=cof
                pbc=bins_cf[idx_bin]/len_C_f if len_C_f>0 else 0.0
                ptd_B_f=(tf_t_d_f+bins[idx_bin]+mu*pbc)/lengths_Dir if lengths_Dir>0 else 0.0
                #print(mu_B_f,pbc,ptd_B_f)
                p_t_d_f+=prod_cof*ptd_B_f
            # normalize {ptd_B_f}
            #assert cnt_total!=p_t_d_f
            p_t_d_f*=((1-cof)/(cof-prod_cof*cof))
            assert p_t_d_f<=1.0 and p_t_d_f>=0
            #print ('p_t_d_f',p_t_d_f)
            pt+=p_t_d_f
        if pt>0:
           score+=log(pt)        
    return score 