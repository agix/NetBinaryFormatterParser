import sys
import json
import struct

myClasses = {}

def LengthPrefixedString(string, options=''):
    ret = ''
    Length = struct.pack('<I', len(string))
    newLength = ''
    if len(string)>128:
        ret = '\x80\x08'
    else :
        for i in range(len(Length)-1, -1, -1):
            if Length[i]=='\x00':
                continue
            else:
                newLength = newLength+Length[:i+1]
                break

        for l in newLength:
            if ord(l)&128:
                ret += chr(ord(l)^128)
            else:
                ret += l
        if len(ret)==0:
            ret = '\x00'

    ret += str(string)
    return ret

def ClassInfo(s):
    ret = ''
    ret += struct.pack('<I', s['ObjectId'])
    ret += LengthPrefixedString(s['Name'])
    ret += struct.pack('<I', s['MemberCount'])
    for m in range(s['MemberCount']):
        ret += LengthPrefixedString(s['MemberNames'][m])

    return ret

def date(s, options):
    return s.decode("hex")

def pack_value(s, options):
    return struct.pack(options[1], s)

def none(s):
    return ''

PrimitiveTypeEnumeration = {
'Boolean':[1,pack_value, [1, '<B']],
'Byte':[2, pack_value, [1, '<b']],
'Char':[3, pack_value, [1, '<b']],
'Decimal':[5, LengthPrefixedString, 0],
'Double':[6, pack_value, [8, '<Q']],
'Int16':[7, pack_value, [2, '<h']],
'Int32':[8, pack_value, [4, '<i']],
'Int64':[9, pack_value, [8, '<q']],
'SByte':[10, pack_value, [1, '<B']],
'Single':[11, pack_value, [4, '<I']],
'TimeSpan':[12, date, [8, '<Q']],
'DateTime':[13, date, [8, '<Q']],
'UInt16':[14, pack_value, [2, '<H']],
'UInt32':[15, pack_value, [4, '<I']],
'UInt64':[16, pack_value, [8, '<Q']],
'Null':[17, pack_value, [1, '<B']],
'String':[18, LengthPrefixedString, 0]
}

def Primitive(s):
    ret = ''
    ret += struct.pack('<B', PrimitiveTypeEnumeration[s][0])
    return ret

def SystemClass(s):
    return LengthPrefixedString(s)

def ClassTypeInfo(s):
    ret = ''
    ret += LengthPrefixedString(s['TypeName'])
    ret += struct.pack('<I', s['LibraryId'])
    return ret

BinaryTypeEnumeration = {
'Primitive':[0, Primitive],
'String':[1, none],
'Object':[2, none],
'SystemClass':[3, SystemClass],
'Class':[4, ClassTypeInfo],
'ObjectArray':[5, none],
'StringArray':[6, none],
'PrimitiveArray':[7, Primitive]
}

def MemberTypeInfo(s, c):
    ret = ''
    for i in range(c):
        ret += struct.pack('<B', BinaryTypeEnumeration[s['BinaryTypeEnums'][i]][0])
    for i in range(c):
        ret += BinaryTypeEnumeration[s['BinaryTypeEnums'][i]][1](s['AdditionalInfos'][i][1])
    return ret

def parse_value(val, typeEnum, info):
    ret = ''
    if typeEnum == 'Primitive':
        ret += PrimitiveTypeEnumeration[info[1]][1](val, PrimitiveTypeEnumeration[info[1]][2])
    else:
        RecordType = RecordTypeEnum[val[0]]
        print val[0]
        ret += struct.pack('<B', RecordType[0])
        ret += RecordType[1](val[1])
    return ret

def parse_values(s, type, c):
    ret = ''
    for i in range(c):
        ret += parse_value(s[i][1], type['BinaryTypeEnums'][i], type['AdditionalInfos'][i])
    return ret

def ClassWithMembersAndTypes(s):
    global myClasses
    ret = ''
    ret += ClassInfo(s['ClassInfo'])
    ret += MemberTypeInfo(s['MemberTypeInfo'], s['ClassInfo']['MemberCount'])
    ret += struct.pack('<I', s['LibraryId'])
    myClasses[s['ClassInfo']['ObjectId']]={'Name': s['ClassInfo']['Name'], 'MemberTypeInfo': s['MemberTypeInfo'], 'MemberCount': s['ClassInfo']['MemberCount']}
    ret += parse_values(s['Values'], s['MemberTypeInfo'], s['ClassInfo']['MemberCount'])
    return ret

