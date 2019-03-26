import lucene
# for customized field
from org.apache.lucene.document import Field
from org.apache.lucene.document import FieldType
from org.apache.lucene.index import IndexOptions

lucene.initVM(vmargs=['-Djava.awt.headless=true'])

CUSTOM_FIELD_TEXT=FieldType()
CUSTOM_FIELD_TEXT.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)
CUSTOM_FIELD_TEXT.setStored(True)
CUSTOM_FIELD_TEXT.setStoreTermVectors(True)
CUSTOM_FIELD_TEXT.setStoreTermVectorPositions(True)
CUSTOM_FIELD_TEXT.setStoreTermVectorOffsets(True)
#CUSTOM_FIELD_TEXT.setStoreTermVectorPayloads(True)
CUSTOM_FIELD_TEXT.setTokenized(True)

CUSTOM_FIELD_TEXT_BF=FieldType()
CUSTOM_FIELD_TEXT_BF.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)
CUSTOM_FIELD_TEXT_BF.setStored(False)
CUSTOM_FIELD_TEXT_BF.setStoreTermVectors(True)
CUSTOM_FIELD_TEXT_BF.setStoreTermVectorPositions(True)
CUSTOM_FIELD_TEXT_BF.setStoreTermVectorOffsets(True)
CUSTOM_FIELD_TEXT_BF.setTokenized(True)

CUSTOM_FIELD_TEXT_DF=FieldType()
CUSTOM_FIELD_TEXT_DF.setIndexOptions(IndexOptions.DOCS_AND_FREQS)
CUSTOM_FIELD_TEXT_DF.setStored(False)
CUSTOM_FIELD_TEXT_DF.setStoreTermVectors(True)
CUSTOM_FIELD_TEXT_DF.setStoreTermVectorPositions(False)
CUSTOM_FIELD_TEXT_DF.setStoreTermVectorOffsets(False)
CUSTOM_FIELD_TEXT_DF.setTokenized(True)

# Note that the difference between endOffset() and startOffset() may not be equal to termText.length(), as the term text may have been altered by a stemmer or some other filter.