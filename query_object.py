# coding=utf-8
from lib_process import superCleanSentence,superCleanSentence_lemma
from lib_process import *
from list_term_object import List_Term_Object
from config import *
from document_object import Document_Object
from nltk.util import ngrams

class Query_Object(Document_Object):
      contents_obj=None
      subqueries=None
      ngrams=None
      query_entities=None
      query_predicates=None
      numeric_data=None
      aggregation_node=None
      
      def __init__(self,query,structure,lucene_handler):
          super().__init__()
          mongoObj=structure.mongoObj
          # query: query_id, clusterd query, raw query
          self.setAttr('qid',query[0])
          self.setAttr('raw_query',query[2])

          if PREPROCESS_TYPE=='STEM':
             self.setAttr('querystr',superCleanSentence(query[2]))
          else:
             self.setAttr('querystr',superCleanSentence_lemma(query[2]))
          
          self.update_terms()
          self.update_bigrams()
             
      def update_terms(self):
          if self.ngrams is None:
             self.ngrams={}
          self.ngrams[1] = ' '.join(self.querystr.split()).split()
          
      def update_bigrams(self):
          if self.ngrams is None:
             self.ngrams={}
          bigram_pairs=list(ngrams(self.ngrams[1],2))
          self.ngrams[2] = [pair[0]+' '+pair[1] for pair in bigram_pairs]
          
                        
        