def SystemClassWithMembersAndTypes(s):
    global myClasses
    ret = ''
    ret += ClassInfo(s['ClassInfo'])
    ret += MemberTypeInfo(s['MemberTypeInfo'], s['ClassInfo']['MemberCount'])
    myClasses[s['ClassInfo']['ObjectId']]={'Name': s['ClassInfo']['Name'], 'MemberTypeInfo': s['MemberTypeInfo'], 'MemberCount': s['ClassInfo']['MemberCount']}
    ret += parse_values(s['Values'], s['MemberTypeInfo'], s['ClassInfo']['MemberCount'])
    return ret

def MemberReference(s):
    return struct.pack('<I', s['IdRef'])

def BinaryLibrary(s):
    ret = ''
    ret += struct.pack('<I', s['LibraryId'])
    ret += LengthPrefixedString(s['LibraryName'])
    return ret

def SerializedStreamHeader(s):
    return struct.pack('<IIII', s['RootId'], s['HeaderId'], s['MajorVersion'], s['MinorVersion'])

BinaryArrayTypeEnumeration = {
'Single':[0],
'Jagged':[1],
'Rectangular':[2],
'SingleOffset':[3],
'JaggedOffset':[4],
'RectangularOffset':[5]
}

def BinaryArray(s):
    ret = ''
    ret += struct.pack('<I', s['ObjectId'])
    ret += struct.pack('<B', BinaryArrayTypeEnumeration[s['BinaryArrayTypeEnum']][0])
    ret += struct.pack('<I', s['Rank'])
    for i in range(s['Rank']):
        ret += struct.pack('<I', s['Lengths'][i])
    if 'Offset' in s['BinaryArrayTypeEnum']:
        for i in range(s['Rank']):
            ret += struct.pack('<I', s['LowerBounds'][i])
    ret += struct.pack('<B', BinaryTypeEnumeration[s['TypeEnum']][0])
    ret += BinaryTypeEnumeration[s['TypeEnum']][1](s['AdditionalTypeInfo'])
    return ret


def BinaryObjectString(s):
    ret = ''
    ret += struct.pack('<I', s['ObjectId'])
    ret += LengthPrefixedString(s['Value'])
    return ret

def ClassWithId(s):
    global myClasses
    ret = ''
    ret += struct.pack('<I', s['ObjectId'])
    ret += struct.pack('<I', s['MetadataId'])
    theclass = myClasses[s['MetadataId']]
    ret += parse_values(s['Values'], theclass['MemberTypeInfo'], theclass['MemberCount'])
    return ret

def ArraySingleObject(s):
    ret = ''
    ret += struct.pack('<I', s['ObjectId'])
    ret += struct.pack('<I', s['Length'])
    for o in range(s['Length']):
        ret += parse_value(s['Values'][o], '', '')
    return ret

def ArraySingleString(s):
    ret = ''
    ret += struct.pack('<I', s['ObjectId'])
    ret += struct.pack('<I', s['Length'])
    for o in range(s['Length']):
        ret += parse_value(s['Values'][o], '', '')
    return ret

def ArraySinglePrimitive(s):
    ret = ''
    ret += struct.pack('<I', s['ObjectId'])
    ret += struct.pack('<I', s['Length'])
    ret += struct.pack('<B', PrimitiveTypeEnumeration[s['PrimitiveTypeEnum']][0])
    for o in range(s['Length']):
        ret += PrimitiveTypeEnumeration[s['PrimitiveTypeEnum']][1](s['Values'][o], PrimitiveTypeEnumeration[s['PrimitiveTypeEnum']][2])
    return ret

def MemberPrimitiveTyped(s):
    memberPrimitiveTyped = {}
    primitive = Primitive(s)
    printverbose('\t'+primitive[0])
    value = primitive[1](s, primitive[2])
    printverbose(value)
    memberPrimitiveTyped['PrimitiveTypeEnum'] = primitive[0]
    memberPrimitiveTyped['Value'] = value
    return memberPrimitiveTyped

