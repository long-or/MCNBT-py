from enum import Enum

class TAG(Enum):
    END        = 0
    BYTE       = 1
    SHORT      = 2
    INT        = 3
    LONG       = 4
    FLOAT      = 5
    DOUBLE     = 6
    BYTE_ARRAY = 7
    STRING     = 8
    LIST       = 9
    COMPOUND   = 10
    INT_ARRAY  = 11
    LONG_ARRAY = 12
TAGLIST = {}

from . import Codec
from .snbt import *
from .error import *
from .tags import *
# from .io import *

TAGLIST[TAG.END]        = TAG_End
TAGLIST[TAG.BYTE]       = TAG_Byte
TAGLIST[TAG.SHORT]      = TAG_Short
TAGLIST[TAG.INT]        = TAG_Int
TAGLIST[TAG.LONG]       = TAG_Long
TAGLIST[TAG.FLOAT]      = TAG_Float
TAGLIST[TAG.DOUBLE]     = TAG_Double
TAGLIST[TAG.STRING]     = TAG_String
TAGLIST[TAG.LIST]       = TAG_List
TAGLIST[TAG.COMPOUND]   = TAG_Compound
TAGLIST[TAG.BYTE_ARRAY] = TAG_ByteArray
TAGLIST[TAG.INT_ARRAY]  = TAG_IntArray
TAGLIST[TAG.LONG_ARRAY] = TAG_LongArray

# __all__ = []
