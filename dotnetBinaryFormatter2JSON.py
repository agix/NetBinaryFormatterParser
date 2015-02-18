import sys
import struct
import datetime
import json

theClass = {}

def nothing(value):
    return value

def date(s, options):
    return struct.unpack(options[1], popp(s, options[0]))[0]

def unpack_value(s, options):
    return struct.unpack(options[1], popp(s,options[0]))[0]

def printverbose(string):
    if len(sys.argv) > 2 and sys.argv[2] == '-v':
        print string

def LengthPrefixedString(s, options=""):
    Length = 0
    shift = 0
    c = True
    while c:
        byte = struct.unpack('<B', popp(s, 1))[0]
        if byte&128:
            byte^=128
        else:
            c = False
        Length += byte<<shift
        shift+=7
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
11:['Single', unpack_value, [4, '<I']],
12:['TimeSpan', date, [8, '<Q']],
13:['DateTime', date, [8, '<Q']],
14:['UInt16', unpack_value, [2, '<H']],
15:['UInt32', unpack_value, [4, '<I']],
16:['UInt64', unpack_value, [8, '<Q']],
17:['Null', unpack_value, [1, '<B']],
18:['String', LengthPrefixedString, 0]
}

def parse_value(object, s):
    if object[0]=="Primitive":
        for p in PrimitiveTypeEnumeration:
            if PrimitiveTypeEnumeration[p][0] == object[1]:
                value = PrimitiveTypeEnumeration[p][1](s, PrimitiveTypeEnumeration[p][2])
        printverbose(object[1]+' : '+str(value))
    else:
        value = parse_object(s)
    return value

def parse_values(objectID, s):
    values = []
    myClass = theClass[objectID]
    a = 0
    for object in myClass[0]:
        printverbose(myClass[1][a]+' : '+object[0])
        a+=1
        values.append(parse_value(object, s))
    return values




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
    classTypeInfo = {}
    TypeName = LengthPrefixedString(s)
    LibraryId = struct.unpack('<I', popp(s, 4))[0]
    classTypeInfo['TypeName'] = TypeName
    classTypeInfo['LibraryId'] = LibraryId
    return classTypeInfo


BinaryTypeEnumeration = {
0:('Primitive', Primitive),
1:('String', none),
2:('Object', none),
3:('SystemClass', SystemClass),
4:('Class', ClassTypeInfo),
5:('ObjectArray', none),
6:('StringArray', none),
7:('PrimitiveArray', Primitive)
}


def SerializedStreamHeader(s):
    serializedStreamHeader = {}
    (RootId, HeaderId, MajorVersion, MinorVersion) = struct.unpack('<IIII', popp(s, 16))
    serializedStreamHeader['RootId'] = RootId
    serializedStreamHeader['HeaderId'] = HeaderId
    serializedStreamHeader['MajorVersion'] = MajorVersion
    serializedStreamHeader['MinorVersion'] = MinorVersion
    printverbose('\tRootId : 0x%x'%RootId)
    printverbose('\tHeaderId : 0x%x'%HeaderId)
    printverbose('\tMajorVersion : 0x%x'%MajorVersion)
    printverbose('\tMinorVersion : 0x%x'%MinorVersion)
    return serializedStreamHeader

def BinaryLibrary(s):
    binaryLibrary = {}
    LibraryId = struct.unpack('<I', popp(s, 4))[0]
    LibraryName = LengthPrefixedString(s)
    binaryLibrary['LibraryId'] = LibraryId
    binaryLibrary['LibraryName'] = LibraryName
    printverbose('\tLibraryId : 0x%x'%LibraryId)
    printverbose('\tLibraryName : %s'%LibraryName)
    return binaryLibrary

def ClassInfo(s):
    classInfo = {}
    ObjectId = struct.unpack('<I', popp(s, 4))[0]
    Name = LengthPrefixedString(s)
    MemberCount = struct.unpack('<I', popp(s, 4))[0]
    MemberNames = []
    for i in range(MemberCount):
        MemberNames.append(LengthPrefixedString(s))
    printverbose('\t\tObjectId : 0x%x'%ObjectId)
    printverbose('\t\tName : %s'%Name)
    printverbose('\t\tMemberCount : %d'%MemberCount)
    printverbose('\t\tMemberNames : %s'%MemberNames)
    classInfo['ObjectId'] = ObjectId
    classInfo['Name'] = Name
    classInfo['MemberCount'] = MemberCount
    classInfo['MemberNames'] = MemberNames
    return classInfo

