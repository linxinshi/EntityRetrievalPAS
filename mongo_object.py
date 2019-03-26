import pymongo
class Mongo_Object(object):
      client = None
      db = None
      conn_wiki = None
      conn_acs = None # article category sentence
      conn_it = None # DBpedia instance types
      conn_wiki_aws = None # article_with_section
      conn_page_id = None
      
      def __init__(self,hostname,port):
          self.client = pymongo.MongoClient(hostname,port)
          self.db = (self.client).wiki2015
          self.conn_wiki_aws=self.db['wiki_article_contents_with_section_clean']
          self.conn_page_id=self.db['page_id']
          self.conn_acs=self.db['article_categories']
          self.conn_it=self.db['instance_types']
          
      def __del__(self):
          (self.client).close()