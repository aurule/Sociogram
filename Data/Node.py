from uuid import uuid4
import Errors

# Represents graph nodes (people, places, groups, etc.)
class Node:
    '''Handle storage and interaction with graph nodes and their properties.'''

    # set up our label, uuid, and attributes (if given)
    # attrs format: [(name, val, vis=False), (name, val, vis=False), ...]
    def __init__(self, lbl, attrs=None):
        '''Create a node.'''
        self.label = lbl
        self.uid = uuid4()
        if attrs != None:
            for element in attrs:
                self.add_attr(element)
        else:
            self.attributes = {}
    
    def add_attr(self, attr):
        '''Add an attribute.'''
        uid = uuid4()
        self.attributes[uid] = {"name": attr[0], "value": attr[1], "visible": attr[2]}
        return uid
    
    def del_attr(self, uid):
        '''Remove an attribute. Raises AttrError exception if attribute doesn't exist.'''
        try:
            self.attributes.remove(uid)
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
    
    def touches(node):
        '''Determine whether this relationship eminates or terminates at node.'''
        return self.to_node == node or self.from_node == node
    
    def spans(a, b):
        '''Determine whether this relationship touches both a and b.'''
        return self.touches(a) and self.touches(b) and a is not b
