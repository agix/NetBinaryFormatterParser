import sys
import json
import struct
from base64 import b64decode, b64encode

# def Length(string):
#     ret = ''
#     Length = struct.pack('<I', len(string))
#     newLength = ''
#     if len(string)>128:
#         ret = '\x80\x08'
#     else :
#         for i in range(len(Length)-1, -1, -1):
#             if Length[i]=='\x00':
#                 continue
#             else:
#                 newLength = newLength+Length[:i+1]
#                 break

#         for l in newLength:
#             if ord(l)&128:
#                 ret += chr(ord(l)^128)
#             else:
#                 ret += l
#         if len(ret)==0:
#             ret = '\x00'
#     return ret

def Length(string):
    value = len(string)
    ret = ''
    while value >= 0x80:
        ret += chr((value | 0x80)&0xff)
        value >>= 7
    ret += chr(value)

    return ret

def LengthPrefixedString(string):
    ret = Length(string)+str(string)
    return ret

def Token_Null(o):
    return ''

def Token_Pair(o):
    one = o[0]
    two = o[1]
    return SerializeValue(one) + SerializeValue(two)

def Token_String(o):
    return LengthPrefixedString(o)

def Token_ArrayList(oList):
    res = struct.pack('<B', len(oList))
    for o in oList:
        res += SerializeValue(o)
    return res

def Token_Int32(o):
    return Length("a"*o)

def Token_IndexedStringAdd(o):
    return LengthPrefixedString(o)

def Token_BinarySerialized(o):
    return LengthPrefixedString(b64decode(o))

TokenEnum = {
# 'Token_Int16':[1, Token_Int16],
'Token_Int32':[2, Token_Int32],
# 'Token_Byte':[3, Token_Byte],
# 'Token_Char':[4, Token_Byte],
'Token_String':[5, Token_String],
# 'Token_DateTime':[6, Token_DateTime],
# 'Token_Double':[7, Token_Double],
# 'Token_Single':[8, Token_Single],
# 'Token_Color':[9, Token_Color],
# 'Token_KnownColor':[10, Token_Color],
# 'Token_IntEnum':[11, Token_IntEnum],
# 'Token_EmptyColor':[12, Token_Color],
'Token_Pair':[15, Token_Pair],
# 'Token_Triplet':[16, Token_Triplet],
# 'Token_Array':[20, Token_Array],
# 'Token_StringArray':[21, Token_StringArray],
'Token_ArrayList':[22, Token_ArrayList],
# 'Token_Hashtable':[23, Token_ArrayList],
# 'Token_HybridDictionary':[24, Token_ArrayList],
# 'Token_Type':[25, Token_Type],
# 'Token_Unit':[27, Token_Unit],
# 'Token_EmptyUnit':[28, Token_EmptyUnit],
# 'Token_EventValidationStore':[29, Token_EventValidationStore],
'Token_IndexedStringAdd':[30, Token_IndexedStringAdd],
# 'Token_IndexedString':[31, Token_IndexedString],
# 'Token_StringFormatted':[40, Token_StringFormatted],
# 'Token_TypeRefAdd':[41, Token_TypeRefAdd],
# 'Token_TypeRefAddLocal':[42, Token_TypeRefAdd],
# 'Token_TypeRef':[43, Token_TypeRef],
'Token_BinarySerialized':[50, Token_BinarySerialized],
# 'Token_SparseArray':[60, Token_SparseArray],
'Token_Null':[100, Token_Null],
# 'Token_EmptyString':[101, Token_EmptyString],
# 'Token_ZeroInt32':[102, Token_ZeroInt32],
# 'Token_True':[103, Token_True],
# 'Token_False':[104, Token_False]
}

Marker_Format = 0xff
Marker_Version_1 = 0x01

def SerializeValue(o):
    token = o.keys()[0]
    value = ''
    value += struct.pack('<B', TokenEnum[token][0])
    value += TokenEnum[token][1](o[token])
    return value

if len(sys.argv) < 2:
    print "Usage: %s <stream>"%sys.argv[0]
    sys.exit(0)

f=open(sys.argv[1])
myObject = json.loads(f.read())
f.close()

binary = chr(Marker_Format) + chr(Marker_Version_1)

binary += SerializeValue(myObject)

f = open(sys.argv[1]+'_binary', 'w')
f.write(b64encode(binary))
f.close()