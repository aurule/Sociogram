import xml.etree.ElementTree as et

def sub_element(parent, name, data=None):
    name = str(name)
    e = et.SubElement(parent, name)
    if data != None:
        data = str(data)
        e.text = data
    return e
