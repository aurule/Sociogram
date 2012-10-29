from gi.repository import GooCanvas
from gi.repository import Gdk
from math import sqrt

import util

def paint(edge):
    '''Draw lobj, an AggLine, as a simple line with text labels along its length.'''
    
    spos = edge.origin.get_xyr() #x, y, radius
    epos = edge.dest.get_xyr() #x, y, radius
            
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
    sheet = edge.stylesheet
    stroke = edge.stylesheet.stroke_color
    text_color = edge.stylesheet.text_color
    font = edge.stylesheet.text_fontdesc
    
    GooCanvas.CanvasPolyline(end_arrow=edge.end_arrow, start_arrow=edge.start_arrow, points=pts, parent=edge, arrow_length=9, arrow_tip_length=7, arrow_width=7, line_width=edge.width/2, stroke_color_rgba=stroke)
    #TODO add dots and text above/left of the line

def show_selected(vertex):
    pass
