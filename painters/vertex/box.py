from gi.repository import GooCanvas
from gi.repository import Gdk

def paint(parent, node):
    '''Draw node as a box surrounding its (centered) label.'''
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

def show_selected(vertex):
    '''Draw selection ring around node.'''
    coords = vertex.get_xyr()
    ring = GooCanvas.CanvasEllipse(parent=vertex.parent, radius_x=coords['radius'], radius_y=coords['radius'], center_x=coords['x'], center_y=coords['y'], fill_color_rgba=0x00000000, stroke_color_rgba=0x000000ff)
    return ring
