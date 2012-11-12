# Module for graph drawing and maintenance
from gi.repository import GooCanvas, Gdk, Pango
import networkx as nx
from textwrap import TextWrapper
from numpy import mean
from math import sqrt
from operator import itemgetter, attrgetter

import Errors
import painters

# Custom canvas class to handle graph drawing and interaction
class Canvas(GooCanvas.Canvas):
    '''Custom GooCanvas that natively handles node/edge drawing with networkx.'''
    
    def __init__(self, vsheet=None, esheet=None, **args):
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
        self.mouseover_callback = None
        self.key_handler = None
        self.cboxes = []
        self.textwrap = TextWrapper(width=8) #text wrapper for node labels
        self.space = None
        self.edge_default_stylesheet = esheet
        self.vertex_default_stylesheet = vsheet
        self.gbox = GooCanvas.CanvasGroup(parent = self.root)
        
        #default to a blank stylesheet if none was provided
        #yes, this will cause big drawing errors if you don't bother to populate it
        if esheet == None:
            self.edge_default_stylesheet = Stylesheet()
        if vsheet == None:
            self.vertex_default_stylesheet = Stylesheet()
    
    def redraw(self, G):
        '''Draw the networkx graph G, including new layout.'''
        #first we clear off the old drawing
        for c in self.cboxes:
            c.remove()
        
        del self.cboxes[:]
        
        #get locations from the graph
        components = nx.connected_component_subgraphs(G)
        for subg in components:
            locations = nx.spring_layout(subg, scale=250*subg.order())
            cbox = SubGraph(parent = self.gbox, locs=locations, graph=subg)
            self.cboxes.append(cbox)
            
            #iterate over the nodes and draw each according to its given positions
            for gnode in subg.nodes_iter():
                nodeobj = G.node[gnode]['node']
                pos = locations[gnode]
                lbl_text = self.textwrap.fill(gnode)
                
                #initialize background ring for spacing
                #done before the vertex so it'll be in the background and not interrupt clicking
                ring = GooCanvas.CanvasEllipse(parent=cbox, fill_color_rgba=0x00000000, stroke_color_rgba=0x00000000)
                
                #TODO assign style info to object based on style rules
                #   change painter if necessary
                ngroup = Vertex(nodeobj, parent=cbox, x=pos[0], y=pos[1], painter=painters.vertex.box, text=lbl_text, sheet=self.vertex_default_stylesheet)
                ngroup.connect("button-press-event", self.node_callback)
                ngroup.connect("enter-notify-event", self.mouseover_callback, True)
                ngroup.connect("leave-notify-event", self.mouseover_callback, False)
                cbox.vertices[ngroup.label] = ngroup
                cbox.spacers[ngroup.label] = ring
    
                #define ring properties
                coords = ngroup.get_xyr()
                ring.set_properties(radius_x=coords['radius'], radius_y=coords['radius'], center_x=coords['x'], center_y=coords['y'])
            
            #iterate through edges and draw each according to its stored relationships
            for snode, enode in subg.edges_iter():
                #get relationship list from original graph to ensure we store references to the correct objects, instead of their copies
                rels = G[snode][enode]['rels']
                #TODO assign style info to object based on style rules
                #   change painter if necessary
                line = AggLine(parent=cbox, fnode=cbox.vertices[snode], tnode=cbox.vertices[enode], rels=rels, painter=painters.edge.line, sheet=self.edge_default_stylesheet)
                cbox.edges.append(line)
                
                line.connect("button-press-event", self.line_callback)
                line.connect("enter-notify-event", self.mouseover_callback, True)
                line.connect("leave-notify-event", self.mouseover_callback, False)
        
        self.pack()
        
    def refresh(self, obj, data = None):
        '''Update visuals without calculating a new layout.'''
        if obj.type == "node":
            subg = None
            if not data == None:
                # If a node got relabeled, we can still avoid a full redraw. However,
                # the subgraph needs to do some rejiggering.
                subg = self.get_container(data)
                subg.refresh_node(obj.label, data)
            
            #redraw vertex and all edges touching it
            v = self.get_vertex(obj.label)
            
            #update vertex data
            #v.node is a reference, and that object has already been updated
            v.label = v.node.label
            v.text = self.textwrap.fill(v.label)
            
            v.draw()
            if not subg == None: subg.add_spacer(v.label) #rejigger spacer
            #redraw all adjacent edges
            for e in self.get_edges(obj.label):
                e.draw()
        elif obj.type == "rel":
            #redraw edge
            e = self.get_edge(obj.from_node, obj.to_node)
            if data == "deleted":
                e.remove_rel(obj)
            else:
                e.add_rel(obj)
            e.draw()
            
    def pack(self):
        '''Pack component subgraphs into the drawing space.'''
        if len(self.cboxes) == 0:
            return
        
        del self.space
        
        #figure out the maximum possible dimensions by layout all our subgraphs end-to-end
        tog = 0
        worst_w = 0
        worst_h = 0
        boxes = []
        for subg in self.cboxes:
            bounds = subg.get_bounds()
            h = bounds.y2 - bounds.y1
            w = bounds.x2 - bounds.x1
            boxes.append((w*h, subg, w, h))
            
            #add each box to either the width or height of the max bounds
            #this ensures relatively sane packing behavior
            worst_w = max(worst_w, w)
            worst_h = max(worst_h, h)
            if tog:
                worst_w += max(w, h)
            else:
                worst_h += max(w, h)
            tog = not tog
        
        #sort the subgraphs by size
        keys = sorted(boxes, reverse=True)
        
        #pack each individually
        self.space = Packer(0, 0, worst_w, worst_h)
        for key, subg, w, h in keys:
            (x, y) = self.space.place(w, h)
            subg.set_properties(x=x, y=y)
    
    def get_vertex(self, label):
        '''Find vertex object by label.'''
        for subg in self.cboxes:
            if label in subg.vertices:
                return subg.vertices[label]
        
        return None
    
    def get_edge(self, tlbl, flbl):
        '''Find the edge between nodes tlbl and flbl.'''
        for subg in self.cboxes:
            #pick the right box
            if tlbl in subg.vertices and flbl in subg.vertices:
                #test every edge
                for edge in subg.edges:
                    if edge.spans(tlbl, flbl): return edge
        
        return None
    
    def get_edges(self, label):
        '''Find all agglines which touch node label.'''
        ret = []
        for subg in self.cboxes:
            #pick the right box
            if label in subg.vertices:
                for edge in subg.edges:
                    if edge.touches(label): ret.append(edge)
        
        return ret
    
    def get_container(self, label):
        '''Find subgraph which contains vertex object labeled "label".'''
        for subg in self.cboxes:
            if label in subg.vertices:
                return subg
        
        return None
    
    def get_bounds(self):
        '''Return the bounds for our master box.'''
        return self.gbox.get_bounds()
    