def MemberTypeInfo(s, c):
    memberTypeInfo = {}
    BinaryTypeEnums = []
    binaryTypeEnums = []
    AdditionalInfos = []
    for i in range(c):
        binaryTypeEnum = BinaryTypeEnumeration[struct.unpack('<B', popp(s, 1))[0]]
        binaryTypeEnums.append(binaryTypeEnum)
        BinaryTypeEnums.append(binaryTypeEnum[0])
    for i in binaryTypeEnums:
        if i[0] == 'Primitive':
            AdditionalInfos.append((i[0],i[1](s)[0]))
        else:
            AdditionalInfos.append((i[0],i[1](s)))
    printverbose('\t\tBinaryTypeEnums : %s'%BinaryTypeEnums)
    printverbose('\t\tAdditionalInfos : %s'%AdditionalInfos)
    memberTypeInfo['BinaryTypeEnums'] = BinaryTypeEnums
    memberTypeInfo['AdditionalInfos'] = AdditionalInfos
    return memberTypeInfo

def ClassWithMembersAndTypes(s):
    classWithMembersAndTypes = {}
    printverbose('\tClassInfo')
    Members = ClassInfo(s)
    MemberCount = Members['MemberCount']
    printverbose('\tMemberTypeInfo')
    MemberTypeI = MemberTypeInfo(s, MemberCount)
    LibraryId = struct.unpack('<I', popp(s, 4))[0]
    printverbose('\tLibraryId : 0x%x'%LibraryId)
    theClass[Members['ObjectId']] = (MemberTypeI['AdditionalInfos'], Members['MemberNames'])
    classWithMembersAndTypes['ClassInfo'] = Members
    classWithMembersAndTypes['MemberTypeInfo'] = MemberTypeI
    classWithMembersAndTypes['LibraryId'] = LibraryId
    classWithMembersAndTypes['Values'] = parse_values(Members['ObjectId'], s)
    return classWithMembersAndTypes

def BinaryObjectString(s):
    binaryObjectString = {}
    ObjectId = struct.unpack('<I', popp(s, 4))[0]
    Value = LengthPrefixedString(s)
    printverbose('\tObjectId : 0x%x'%ObjectId)
    printverbose('\tValue : %s'%Value)
    binaryObjectString['ObjectId'] = ObjectId
    binaryObjectString['Value'] = Value
    return binaryObjectString

def ClassWithId(s):
    classWithId = {}
    ObjectId = struct.unpack('<I', popp(s, 4))[0]
    MetadataId = struct.unpack('<I', popp(s, 4))[0]
    printverbose('\tObjectId : 0x%x'%ObjectId)
    classWithId['ObjectId'] = ObjectId
    classWithId['MetadataId'] = MetadataId
    classWithId['Values'] = parse_values(MetadataId, s)
    return classWithId

def MemberReference(s):
    memberReference = {}
    IdRef = struct.unpack('<I', popp(s, 4))[0]
    printverbose('\tIdRef : 0x%x'%IdRef)
    memberReference['IdRef'] = IdRef
    return memberReference

def SystemClassWithMembersAndTypes(s):
    systemClassWithMembersAndTypes = {}
    printverbose('\tClassInfo')
    Members = ClassInfo(s)
    MemberCount = Members['MemberCount']
    printverbose('\tMemberTypeInfo')
    MemberTypeI = MemberTypeInfo(s, MemberCount)
    theClass[Members['ObjectId']] = (MemberTypeI['AdditionalInfos'], Members['MemberNames'])
    systemClassWithMembersAndTypes['ClassInfo'] = Members
    systemClassWithMembersAndTypes['MemberTypeInfo'] = MemberTypeI
    systemClassWithMembersAndTypes['Values'] = parse_values(Members['ObjectId'], s)
    return systemClassWithMembersAndTypes


def BinaryArray(s):
    binaryArray = {}
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
    printverbose('\tObjectId : 0x%x'%ObjectId)
    printverbose('\tBinaryArrayTypeEnum : %s'%BinaryArrayTypeEnum)
    printverbose('\tRank : %d'%Rank)
    printverbose('\tLengths : %s'%Lengths)
    printverbose('\tLowerBounds : %s'%LowerBounds)
    printverbose('\tTypeEnum : %s'%TypeEnum[0])
    printverbose('\tAdditionalTypeInfo : ')
    printverbose(AdditionalTypeInfo)
    binaryArray['ObjectId'] = ObjectId
    binaryArray['BinaryArrayTypeEnum'] = BinaryArrayTypeEnum
    binaryArray['Rank'] = Rank
    binaryArray['Lengths'] = Lengths
    binaryArray['LowerBounds'] = LowerBounds
    binaryArray['TypeEnum'] = TypeEnum[0]
    binaryArray['AdditionalTypeInfo'] = AdditionalTypeInfo
    return binaryArray

