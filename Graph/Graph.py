# Module for graph drawing and maintenance
from gi.repository import GooCanvas
from gi.repository import Gdk
import networkx as nx
from textwrap import TextWrapper

# Wrapper for CanvasPoints to allow sane object creation
class PointsFactory():
    def Points(xyarr):
        pts = GooCanvas.CanvasPoints.new(xyarr.len())
        for key,pair in xyarr:
            pts.set_point(key, pair[0], pair[1])
        return pts

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
        self.cboxes = list()
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
        self.cboxes = list()
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
            locations = nx.spring_layout(subg, scale=40*subg.order())
        
            #iterate over the nodes and draw each according to its given positions
            for gnode in subg.nodes_iter(True):
                pos = locations[gnode[0]]
                
                lbl_text = self.textwrap.fill(gnode[0])
                self.add_node(gnode[1]['node'], label=lbl_text, parent=self.gbox, x=pos[0], y=pos[1])
            #TODO draw lines
        
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
    
    # Draw an edge on the graph derived from all the links between two nodes.
    def add_line(self, lobj, parent=None, startx=0, starty=0, endx=1, endy=1):
        pass
    
    # Pack the graphs component subgraphs into as small a space as possible.
    def pack(self):
        pass
