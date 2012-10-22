from gi.repository import GooCanvas
from gi.repository import Gdk
from math import sqrt

import util

def paint(parent, start, end, lobj):
    '''Draw lobj, an AggLine, as a simple line with text labels along its length.'''
    spos = start#self.vertices[start].get_xyr() #x, y, radius
    epos = end#self.vertices[end].get_xyr() #x, y, radius
            
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
    pts = util.mkpoints([(startx, starty), (endx, endy)])
    
    #draw the line
    GooCanvas.CanvasPolyline(end_arrow=lobj.end_arrow, start_arrow=lobj.start_arrow, points=pts, parent=parent, arrow_length=9, arrow_tip_length=7, arrow_width=7, line_width=lobj.width/2)
    #TODO add dots and text above/left of the line

def show_selected(parent, node, state):
    pass
