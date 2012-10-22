from gi.repository import GooCanvas

def mkpoints(xyarr):
    '''Create a new Points object with coordinates from xyarr.'''
    pts = GooCanvas.CanvasPoints.new(len(xyarr))
    key = 0
    for x, y in xyarr:
        pts.set_point(key, x, y)
        key += 1
    return pts