def ObjectNull(s):
    pass

def ObjectNullMultiple256(s):
    objectNullMultiple256 = {}
    NullCount = struct.unpack('<B', popp(s, 1))[0]
    printverbose('\tNullCount : %d'%NullCount)
    objectNullMultiple256['NullCount'] = NullCount
    return objectNullMultiple256

def ObjectNullMultiple(s):
    objectNullMultiple = {}
    NullCount = struct.unpack('<I', popp(s, 4))[0]
    printverbose('\tNullCount : %d'%NullCount)
    objectNullMultiple['NullCount'] = NullCount
    return objectNullMultiple

def ClassWithMembers(s):
    classWithMembers = {}
    printverbose('\tClassInfo')
    Members = ClassInfo(s)
    LibraryId = struct.unpack('<I', popp(s, 4))[0]
    printverbose('\tLibraryId : 0x%x'%LibraryId)
    classWithMembers['ClassInfo'] = Members
    classWithMembers['LibraryId'] = LibraryId
    return classWithMembers

def SystemClassWithMembers(s):
    systemClassWithMembers = {}
    printverbose('\tClassInfo')
    Members = ClassInfo(s)
    systemClassWithMembers['ClassInfo'] = Members
    return systemClassWithMembers

def MemberPrimitiveTyped(s):
    memberPrimitiveTyped = {}
    primitive = Primitive(s)
    printverbose('\t'+primitive[0])
    value = primitive[1](s, primitive[2])
    printverbose(value)
    memberPrimitiveTyped['PrimitiveTypeEnum'] = primitive[0]
    memberPrimitiveTyped['Value'] = value
    return memberPrimitiveTyped

def ArraySingleObject(s):
    arraySingleObject = {}
    ObjectId = struct.unpack('<I', popp(s, 4))[0]
    Length = struct.unpack('<I', popp(s, 4))[0]
    printverbose('\tObjectId : 0x%x'%ObjectId)
    printverbose('\tLength : 0x%x'%Length)
    arraySingleObject['ObjectId'] = ObjectId
    arraySingleObject['Length'] = Length
    arraySingleObject['Values'] = []
    for o in range(Length):
        arraySingleObject['Values'].append(parse_object(s))
    return arraySingleObject

def ArraySinglePrimitive(s):
    arraySinglePrimitive = {}
    ObjectId = struct.unpack('<I', popp(s, 4))[0]
    Length = struct.unpack('<I', popp(s, 4))[0]
    printverbose('\tObjectId : 0x%x'%ObjectId)
    printverbose('\tLength : 0x%x'%Length)
    primitive = Primitive(s)
    printverbose('\t'+primitive[0])
    arraySinglePrimitive['ObjectId'] = ObjectId
    arraySinglePrimitive['Length'] = Length
    arraySinglePrimitive['PrimitiveTypeEnum'] = primitive[0]
    arraySinglePrimitive['Values'] = []
    for o in range(Length):
        value = primitive[1](s, primitive[2])
        printverbose(value)
        arraySinglePrimitive['Values'].append(value)
    return arraySinglePrimitive

def ArraySingleString(s):
    arraySingleString = {}
    ObjectId = struct.unpack('<I', popp(s, 4))[0]
    Length = struct.unpack('<I', popp(s, 4))[0]
    printverbose('\tObjectId : 0x%x'%ObjectId)
    printverbose('\tLength : 0x%x'%Length)
    arraySingleString['ObjectId'] = ObjectId
    arraySingleString['Length'] = Length
    arraySingleString['Values'] = []
    for o in range(Length):
        value = LengthPrefixedString(s)
        printverbose('\t\t'+value)
        arraySingleString['Values'].append(value)
    return arraySingleString



RecordTypeEnum = {
0:['SerializedStreamHeader', SerializedStreamHeader],
1:['ClassWithId', ClassWithId],
2:['SystemClassWithMembers', SystemClassWithMembers],
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
14:['ObjectNullMultiple', ObjectNullMultiple],
15:['ArraySinglePrimitive', ArraySinglePrimitive],
16:['ArraySingleObject', ArraySingleObject],
17:['ArraySingleString', ArraySingleString],
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
    printverbose(RecordTypeEnum[RecordType][0])
    return (RecordTypeEnum[RecordType][0], RecordTypeEnum[RecordType][1](s))


if len(sys.argv) < 2:
    print "Usage: %s <stream> (-v)"%sys.argv[0]
    sys.exit(0)

f=open(sys.argv[1])
stream = list(f.read())
f.close()

myObject = {}
z=0
while(len(stream)!=0):
    a = parse_object(stream)
    myObject[z] = a
    z+=1

print json.dumps(myObject)
