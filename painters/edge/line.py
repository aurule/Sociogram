from gi.repository import GooCanvas, Gdk, Gtk
from math import sqrt, atan, degrees

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
    
    #get style data from edge stylesheet
    sheet = edge.stylesheet
    stroke = edge.stylesheet.stroke_color
    text_color = edge.stylesheet.text_color
    font = edge.stylesheet.text_fontdesc
    
    #draw the line
    GooCanvas.CanvasPolyline(end_arrow=edge.end_arrow, start_arrow=edge.start_arrow, points=pts, parent=edge, arrow_length=9, arrow_tip_length=7, arrow_width=7, line_width=edge.width/2, stroke_color_rgba=stroke)
    
    #draw a label above the center of the line
    center = edge.get_xyr()
    text_color = edge.stylesheet.text_color
    font = edge.stylesheet.text_fontdesc
    #the label field is a dict of three labels, each a list of [weight,text]
    label = edge.label
    
    cx = center['x']
    cy = center['y']
    
    #first get the rotation
    dx = spos['x'] - epos['x']
    dy = spos['y'] - epos['y']
    deg = degrees(atan(dy/dx))
    
    #then find the offset
    mag = sqrt(dx*dx + dy*dy)
    dx = dx/mag
    dy = dy/mag
    
    #Pick which perpendicular based on dx to keep it "above" the line (bottoms
    #of letters always face the line).
    nx = -dy if dx < 0 else dy
    ny = dx if dx < 0 else -dx
    
    #multiply for distance from the line, and adj to eminate from the center coords
    topx = nx*3 + cx
    topy = ny*3 + cy
    
    botx = -nx*3 + cx
    boty = -ny*3 + cy
    
    #make the label
    tpart = '< '+label['to'][1] if label['to'] else '';
    fpart = label['from'][1]+' >' if label['from'] else '';
    toptext = tpart+"\t"+fpart
    bottext = '< '+label['bidir'][1]+' >' if label['bidir'] else '';
    
    toplbl = GooCanvas.CanvasText(parent=edge, text=toptext, alignment="center", fill_color_rgba=text_color, font_desc=font, anchor=GooCanvas.CanvasAnchorType.SOUTH, x=topx, y=topy)
    botlbl = GooCanvas.CanvasText(parent=edge, text=bottext, alignment="center", fill_color_rgba=text_color, font_desc=font, anchor=GooCanvas.CanvasAnchorType.NORTH, x=botx, y=boty)
    
    #rotate the label appropriately
    toplbl.rotate(deg, topx, topy)
    botlbl.rotate(deg, botx, boty)

def show_selected(vertex):
    pass