class Packer(object):
    '''Tree for packing rectangles into an area.'''
    def __init__(self, x, y, width, height):
        '''Set up this node of the tree.'''
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.child = None
        self.used = False
    
    def place(self, width, height):
        '''Find coordinates for a box of width,height.'''
        if self.child != None:
            #if we aren't a child, try our 0 child first
            coords = self.child[0].place(width, height)
            if coords != None:
                return coords
        
            #if that fails, try the 1 child
            return self.child[1].place(width, height)
        else:
            #if we're a leaf...
            #can't place something if we're occupied
            if self.used: return None
            #nor if the box is too big for us
            if width > self.w or height > self.h: return None
            #but if it's exactly the right size, go ahead
            if width == self.w and height == self.h:
                self.used = True
                return (self.x, self.y)
            
            #by now, we have the space to hold said box, so let's allocate it
            self.child = []
            
            dw = self.w - width
            dh = self.h - height
            
            if dw > dh:
                #set up children so child[0] has the exact width needed
                self.child.append(Packer(self.x, self.y, width, self.h))
                self.child.append(Packer(self.x + width, self.y, self.w - width, self.h))
            else:
                #set up children so child[0] has the exact height needed
                self.child.append(Packer(self.x, self.y, self.w, height))
                self.child.append(Packer(self.x, self.y + height, self.w, self.h - height))
            
            #ask our tailored child to place the box
            return self.child[0].place(width, height)

