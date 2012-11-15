'''
   Copyright (c) 2012 Peter Andrews

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

from gi.repository import GooCanvas, Gdk, Gtk
from math import sqrt, atan, degrees

import util

def _adj_coords(edge):
    '''Adjust endpoint coordinates for node radii.'''
    
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
    
    return (startx, starty, endx, endy, dx, dy)

def paint(edge):
    '''Draw lobj, an AggLine, as a simple line with text labels along its length.'''
    startx, starty, endx, endy, dx, dy = _adj_coords(edge)
    
    #construct the points
    pts = util.mkpoints([(startx, starty), (endx, endy)])
    
    #get style data from edge stylesheet
    sheet = edge.stylesheet
    stroke = sheet.stroke_color
    text_color = sheet.text_color
    font = sheet.text_fontdesc
    
    #draw the line
    GooCanvas.CanvasPolyline(end_arrow=edge.end_arrow, start_arrow=edge.start_arrow, points=pts, parent=edge, arrow_length=9, arrow_tip_length=7, arrow_width=7, line_width=edge.width/2, stroke_color_rgba=stroke)
    
    #draw a label above the center of the line
    center = edge.get_xyr()
    text_color = edge.stylesheet.text_color
    font = edge.stylesheet.text_fontdesc
    #the label field is a dict of three labels, each a list of [weight,text]
    label = edge.label
    origin = edge.origin.label
    dest = edge.dest.label
    
    cx = center['x']
    cy = center['y']
    
    deg = degrees(atan(dy/dx))
    
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
    parts = []
    if label['to']: parts.append(' '.join((origin, label['to'][1], dest)))
    if label['from']: parts.append(' '.join((dest, label['from'][1], origin)))
    toptext = "; ".join(parts)
    
    bottext = 'Both '+label['bidir'][1] if label['bidir'] else '';
    
    toplbl = GooCanvas.CanvasText(parent=edge, text=toptext, alignment="center", fill_color_rgba=text_color, font_desc=font, anchor=GooCanvas.CanvasAnchorType.SOUTH, x=topx, y=topy)
    botlbl = GooCanvas.CanvasText(parent=edge, text=bottext, alignment="center", fill_color_rgba=text_color, font_desc=font, anchor=GooCanvas.CanvasAnchorType.NORTH, x=botx, y=boty)
    
    #rotate the label appropriately
    toplbl.rotate(deg, topx, topy)
    botlbl.rotate(deg, botx, boty)

def show_selected(edge):
    '''Draw a highlight outline around the edge.'''
    startx, starty, endx, endy, dx, dy = _adj_coords(edge)
    
    #construct the points
    pts = util.mkpoints([(startx, starty), (endx, endy)])
    sheet = edge.stylesheet
    stroke = sheet.sel_color
    width = edge.width/2 + sheet.sel_width*2
    
    arrow_len = 10*(edge.width/2)/width
    arrow_tip_len = 7*(edge.width/2)/width
    arrow_width = 9*(edge.width/2)/width
    
    #draw the line
    highlight = GooCanvas.CanvasPolyline(end_arrow=edge.end_arrow, start_arrow=edge.start_arrow, arrow_length=arrow_len, arrow_tip_length=arrow_tip_len, arrow_width=arrow_width, points=pts, parent=edge, line_width=width, stroke_color_rgba=stroke)
    highlight.lower(edge.get_child(0))
    
    return highlight
