#<======================================================================================================================================>#
#headers
import os
import re
import nltk
import pylab
import unicodedata
import networkx as nx
from networkx.readwrite import json_graph
from whoosh.fields import ID,TEXT, Schema
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser
import sigmajsonmaker as sjm
import numpy.random as nr
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#used to store already existing entities
#global variables
entities = []
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#relation class
class Relation(object):
    def __init__(self, relation = None, file = None, dataset = None, destination = None):
        self.relation = relation
        self.file = file
        self.dataset = dataset
        self.destination = destination
    
    def addRelation(self, relation):
        self.relation.append(relation)
    
    def addPath(self, file):
        self.file = file
    
    def addDataset(self, dataset):
        self.dataset = dataset
    
    def addDestination(self, destination):
        self.destination = destination
    
    def getRelationName(self):
        return self.relation
        
    def getPath(self):
        return self.file
    
    def getDataset(self):
        return self.dataset
    
    def getDestination(self):
        return self.destination
    
    
    def getRelation(self):
        return self.relation + "," + self.destination + "," + self.file + "," + self.dataset
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#entity class
class Entity(object):
    def __init__(self, name = None):
        self.name = name
        self.properties = []
        self.relations = []
    
    def addProperty(self, property):
        self.properties.append(property)
    
    def addName(self, name):
        self.name = name
    
    def addRelation(self, relation, file, dataset, destination):
        self.relations.append(Relation(relation, file, dataset, destination))
    
    def mergeRelations(self):
        relationMerge = ""
        for i in self.relations:
            relationMerge = relationMerge + i.getRelation() + ":"
        return relationMerge
    
    def mergeProperties(self):
        propertyMerge = ""
        for i in self.properties:
            propertyMerge = propertyMerge + i + ":"
        return propertyMerge
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#used to store new entities in the database
def addObjects(dataset):
    schema = Schema(name = ID(unique = True, stored = True), properties = TEXT(stored = True), relations = TEXT(stored = True))
    if not os.path.exists(dataset + "Database"):
        os.mkdir(dataset + "Database")
    ix = create_in(dataset + "Database",schema)
    ix = open_dir(dataset + "Database")
    writer = ix.writer()
    for i in entities:
        n = i.name
        p = i.mergeProperties()
        r = i.mergeRelations()
        writer.add_document(name = unicode(n), properties = unicode(p), relations = unicode(r))
    writer.commit()
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#used to fetch data from the database
def getObjects(dataset, entityName = None):
    schema = Schema(name = ID(unique = True, stored = True), properties = TEXT(stored = True), relations = TEXT(stored = True))
    
    ix = open_dir(dataset + "Database")
    parser = QueryParser("name",ix.schema)
    myquery = parser.parse(unicode(entityName))
    
    searcher = ix.searcher()
    results = searcher.search(myquery)
    
    return results
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#used to fetch data from the database
def parseResultsToEntities(results):
    res = []
    i = 0
    
    while i < len(results):
        newEntity = Entity(results[i]['name'].encode('ascii','ignore'))
        prop = results[i]['properties'].encode('ascii','ignore')
        rel = results[i]['relations'].encode('ascii','ignore')
        #print newEntity.name, prop, rel
        
        #to extract properties from whoosh results
        start = 0
        end = 0
        j = 0
        while j < len(prop):
            if prop[j] == ":":
                end = j
                newEntity.addProperty(prop[start:end])
                start = j + 1
            j = j + 1
        
        #to extract relations from whoosh results
        start = 0
        end = 0
        j = 0
        k = 0
        relation = ""
        destination = ""
        path = ""
        dset = ""
        while j < len(rel):
            if rel[j] == "," and k == 0:
                end = j
                relation = rel[start:end]
                start = j + 1
                k = k + 1
            elif rel[j] == "," and k == 1:
                end = j
                destination = rel[start:end]
                start = j + 1
                k = k + 1
            elif rel[j] == "," and k == 2:
                end = j
                path = rel[start:end]
                start = j + 1
                k = k + 1
            elif rel[j] == ":":
                end = j
                dset = rel[start:end]
                start = j + 1
                k = 0
                newEntity.addRelation(relation, path, dset, destination)
            j = j + 1
        
        res = res + [newEntity]
        i = i + 1
    
    return res
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#create a networkx graph from the results
def createGraphJson(res):
    g = nx.DiGraph()
    edgeList = []
    n = ""
    d = ""
    r = ""
    if len(res) == 0:
        return 1
    
    r = res[0].name
    g.add_node(r)

    n = res[0].name
    for i in res[0].relations:
        d = i.destination
        g.add_node(d)
        edgeList = edgeList + [(n,d)]
    g.add_edges_from(edgeList)
    nx.draw(g)
    pylab.show()
    t = json_graph.tree_data(g, root = r)
    x = str(t)
    x=re.sub("id","name",x)
    x=re.sub("\'","\"",x)
    print x
    return 0
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#create a networkx graph from the results
def createGraphJsonMultiLevel(res):
    g = nx.DiGraph()
    edgeList = []
    n = ""
    d = ""
    r = ""
    if len(res) == 0:
        return 1
    
    r = res[0].name
    g.add_node(r,label=r,size=8,x=nr.random_integers(12),y=nr.random_integers(12),color = "blue")
    z=''
    k = 0
    count = 0
    while k < len(res):
        n = res[k].name
        for i in res[k].relations:
            d = i.destination
            g.add_node(d,label=d,size=3,x=nr.random_integers(12),y=nr.random_integers(12))
	    z = i.relation
            count =  count + 1
            g.add_edge(n,d,id="e"+str(count))
            if len(getObjects("moto_bulk",d)) > 0 and len(parseResultsToEntities(getObjects("moto_bulk",d))) > 0:
		result = parseResultsToEntities(getObjects("moto_bulk",d))		
		for m in result:
		    if m not in res:
			res = res + [m]
                	print "new node added"
        k = k + 1

    #g.add_edges_from(edgeList)
    #t=sjm.getJson(g)
    #nx.draw(g)
    #pylab.show()
    x=sjm.getJson(g)
    #x = str(t)
    #x=re.sub("\'id\'","\'name\'",x)
    #x=re.sub("\'","\"",x) 
    print x
    fl=open("data.json","w")
    fl.write(x)
    fl.close()
    return 0
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#add relations to database
def addRel(source, relation, destination, file, dataset):
    global entities
    found = 0
    for i in entities:
        if i.name == source:
            found = 1
            count = 0
            for j in i.relations:
                if j.relation == relation and j.file == file and j.destination == destination:
                    count = 1
                    break
            if count == 0:
                i.addRelation(relation, file, dataset, destination)
            break
    if found == 0:
        newentity = Entity(source)
        newentity.addRelation(relation, file, dataset, destination)
        entities = entities + [newentity]
    return 1
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#add properties to database
def addProp(source, destination, dataset):
    global entities
    found = 0
    for i in entities:
        if i.name == source:
            found = 1
            if destination in i.properties:
                break
            else:
                i.addProperty(destination)
                break
    if found == 0:
        newentity = Entity(source)
        newentity.addProperty(destination)
        entities = entities + [newentity]
    return 1
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#used to split the sentence and infer relationships or properties
def splitSentence(sentence, file, dataset):
    global entities
    words = nltk.word_tokenize(sentence)
    words = nltk.pos_tag(words)

    print words
    
    if len(words) > 100:
        return -1
    
    if words[0][1] not in ["NNP", "NNPS"]:
        return -1

    propernouns = []
    nouns = []
    verbs = []
    connectors = []
    adjectives = []
    location = []

    sourceEntity = ""
    targetEntity = ""
    found = 0
    count = 0
    startindex = 0
    endindex = 0

    for i in words:
        if i[1] in ["NNP", "NNPS"]:
            propernouns = propernouns + [count]
        if i[1] in ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]:
            verbs = verbs + [count]
        if i[1] in ["JJ", "JJS"]:
            adjectives = adjectives + [count]
        if i[1] in["CC"]:
            connectors = connectors + [count]
        if i[1] in ["NN", "NNS"]:
            nouns = nouns + [count]
        if i[1] in ["IN"]:
            location = location + [count]
        count = count + 1

    print propernouns
    print nouns
    print verbs
    print adjectives
    print connectors
    print location
    
    complex = 0
    #for handling complex sentences
    for i in range(len(words)):
        if words[i][0] == ",":
            complex = 1
            if words[i + 1][0] == "and":
                if words[i - 1][1] == words[i + 2][1]:
                    splitSentence(sentence[:sentence.index(', and') + 2] + sentence[sentence.index(', and') + 6:], file, dataset)
                else:
                    splitSentence(sentence[:sentence.index(', and')] + sentence[sentence.index(', and') + 1:], file, dataset)
            elif words[i + 1][0] == "but":
                splitSentence(sentence[:sentence.index(', but')] + sentence[sentence.index(', but') + 1:], file, dataset)
            else:
                splitSentence(sentence[:sentence.index(',')]+ sentence[sentence.index(',') + len(words[i + 1][0]) + 2:], file, dataset)
                splitSentence(sentence[:(sentence.index(',') - len(words[i - 1][0]))] + sentence[sentence.index(',') + 1:], file, dataset)
            return 0
        if words[i][0] == "but":
            complex = 1
            if words[i + 1][1] in ["NN", "NNS", "NNP", "NNPS"]:
                splitSentence(sentence[:sentence.index('but') - 1], file, dataset)
                splitSentence(sentence[sentence.index('but') + 4:], file, dataset)
            else:
                count = 0
                j = i + 1
                while j < len(words):
                    if words[j][1] in ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]:
                        count = count + 1
                    j = j + 1
                if count > 0:
                    j = i
                    count = 0
                    while j >= 0:
                        if words[j][1] in ["NN", "NNS", "NNP", "NNPS"]:
                            count = count + 1
                        if count == 2:
                            break
                        j = j - 1
                    splitSentence(sentence[:sentence.index('but') - 1], file, dataset)
                    splitSentence(words[j][0] + sentence[sentence.index('but') + 3:], file, dataset)
                else:
                    j = i
                    count = 0
                    while j >= 0:
                        if words[j][1] in ["NN", "NNS", "NNP", "NNPS"]:
                            count = count + 1
                        if count == 2:
                            break
                        j = j - 1
                    n = words[j][0]
                    j = i
                    while j >= 0:
                        if words[j][1] in ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"]:
                            break
                        j = j - 1
                    v = words[j][0]
                    splitSentence(sentence[:sentence.index('but') - 1], file, dataset)
                    splitSentence(n + ' ' + v + sentence[sentence.index('but') + 3:], file, dataset)
            return 0
        if words[i][0] == "because":
            complex = 1
            if words[i + 1][1] in ["NN", "NNS", "NNP", "NNPS"]:
                ##fails for sentences starting with "Because"
                splitSentence(sentence[:sentence.index('because') - 1], file, dataset)
                splitSentence(sentence[sentence.index('because') + 8:], file, dataset)
            else:
                ##fails for sentences starting with "Because"
                splitSentence(sentence[:sentence.index('because') - 1], file, dataset)
            return 0
        if words[i][0] == "which":
            complex = 1
            if words[i + 1][0] in ["is", "are"]:
                j = i - 1
                while words[j][1] not in ["NN", "NNS", "NNP", "NNPS"]:
                    j = j - 1
                splitSentence(sentence[:sentence.index('which') - 1], file, dataset)
                splitSentence(words[j][0] + sentence[:sentence.index('which') + 6 ], file, dataset)
            if words[i + 1][0] == "in" and words[i + 2][0] == "turn":
                splitSentence(sentence[:sentence.index('which') - 1], file)
                splitSentence(words[j][0] + sentence[:sentence.index('which') + 14 ], file, dataset)
            return 0
        if words[i][0] == "although":
            complex = 1
            if words[i + 1][1] in ["NN", "NNS", "NNP", "NNPS"]:
                ##fails for sentences starting with "Although"
                splitSentence(sentence[:sentence.index('although') - 1], file, dataset)
                splitSentence(sentence[sentence.index('although') + 9:], file, dataset)
            else:
                ##fails for sentences starting with "Although"
                splitSentence(sentence[:sentence.index('although') - 1], file, dataset)
            return 0
        if words[i][0] == "instead":
            complex = 1
            splitSentence(sentence[:sentence.index('instead') - 1], file, dataset)
            return 0
        if words[i][0] == "inspite":
            complex = 1
            splitSentence(sentence[:sentence.index('inspite') - 1], file, dataset)
            return 0
        if words[i][0] == "for" and words[i + 1][0] == "example":
            complex = 1
            ##fails for sentences starting with "For example"
            splitSentence(sentence[:sentence.index('for example') - 1], file, dataset)
            splitSentence(sentence[sentence.index('for example') + 12:], file, dataset)
            return 0
        if words[i][0] == "hence":
            complex = 1
            splitSentence(sentence[:sentence.index('hence') - 1], file, dataset)
            splitSentence(sentence[sentence.index('hence') + 6:], file, dataset)
            return 0
        if words[i][0] == "therefore":
            complex = 1
            splitSentence(sentence[:sentence.index('therefore,') - 1], file, dataset)
            splitSentence(sentence[sentence.index('therefore,') + 11:], file, dataset)
            return 0
        if words[i][0] == "besides":
            complex = 1
            splitSentence(sentence[:sentence.index('besides,') - 1], file, dataset)
            splitSentence(sentence[sentence.index('besides,') + 8:], file, dataset)
            return 0
        if words[i][0] == "or":
            complex = 1
            splitSentence(sentence[:sentence.index('or')]+ sentence[sentence.index('or') + len(words[i + 1][0]) + 4:], file, dataset)
            splitSentence(sentence[:(sentence.index('or') - len(words[i - 1][0]) - 1)] + sentence[sentence.index('or') + 3:], file, dataset)
            return 0
        if words[i][0] == "also":
            complex = 1
            splitSentence(sentence[:sentence.index('also')]+ sentence[sentence.index('also') + 5:], file, dataset)
            return 0
        if words[i][0] == "and":
            complex = 1
            splitSentence(sentence[:sentence.index('and') - 1], file, dataset)
            splitSentence(sentence[sentence.index('and') + 4:], file, dataset)
            return 0

    if complex == 1:
        return 0

    for i in verbs:
        j = i + 1
        while j < len(words):
            if words[j][1] in ["NN", "NNS", "NNP", "NNPS"]:
                break
            j = j + 1
        if j == len(words):
            return -1
        targetEntity = words[j][0]
        if (i > 0):
            j = i - 1
        while j >= 0:
            if words[j][1] in ["NN", "NNS", "NNP", "NNPS"]:
                break
            j = j - 1
        sourceEntity = words[j][0]
        
        if words[i][0] in ["is", "has"]:
            if words[i + 1][0] == "not":
                if i + 2 in location:
                    addProp(sourceEntity, words[i + 1][0] + words[i + 2][0] + targetEntity, dataset)
                else:
                    addProp(sourceEntity, words[i + 1][0] + targetEntity, dataset)
            elif words[i - 1][0] == "not":
                if i + 1 in location:
                    addProp(sourceEntity, words[i - 1][0] + words[i + 1][0] + targetEntity, dataset)
                else:
                    addProp(sourceEntity, words[i - 1][0] + targetEntity, dataset)
            else:
                addProp(sourceEntity, targetEntity, dataset)
        else:
            if words[i + 1][0] == "not":
                if i + 2 in location:
                    addRel(sourceEntity, words[i][0] + words[i + 1][0] + words[i + 2][0], targetEntity, file, dataset)
                else:
                    addRel(sourceEntity, words[i][0] + words[i + 1][0], targetEntity, file, dataset)
            elif words[i - 1][0] == "not":
                if i + 1 in location:
                    addRel(sourceEntity, words[i - 1][0] + words[i][0] + words[i + 1][0], targetEntity, file, dataset)
                else:
                    addRel(sourceEntity, words[i - 1][0] + words[i][0], targetEntity, file, dataset)
            else:
                addRel(sourceEntity, words[i][0], targetEntity, file, dataset)

    for i in adjectives:
        j = i - 1
        while j >= 0:
            if words[j] in ["NN", "NNS", "NNP", "NNPS"]:
                break
            j = j - 1
        sourceEntity = words[j][0]
        addProp(sourceEntity, words[i][0], dataset)

    return 1
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#accessing the dataset
def documentsPath(path):
    if not os.path.exists(path):
        print "Path does nor exist!!!"
    
    files = os.listdir(path)
    if '.DS_Store' in files:
        files.remove('.DS_Store')
    print files
    for i in files:
        f = open(path + "/" + i, "r")
        passage = f.read()
        re.sub("\((.)*\)","",passage)
        re.sub("\'|\'|\"|\"","",passage)
        index = 0
        start = 0
        while index in range(len(passage)):
            if passage[index] == ".":
                sentence = passage[start:index]
                splitSentence(sentence, i, path)
                index = index + 1
                start = index
            else:
                index = index + 1

    addObjects(path)

    return entities
#<======================================================================================================================================>#

#<======================================================================================================================================>#
#k = []
#l=''
#fl=  open("whatIsQueriable.txt","w")
#k = documentsPath("moto_bulk")
#i1=''
#i2=''
#i3=''
#for i in k:
 #   l=l+"\n" + i.name +  "\n\t-" +  i.mergeProperties() +  "\n\t-" +  i.mergeRelations()
  #  fl.write(l)
   # print "\n", i.name, "\n\t-", i.mergeProperties(), "\n\t-", i.mergeRelations()
#fl.close()
#onto.createGraphJson(onto.parseResultsToEntities(onto.getObjects("moto_bulk","engineering")))
#<======================================================================================================================================>#
