import lucene
from java.io import File
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis.core import SimpleAnalyzer
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, DirectoryReader, Term
from org.apache.lucene.store import MMapDirectory
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher, ScoreDoc, TopScoreDocCollector,TermQuery
from org.apache.lucene.search.similarities import BM25Similarity
from org.apache.lucene.util import BytesRef, BytesRefIterator

from org.apache.lucene.search.spans import SpanQuery, SpanTermQuery,SpanNearQuery 
from org.apache.lucene.search.spans import SpanWeight, Spans
from org.apache.lucene.search import DocIdSetIterator
from config import LIST_F

class Lucene_Object(object):
      lucene_vm_init=None
      index_name=None
      index_dir=None
      index_mm=None
      analyzer=None
      config=None
      reader=None
      searchers=None

      is_bigram_cache_used=None
      conn_bigram_tf_cache=None
      conn_bigram_cf_cache=None
      conn_mapping_prob_cache=None
      total_field_freq=None
      
      def __init__(self,LUCENE_INDEX_DIR,similarity='BM25',lucene_vm_flag=False,is_bigram_cache_used=False,mongoObj=None):
          if lucene_vm_flag==False:
             lucene.initVM(vmargs=['-Djava.awt.headless=true'])
          self.lucene_vm_init=True
          self.index_dir=LUCENE_INDEX_DIR
          self.index_mm = MMapDirectory(Paths.get(LUCENE_INDEX_DIR))
          self.analyzer = SimpleAnalyzer()
          self.config = IndexWriterConfig(self.analyzer)
          self.reader = DirectoryReader.open(self.index_mm)
          self.searchers = []
          self.searchers.append(IndexSearcher(self.reader))
          if similarity=='BM25':
            (self.searchers[0]).setSimilarity(BM25Similarity())
            
          # load bigram cache
          self.is_bigram_cache_used=is_bigram_cache_used
          if is_bigram_cache_used==True:
             seperate_char='/' if self.index_dir.find('/')>-1 else '\\'
             index_name=self.index_dir.split(seperate_char)[-1]
             self.index_name=index_name             
             self.conn_bigram_tf_cache=mongoObj.db[index_name+'_tf_cache']
             self.conn_bigram_cf_cache=mongoObj.db[index_name+'_cf_cache']
             if 'stemmed_wikipedia' in LIST_F or 'wikipedia' in LIST_F:
                self.conn_mapping_prob_cache=mongoObj.db[index_name+'_mapping_prob_cache_with_wikipedia']
             else:
                self.conn_mapping_prob_cache=mongoObj.db[index_name+'_mapping_prob_cache']      
      
      def getSecondarySearcher(self):
          if len(self.searchers)<2:
             self.searchers.append(IndexSearcher(self.reader))
          return self.searchers[1]
      
      def retrieve(self,query,field,hitsPerPage):
          querystr=query
          
          # build query
          q_lucene = QueryParser(field, self.analyzer).parse(querystr)
          # build searcher    
          searcher=(self.searchers[0])
          collector = TopScoreDocCollector.create(hitsPerPage)
          searcher.search(q_lucene, collector);
          hits = collector.topDocs().scoreDocs;
          
          len_hits=len(hits)
          results=[(searcher.doc(hits[j].doc),hits[j].doc) for j in range(len_hits)]
          return results
          
      def findDoc(self,title,field,is_docid_required=False):
          searcher=self.getSecondarySearcher()
          t=Term(field,title)
          query=TermQuery(t)
          docs=searcher.search(query,1)
          if docs.totalHits==0:
             if is_docid_required==True:
                 return None,None
             else:
                 return None
          docID=(docs.scoreDocs)[0].doc
          d=searcher.doc(docID)
          if is_docid_required==False:
             return d
          else:
             return d,docID
                      
      def get_term_freq(self,docid,field,terms=None):
          if terms is None:
             terms=self.reader.getTermVector(docid,field)
          term_freq={}
          if terms is not None:
             te_itr=terms.iterator()
             for bytesref in BytesRefIterator.cast_(te_itr):
                 t=bytesref.utf8ToString()
                 freq=te_itr.totalTermFreq()
                 term_freq[t]=freq                
          return term_freq
      def get_term_vectors(self,docid):
          # get term vectors for all indexed fields
          return self.reader.getTermVectors(docid)       
          
      def get_coll_termfreq(self, term, field):
          """ 
          Returns collection term frequency for the given field.

          :param term: string
          :param field: string, document field
          :return: int
          """
          return self.reader.totalTermFreq(Term(field, term))

      def get_doc_freq(self, term, field):
          """
          Returns document frequency for the given term and field.

          :param term: string, term
          :param field: string, document field
          :return: int
          """
          return self.reader.docFreq(Term(field, term))

      def get_doc_count(self, field):
          """
          Returns number of documents with at least one term for the given field.

          :param field: string, field name
          :return: int
          """
          return self.reader.getDocCount(field)

      def get_coll_length(self, field):
          """ 
          Returns length of field in the collection.

          :param field: string, field name
          :return: int
          """
          return self.reader.getSumTotalTermFreq(field)

      def get_avg_len(self, field):
          """ 
          Returns average length of a field in the collection.

          :param field: string, field name
          """
          
          n = self.reader.getDocCount(field)  # number of documents with at least one term for this field
          len_all = self.reader.getSumTotalTermFreq(field)
          if n == 0:
             return 0
          else:
             return len_all / float(n)
             
      def get_total_field_freq(self,fields):
          """Returns total occurrences of all fields"""
          if self.total_field_freq is None:
             total_field_freq = 0
             for f in fields:
                 total_field_freq += self.get_doc_count(f)
                 self.total_field_freq = total_field_freq
          return self.total_field_freq    
          
      def get_mapping_prob_cached(self,term,ordered,slop):
          if self.conn_mapping_prob_cache is not None:
             return self.conn_mapping_prob_cache.find_one({'term':term,'ordered':ordered,'slop':slop})
          else:
             return None
      def insert_mapping_prob_cached(self,term,ordered,slop,weights):
          if self.conn_mapping_prob_cache is not None:
             self.conn_mapping_prob_cache.insert({'term':term,'ordered':ordered,'slop':slop,'weights':weights})
                     
      def get_coll_bigram_freq(self,bigram,field,ordered,slop,title,**kwargs):
          field_id=kwargs.get('field_id','title')
          is_cached=kwargs.get('is_cached',True)
          is_bigram_cache_used=(self.is_bigram_cache_used and is_cached)
          if is_bigram_cache_used:
             item_tf=self.conn_bigram_tf_cache.find_one({field_id:title,'bigram':bigram,'field':field,'ordered':ordered,'slop':slop})
             item_cf=self.conn_bigram_cf_cache.find_one({'bigram':bigram,'field':field,'ordered':ordered,'slop':slop})
             if item_cf is not None:
                cf=int(item_cf['value'])
                if item_tf is not None:
                   tf=int(item_tf['value'])
                else:
                   tf=0
                return (tf,cf)
          searcher=self.getSecondarySearcher()
          SpanClauses=[]
          #print ('bigram='+bigram)
          for term in bigram.split(' '):
              #print (field,term)
              SpanClauses.append(SpanTermQuery(Term(field,term)))
          #print ('--------')
          builder=SpanNearQuery.Builder(field,ordered)
          for clause in SpanClauses:
              builder.addClause(clause)
          builder.setSlop(slop) 
          q_lucene=builder.build()
          
          sw=q_lucene.createWeight(searcher,False)
          list_leaves=self.reader.getContext().leaves()
          cf=0
          doc_phrase_freq={}
          for leave in list_leaves:
              spans = sw.getSpans(leave, SpanWeight.Postings.POSITIONS)
              if spans is None:
                 continue
              while spans.nextDoc()!=DocIdSetIterator.NO_MORE_DOCS:
                    id=leave.reader().document(spans.docID()).get(field_id)
                    if is_bigram_cache_used:
                       item_tf=self.conn_bigram_tf_cache.find_one({field_id:id,'bigram':bigram,'field':field,'ordered':ordered,'slop':slop})
                       if item_tf is not None:
                          tf=item_tf['value']
                          doc_phrase_freq[id]=tf
                          cf+=tf
                          continue
                       
                    if id not in doc_phrase_freq:
                       doc_phrase_freq[id]=0
                    while spans.nextStartPosition()!=Spans.NO_MORE_POSITIONS:
                          doc_phrase_freq[id]+=1
                          cf+=1
                    
                    if is_bigram_cache_used:
                       self.conn_bigram_tf_cache.insert({field_id:id,'bigram':bigram,'field':field,'ordered':ordered,'slop':slop,'value':doc_phrase_freq[id]})

          if is_bigram_cache_used:
             self.conn_bigram_cf_cache.insert({'bigram':bigram,'field':field,'ordered':ordered,'slop':slop,'value':cf})
          tf=doc_phrase_freq.get(title,0)
          return tf,cf