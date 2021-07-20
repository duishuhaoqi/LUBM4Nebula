# coding:utf-8
import pandas as pd
import os
import time
import json
import csv

start: float = time.perf_counter()


class Entity:
    def __init__(self):
        self.URI = ""
        self.type = "UNTYPED"
        self.attribute = {}
        self.vid = ""

    def addProperty(self, key, val):
        self.attribute[key] = val


class EntityTable:
    def __init__(self):
        self.name = ""
        self.cs = []
        self.entityList = []


class Edge:
    def __init__(self):
        self.start = ""
        self.end = ""
        self.type = "UNTYPED"
        self.attribute = {}


class EdgeTable:
    def __init__(self):
        self.name = ""
        self.edgeList = []


def getSubject(line):
    Subject = ""
    tag = 0
    for i in range(len(line)):
        if (line[i] == '<' and tag == 0):
            tag = 1
        elif (line[i] == '>' and tag == 1):
            return Subject
        else:
            Subject += line[i]


def getPredicate(line):
    Predicate = ""
    tag = 0
    for i in range(len(line)):
        if (line[i] == '<' and tag == 0):
            tag = 1
        elif (line[i] == '<' and tag == 1):
            tag = 2
        elif (line[i] == '>' and tag == 2):
            return Predicate
        elif (tag == 2):
            Predicate += line[i]


def getObeject(line):
    Object = ""
    tag = 0
    for i in range(len(line)):
        if (line[i] == '<' and tag == 0):
            tag = 1
        elif (line[i] == '<' and tag == 1):
            tag = 2
        elif ((line[i] == '<' or line[i] == '\"') and tag == 2):
            tag = 3
        elif (tag == 3):
            if (line[i] == '>' or line[i] == '\"'):
                return Object
            Object += line[i]
    return Object


def haveLiteral(line):
    num = 0  # 计数双引号的个数
    for i in range(len(line)):
        if (line[i] == '\"'):
            num += 1
    if (num >= 2):
        return True
    else:
        return False


def haveType(line):
    if getPredicate(line) is None:
        return False
    if ("#type" in getPredicate(line)):
        return True
    else:
        return False


VertexMap = {}  # 将每个实体（结点）的URI映射为一个编号
EntityTypeMap = {}  # 将每个实体（结点）的类型映射为一个编号
EdgeMap = {}  # 将每个边（关系）的类型映射为一个编号

entityTypeTables = []
edgeTypeTables = []
entities = []

uri2id = {}  # 将URI映射为id的字典
label2id = {}  # 将Label映射为id的字典，避免elabel和vlabel重复的问题

if ("UNTYPED" not in EntityTypeMap):  # 为未声明类型的实体，建立一个实体type表
    tmpID = len(EntityTypeMap)
    EntityTypeMap["UNTYPED"] = tmpID  # 字典里加入新的type

    newEntityTable = EntityTable()
    newEntityTable.name = "UNTYPED"
    entityTypeTables.append(newEntityTable)

fileObject = open("lubm0.nt", encoding='UTF-8')

num = 0
# next(fileObject)  # 跳过第一行
# next(fileObject)  # 跳过第一行

for line in fileObject:
    line = line.strip('\n')
    num = num + 1

    sub = getSubject(line)
    pre = getPredicate(line)
    obj = getObeject(line)

    if sub not in VertexMap:  # 主语为一个新出现的实体
        tmpURIID = len(VertexMap)
        VertexMap[sub] = tmpURIID

        newEntity = Entity()
        newEntity.URI = sub
        tmpPre = "uri"
        tmpObj = sub
        newEntity.addProperty(tmpPre, tmpObj)
        newEntity.vid = tmpURIID
        entities.append(newEntity)

    if haveLiteral(line):  # 宾语为literal
        index = VertexMap[sub]
        tmpEntity = entities[index]
        tmpEntity.addProperty(pre, obj)  # 为实体添加属性

    elif haveType(line):  # 谓语为type
        if obj not in EntityTypeMap:  # 新出现的实体的type，建立一个新实体type表
            tmpID = len(EntityTypeMap)
            EntityTypeMap[obj] = tmpID  # 字典里加入新的type

            newEntityTable = EntityTable()
            newEntityTable.name = obj
            entityTypeTables.append(newEntityTable)  # 建立新的type表并加入到实体type表的列表中

        index = VertexMap[sub]
        tmpEntity = entities[index]  # 为实体添加type
        tmpEntity.type = obj

    else:  # 实体-关系-实体
        if obj not in VertexMap:  # 宾语为一个新出现的实体
            tmpID = len(VertexMap)
            VertexMap[obj] = tmpID

            newEntity = Entity()
            newEntity.URI = obj
            tmpPre = "uri"
            tmpObj = obj
            newEntity.addProperty(tmpPre, tmpObj)
            newEntity.vid = tmpID
            entities.append(newEntity)

        if (pre not in EdgeMap):  # 新出现的谓语，要建立一个新的边类型表
            tmpID = len(EdgeMap)
            EdgeMap[pre] = tmpID

            newEdgeTable = EdgeTable()
            newEdgeTable.name = pre  # 建立一个新的type表

            newEdge = Edge()
            newEdge.start = sub
            newEdge.end = obj
            newEdge.type = pre
            newEdgeTable.edgeList.append(newEdge)  # 将新边加入到对应Type的表中
            edgeTypeTables.append(newEdgeTable)  # 将新表加入到表的列表中
        else:
            tmpID = EdgeMap[pre]
            tmpEdgeTable = edgeTypeTables[tmpID]  # 找到应该存放的Type表
            newEdge = Edge()
            newEdge.start = sub
            newEdge.end = obj
            newEdge.type = pre
            tmpEdgeTable.edgeList.append(newEdge)  # 将新边加入到找到的Type表中
