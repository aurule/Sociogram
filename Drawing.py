# Module for graph drawing and maintenance
from gi.repository import GooCanvas
from gi.repository import Gdk
import networkx as nx
from textwrap import TextWrapper
from numpy import mean
from math import sqrt

import Errors
import painters

# Custom canvas class to handle graph drawing and interaction
class Canvas(GooCanvas.Canvas):
    '''Custom GooCanvas that natively handles node/edge drawing with networkx.'''
    
    def __init__(self, **args):
        '''Create a Canvas object. **args are passed to GooCanvas.Canvas constructor.'''
        GooCanvas.Canvas.__init__(self, **args)
        self.set_properties(automatic_bounds=True,
                            integer_layout=False,
                            bounds_from_origin=False,
                            bounds_padding=10)
        self.root = self.get_root_item()
        self.root.set_properties(fill_color='white')
        
        #initialize internal vars
        self.zoom = False
        self.node_callback = None
        self.line_callback = None
        self.key_handler = None
        self.cboxes = []
        self.vertices = {}
        self.textwrap = TextWrapper(width=10) #text wrapper for node labels
    
    def redraw(self, G):
        '''Draw the networkx graph G.'''
        del self.cboxes[:]
        self.vertices.clear()
        linked_nodes = []
        #first we clear off the old drawing
        try:
            self.gbox.remove()
        except AttributeError:
            pass
        
        #set up new box
        self.gbox = GooCanvas.CanvasGroup(parent=self.root)
        
        #get locations from the graph
        components = nx.connected_component_subgraphs(G)
        for subg in components:
            cbox = GooCanvas.CanvasGroup(parent = self.gbox)
            self.cboxes.append(cbox)
            locations = nx.spring_layout(subg, scale=100*subg.order())
        
            #iterate over the nodes and draw each according to its given positions
            for gnode in subg.nodes_iter(True):
                pos = locations[gnode[0]]
                
                lbl_text = self.textwrap.fill(gnode[0])
                #TODO assign style info to object based on style rules
                #   change painter if necessary
                ngroup = Vertex(gnode[1]['node'], parent=self.gbox, x=pos[0]+50, y=pos[1]+50, painter=painters.vertex.box)
                ngroup.connect("button-press-event", self.node_callback)
                self.vertices[ngroup.label] = ngroup
    
                coords = ngroup.get_xyr()
                ring = GooCanvas.CanvasEllipse(parent=cbox, radius_x=coords['radius'], radius_y=coords['radius'], center_x=coords['x'], center_y=coords['y'], fill_color_rgba=0x00000000, stroke_color_rgba=0x00000000)
            
            #iterate through edges and draw each according to its stored relationships
            for snode, enode, props in subg.edges_iter(data=True):
                #TODO assign style info to object based on style rules
                #   change painter if necessary
                line = AggLine(parent=self.gbox, fnode=self.vertices[snode], tnode=self.vertices[enode], rels=props['rels'], painter=painters.edge.line)
                
                #TODO attach this callback to individual relationships, not just the aggline
                #line.connect("button-press-event", self.line_callback)
        
        self.pack()
    
    # Pack the graphs component subgraphs into as small a space as possible.
    def pack(self):
        '''Pack component subgraphs into the drawing space.'''
        for sub in self.cboxes:
            #TODO all of it
            pass
        
class AggLine(GooCanvas.CanvasGroup):
    '''Represent an aggregate line with properties derived from all the relationships between its start and end points.'''
    
    def __init__(self, fnode, tnode, rels=None, painter=None, **args):
        '''Create a new aggregate line.'''
        GooCanvas.CanvasGroup.__init__(self, **args)

        self.type = 'rel'
        self.start_arrow = False
        self.end_arrow = False
        self.width = 5
        self.weights = []
        self.origin = fnode #Node object
        self.dest = tnode #Node object
        self.labels = [] #list of tuples (label, dir) where dir is 'from', 'to', or 'both'
        self.painter = painter
        self.selected = False

        #parse relationships
        if rels != None:
            for rel in rels:
                self.add_rel(rel)
        
        #draw if we're able
        if painter != None: self.draw()
    
    def add_rel(self, rel):
        '''Add properties from a relationship object.'''
        
        #add labels and arrows according to directionality
        if rel.mutual:
            self.labels.append((rel.label, 'both'))
            if not (self.start_arrow and self.end_arrow):
                self.start_arrow = True
                self.end_arrow = True
        if rel.ends_at(self.origin.label):
            self.labels.append((rel.label, 'from'))
            if not self.start_arrow:
                self.start_arrow = True
        if rel.ends_at(self.dest.label):
            self.labels.append((rel.label, 'to'))
            if not self.end_arrow:
                self.end_arrow = True
        
        #add weight to width concern
        self.weights.append(rel.weight)
        self.calc_width()
    
    def calc_width(self):
        '''Calculate line width from relationship weights.'''
        self.width = mean(self.weights)

    def set_painter(self, painter):
        '''Set the painting function used to draw this vertex, then call it.'''
        self.painter = painter
    
    def draw(self):
        if self.painter == None:
            return
        
        shape = self.painter.paint(parent=self, start=self.origin.get_xyr(), end=self.dest.get_xyr(), lobj=self)
    
    def set_selected(self, state):
        '''Mark our selected status and draw selection ring.'''
        self.selected = state
        self.painter.show_selected(state)

class Vertex(GooCanvas.CanvasGroup):
    '''Represent a node on the canvas.'''
    
    def __init__(self, node, x=0, y=0, painter=None, **args):
        '''Create a new Vertex which represents node.'''
        GooCanvas.CanvasGroup.__init__(self, **args)
        
        self.type = 'node'
        self.node = node
        self.label = node.label
        self.x = x
        self.y = y
        self.radius = 0
        self.painter = painter
        self.selected = False
        self.selring = None
        
        #if we were initialized with a painting function, draw immediately
        if painter != None: self.draw()

    def set_painter(self, painter):
        '''Set the painting function used to draw this object.'''
        self.painter = painter
    
    def draw(self):
        '''Draw with our painter, then recalculate x, y, and radius.'''
        if self.painter == None:
            return
        
        shape = self.painter.paint(parent=self, node=self.node)
        self.width = shape['width']
        self.height = shape['height']
        
        #now that something's drawn, center ourselves around our original x,y
        self.set_properties(x = self.x - self.width/2, y = self.y - self.height/2)
        
        #calculate and store our new radius
        bounds = self.get_bounds()
        dx = bounds.x1 - self.x
        dy = bounds.y1 - self.y
        self.radius = sqrt(dx*dx + dy*dy)
    
    def get_xyr(self):
        '''Return a dict of x, y, and radius.'''
        return {'x':self.x, 'y':self.y, 'radius':self.radius}
    
    def set_selected(self, state):
        '''Mark our selected status and draw selection ring.'''
        self.selected = state
        
        if self.selected:
            self.selring = self.painter.show_selected(self)
        else:
            self.selring.remove()
