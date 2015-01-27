import sys
import struct
import datetime

theClass = {}

def nothing(value):
    return value

def date(s, options):
    return struct.unpack(options[1], popp(s, options[0]))[0]

def unpack_value(s, options):
    return struct.unpack(options[1], popp(s,options[0]))[0]

def parse_value(object, s):
    if object[0]=="Primitive":
        print object[1][0]+' : '+str(object[1][1](s, object[1][2]))
    else:
        parse_object(s)

def parse_values(objectID, s):
    myClass = theClass[objectID]
    a = 0
    for object in myClass[0]:
        print myClass[1][a]+' : '+object[0]
        a+=1
        parse_value(object, s)

def LengthPrefixedString(s, options=""):
    Length = 0
    byte = 128
    while byte&128:
        Length = Length << 8
        byte = struct.unpack('<B', popp(s, 1))[0]
        Length += byte
    return popp(s, Length)

PrimitiveTypeEnumeration = {
1:['Boolean',unpack_value, [1, '<B']],
2:['Byte', unpack_value, [1, '<b']],
3:['Char', unpack_value, [1, '<b']],
5:['Decimal', LengthPrefixedString, 0],
6:['Double', unpack_value, [8, '<Q']],
7:['Int16', unpack_value, [2, '<h']],
8:['Int32', unpack_value, [4, '<i']],
9:['Int64', unpack_value, [8, '<q']],
10:['SByte', unpack_value, [1, '<B']],
11:['Single', unpack_value, [1, '<B']],
12:['TimeSpan', date, [8, '<Q']],
13:['DateTime', date, [8, '<Q']],
14:['UInt16', unpack_value, [2, '<H']],
15:['UInt32', unpack_value, [4, '<I']],
16:['UInt64', unpack_value, [8, '<Q']],
17:['Null', unpack_value, [1, '<B']],
18:['String', LengthPrefixedString, 0]
}

BinaryArrayTypeEnumeration = {
0:['Single'],
1:['Jagged'],
2:['Rectangular'],
3:['SingleOffset'],
4:['JaggedOffset'],
5:['RectangularOffset']
}


def Primitive(s):
    return PrimitiveTypeEnumeration[struct.unpack('<B', popp(s, 1))[0]]

def SystemClass(s):
    return LengthPrefixedString(s)

def none(s):
    pass

def ClassTypeInfo(s):
    TypeName = LengthPrefixedString(s)
    LibraryId = struct.unpack('<I', popp(s, 4))[0]
    return (TypeName, LibraryId)


BinaryTypeEnumeration = {
0:['Primitive', Primitive],
1:['String', none],
2:['Object', none],
3:['SystemClass', SystemClass],
4:['Class', ClassTypeInfo],
5:['ObjectArray', none],
6:['StringArray', none],
7:['PrimitiveArray', Primitive]
}


def SerializedStreamHeader(s):
    (RootId, HeaderId, MajorVersion, MinorVersion) = struct.unpack('<IIII', popp(s, 16))
    print '\tRootId : 0x%x'%RootId
    print '\tHeaderId : 0x%x'%HeaderId
    print '\tMajorVersion : 0x%x'%MajorVersion
    print '\tMinorVersion : 0x%x'%MinorVersion

def BinaryLibrary(s):
    LibraryId = struct.unpack('<I', popp(s, 4))[0]
    LibraryName = LengthPrefixedString(s)
    print '\tLibraryId : 0x%x'%LibraryId
    print '\tLibraryName : %s'%LibraryName

def ClassInfo(s):
    ObjectId = struct.unpack('<I', popp(s, 4))[0]
    Name = LengthPrefixedString(s)
    MemberCount = struct.unpack('<I', popp(s, 4))[0]
    MemberNames = []
    for i in range(MemberCount):
        MemberNames.append(LengthPrefixedString(s))
    print '\t\tObjectId : 0x%x'%ObjectId
    print '\t\tName : %s'%Name
    print '\t\tMemberCount : %d'%MemberCount
    print '\t\tMemberNames : %s'%MemberNames
    return (MemberCount, MemberNames, ObjectId)

def MemberTypeInfo(s, c):
    BinaryTypeEnums = []
    AdditionalInfos = []
    for i in range(c):
        BinaryTypeEnums.append(BinaryTypeEnumeration[struct.unpack('<B', popp(s, 1))[0]])
    for i in BinaryTypeEnums:
        AdditionalInfos.append((i[0],i[1](s)))
    print '\t\tBinaryTypeEnums : %s'%BinaryTypeEnums
    print '\t\tAdditionalInfos : %s'%AdditionalInfos
    return AdditionalInfos

