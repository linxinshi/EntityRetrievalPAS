import sys, platform
import string
from gensim.corpora.wikicorpus import *

DEBUG_MODE=False
MONGO_MODE=True

if MONGO_MODE==True:
   import pymongo

def main():
    if len(sys.argv)<2:
       print ('error: too few arguments')
       print ('command:  python extract_wikipedia_article_content.py FILENAME')
       quit()

    # create mongoDB connection
    if MONGO_MODE==True:
       client = pymongo.MongoClient("localhost",27017)
       db = client.wiki2015
       table_connection=db['wiki_article_contents']   
       bulk = table_connection.initialize_ordered_bulk_op()
    
    # create file object
    filename=sys.argv[1]
    print ('processing '+filename)
    
    cnt=0
    with open(filename,'r',encoding='utf-8') as src:
         for page_pair in extract_pages(src):
             label,content,page_id=page_pair[0],page_pair[1],page_pair[2]
             
             pair_tokens=process_article((content,False,label,page_id))
             content=' '.join(pair_tokens[0])
             
             if DEBUG_MODE==True:
                print ('%s\t%s\t%s'%(label,page_id,content.encode('GBK', 'ignore')))
             if MONGO_MODE==True:
                bulk.insert({'label':label,'id':page_id,'content':content})
                
             #cnt+=1
             #if cnt>3:
                #break
                
         if MONGO_MODE==True:
            bulk.execute()
            
    if MONGO_MODE==True:
       client.close()

if __name__ == '__main__':
   if platform.python_version()[0]=='2':
      reload(sys)
      sys.setdefaultencoding('utf-8')
   main()