def MemberPrimitiveTyped(s):
    ret = ''
    ret += struct.pack('<B', PrimitiveTypeEnumeration[s['PrimitiveTypeEnum']][0])
    ret += PrimitiveTypeEnumeration[s['PrimitiveTypeEnum']][1](s['Value'], PrimitiveTypeEnumeration[s['PrimitiveTypeEnum']][2])
    return ret

def MethodCall(s):
    ret = ''
    ret += struct.pack('<I', s['MessageEnum'])
    ret += StringValueWithCode(s['MethodName'])
    ret += StringValueWithCode(s['TypeName'])
    if s['MessageEnum'] & MessageFlagsEnum['NoContext'] == 0:
        ret += StringValueWithCode(s['CallContext'])
    if s['MessageEnum'] & MessageFlagsEnum['NoArgs'] == 0:
        ret += ArrayOfValueWithCode(s['Args'])
    return ret

def MethodReturn(s):
    ret = ''
    ret += struct.pack('<I', s['MessageEnum'])
    ret += StringValueWithCode(s['MethodName'])
    ret += StringValueWithCode(s['TypeName'])
    if s['MessageEnum'] & MessageFlagsEnum['NoContext'] == 0:
        ret += StringValueWithCode(s['CallContext'])
    if s['MessageEnum'] & MessageFlagsEnum['NoArgs'] == 0:
        ret += ArrayOfValueWithCode(s['Args'])
    return ret

def ArrayOfValueWithCode(s):
    ret = ''
    ret += struct.pack('<I', s['Length'])
    for v in s['ListOfValueWithCode']:
        ret += struct.pack('<B', PrimitiveTypeEnumeration[v['PrimitiveTypeEnum']][0])
        ret += PrimitiveTypeEnumeration[v['PrimitiveTypeEnum']][1](v['Value'], PrimitiveTypeEnumeration[v['PrimitiveTypeEnum']][2])
    return ret

def StringValueWithCode(s):
    ret = ''
    ret += struct.pack('<B', PrimitiveTypeEnumeration['String'][0])
    ret += LengthPrefixedString(s)
    return ret


MessageFlagsEnum = {
    'NoArgs': 0x00000001,
    'ArgsInline': 0x00000002,
    'ArgsIsArray': 0x00000004,
    'ArgsInArray': 0x00000008,
    'NoContext': 0x00000010,
    'ContextInline': 0x00000020,
    'ContextInArray': 0x00000040,
    'MethodSignatureInArray': 0x00000080,
    'PropertiesInArray': 0x00000100,
    'NoReturnValue': 0x00000200,
    'ReturnValueVoid': 0x00000400,
    'ReturnValueInline': 0x00000800,
    'ReturnValueInArray': 0x00001000,
    'ExceptionInArray': 0x00002000,
    'GenericMethod': 0x00008000
}

RecordTypeEnum = {
'SerializedStreamHeader':[0, SerializedStreamHeader],
'ClassWithId':[1, ClassWithId],
'SystemClassWithMembers':[2, ],
'ClassWithMembers':[3, ],
'SystemClassWithMembersAndTypes':[4, SystemClassWithMembersAndTypes],
'ClassWithMembersAndTypes':[5, ClassWithMembersAndTypes],
'BinaryObjectString':[6, BinaryObjectString],
'BinaryArray':[7, BinaryArray],
'MemberPrimitiveTyped':[8, MemberPrimitiveTyped],
'MemberReference':[9, MemberReference],
'ObjectNull':[10, none],
'MessageEnd':[11, none],
'BinaryLibrary':[12, BinaryLibrary],
'ObjectNullMultiple256':[13, ],
'ObjectNullMultiple':[14, ],
'ArraySinglePrimitive':[15, ArraySinglePrimitive],
'ArraySingleObject':[16, ArraySingleObject],
'ArraySingleString':[17, ArraySingleString],
'MethodCall':[21, MethodCall],
'MethodReturn':[22, MethodReturn]
}

if len(sys.argv) < 2:
    print "Usage: %s <stream>"%sys.argv[0]
    sys.exit(0)

f=open(sys.argv[1])
myObject = json.loads(f.read())
f.close()

binary = ''

for o in range(len(myObject)):
    RecordType = RecordTypeEnum[myObject[str(o)][0]]
    print myObject[str(o)][0]
    binary += struct.pack('<B', RecordType[0])
    binary += RecordType[1](myObject[str(o)][1])

f = open(sys.argv[1]+'_binary', 'w')
f.write(binary)
f.close()