# coding=utf-8
import string
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import defaultdict
from lib_process import stemSentence,remove_stopwords,cleanSentence
from list_term_object import List_Term_Object

class Doc_Tree_Object:
      T=None
      title=None
      size=None
      depth2idx=None
      used_content_field=None
      temp_max=None
      
      def __init__(self,article):
          article=article.strip()
          self.depth2idx={}
          self.size=0
          self.used_content_field='stemmed_contents'
          self.T=self.docTree()
          self.initializeNode(self.T,'ROOT',1)
          self.createDocumentTree(self.T,article)
          self.temp_max=0
          
      def docTree(self): 
          return defaultdict(self.docTree)

      def calcSectionDepth(self,line):
          dep=0
          for chr in line:
              if chr=='=':
                 dep+=1
              else:
                 break
          return dep

      def initializeNode(self,T,label,depth):
          self.size+=1
          p=self.size
          #print ('create label=%s  depth=%d'%(label,depth))
          T[p]['stemmed_contents']=[]
          T[p]['list_term_object']=None
          T[p]['label']=label
          T[p]['depth']=depth
          T[p]['child']=[]
          T[p]['father']=None
          
          if depth not in self.depth2idx:
             self.depth2idx[depth]=[]
          self.depth2idx[depth].append(p)
          
          return p
            
      def createDocumentTree(self,T,article):
          cur_node=1
          for line in article.split('\n'):
              depth=self.calcSectionDepth(line)
              if line.startswith('=')==False or line.endswith('=')==False:
                 T[cur_node][self.used_content_field].append(line)
              else:
                 # find new section
                 label=line.split('='*depth)[1]
                 new_node=self.initializeNode(T,label,depth)
                 if T[cur_node]['depth']>=depth:
                    while (cur_node is not None) and (T[cur_node]['depth']>=depth):
                          cur_node=T[cur_node]['father']
                 T[cur_node]['child'].append(new_node)
                 T[new_node]['father']=cur_node
                 cur_node=new_node      
          return T

      def traverse(self,root=1):
          T=self.T
          print ('label=%s father=%s depth=%d'%(T[root]['label'],T[root]['father'],T[root]['depth']))
          print ('child='+str(T[root]['child']))
          print ('contents=%s'%(str(T[root][self.used_content_field])))
          #print ('contents=%s'%(str(T[root]['contents']).encode('utf-8','ignore')))
          print ('-----')
          for c in T[root]['child']:
              self.traverse(c)

      def getSubTreePathContent(self,root,list_str_node,s):
          T=self.T
          str=' '.join(T[root][self.used_content_field])
          st=s+' '+str
          if len(T[root]['child'])==0:
             list_str_node.append(st.strip())
             return
          for c in T[root]['child']:
              self.getSubTreePathContent(c,list_str_node,st)
      '''
      def getSubTreePathContent(self,root):
          T=self.T
          str=' '.join(T[root][self.used_content_field])
          list_str_path=[]
          for c in T[root]['child']:
              list_str_c=self.getSubTreePathContent(c)
              list_str_path=[(str+' '+str_c).strip() for str_c in list_str_c]
          return list_str_path
      '''    
      def getSubTreeContent(self,root):
          T=self.T
          str=' '.join(T[root][self.used_content_field])
          for c in T[root]['child']:
              str=str+' '+self.getSubTreeContent(c)
          return str.strip()
          
      def getNodeByDepth(self,depth):
          if depth in self.depth2idx:
             return self.depth2idx[depth]
          else:
             return []
             
      def getSubTreePathContentByDepth(self,depth,list_str_node):
          # notice, output is an iterator
          list_node=self.getNodeByDepth(depth)
          list_temp=[]
          for v in list_node:
              s=''
              self.getSubTreePathContent(v,list_str_node,s)
          
      def getSubTreeContentByDepth(self,depth):
          # notice, output is an iterator
          list_node=self.getNodeByDepth(depth)
          list_temp=[self.getSubTreeContent(v) for v in list_node]
          return [item for item in list_temp if len(item)>10]
      
      def getFormattedOutput(self):
          list_section_content=[]
          self.traverseAndOutput(1,1,list_section_content)
          return '\n'.join(list_section_content)
      
      def traverseAndOutput(self,v,depth,list_section_content):
          label=self.T[v]['label']
          temp_line=' '.join(self.T[v][self.used_content_field])
          content=temp_line
          if depth>1:
             section=('%s%s%s\n%s'%('='*depth,label,'='*depth,content))
          else:
             section=('%s'%(content))
          list_section_content.append(section)
          for c in self.T[v]['child']:
              self.traverseAndOutput(c,depth+1,list_section_content)