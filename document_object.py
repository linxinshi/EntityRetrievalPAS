
class Document_Object(object):
      dict_attr=None
      
      def __init__(self):
          self.dict_attr={}
          
      #def get(self,attrName,default_value):
          #return self.dict_attr.get(attrName,default_value)
      def __getattr__(self,attrName):
          return self.dict_attr[attrName]
      
      def setAttr(self,attrName,value):
          self.dict_attr[attrName]=value