def ClassWithMembersAndTypes(s):
    print '\tClassInfo'
    Members = ClassInfo(s)
    MemberCount = Members[0]
    print '\tMemberTypeInfo'
    MemberTypeI = MemberTypeInfo(s, MemberCount)
    LibraryId = struct.unpack('<I', popp(s, 4))[0]
    print '\tLibraryId : 0x%x'%LibraryId
    theClass[Members[2]] = (MemberTypeI, Members[1])
    parse_values(Members[2], s)

def BinaryObjectString(s):
    ObjectId = struct.unpack('<I', popp(s, 4))[0]
    Value = LengthPrefixedString(s)
    print '\tObjectId : 0x%x'%ObjectId
    print '\tValue : %s'%Value

def ClassWithId(s):
    ObjectId = struct.unpack('<I', popp(s, 4))[0]
    MetadataId = struct.unpack('<I', popp(s, 4))[0]
    print '\tObjectId : 0x%x'%ObjectId
    parse_values(MetadataId, s)

def MemberReference(s):
    IdRef = struct.unpack('<I', popp(s, 4))[0]
    print '\tIdRef : 0x%x'%IdRef

def SystemClassWithMembersAndTypes(s):
    print '\tClassInfo'
    Members = ClassInfo(s)
    MemberCount = Members[0]
    print '\tMemberTypeInfo'
    MemberTypeInfo(s, MemberCount)

def BinaryArray(s):
    ObjectId = struct.unpack('<I', popp(s, 4))[0]
    BinaryArrayTypeEnum = BinaryArrayTypeEnumeration[struct.unpack('<B', popp(s, 1))[0]]
    Rank = struct.unpack('<I', popp(s, 4))[0]
    Lengths = []
    LowerBounds = []
    for i in range(Rank):
        Lengths.append(struct.unpack('<I', popp(s, 4))[0])
    if Rank>1:
        for i in range(Rank):
            LowerBounds.append(struct.unpack('<I', popp(s, 4))[0])
    TypeEnum = BinaryTypeEnumeration[struct.unpack('<B', popp(s, 1))[0]]
    AdditionalTypeInfo = TypeEnum[1](s)
    print '\tObjectId : 0x%x'%ObjectId
    print '\tBinaryArrayTypeEnum : %s'%BinaryArrayTypeEnum
    print '\tRank : %d'%Rank
    print '\tLengths : %s'%Lengths
    print '\tLowerBounds : %s'%LowerBounds
    print '\tTypeEnum : %s'%TypeEnum[0]
    print '\tAdditionalTypeInfo : ',
    print AdditionalTypeInfo

def ObjectNull(s):
    pass

def ObjectNullMultiple256(s):
    NullCount = struct.unpack('<B', popp(s, 1))[0]
    print '\tNullCount : %d'%NullCount

def ClassWithMembers(s):
    print '\tClassInfo'
    ClassInfo(s)
    LibraryId = struct.unpack('<I', popp(s, 4))[0]
    print '\tLibraryId : 0x%x'%LibraryId

def MemberPrimitiveTyped(s):
    primitive = Primitive(s)
    print '\t'+primitive[0]
    print primitive[1](s, primitive[2])



RecordTypeEnum = {
0:['SerializedStreamHeader', SerializedStreamHeader],
1:['ClassWithId', ClassWithId],
2:['SystemClassWithMembers'],
3:['ClassWithMembers', ClassWithMembers],
4:['SystemClassWithMembersAndTypes', SystemClassWithMembersAndTypes],
5:['ClassWithMembersAndTypes', ClassWithMembersAndTypes],
6:['BinaryObjectString', BinaryObjectString],
7:['BinaryArray', BinaryArray],
8:['MemberPrimitiveTyped', MemberPrimitiveTyped],
9:['MemberReference', MemberReference],
10:['ObjectNull', ObjectNull],
11:['MessageEnd', none],
12:['BinaryLibrary', BinaryLibrary],
13:['ObjectNullMultiple256', ObjectNullMultiple256],
14:['ObjectNullMultiple'],
15:['ArraySinglePrimitive'],
16:['ArraySingleObject'],
17:['ArraySingleString'],
21:['MethodCall'],
22:['MethodReturn']
}


def popp(s, n):
    a = ''
    for c in range(n):
        a += s.pop(0)
    return a

def parse_object(s):
    RecordType = struct.unpack('<B',popp(s,1))[0]
    print RecordTypeEnum[RecordType][0]
    return (RecordTypeEnum[RecordType][0], RecordTypeEnum[RecordType][1](s))


if len(sys.argv) != 2:
    print "Usage: %s <stream>"%sys.argv[0]
    sys.exit(0)

f=open(sys.argv[1])
stream = list(f.read())
f.close()

while(len(stream)!=0):
    a = parse_object(stream)