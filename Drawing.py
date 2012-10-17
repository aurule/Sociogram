# Module for graph drawing and maintenance
from gi.repository import GooCanvas
from gi.repository import Gdk
import networkx as nx
from textwrap import TextWrapper
from numpy import dot
from math import sqrt

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
        self.nodecoords = {}
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
        self.nodecoords.clear()
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
                nbox = self.add_node(gnode[1]['node'], label=lbl_text, parent=self.gbox, x=pos[0], y=pos[1])
                
                #calculate and store the node's bounding radius along with its coords
                bounds = nbox.get_bounds()
                dx = bounds.x1 - pos[0]
                dy = bounds.y1 - pos[0]
                radius = sqrt(dx*dx + dy*dy)
                self.nodecoords[gnode[0]] = (pos[0], pos[1], radius)
                print pos
            
            #iterate through edges and draw each according to its stored relationships
            for snode, enode, props in subg.edges_iter(data=True):
                rels = props['rels']
                line = AggLine(rels)
                self.add_line(line, snode, enode, parent=self.gbox)
            
        
        self.pack()
    
    def add_node(self, nobj, label=None, parent=None, x=0, y=0):
        '''Add a node to the graph. nobj is a Data.Node object.'''
        #TODO
        #apply style rules
        #show displayed attributes
        #externalize colors and paramaterize shape drawing
        
        if label == None:
            label = nobj.label
        
        #create a group for this node's elements
        ngroup = GooCanvas.CanvasGroup(parent=parent, x=x, y=y)
        ngroup.connect("button-press-event", self.node_callback)
        
        box = GooCanvas.CanvasRect(parent=ngroup, stroke_color_rgba=0x000000ff, fill_color_rgba=0xffff00ff)
        lbl = GooCanvas.CanvasText(parent=ngroup, text=label, alignment="center", fill_color='black')
        
        lbl_bounds = lbl.get_bounds()
        lw = lbl_bounds.x2 - lbl_bounds.x1
        lh = lbl_bounds.y2 - lbl_bounds.y1
        biggest = lw if lw > lh else lh
        
        lbl.set_properties(x=10+(biggest-lw)/2, y=10+(biggest-lh)/2)
        box.set_properties(width=biggest+20, height=biggest+20)
        
        return ngroup
    
    # Draw an edge on the graph 
    def add_line(self, lobj, snode, enode, parent=None):
        '''Draw an edge on the graph with properties from AggLine lobj.'''
        spos = self.nodecoords[snode] #x, y, radius
        epos = self.nodecoords[enode] #x, y, radius
        
        #TODO calculate x and y values for the center of the circle
        #   spos and epos have x,y at the upper-left corner, which lies on the circle
        start_center - {'x': spos[0], 'y': spos[1], 'rad': spos[2])
        end_center = ('x': epos[0], 'y': epos[1], 'rad': epos[2])
        
        #calculate magnitude of vector from spos to epos
        dx = start_center['x'] - end_center['x']
        dy = start_center['y'] - end_center['y']
        mag = sqrt(dx*dx + dy*dy)
        
        #adjust deltas
        dx = dx/mag
        dy = dy/mag
        
        #calculate start and end coords from the node radii
        #TODO update to use center x and y coords for both start and end
        startx = spos[0] - dx*(mag - spos[2])
        starty = spos[1] - dy*(mag - spos[2])
        endx = spos[0] - dx*(mag - epos[2])
        endy = spos[1] - dy*(mag - epos[2])
        
        startx = spos[0]
        starty = spos[1]
        endx = epos[0]
        endy = epos[1]
        
        #construct the points
        pts = self.mkpoints([(startx, starty), (endx, endy)])
        
        #draw the line
        #TODO base arrow stuff on lobj
        GooCanvas.CanvasPolyline(end_arrow=True, start_arrow=False, points=pts, parent=parent, arrow_length=10, arrow_tip_length=8, arrow_width=8)
    
    # Pack the graphs component subgraphs into as small a space as possible.
    def pack(self):
        pass
    
    def mkpoints(self, xyarr):
        '''Create a new Points object with coordinates from xyarr.'''
        pts = GooCanvas.CanvasPoints.new(len(xyarr))
        key = 0
        for x, y in xyarr:
            pts.set_point(key, x, y)
            key += 1
        return pts

class AggLine:
    '''Represents an aggregate line with properties derived from all the relationships between its start and end points.'''
    
    def __init__(self, rels):
        '''Create a new aggregate line.'''

        self.start_arrow = False
        self.end_arrow = False
        self.width = 5

        if rels == None:
            return
        
        for rel in rels:
            self.add_rel(rel)
    
    def add_rel(self, rel):
        '''Add properties from a relationship object.'''
        #TODO determine arrows, labels, thickness, etc. from the relationship
