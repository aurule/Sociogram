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

from gi.repository import GooCanvas
from gi.repository import Gdk

def paint(vertex):
    '''Draw vertex as a box surrounding its (centered) label.'''
    #get style data from vertex stylesheet
    label = vertex.text
    stroke = vertex.stylesheet.stroke_color
    fill = vertex.stylesheet.fill_color
    text_color = vertex.stylesheet.text_color
    font = vertex.stylesheet.text_fontdesc
    
    box = GooCanvas.CanvasRect(parent=vertex, stroke_color_rgba=stroke, fill_color_rgba=fill)
    lbl = GooCanvas.CanvasText(parent=vertex, text=label, alignment="center", fill_color_rgba=text_color, font_desc=font)
    
    lbl_bounds = lbl.get_bounds()
    lw = lbl_bounds.x2 - lbl_bounds.x1
    lh = lbl_bounds.y2 - lbl_bounds.y1
    biggest = lw if lw > lh else lh
    
    lbl.set_properties(x=10+(biggest-lw)/2, y=10+(biggest-lh)/2)
    box.set_properties(width=biggest+20, height=biggest+20)
    
    props = {'width': biggest+20, 'height': biggest+20}
    return props

def show_selected(vertex):
    '''Draw selection ring around vertex.'''
    coords = vertex.get_xyr()
    stroke = vertex.stylesheet.sel_color
    ring = GooCanvas.CanvasEllipse(parent=vertex.parent, radius_x=coords['radius'], radius_y=coords['radius'], center_x=coords['x'], center_y=coords['y'], fill_color_rgba=0x00000000, stroke_color_rgba=stroke)
    ring.lower(vertex)
    
    return ring
