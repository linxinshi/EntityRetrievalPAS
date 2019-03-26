# coding=utf-8
import networkx
from mongo_object import Mongo_Object
from lib_process import load_zipped_pickle
from config import *

class Structure_Object(object):
      entityScore=None
      entityObjects=None
      currentEntity=None
      idx_entity=None

      cat_dag=None
      mongoObj=None
      
      def __init__(self,conf_paras,id_process=0):
          self.entityScore={}
          self.entity2ID={}
          self.ID2entity={}
          self.entityObjects={}
          self.entityReport={}
          self.idx_entity=0
          self.currentEntity=set()
          
          # initialize mongodb client
          self.mongoObj=Mongo_Object('localhost',mongo_port)
          
          # initialize category dag
          if IS_SAS_USED==True:
             print ('id=%d  loading category structure'%(id_process))
             if conf_paras.param_server.get('SAS_MODE')=='TOPDOWN':
                self.cat_dag=load_zipped_pickle(PATH_CATEGORY_DAG).reverse()
             else:
                self.cat_dag=load_zipped_pickle(PATH_CATEGORY_DAG)
             print ('id=%d  finish loading category structure'%(id_process))
          
      def clear(self):
          # self.partScore.clear()
          #self.entityObjects.clear()
          self.entityScore.clear()
          self.idx_entity=0
          self.currentEntity.clear()
                
      