print(num)

for entityIns in entities:  # 将实体按类型划分到不同的EntityTable
    entityType = entityIns.type
    typeIndex = EntityTypeMap[entityType]
    tmpAttribute = list(entityIns.attribute.keys())
    tmpTable = entityTypeTables[typeIndex]  # 向实体类型相对应的表中加入实体
    # uri2id[entityIns.URI] = entityIns.sid
    tmpTable.cs = tmpTable.cs + tmpAttribute
    tmpTable.cs = sorted(set(tmpTable.cs), key=tmpTable.cs.index)
    # tmpTable.cs = list(set(tmpTable.cs + tmpAttribute))
    tmpTable.entityList.append(entityIns)

# 生成建立点表和边表的YAML文件
sqlFile = open("createTable.sql", "w")

for entityIns in entityTypeTables:  # 输出所有节点类型的type表
    if (entityIns.entityList):
        root = os.getcwd()
        vertexTableName = entityIns.name.split('/')[-1]
        tmpSqlString = "CREATE TAG IF NOT EXISTS " + "\'" + vertexTableName + "\'" + "("

        if ((vertexTableName == "order") | (vertexTableName == "similar")):
            vertexTableName = vertexTableName + "_t"

        if ('#' in vertexTableName):
            vertexTableName = vertexTableName.replace('#', '_', 20)

        if ('-' in vertexTableName):
            vertexTableName = vertexTableName.replace('-', '_', 20)

        # if ('.' in vertexTableName):
        #     vertexTableName = vertexTableName.replace('.', '_', 20)

        # label2id
        flag = vertexTableName not in label2id
        if flag == True:
            tmpLabelId = len(label2id)
            label2id[vertexTableName.lower()] = tmpLabelId  # 如果字典中没有，加入新的label
        else:
            vertexTableName = vertexTableName + "_v"
        ##

        filepath = root + "\\vertex" + '\\' + vertexTableName + ".csv"  # 截取最后一个/后的字符串
        tmpList = []

        tmpCS = entityIns.cs
        tmpColumn = []
        tmpColumn.append("vid")
        tmpColumn = tmpColumn + tmpCS

        for ent in entityIns.entityList:
            tmpEntityList = []
            tmpEntityList.append(ent.vid)
            for cs in tmpCS:
                if cs in ent.attribute.keys():
                    tmpValue = ent.attribute[cs]
                    tmpEntityList.append(tmpValue)
                else:
                    tmpEntityList.append("")
            tmpList.append(tmpEntityList)

        dataframe = pd.DataFrame(columns=tmpColumn, data=tmpList)
        dataframe.to_csv(filepath, index=False, sep='|', header=False, quoting=csv.QUOTE_NONE)

        # 构造yaml脚本中的指令
        for cs in tmpCS:
            tmpSqlString += "'" + cs + "'" + " string,"
        tmpSqlString = tmpSqlString[:-1]
        tmpSqlString += ");\n"
        # tmpSqlString = "CREATE TAG IF NOT EXISTS" + vertexTableName + ";\n"
        sqlFile.write(tmpSqlString)

sqlFile.write("\n")

for edgeIns in edgeTypeTables:
    if (not edgeIns.name is None and edgeIns.edgeList):
        root = os.getcwd()

        edgeTableName = edgeIns.name.split('/')[-1]

        if ((edgeTableName == "order") | (edgeTableName == "similar")):
            edgeTableName = edgeTableName + "_t"

        if ('#' in edgeTableName):
            edgeTableName = edgeTableName.replace('#', '_', 20)

        if ('-' in edgeTableName):
            edgeTableName = edgeTableName.replace('-', '_', 20)

        ## label2id
        flag = edgeTableName.lower() not in label2id
        if flag == True:
            tmpLabelId = len(label2id)
            label2id[edgeTableName] = tmpLabelId  # 如果字典中没有，加入新的label
        else:
            edgeTableName = edgeTableName + "_e"
        ##

        filepath = root + "/edge" + '/' + edgeTableName + ".csv"

        tmpStart = []
        tmpEnd = []
        tmpAttribute = []
        tmpID = []
        for edg in edgeIns.edgeList:
            tmpStart.append(VertexMap[edg.start])
            tmpEnd.append(VertexMap[edg.end])
        dataframe = pd.DataFrame({'startURI': tmpStart, 'endURI': tmpEnd})
        dataframe.to_csv(filepath, index=False, sep='|', header=False, quoting=csv.QUOTE_NONE)

        # 构造yaml脚本中的指令
        tmpSqlString = "CREATE EDGE IF NOT EXISTS " + "\'" + edgeTableName + "\'" + "()" + ";\n"
        sqlFile.write(tmpSqlString)

sqlFile.write("\n")
sqlFile.close()

fileObject.close()

elapsed = (time.perf_counter() - start)
print("Time used:", elapsed)

# make shell 生成执行命令的脚本
