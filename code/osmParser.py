from imposm.parser import OSMParser
import snap
import json
import pickle

DATA_PATH = "../data/"

class Node:
	def __init__(self, osmid, tags, coords):
		self._osmid = osmid
		self._tags = tags
		self._coords = (coords[1], coords[0])

	# OSM id, int
	def osmid(self):
		return self._osmid

	# tags, dict
	def tags(self):
		return self._tags

	# coordinates, (latitude, longitude)
	def coords(self):
		return self._coords

class Way:
	def __init__(self, osmid, tags, refs):
		self._osmid = osmid
		self._tags = tags
		self._refs = refs

	def osmid(self):
		return self._osmid

	def tags(self):
		return self._tags

	def refs(self):
		return self._refs

# simple class that handles the parsed OSM data.
class ParseOSM(object):
	nodes = {} # format: osmid : Node
	ways = {} # format: osmid : Way

	def waysCallback(self, w):
		for tup in w:
			self.ways[tup[0]] = Way(tup[0], tup[1], tup[2])

	def nodesCallback(self, n):
		for tup in n:
			self.nodes[tup[0]] = Node(tup[0], tup[1], tup[2])

class GraphParser():
	# create snap graph from parsed nodes and ways
	def createGraph(self, osm):
		G = snap.TUNGraph.New()
		renumbered = {}
		idToOsmid = {}
		counter = 0

		for osmid in osm.ways:
			refs = osm.ways[osmid].refs()
			if 'highway' in osm.ways[osmid].tags():
				for i in range(0, len(refs) - 1):
					start = refs[i]
					end = refs[i+1]

					# not all edges in a way are in nodes in the graph if at the boundary
					if start not in osm.nodes or end not in osm.nodes:
						continue

					# if way is a road, add nodes if they haven't been added before
					if start not in renumbered:
						renumbered[start] = counter
						idToOsmid[counter] = start
						G.AddNode(counter)
						counter += 1
					if end not in renumbered:
						renumbered[end] = counter
						idToOsmid[counter] = end
						G.AddNode(counter)
						counter += 1

					G.AddEdge(renumbered[start], renumbered[end])

		return G, idToOsmid

def parseToGraph(file_name, concurrency=4):
	# instantiate counter and parser and start parsing
	o = ParseOSM()
	p = OSMParser(concurrency=concurrency, ways_callback=o.waysCallback, nodes_callback=o.nodesCallback)
	p.parse(file_name)

	G, idToOsmid = GraphParser().createGraph(o)
	return G, idToOsmid, o # graph, idToOsmid, ParseOSM object

def saveToFile(G, idToOsmid, osm, name):
	out = snap.TFOut(DATA_PATH + name + ".graph") # graph saved as _.graph
	G.Save(out)
	out.Flush()

	idOut = open(DATA_PATH + name + ".id", 'w')
	pickle.dump(idToOsmid, idOut, 1)

	nodesOut = open(DATA_PATH + name + ".nodes", 'w')
	pickle.dump(osm.nodes, nodesOut, 1)

	edgesOut = open(DATA_PATH + name + ".edges", 'w')
	pickle.dump(osm.nodes, edgesOut, 1)

def loadFromFile(name):
	G = snap.TUNGraph.Load(snap.TFIn(DATA_PATH + name + ".graph"))

	idIn = open(DATA_PATH + name + ".id", 'r')
	idToOsmid = pickle.load(idIn)

	osm = ParseOSM()
	nodesIn = open(DATA_PATH + name + ".nodes", 'r')
	osm.nodes = pickle.load(nodesIn)

	edgesIn = open(DATA_PATH + name + ".edges", 'r')
	osm.edges = pickle.load(edgesIn)

	return G, idToOsmid, osm


fileName = 'stanford'
# G, idToOsmid, o = parseToGraph(fileName + '.osm')
# saveToFile(G, idToOsmid, o, fileName)

G, idToOsmid, o = loadFromFile(fileName)

print G.GetNodes()
nodeToBetweenness = snap.TIntFltH()
edgeToBetweenness = snap.TIntPrFltH()
betweenness = snap.GetBetweennessCentr(G, nodeToBetweenness, edgeToBetweenness)

maxCentrality = 0
maxNode = None
for node in nodeToBetweenness:
	print o.nodes[idToOsmid[node]].tags()
	print "Centrality:", nodeToBetweenness[node]
	if nodeToBetweenness[node] > maxCentrality:
		maxCentrality = nodeToBetweenness[node]
		maxNode = node

print maxCentrality
print o.nodes[idToOsmid[maxNode]].osmid(), o.nodes[idToOsmid[maxNode]].tags(), o.nodes[idToOsmid[maxNode]].coords()
