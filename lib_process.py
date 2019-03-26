# -*- coding: utf-8 -*- 
import string
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords
from unidecode import unidecode
    
tabin=[ord(ch) for ch in string.punctuation]
tabout=[' ' for i in range(len(tabin))]
trantab=dict(zip(tabin,tabout)) 

for ch in "–—。，、）（·！】【`‘’":
    trantab[ord(ch)]=' '
    
whitelist=set(['win','won','most','biggest','largest','fastest'])
blacklist=set(['give','also',' ','and','of','in','list','-PRON-','does','any'])
stop = set(stopwords.words('english'))
filter_list=(stop|blacklist)-whitelist
stemmer=SnowballStemmer('english')

def findOneDBEntry(conn,condition_field,value,result_field):
    item=conn.find_one({condition_field:value})
    if item is None:
       return None
    return item[result_field]
    
def findAllDBEntry(conn,condition_field,value):
    list_doc=conn.find({condition_field:value})
    if list_doc is None:
       return None
    return list_doc  
    
def save_zipped_pickle(obj, filename, protocol=-1):
    import pickle,gzip
    with gzip.open(filename, 'wb') as f:
         pickle.dump(obj, f, protocol)
         
def load_zipped_pickle(filename):
    import pickle,gzip
    with gzip.open(filename, 'rb') as f:
         loaded_object = pickle.load(f)
         return loaded_object
         
def save_obj(obj,filename):
    import pickle
    with open(filename,'wb') as f:
         pickle.dump(obj,f,pickle.HIGHEST_PROTOCOL)

def load_obj(filename):
    import pickle
    with open(filename, 'rb') as f:
         return pickle.load(f)

def remove_stopwords(line,SEPERATE_CHAR=' '):
    line=line.strip()
    if len(line)==0:
       return ''
    list=line.split(SEPERATE_CHAR)
    res_list=[]
    res_list=[word for word in list if word not in filter_list]
    return SEPERATE_CHAR.join(res_list)


def cleanSentence(line,isLower=True,SEPERATE_CHAR=' '):
    if len(line)==0:
       return ''
    
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

def cleanAccentedCharacter(line):
    return unidecode(line)
    
def superCleanSentence(line):
    # lower clean stem stopword_removed
    #line = cleanAccentedCharacter(line)    
    line = line.translate(trantab).lower()
    list_term=line.split()
    stemlist=[stemmer.stem(word) for word in list_term if word not in filter_list]
    temp_str=' '.join(stemlist)
    return temp_str     

def superCleanSentence_lemma(line):
    # lower clean lemmatize stopword_removed    
    #line = line.translate(trantab)
    import spacy
    spacy_nlp=spacy.load('en', disable=['parser', 'ner'])
    doc = spacy_nlp(line)
    temp_str=' '.join([token.lemma_ for token in doc if token.lemma_ not in filter_list])
    return ' '.join(temp_str.translate(trantab).split())  