class AggLine(GooCanvas.CanvasGroup):
    '''Represent an aggregate line with properties derived from all the relationships between its start and end points.'''
    
    def __init__(self, fnode, tnode, rels=None, painter=None, sheet=None, **args):
        '''Create a new aggregate line.'''
        GooCanvas.CanvasGroup.__init__(self, **args)

        self.type = 'edge'
        self.start_arrow = False
        self.end_arrow = False
        self.width = 5
        self.weights = []
        self.origin = fnode #vertex object
        self.dest = tnode #vertex object
        self.labels_both = []
        self.labels_from = []
        self.labels_to = []
        self.rels = []
        self.label = {'bidir': '', 'from': '', 'to': ''}
        self.painter = painter
        self.selected = False
        self.stylesheet = sheet
        self.selring = None
        
        if sheet == None:
            self.stylesheet = Stylesheet()

        #parse relationships
        if rels != None:
            for rel in rels:
                self._add_rel(rel)
            self.calc_width()
            self.calc_label()
            self.rels = sorted(self.rels, key=attrgetter('weight', 'label'), reverse=True)
        
        #draw if we're able
        if painter != None: self.draw()
        
        self.connect("query-tooltip", self.rel_tooltip)
    
    def spans(self, lbl1, lbl2):
        '''Return whether or not we touch vertices with labels lbl1 and lbl2.'''
        if lbl1 == lbl2: return False
        
        ends = (lbl1, lbl2)

        olbl = self.origin.label
        dlbl = self.dest.label
        
        if (olbl in ends) and (dlbl in ends): return True
        return False
    
    def touches(self, label):
        '''Determine if one of our endpoints has the given label.'''
        ends = (self.origin.label, self.dest.label)
        return label in ends
    
    def rel_tooltip(self, me, x, y, kbd, tooltip):
        '''Event handler to set a tooltip message containing our relationships.'''
        if not (self.start_arrow or self.end_arrow):
            return False
        
        outtext = []
        fname = self.origin.label
        tname = self.dest.label
        
        for rel in self.rels:
            if rel.mutual:
                text = "Both <b>"+rel.label+"</b>"
            else:
                text = rel.from_node+" <b>"+rel.label+"</b> "+rel.to_node
            outtext.append(text)
        
        out = "\n".join(outtext)
        tooltip.set_markup(out) #set our tooltip
        
        #reply that this event has been handled
        return True
    
    def get_heaviest(self):
        '''Find the relationship with the highest weight.'''
        return self.rels[0]
    
    def add_rel(self, rel):
        '''Add properties from a relationship object.'''
        self._add_rel(rel)
        
        self.calc_width() #calculate new average weight
        self.calc_label() #calculate new label text
        self.rels = sorted(self.rels, key=attrgetter('weight', 'label'), reverse=True)
    
    def _add_rel(self, rel):
        '''Internal function to add relationship properties without any recalculating.'''
        #if the new relationship has the same id as one already added, remove the old one first
        if self.rels.count(rel):
            self.rels.remove(rel)
        
        self.rels.append(rel)
    
    def remove_rel(self, rel):
        '''Remove a relationship.'''
        if self.rels.count(rel):
            self.rels.remove(rel)
        
        self.calc_width() #calculate new average weight
        self.calc_label() #calculate new label text
        self.rels = sorted(self.rels, key=attrgetter('weight', 'label'), reverse=True)
    
    def calc_width(self):
        '''Calculate line width from relationship weights.'''
        del self.weights[:]
        for rel in self.rels:
            #store weights for other potential uses
            self.weights.append(rel.weight)
            
        self.width = mean(self.weights)

    def calc_label(self):
        '''Decide on label text, given label weights and directions.'''
        self.start_arrow = False
        self.end_arrow = False
        del self.labels_both[:]
        del self.labels_from[:]
        del self.labels_to[:]
        for rel in self.rels:
            #add labels and arrows according to directionality
            if rel.mutual:
                self.labels_both.append([rel.weight, rel.label])
                if not (self.start_arrow and self.end_arrow):
                    self.start_arrow = True
                    self.end_arrow = True
            else:
                if rel.ends_at(self.origin.label):
                    self.labels_from.append([rel.weight, rel.label])
                    if not self.start_arrow:
                        self.start_arrow = True
                if rel.ends_at(self.dest.label):
                    self.labels_to.append([rel.weight, rel.label])
                    if not self.end_arrow:
                        self.end_arrow = True
        
        #sort by weight, then by text
        lbl_bidir = sorted(self.labels_both, key=itemgetter(0, 1))
        lbl_from = sorted(self.labels_from, key=itemgetter(0, 1))
        lbl_to = sorted(self.labels_to, key=itemgetter(0, 1))
        
        #take the last element from each and splice it into the label field
        self.label['bidir'] = lbl_bidir[-1] if lbl_bidir else ''
        self.label['from'] = lbl_from[-1] if lbl_from else ''
        self.label['to'] = lbl_to[-1] if lbl_to else ''

    def set_painter(self, painter):
        '''Set the painting function used to draw this vertex, then call it.'''
        self.painter = painter
    
    def draw(self):
        '''Draw with our painter.'''
        if self.painter == None:
            return
        
        #remove any child objects we have
        for x in reversed(xrange(self.get_n_children())):
            self.get_child(x).remove()
        
        shape = self.painter.paint(self)
    
    def set_selected(self, state):
        '''Mark our selected status and draw selection ring.'''
        self.selected = state
        
        if self.selected:
            self.selring = self.painter.show_selected(self)
        else:
            self.selring.remove()
    
    def clear_rels(self):
        '''Clear out all relationship-derived data.'''
        del self.weights[:]
        del self.labels[:]
    
    def get_xyr(self):
        '''Return our central x and y coords, and a placeholder radius.'''
        xyr1 = self.origin.get_xyr()
        xyr2 = self.dest.get_xyr()
        x = (xyr1['x'] + xyr2['x']) / 2
        y = (xyr1['y'] + xyr2['y']) / 2
        
        return {'x':x, 'y':y, 'radius':0}
    
    def shift(self, oldlbl, new_obj):
        '''Change an endpoint to use a new object.'''
        if self.origin.label == oldlbl: self.origin = new_obj
        elif self.dest.label == oldlbl: self.dest = new_obj

