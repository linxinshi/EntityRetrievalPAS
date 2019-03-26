from lib_process import *
from list_term_object import List_Term_Object
from config import *
from doc_tree_object import Doc_Tree_Object

from document_object import Document_Object
from nltk.util import ngrams

class Entity_Object(Document_Object):
      categories=None
      bigrams=None
      dict_attr=None
      wiki_doc_tree=None
      term_freqs=None
      lengths=None
      fields=None
      
      def __init__(self):
          self.dict_attr={}
      def updateFromIndex(self,d_pair,mongoObj,lucene_obj):
          # d_pair:(document,docid) entity: dict   
          entity,docid=d_pair[0],d_pair[1]
          for idf in entity.iterator():
              # only show fields that are set to stored
              self.setAttr(idf.name(),idf.stringValue())  
          
          if IS_SAS_USED==True:
             self.update_categories(mongoObj)

          self.update_term_freqs(docid,lucene_obj)
          
          if IS_WIKI_DOC_TREE_USED==True:
             wiki_id=findOneDBEntry(mongoObj.conn_page_id,'uri',self.uri,'wiki_id')
             article=findOneDBEntry(mongoObj.conn_wiki_aws,'wiki_id',wiki_id,'content')
             if article is not None:
                self.wiki_doc_tree=Doc_Tree_Object(article)
                self.wiki_doc_tree.title=self.title
          
      def update_term_freqs(self,docid,lucene_obj):
          self.term_freqs={}
          self.lengths={}
          
          tv_fields=lucene_obj.get_term_vectors(docid)
          for f in tv_fields.iterator():
              # condition may be problematic
              if MODEL_NAME not in ['fsdm_elr'] and f not in LIST_F:
                 continue
        
              terms=tv_fields.terms(f)
              try:
                self.term_freqs[f]=lucene_obj.get_term_freq(docid,f,terms)
                self.lengths[f]=sum(self.term_freqs[f].values())
              except:
                self.term_freqs[f]={}
                self.lengths[f]=0
                
              if MODEL_NAME not in ['fsdm_elr']:
                  for f in LIST_F:
                        if f not in self.term_freqs:
                           self.term_freqs[f]={}
                           self.lengths[f]=0
          self.fields=self.term_freqs
          #print (self.lengths)
          '''    
          for f in LIST_F:
              try:
                self.term_freqs[f]=lucene_obj.get_term_freq(docid,f)
                self.lengths[f]=sum(self.term_freqs[f].values())
              except:
                self.term_freqs[f]={}
                self.lengths[f]=0
          '''
          
      def update_categories(self,mongoObj):
          conn=mongoObj.conn_acs if TAXONOMY=='Wikipedia' else mongoObj.conn_it
          field='categories' if TAXONOMY=='Wikipedia' else 'type'
          if conn==None:
             return
          item=conn.find_one({'uri':self.uri})
          if item is None:
             self.categories=[]
             return
          if TAXONOMY=='Wikipedia':
             self.categories=item[field]
          else:
             temp=item[field]
             pos=temp.rfind('/')
             self.categories=[temp[pos+1:-1]]
          
      def update_bigrams(self,field,value):
          if self.bigrams==None:
             self.bigrams={}
          for bigram in ngrams(value.split(),2):
              if (field,bigram) not in self.bigrams:
                 self.bigrams[(field,bigram)]=0
              self.bigrams[(field,bigram)]+=1          

