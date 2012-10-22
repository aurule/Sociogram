# Module for graph drawing and maintenance
from gi.repository import GooCanvas
from gi.repository import Gdk
import networkx as nx
from textwrap import TextWrapper
from numpy import dot, mean
from math import sqrt

import Errors

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
        self.cboxes = []
        self.vertices = {}
        self.textwrap = TextWrapper(width=10) #text wrapper for node labels
        
        #connect signals
        self.connect("key_press_event", Canvas.eventhandler)
        self.connect("key_release_event", Canvas.eventhandler)
        self.connect("event", Canvas.eventhandler)
    
    #imported from elsewhere
    #TODO clean up and customize
    def eventhandler(self, e):
        '''Called by GTK whenever we get mouse or keyboard interactions.'''
        if e.type == Gdk.EventType.KEY_PRESS:
            kvn = Gdk.keyval_name(e.keyval)
            if kvn == 'a':
                self.scroll_to(0,0)
            if kvn == 'Control_L':
                if not self.zoom:
                    self.zoom = True
            elif kvn == 'plus' and self.zoom:
                self.props.scale *= 1.2
            elif kvn == 'minus' and self.zoom:
                self.props.scale *= 0.8
            return False
        elif e.type == Gdk.EventType.KEY_RELEASE:
            if Gdk.keyval_name(e.keyval) == 'Control_L':
                self.zoom = False
                return True
        elif e.type == Gdk.EventType.SCROLL and self.zoom:
            if e.direction == Gdk.SCROLL_UP:
                self.props.scale *= 1.2
            elif e.direction == Gdk.SCROLL_DOWN:
                self.props.scale *= 0.8
            return True
        elif e.type == Gdk.EventType.BUTTON_PRESS:
            print e.get_coords()
        return False
    
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
                ngroup = Vertex(gnode[1]['node'], parent=self.gbox, x=pos[0], y=pos[1], painter=self.boxpainter)
                ngroup.connect("button-press-event", self.node_callback)
                self.vertices[ngroup.label] = ngroup
            
            #iterate through edges and draw each according to its stored relationships
            for snode, enode, props in subg.edges_iter(data=True):
                line = AggLine(snode, enode, rels=props['rels'], painter=self.linepainter, parent=self.gbox)
                line.connect("button-press-event", self.line_callback)
            
        
        self.pack()
    
    # Pack the graphs component subgraphs into as small a space as possible.
    def pack(self):
        #TODO all of it
        pass
    
    def mkpoints(self, xyarr):
        '''Create a new Points object with coordinates from xyarr.'''
        pts = GooCanvas.CanvasPoints.new(len(xyarr))
        key = 0
        for x, y in xyarr:
            pts.set_point(key, x, y)
            key += 1
        return pts
    
    #TODO externalize
    def boxpainter(self, parent, node):
        label = node.label
        box = GooCanvas.CanvasRect(parent=parent, stroke_color_rgba=0x000000ff, fill_color_rgba=0xffff00ff)
        lbl = GooCanvas.CanvasText(parent=parent, text=label, alignment="center", fill_color='black')
        
        lbl_bounds = lbl.get_bounds()
        lw = lbl_bounds.x2 - lbl_bounds.x1
        lh = lbl_bounds.y2 - lbl_bounds.y1
        biggest = lw if lw > lh else lh
        
        lbl.set_properties(x=10+(biggest-lw)/2, y=10+(biggest-lh)/2)
        box.set_properties(width=biggest+20, height=biggest+20)
        
        props = {'width': biggest+20, 'height': biggest+20}
        return props
    
    #TODO externalize
    def linepainter(self, parent, start, end, lobj):
        '''Draw an edge on the graph with properties from AggLine lobj.'''
        spos = self.vertices[start].get_xyr() #x, y, radius
        epos = self.vertices[end].get_xyr() #x, y, radius
                
        #calculate magnitude of vector from spos to epos
        dx = spos['x'] - epos['x']
        dy = spos['y'] - epos['y']
        mag = sqrt(dx*dx + dy*dy)
        
        #adjust deltas
        dx = dx/mag
        dy = dy/mag
        
        #calculate start and end coords from the node radii
        startx = epos['x'] + dx*(mag - spos['radius'])
        starty = epos['y'] + dy*(mag - spos['radius'])
        endx = spos['x'] - dx*(mag - epos['radius'])
        endy = spos['y'] - dy*(mag - epos['radius'])
        
        #construct the points
        pts = self.mkpoints([(startx, starty), (endx, endy)])
        
        #draw the line
        GooCanvas.CanvasPolyline(end_arrow=lobj.end_arrow, start_arrow=lobj.start_arrow, points=pts, parent=parent, arrow_length=9, arrow_tip_length=7, arrow_width=7, line_width=lobj.width/2)
        #TODO add dots and text above/left of the line
        

class AggLine(GooCanvas.CanvasGroup):
    '''Represents an aggregate line with properties derived from all the relationships between its start and end points.'''
    
    def __init__(self, fnode, tnode, rels=None, painter=None, **args):
        '''Create a new aggregate line.'''
        GooCanvas.CanvasGroup.__init__(self, **args)

        self.start_arrow = False
        self.end_arrow = False
        self.width = 5
        self.weights = []
        self.origin = fnode
        self.dest = tnode
        self.labels = [] #list of tuples (label, dir) where dir is 'from', 'to', or 'both'
        self.painter = None

        #parse relationships
        if rels != None:
            for rel in rels:
                self.add_rel(rel)
        
        #draw if we're able
        if painter != None: self.set_painter(painter)
    
    def add_rel(self, rel):
        '''Add properties from a relationship object.'''
        
        #add labels and arrows according to directionality
        if rel.mutual:
            self.labels.append((rel.label, 'both'))
            if not (self.start_arrow and self.end_arrow):
                self.start_arrow = True
                self.end_arrow = True
        if rel.ends_at(self.origin):
            self.labels.append((rel.label, 'from'))
            if not self.start_arrow:
                self.start_arrow = True
        if rel.ends_at(self.dest):
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
        self.painter = painter
        shape = painter(parent=self, start=self.origin, end=self.dest, lobj=self)

class Vertex(GooCanvas.CanvasGroup):
    '''Represents a shape+label on the canvas.'''
    
    def __init__(self, node, x=0, y=0, painter=None, **args):
        GooCanvas.CanvasGroup.__init__(self, **args)
        
        self.node = node
        self.label = node.label
        self.x = x
        self.y = y
        self.radius = 0
        self.painter = None
        
        #if we were initialized with a painting function, draw immediately
        if painter != None: self.set_painter(painter)

    def set_painter(self, painter):
        self.painter = painter
        
        shape = painter(parent=self, node=self.node)
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
        return {'x':self.x, 'y':self.y, 'radius':self.radius}