class Vertex(GooCanvas.CanvasGroup):
    '''Represent a node on the canvas.'''
    
    def __init__(self, node, x=0, y=0, painter=None, text=None, sheet=None, **args):
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
        self.text = text
        self.stylesheet = sheet
        
        #get default stylesheet if none was provided
        if sheet == None:
            self.stylesheet = Stylesheet()
        
        #default text is our label
        if text == None:
            self.text = self.label
        
        #if we were initialized with a painting function, draw immediately
        if painter != None: self.draw()
        
        self.connect("query-tooltip", self.attr_tooltip)
    
    def attr_tooltip(self, me, x, y, kbd, tooltip):
        '''Event handler to set a tooltip message containing our attributes.'''
        if len(self.node.attributes) == 0:
            return False
        
        outtext = []
        
        #get our attributes
        attrs = self.node.attributes.itervalues()
        #show in sorted order
        for attr in sorted(attrs, key=itemgetter('name', 'value')):
            outtext.append("<b>"+attr['name']+"</b>: "+attr['value'])
        out = "\n".join(outtext)
        tooltip.set_markup(out) #set our tooltip
        
        #reply that this event has been handled
        return True

    def set_painter(self, painter):
        '''Set the painting function used to draw this object.'''
        self.painter = painter
    
    def draw(self):
        '''Draw with our painter, then recalculate x, y, and radius.'''
        if self.painter == None:
            return        
        
        #remove any child objects we have
        for x in reversed(xrange(self.get_n_children())):
            self.get_child(x).remove()
        
        #draw some new ones
        shape = self.painter.paint(self)
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

class SubGraph(GooCanvas.CanvasGroup):
    '''Represents a connected subgraph on the graph.'''
    
    def __init__(self, locs=None, graph=None, **args):
        '''Set up accounting structures and init canvasgroup.'''
        GooCanvas.CanvasGroup.__init__(self, **args)
        
        self.locations = locs
        self.G = graph
        self.vertices = {}
        self.spacers = {} #dict of spacing rings for each vertex
        self.edges = []
    
    def refresh_node(self, newlbl, oldlbl):
        '''Relabel an existing node without recalculating.'''
        # Note: Because each AggLine stores its origin and destination nodes as
        # references to Vertex objects, we only need to update the vertices.
        
        #update internal vertices list
        self.vertices[newlbl] = self.vertices[oldlbl]
        del self.vertices[oldlbl]
        
        #nix the old (and now likely incorrect) spacer
        #calling function will probably want to have us add a new one with add_spacer
        del self.spacers[oldlbl]
        
        #relabel our subgraph
        nx.relabel_nodes(self.G, {oldlbl:newlbl}, False)
    
    def add_spacer(self, vname):
        '''Add a spacer for the vertex named "vname".'''
        v = self.vertices[vname]
        coords = v.get_xyr()
        ring = GooCanvas.CanvasEllipse(parent=self, fill_color_rgba=0x00000000, stroke_color_rgba=0x00000000, radius_x=coords['radius'], radius_y=coords['radius'], center_x=coords['x'], center_y=coords['y'])
        ring.lower(v)

class Stylesheet(object):
    '''Defines styling properties for a vertex or edge.'''
    
    def __init__(self):
        '''Set default drawing values.'''
        #vertex: background color of the box
        self.fill_color = None
        
        #vertex: color of the box outline
        #edge: color of the edge line
        self.stroke_color = None
        
        #color of the text shown
        self.text_color = None
        
        #font description for the text shown
        #must be a PangoTextDescription object
        #setter function provided for convenience
        self.text_fontdesc = None
        
        #vertex: color of the highlight ring
        #edge: color of the highlight border
        self.sel_color = None
    
    def set_fontdesc(self, desc):
        '''Convert a textual font description into a PangoFontDescription object.'''
        #see http://www.pygtk.org/docs/pygtk/class-pangofontdescription.html for format
        self.text_fontdesc = Pango.FontDescription(desc)
