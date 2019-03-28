#coding='UTF-8'
import sys, os, string, platform
from gensim.corpora.wikicorpus import *
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords


import lucene
from java.io import File
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, StringField, TextField, StoredField
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, DirectoryReader, Term
from org.apache.lucene.store import MMapDirectory
from org.apache.lucene.util import Version
from org.apache.lucene.queryparser.classic import ParseException, QueryParser
from org.apache.lucene.search import IndexSearcher, Query, ScoreDoc, TopScoreDocCollector
from org.apache.lucene.search.similarities import BM25Similarity
from org.apache.lucene.search import PhraseQuery, BooleanQuery, TermQuery, BooleanClause

from org.apache.lucene.document import FieldType

# has java VM for Lucene been initialized
lucene_vm_init = False


DEBUG_MODE=False

def remove_stopwords(line,SEPERATE_CHAR=' '):
    line=line.strip()
    if len(line)==0:
       return ''
    list=line.split(SEPERATE_CHAR)
    res_list=[]
    whitelist=set(['win','won','most','biggest','largest','fastest'])
    blacklist=set(['give','also',' ','and','of','in','list'])
    stop = set(stopwords.words('english'))
    
    filter_list=(stop|blacklist)-whitelist
    res_list=[word for word in list if word not in filter_list]
    return SEPERATE_CHAR.join(res_list)


def cleanSentence(line,isLower=True,SEPERATE_CHAR=' '):
    if len(line)==0:
       return ''
    
    tabin=[ord(ch) for ch in string.punctuation]
    tabout=[' ' for i in range(len(tabin))]
    trantab=dict(zip(tabin,tabout))
    
    for ch in "–—。，、）（·！】【`":
        trantab[ord(ch)]=' '
    
    line = line.translate(trantab)
    if isLower==True:
       line=line.lower()
    line=SEPERATE_CHAR.join(line.split())
    return line

def stemSentence(line,stemmer=SnowballStemmer('english'),isCleanNeeded=True):
    if isCleanNeeded==True:
       line=cleanSentence(line,True)
    if stemmer is None:
       stemmer=SnowballStemmer('english')
    list=line.split(' ')
    stemlist=[stemmer.stem(word) for word in list]
    res=' '.join(stemlist)
    return res    

def addDoc(w,data):
    doc = Document()
    #print ('----------------------------')
    for field in data:
        value,type=data[field][0],data[field][1]
        if type=='StringField':
           doc.add(StringField(field,value,Field.Store.YES))
        elif type=='TextField':
           doc.add(TextField(field,value,Field.Store.YES))
        elif type=='CUSTOM_FIELD_TEXT':
           doc.add(Field(field,value,CUSTOM_FIELD_TEXT))
        elif type=='INTEGER_STORED':
           doc.add(StoredField(field,value))
        else:
           print ('UNKNOWN FIELD')
           
    w.addDocument(doc)
    
    
def main():
    if len(sys.argv)<2:
       print ('error: too few arguments')
       print ('command:  python build_index_wikipedia.py FILENAME')
       quit()

    # create file object
    filename=sys.argv[1]
    print ('processing '+filename)
    
    cnt=0
    stemmer=SnowballStemmer('english')

    try:
       lucene.initVM(vmargs=['-Djava.awt.headless=true'])
       lucene_vm_init = True
    except:
       print ('JavaVM already running')
       
    LUCENE_INDEX_DIR='mmapDirectory\\index_wikipedia_2015'
    is_index_Exist = os.path.exists(LUCENE_INDEX_DIR)
    # specify index path 
    index_mm = MMapDirectory(Paths.get(LUCENE_INDEX_DIR))
    
    # configure search engine
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    #config=config.setRAMBufferSizeMB(1024.0)  # experimental setting !!
    
    # write data to index
    if not is_index_Exist:
       print ('begin backup code files')
       system_flag=platform.system()
       cmd='robocopy %s %s\code_files *.py'%(r'%cd%',LUCENE_INDEX_DIR) if system_flag=='Windows' else 'cp *.py %s\code_files'%(LUCENE_INDEX_DIR)
       os.system(cmd)
        
       w = IndexWriter(index_mm,config)
       
    data={}
    with open(filename,'r',encoding='utf-8') as src:
         for page_pair in extract_pages(src):
             label,content,page_id=page_pair[0],page_pair[1],page_pair[2]
             
             pair_tokens=process_article((content,False,label,page_id))
             content=remove_stopwords(' '.join(pair_tokens[0]),' ')
             
             if len(content.split())<10:
                continue
             
             stemmed_content=stemSentence(content,stemmer,False)
             
             if DEBUG_MODE==True:
                try:
                   print ('%s\n%s\n%s\n%s'%(label,page_id,content,stemmed_content))
                except:
                   print ('encoding error')
             
             data.clear()
             data['label']=(label,'StringField')
             data['label_lower']=(label.lower(),'StringField')
             data['label_lower_text']=(label.lower(),'TextField')
             data['wiki_id']=(page_id,'StringField')
             #data['content']=(content,'TextField')
             data['stemmed_content']=(stemmed_content,'TextField')
             addDoc(w,data)
             
             cnt+=1
             #if cnt>20:
                #break
             if cnt%5000==0:
                print ('finish %d'%(cnt))
                
    w.close()

if __name__ == '__main__':
   main()