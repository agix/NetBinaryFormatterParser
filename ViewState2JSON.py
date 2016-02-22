import sys
import struct
import datetime
import json
from base64 import b64decode, b64encode

def printverbose(string):
    if len(sys.argv) > 2 and sys.argv[2] == '-v':
        print string

def popp(s, n):
    a = ''
    for c in range(n):
        a += s.pop(0)
    return a

Marker_Format = 0xff
Marker_Version_1 = 0x01

def Length(s):
    l = 0
    shift = 0
    c = True
    while c:
        byte = struct.unpack('<B', popp(s, 1))[0]
        if byte&128:
            byte^=128
        else:
            c = False
        l += byte<<shift
        shift+=7
    return l

def LengthPrefixedString(s):
    return popp(s, Length(s))

def Token_Null(s):
    return None

def Token_EmptyString(s):
    return ""

def Token_String(s):
    return LengthPrefixedString(s)

def Token_ZeroInt32(s):
    return 0

def Token_Int32(s):
    return Length(s)

def Token_Pair(s):
    return (DeserializeValue(s), DeserializeValue(s))

def Token_Triplet(s):
    return (DeserializeValue(s), DeserializeValue(s), DeserializeValue(s))

StringList = []

def Token_IndexedString(s):
    index = struct.unpack('<B',popp(s,1))[0]
    return StringList[index]

def Token_IndexedStringAdd(s):
    StringList.append(Token_String(s))
    return StringList[-1]

def Token_ArrayList(s):
    count = Length(s)
    array = []
    for i in range(count):
        array.append(DeserializeValue(s))
    return array

def Token_True(s):
    return True

def Token_False(s):
    return False

def Token_Byte(s):
    return struct.unpack('<B', popp(s,1))[0]

def Token_Double(s):
    return struct.unpack('<Q', popp(s,8))[0]

def Token_DateTime(s):
    return Token_Double(s)

def Token_Int16(s):
    return struct.unpack('<H', popp(s,2))[0]

def Token_Single(s):
    return struct.unpack('<I', popp(s,4))[0]

TypeList = []

def Token_Type(s):
    token = struct.unpack('<B',popp(s,1))[0]
    printverbose(TokenEnum[token][0])
    return RecordTypeEnum[RecordType][1](s)

def Token_TypeRef(s):
    index = Length(s)
    return TypeList[index]

def Token_TypeRefAdd(s):
    TypeList.append(Token_String(s))
    return TypeList[-1]

def Token_StringArray(s):
    count = Length(s)
    array = []
    for i in range(count):
        array.append(Token_String(s))
    return array

def Token_Array(s):
    type = Token_Type(s)
    count = Length(s)
    array = []
    for i in range(count):
        array.append(DeserializeValue(s))
    return array

def Token_IntEnum(s):
    value = {}
    value[Token_Type(s)] = Length(s)
    return value

def Token_Color(s):
    return Token_Int32(s)

def Token_EmptyColor(s):
    return None

def Token_KnownColor(s):
    return Length(s)

def Token_Unit(s):
    value = {}
    value[Token_Double(s)] = Token_Int32(s)
    return value

def Token_EmptyUnit(s):
    return None

def Token_EventValidationStore(s):
    print "Not Implemented"
    sys.exit()

def Token_SparseArray(s):
    print "Not Implemented"
    sys.exit()

def Token_StringFormatted(s):
    value = {}
    value[Token_Type(s)] = Token_String(s)
    return value

def Token_BinarySerialized(s):
    return b64encode(LengthPrefixedString(s))

def Token_HybridDictionary(s):
    count = Length(s)
    array = []
    for i in range(count):
        array.append({'Key': DeserializeValue(s), 'Value': DeserializeValue(s)})
    return array

TokenEnum = {
1:['Token_Int16', Token_Int16],
2:['Token_Int32', Token_Int32],
3:['Token_Byte', Token_Byte],
4:['Token_Char', Token_Byte],
5:['Token_String', Token_String],
6:['Token_DateTime', Token_DateTime],
7:['Token_Double', Token_Double],
8:['Token_Single', Token_Single],
9:['Token_Color', Token_Color],
10:['Token_KnownColor', Token_Color],
11:['Token_IntEnum', Token_IntEnum],
12:['Token_EmptyColor', Token_Color],
15:['Token_Pair', Token_Pair],
16:['Token_Triplet', Token_Triplet],
20:['Token_Array', Token_Array],
21:['Token_StringArray', Token_StringArray],
22:['Token_ArrayList', Token_ArrayList],
23:['Token_Hashtable', Token_ArrayList],
24:['Token_HybridDictionary', Token_HybridDictionary],
25:['Token_Type', Token_Type],
27:['Token_Unit', Token_Unit],
28:['Token_EmptyUnit', Token_EmptyUnit],
29:['Token_EventValidationStore', Token_EventValidationStore],
30:['Token_IndexedStringAdd', Token_IndexedStringAdd],
31:['Token_IndexedString', Token_IndexedString],
40:['Token_StringFormatted', Token_StringFormatted],
41:['Token_TypeRefAdd', Token_TypeRefAdd],
42:['Token_TypeRefAddLocal', Token_TypeRefAdd],
43:['Token_TypeRef', Token_TypeRef],
50:['Token_BinarySerialized', Token_BinarySerialized],
60:['Token_SparseArray', Token_SparseArray],
100:['Token_Null', Token_Null],
101:['Token_EmptyString', Token_EmptyString],
102:['Token_ZeroInt32', Token_ZeroInt32],
103:['Token_True', Token_True],
104:['Token_False', Token_False]
}

def DeserializeValue(s):
    token = struct.unpack('<B',popp(s,1))[0]
    printverbose(TokenEnum[token][0])
    value = {}
    value[TokenEnum[token][0]] = TokenEnum[token][1](s)
    return value


def Deserialize(s):
    formatMarker = struct.unpack('<B',popp(s,1))[0]
    if formatMarker == Marker_Format:
        versionMarker = struct.unpack('<B',popp(s,1))[0]
        if versionMarker == Marker_Version_1:
            return DeserializeValue(s)
        else:
            return {}
    else:
        return {}

if len(sys.argv) < 2:
    print "Usage: %s <stream> (-v)"%sys.argv[0]
    sys.exit(0)

f=open(sys.argv[1])
stream = list(b64decode(f.read()))
f.close()

myObject = Deserialize(stream)

print json.dumps(myObject)

if len(stream) > 0:
    print ''.join(stream).encode("hex")