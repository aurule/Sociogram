from uuid import uuid4
import networkx as nx
import Errors

# Represents graph nodes (people, places, groups, etc.)
class Node(object):
    '''Handle storage and interaction with graph nodes and their properties.'''

    # set up our label, uuid, and attributes (if given)
    # attrs format: [(name, val, vis=False), (name, val, vis=False), ...]
    def __init__(self, lbl, attrs=None):
        '''Create a node.'''
        self.label = lbl
        self.uid = uuid4()
        self.attributes = {}
        
        if attrs != None:
            for element in attrs:
                self.add_attr(element)
    
    def add_attr(self, attr):
        '''Add an attribute.'''
        uid = str(uuid4())
        self.attributes[uid] = {"name": attr[0], "value": attr[1], "visible": attr[2]}
        return uid
    
    def del_attr(self, uid):
        '''Remove an attribute. Raises AttrError exception if attribute doesn't exist.'''
        try:
            del self.attributes[uid]
        except:
            raise AttrError("Attribute UUID %s does not exist" % uid)
    
    # Our label is the only thing that should be printed by default
    def __str__(self):
        return self.label

class Relationship(Node):
    '''Handle storage and interaction with node-to-node relationships, and their attributes.'''

    #wgt is an int; bidir is bool
    def __init__(self, lbl, fnode, tnode, wgt, bidir, attrs=None):
        '''Create a relationship.'''
        Node.__init__(self, lbl, attrs)
        self.from_node = fnode
        self.to_node = tnode
        self.weight = wgt
        self.mutual = bidir
    
    def touches(self, node):
        '''Determine whether this relationship eminates or terminates at node.'''
        return self.to_node == node or self.from_node == node
    
    def spans(self, a, b):
        '''Determine whether this relationship touches both a and b.'''
        return self.touches(a) and self.touches(b) and a is not b
    
    def ends_at(self, node):
        '''Determine whether this relationship terminates at node.'''
        return self.to_node == node

class Sociograph(nx.Graph):
    '''Maintain independent data model using a networkx graph.'''
    
    def __init__(self):
        nx.Graph.__init__(self)
    
    def add_rel(self, rel):
        '''Add a relationship, creating an edge if necessary.'''
        fname = rel.from_node
        tname = rel.to_node
        
        #update existing edge if possible, otherwise add new edge
        if self.has_edge(fname, tname):
            self[fname][tname]['rels'].append(rel)
            new_edge = False
        else:
            self.add_edge(fname, tname, rels=[rel])
            new_edge = True
        
        return new_edge
    
    def remove_rel(self, rel):
        '''Remove a relationship, as well as its edge if possible.'''
        
        #remove relationship
        flbl = rel.from_node
        tlbl = rel.to_node
        rel_list = self[flbl][tlbl]['rels']
        
        if len(rel_list) == 1 and rel_list[0].uid == rel.uid:
            #if there's only one rel for this edge, remove the whole edge
            self.remove_edge(flbl, tlbl)
            return True
        else:
            #if the edge has more than one rel, just remove this rel
            for k in rel_list:
                if k.uid == rel.uid:
                    rel_list.remove(rel)
                    ret = True
            if ret:
                return True
        
        #relationship doesn't exist
        return None
    
    def move_rel(self, rel, origin=None, dest=None):
        '''Move a relationship from one edge to another.'''
        if origin == None and dest == None:
            return
        
        self.remove_rel(rel)
        if origin: rel.from_node = origin
        if dest: rel.to_node = dest
        self.add_rel(rel)
