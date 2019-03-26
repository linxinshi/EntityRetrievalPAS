# -*- coding: utf-8 -*-
from config import *
from document_object import Document_Object

class Config_Object(object):
      param_server=None
      train_param_step_server=None
      def setAttr(self,server,key,value):
          server[key]=value
          
      def __init__(self):
          # plus self. !
          
          self.param_server={}  # store model parameters for tuning
          self.train_param_step_server={}
          if MODEL_NAME in ['fsdm','sdm']:
             self.setAttr(self.param_server,'LAMBDA_T',0.8)
             self.setAttr(self.param_server,'LAMBDA_O',0.1)
             self.setAttr(self.param_server,'LAMBDA_U',0.1)
          elif MODEL_NAME=='bm25f':
                 self.setAttr(self.param_server,'k1',1.2)
                 self.setAttr(self.param_server,'b',0.75)
          else:
             self.setAttr(self.param_server,'LAMBDA_T',1.0)
             self.setAttr(self.param_server,'LAMBDA_O',0.0)
             self.setAttr(self.param_server,'LAMBDA_U',0.0)
          
          # for structure-aware smoothing
          self.setAttr(self.param_server,'SAS_MODE','BOTTOMUP')
          self.setAttr(self.param_server,'TAXONOMY','Wikipedia')  # Wikipedia or DBpedia
          self.setAttr(self.param_server,'LIMIT_SAS_PATH_LENGTH',2)
          # 10,20
          self.setAttr(self.param_server,'TOP_CATEGORY_NUM',10)
          # 30
          self.setAttr(self.param_server,'TOP_PATH_NUM_PER_CAT',500)
          self.setAttr(self.param_server,'ALPHA_SAS',0.75)

          # for doc smoothing
          self.setAttr(self.param_server,'LIMIT_D_PATH_LENGTH',10)
          self.setAttr(self.param_server,'ALPHA_D',1.0)
          self.setAttr(self.param_server,'WIKI_LAMBDA_T',1.0)
          self.setAttr(self.param_server,'WIKI_LAMBDA_O',0.0)
          self.setAttr(self.param_server,'WIKI_LAMBDA_U',0.0)