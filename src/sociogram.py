#!/usr/bin/env python2

#import system libraries
from __future__ import division
from gi.repository import Gtk, GooCanvas, Gdk
import networkx as nx
import xml.etree.ElementTree as et
from time import time
from os.path import basename

#import local libraries
import Errors
import Graph
import Drawing
from ETree import sub_element as sub

class Sociogram(object):
    def __init__(self):
        '''Set up internals and instantiate/fix up GUI using Gtk.Builder.'''
        self.version = "preview 1"
        self.G = Graph.Sociograph() # instantiate the graph for storage and positioning
        #placeholders for selecting objects
        self.selection = None
        self.seltype = None
        self.seldata = None
        self.highlight_dist = 1
        self.highlight = False
        self.savepath = None
        self.lastsave = time()
        self.dirty = False
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/sociogram.ui")

        #set default type for new objects
        self.builder.get_object("newtypesel").set_active(0)
        
        self.node_lbl_store = Gtk.ListStore(str)
        
        completions = []
        for t in range(5):
            x = Gtk.EntryCompletion()
            x.set_model(self.node_lbl_store)
            x.set_text_column(0)
            x.set_minimum_key_length(1)
            x.set_inline_completion(True)
            x.set_popup_single_match(False)
            completions.append(x)
        
        #populate from_combo, to_combo, attr_edit_name with liststore and renderer
        from_combo = self.builder.get_object("from_combo")
        from_combo.set_model(self.node_lbl_store)
        self.from_main = self.builder.get_object("from_combo_entry")
        self.from_main.set_completion(completions[0])
        
        to_combo = self.builder.get_object("to_combo")
        to_combo.set_model(self.node_lbl_store)
        self.to_main = self.builder.get_object("to_combo_entry")
        self.to_main.set_completion(completions[1])
        
        #populate from_combo_dlg and to_combo_dlg from the same model as above
        from_combo_dlg = self.builder.get_object("from_combo_dlg")
        from_combo_dlg.set_model(self.node_lbl_store)
        self.from_dlg = self.builder.get_object("from_combo_dlg_entry")
        self.from_dlg.set_completion(completions[2])
        
        to_combo_dlg = self.builder.get_object("to_combo_dlg")
        to_combo_dlg.set_model(self.node_lbl_store)
        self.to_dlg = self.builder.get_object("to_combo_dlg_entry")
        self.to_dlg.set_completion(completions[3])
        
        #add completion to toolbar node search field
        searchbar = self.builder.get_object("search_entry")
        searchbar.set_completion(completions[4])
        
        
        #connect attribute view with attribute list, create columns, and make it all sortable
        editname = Gtk.CellRendererText()
        editname.set_property("editable", True)
        editname.connect("edited", self.update_attrs, 0)
        editval = Gtk.CellRendererText()
        editval.set_property("editable", True)
        editval.connect("edited", self.update_attrs, 1)
        
        self.attr_store = Gtk.ListStore(str, str, bool, str)
        self.attr_store.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.attr_disp = self.builder.get_object("attrstree")
        self.attr_disp.set_rules_hint(True)
        self.attr_disp.set_model(self.attr_store)
        self.namecol = Gtk.TreeViewColumn("Name", editname, text=0)
        self.namecol.set_sort_column_id(0)
        self.namecol.set_expand(True)
        col2 = Gtk.TreeViewColumn("Value", editval, text=1)
        col2.set_sort_column_id(1)
        col2.set_expand(True)
        togglecell = Gtk.CellRendererToggle()
        togglecell.connect("toggled", self.update_attrs, None, 2)
        col3 = Gtk.TreeViewColumn("Visible", togglecell, active=2)
        col3.set_sort_column_id(2)
        self.attr_disp.append_column(self.namecol)
        self.attr_disp.append_column(col2)
        self.attr_disp.append_column(col3)

        
        self.rel_store = Gtk.ListStore(str, str)
        rel_combo = self.builder.get_object("rel_combo")
        rel_combo.set_model(self.rel_store)
        cell = Gtk.CellRendererText()
        rel_combo.pack_start(cell, True)
        rel_combo.add_attribute(cell, 'text', 0)

        #create canvas object and add to the scroll window
        #VERY IMPORTANT. using the normal window.add() call fails, but setting the parent like this makes everything fine
        self.canvas = Drawing.Canvas(parent=self.builder.get_object("canvas_scroll"), has_tooltip=True)
        #attach callbacks
        self.canvas.node_callback = self.node_clicked
        self.canvas.line_callback = self.line_clicked
        self.canvas.key_handler = self.canvas_key_handler
        self.canvas.connect("button-press-event", self.canvas_clicked)
        self.canvas.connect("scroll-event", self.scroll_handler)
        self.canvas.mouseover_callback = self.update_pointer
        
        #TODO once the prefs dialog is implemented, this should be moved to a separate default style update function
        #populate our default styling
        sheet = self.canvas.edge_default_stylesheet
        sheet.stroke_color = 0x000000ff
        sheet.set_fontdesc('sans normal 11')
        sheet.sel_color = 0xff0000ff
        sheet.sel_width = 1
        sheet.text_color = 0x000000ff
        sheet.set_fontdesc('sans normal 11')
        
        sheet = self.canvas.vertex_default_stylesheet
        sheet.fill_color = 0xffff00ff
        sheet.stroke_color = 0x000000ff
        sheet.sel_color = 0x000000ff
        sheet.text_color = 0x000000ff
        sheet.set_fontdesc('sans normal 11')
        
        
        # Declare references for all the dialogs and popups we need. We do keep
        # the builder around, so this is mostly for code readability.
        # TODO instantiate reference to everything we care about, so that the
        #   expensive builder can be nixed.
        self.not_implemented_box = self.builder.get_object("not_implemented_err")
        self.about_dlg = self.builder.get_object("about_dlg")
        self.add_item_dlg = self.builder.get_object("add_item_dlg")
        self.dup_err_dlg = self.builder.get_object("dup_err_dlg")
        self.export_dlg = self.builder.get_object("export_dlg")
        self.node_style_dlg = self.builder.get_object("node_style_popup")
        self.paste_warn_dlg = self.builder.get_object("paste_warning_dlg")
        self.prefs_dlg = self.builder.get_object("prefs_dlg")
        self.rel_style_dlg = self.builder.get_object("rel_style_popup")
        self.style_dlg = self.builder.get_object("style_dlg")
        self.blank_err_dlg = self.builder.get_object("blank_err_dlg")
        self.find_dlg = self.builder.get_object("find_dlg")
        self.save_dlg = self.builder.get_object("save_dlg")
        self.open_dlg = self.builder.get_object("open_dlg")
        self.save_warning = self.builder.get_object("savewarn_dlg")
        self.save_close_warning = self.builder.get_object("savewarn_close_dlg")
        
        self.hscroll = self.builder.get_object("horiz_scroll_adj")
        self.vscroll = self.builder.get_object("vertical_scroll_adj")
        self.scale_adj = self.builder.get_object("scale_adj")
        
        #set our version string
        self.builder.get_object("about_dlg").set_version(self.version)
        
        #initialize our fullscreen tracker
        self.fullscreen = False
        
        #show the main window
        self.window = self.builder.get_object("sociogram_main")
        self.window.show_all()
        
        # Attach handlers to signals described in the .ui file.
        # TODO once functionality is finalized, remove redundant signals
        handlers_main = {
            "app.quit": self.do_quit,
            "app.newfile": self.make_new,
            "app.openfile": self.openfile,
            "app.savefile": self.save,
            "app.saveas": self.save_new,
            "app.do_export": self.show_dev_error,
            "app.do_find": self.show_dev_error,
            "app.help": self.show_dev_error,
            "app.undo": self.show_dev_error,
            "app.redo": self.show_dev_error,
            "app.search": self.find_node,
            "app.reset_search_icon": self.set_search_icon,
            "app.toggle_widget": self.toggle_widget,
            "app.toggle_fs": self.toggle_fullscreen,
            "app.track_fs": self.track_fullscreen,
            "app.hide_add_controls": self.hide_addbox_controls,
            "app.deep_find": self.show_dev_error,
            "app.show_dlg": self.show_dlg,
            "app.show_add": self.show_add,
            "app.dlg_sanity": self.check_new_dlg_sanity,
            "app.set_highlight_radius": self.set_highlight_dist,
            "app.check_name": self.check_label,
            "app.canvas_keys": self.canvas_key_handler,
            "app.zoom_in": self.zoom_in_step,
            "app.zoom_out": self.zoom_out_step,
            "app.zoom_reset": self.zoom_reset,
            "app.zoom_fit": self.zoom_fit,
            "app.cancel_newname": self.cancel_name_edit,
            "app.zoom_changed": self.update_zoom,
            "app.check_endpoint": self.check_endpoint,
            "app.cancel_endpoint": self.cancel_endpoint,
            "app.set_selrel": self.pick_rel,
            "data.add": self.show_dev_error,
            "data.copyattrs": self.show_dev_error,
            "data.pasteattrs": self.do_paste,
            "data.delsel": self.delete_selection,
            "data.update_lbl": self.update_lbl,
            "data.update_origin": self.update_origin,
            "data.update_dest": self.update_dest,
            "data.update_weight": self.update_weight,
            "data.update_bidir": self.update_bidir,
            "data.newattr": self.add_attr,
            "data.delattr": self.del_attr,
            "data.updateattr": self.show_dev_error,
            "graph.toggle_highlight": self.toggle_highlight,
            "graph.refresh": self.redraw
        }
        self.builder.connect_signals(handlers_main)
        
        #disable sidebar programmatically, so that labels will be drawn correctly
        self.builder.get_object("sidebarbox").set_sensitive(False)
    
    def nothing(self, a=None, b=None, c=None):
        print 'nothing'
    
    def do_quit(self, widget=None, data=None):
        '''Handle quitting.'''
        self.confirm_discard(closing=True)
        
        Gtk.main_quit()
    
    def set_dirty(self, val):
        '''Mark the current file as "dirty", indicating unsaved changes.'''
        if val == self.dirty: return
        
        self.dirty = val
        if not self.dirty:
            self.lastsave = time()
        
        #TODO update UI indicator
    
    def confirm_discard(self, closing=False):
        '''Prompt the user to save unfinished changes, if necessary.
        Returns True if it's OK to continue, and False if not.'''
        if self.dirty:
            #warn about closing current document
            dlg = self.save_close_warning if closing else self.save_warning
            if self.savepath == None:
                dlg.set_markup(_("Save your changes before closing?"))
            else:
                dlg.set_markup(_("Save your changes to %s before closing?") %basename(self.savepath))
            
            period = int((time() - self.lastsave)/60)
            dlg.format_secondary_text(_("If you don't save, changes from the last %s minutes will be lost.") %period)
            response = dlg.run()
            dlg.hide()

            if response == 5:
                self.save() #save it and continue
            elif response != 2:
                return False #cancel and prevent any further action
            
        #either we've saved or been told not to, so clear the calling function to go ahead
        return True
    
    def make_new(self, widget=None, data=None):
        '''Event handler and standalone. Wipe the current data and load defaults.'''
        if not self.confirm_discard(): return
        
        self.clear_select()
        self.rel_store.clear()
        self.attr_store.clear()
        self.node_lbl_store.clear()
        
        self.zoom_reset()
        self.G.clear()
        
        self.redraw()
    
    def openfile(self, widget=None, data=None):
        '''Event handler and standalone. Pick a file and load from it.'''
        if not self.confirm_discard(): return
        
        open_dlg = self.builder.get_object("open_dlg")
        if self.savepath != None:
            open_dlg.set_filename(self.savepath)
        
        response = open_dlg.run()
        open_dlg.hide()
        if response:
            #clear existing data
            self.make_new()
            
            self.savepath = open_dlg.get_filename()
            tree = et.parse(self.savepath)
            root = tree.getroot()
            
            if self.version != root.attrib['version']:
                #TODO warn that we're opening a version other than our own
                pass
            
            #import document-specific settings
            settings = root.find('settings')
            scale = settings.find('scale').text
            self.scale_adj.set_value(float(scale))
            
            #import document data
            data = root.find('data')
            for node in data.iter('node'):
                #add node
                uid = node.find('uid').text
                label = node.find('label').text
                
                #construct attributes list
                attrs = []
                for a in node.iter('attr'):
                    name = a.find('name').text
                    val = a.find('value').text
                    vis = True if a.find('visible').text == "True" else False
                    u = a.find('uid').text
                    attrs.append((name, val, vis, u))
                
                self._add_node(label, uid=uid, attrs=attrs)
            
            for edge in data.iter('rel'):
                #add edge
                uid = edge.find('uid').text
                label = edge.find('label').text
                
                #construct attributes list
                attrs = []
                for a in edge.iter('attr'):
                    name = a.find('name').text
                    val = a.find('value').text
                    vis = True if a.find('visible').text == "True" else False
                    u = a.find('uid').text
                    attrs.append((name, val, vis, u))
                
                origin = edge.find('origin').text
                dest = edge.find('dest').text
                mutual = True if edge.find('mutual').text == "True" else False
                weight = int(float(edge.find('weight').text))
                
                self._add_rel(label, origin, dest, weight, mutual, attrs=attrs, uid=uid)
            
            self.redraw()
            #TODO send "opened" message through status bar
    
    def save(self, widget=None, data=None):
        '''Event handler and standalone. Save to known path.'''
        if self.savepath == None:
            self.save_new()
            return
        
        if not self.dirty: return
        
        #construct XML
        #create base element and record program version
        root = et.Element('sociogram', attrib={'version':self.version})
        
        #create settings
        settings = sub(root, 'settings')
        sub(settings, 'scale', self.scale_adj.get_value())
        
        #create data holder
        data = sub(root, 'data')
        #create nodes
        for node in self.G.nodes_iter():
            n = self.G.node[node]['node']
            node = sub(data, 'node')
            #store uid, label, attributes
            uid = sub(node, 'uid', n.uid)
            label = sub(node, 'label', n.label)
            for aid, aval in n.attributes.iteritems():
                attr = sub(node, 'attr')
                sub(attr, 'uid', aid)
                sub(attr, 'name', aval['name'])
                sub(attr, 'value', aval['value'])
                sub(attr, 'visible', aval['visible'])
        
        for f, t in self.G.edges_iter():
            for e in self.G[f][t]['rels']:
                edge = sub(data, 'rel')
                #store uid, label attributes, origin, destination, weight, mutual
                sub(edge, 'uid', e.uid)
                sub(edge, 'label', e.label)
                for aid, aval in e.attributes.iteritems():
                    attr = sub(edge, 'attr')
                    sub(attr, 'uid', aid)
                    sub(attr, 'name', aval['name'])
                    sub(attr, 'value', aval['value'])
                    sub(attr, 'visible', aval['visible'])
                sub(edge, 'origin', e.from_node)
                sub(edge, 'dest', e.to_node)
                sub(edge, 'weight', e.weight)
                sub(edge, 'mutual', e.mutual)
        
        #write xml to self.savepath
        tree = et.ElementTree(element=root)
        tree.write(self.savepath, encoding="UTF-8")
        
        self.set_dirty(False)
        #TODO send "saved" message through status bar
    
    def save_new(self, widget=None, data=None):
        '''Event handler and standalone. Pick save location, then save.'''
        save_dlg = self.builder.get_object("save_dlg") 
        if self.savepath != None:
            save_dlg.set_filename(self.savepath)
        else:
            save_dlg.set_current_name("sociogram.xml")
        
        response = save_dlg.run()
        save_dlg.hide()
        uri = save_dlg.get_filename()
        
        if uri != None:
            self.savepath = uri
            self.set_dirty(True)
            self.save()
    
    def update_pointer(self, widget, data=None, extra=None, hand=None):
        '''Event handler to pick the pointer used on the graph.'''
        if hand:
            cursor = Gdk.Cursor(Gdk.CursorType.HAND1)
        else:
            cursor = None
        rwin = self.builder.get_object("canvas_eventbox").get_window()
        rwin.set_cursor(cursor)
    
    def set_highlight_dist(self, widget, data=None):
        '''Event handler. Update our internal highlight distance.'''
        self.highlight_dist = widget.get_value()
        self._do_highlight()
    
    def toggle_highlight(self, widget, data=None):
        '''Event handler. Turn highlight mode on or off.'''
        self.highlight = widget.get_active()
        self.builder.get_object("highlight_btn").set_active(self.highlight)
        self.builder.get_object("menu_highlight").set_active(self.highlight)
        self._do_highlight()
    
    def _do_highlight(self):
        '''Set params for the special "highlight" draw mode and draw it.'''
        if not (self.highlight and self.seltype == 'node'):
            return
        
        #TODO
        #   iterate out from the selected node
        #   mark/store those nodes and paths
        #   trigger a special canvas.freshen operation
    
    def add_attr(self, widget, data=None):
        '''Event handler. Adds an attribute to the current selection.'''
        if self.selection == None:
            return
        
        #add to underlying Node object
        uid = self.seldata.add_attr(("attribute", "value", False))
        #add to the store
        newrow = self.attr_store.append(("attribute", "value", False, uid))
        path = self.attr_store.get_path(newrow)
        #start editing right away
        self.attr_disp.set_cursor(path, self.namecol, True)
        
        self.set_dirty(True)
    
    def next_field(self, widget, data=None):
        pass
    
    def del_attr(self, widget, data=None):
        '''Event handler. Removes the currently highlighted attribute from the current selection.'''
        
        tree_selection = self.attr_disp.get_selection()
        if self.selection == None or tree_selection == None:
            return
        
        selrow = tree_selection.get_selected()[1]
        auid = self.attr_store.get_value(selrow, 3)
        
        #remove from underlying Node object
        self.seldata.del_attr(auid)
        #now from the store
        self.attr_store.remove(selrow)
        
        self.set_dirty(True)
    
    def update_attrs(self, widget, path=None, text=None, col=None):
        '''Event handler. Change name or value of currently selected attribute.'''
        
        tree_selection = self.attr_disp.get_selection()
        if self.selection == None or tree_selection == None:
            return
            
        #get the attribute ID
        #selrow = tree_selection.get_selected()[1]
        auid = self.attr_store[path][3]
        
        #update attribute
        attr = self.seldata.attributes[auid]
        if col==0:
            attr['name'] = text
        elif col==1:
            attr['value'] = text
        elif col==2:
            attr['visible'] = not attr['visible']
        
        #update store
        #once we do this, the original path is no longer valid
        if text != None:
            self.attr_store[path][col] = text
        else:
            self.attr_store[path][col] = attr['visible']
        
        #refresh only, no need for a complete redraw
        self.refresh(self.seldata)
        self.set_dirty(True)
    
    def show_add(self, widget, data=None):
        '''Show Add Object dialog after resetting field defaults and ensuring sane Relationship availability.'''
        #show the thing
        self.builder.get_object("new_type_box").set_sensitive(self.G.order() > 1) #disallow Relationships unless we have enough nodes
        self.builder.get_object("name_entry_dlg").grab_focus() #focus on the label field
        response = self.add_item_dlg.run()
        self.add_item_dlg.hide()
        
        #only add things if the OK button was pressed
        if response == 4:
            #add a new object
            obj_type = self.builder.get_object("newtypesel").get_active_text()
            
            lbl = self.builder.get_object("name_entry_dlg").get_text()
            
            #get the rest of our data
            paste = self.builder.get_object("use_copied_attrs").get_active()
            if "Rel" in obj_type:
                #grab extra data fields
                fnode = self.from_dlg.get_text()
                tnode = self.to_dlg.get_text()
                weight = self.builder.get_object("weight_spin_dlg").get_value()
                bidir = self.builder.get_object("bidir_new").get_active()
                rel, new_edge = self._add_rel(lbl, fnode, tnode, weight, bidir, paste)
                if not new_edge:
                    #TODO just do a refresh if possible
                    pass
            else:
                node = self._add_node(lbl, paste)
            
            self.set_dirty(True)
            
            self.redraw()
            if "Rel" in obj_type:
                #get proper edge
                obj = self.canvas.get_edge(fnode, tnode)
            else:
                #get proper node
                obj = self.canvas.get_vertex(lbl)
            self.set_selection(obj)
        
        #clear the dialog's values
        self.builder.get_object("newtypesel").set_active(0)
        self.builder.get_object("name_entry_dlg").set_text('')
        self.from_dlg.set_text('')
        self.to_dlg.set_text('')
        self.builder.get_object("weight_spin_dlg").set_value(5)
        self.builder.get_object("bidir_new").set_active(False)
        self.builder.get_object("use_copied_attrs").set_active(False)
    
    def _add_node(self, lbl, paste=False, attrs=None, uid=None):
        '''Internal function. Add a node and handle bookkeeping.'''
        #make sure the node doesn't already exist
        if lbl in self.G: 
            self.show_dup_node_error()
            return
        
        #create object and update data
        node = Graph.Node(lbl, attrs=attrs, uid=uid)
        self.G.add_node(lbl, {"node": node}) #add to graph
        self.node_lbl_store.append([lbl]) #update name list for the dropdowns
        
        if paste:
            self._paste_attrs(node)
    
    def _add_rel(self, lbl, fname, tname, weight, bidir, paste=False, attrs=None, uid=None):
        '''Internal function. Add a relationship and handle bookkeeping.'''
        #make sure both nodes exist
        if fname not in self.G:
            raise Errors.MissingNode("Node %s not in graph." % fname)
        if tname not in self.G:
            raise Errors.MissingNode("Node %s not in graph." % tname)
        
        #create relationship object
        rel = Graph.Relationship(lbl, fname, tname, weight, bidir, attrs, uid)
        
        new_edge = self.G.add_rel(rel)
        
        if paste:
            self._paste_attrs(rel)
        
        return (rel, new_edge)
    
    def hide_addbox_controls(self, widget, data=None):
        '''Event handler. Toggles visibility of Relationship-specific fields in the Add Object dialog based on selected Type.'''
        obj_type = widget.get_active_text()
        vis = "Rel" in obj_type
        for wname in ["frombox_dlg", "tobox_dlg", "weightbox_dlg", "bidir_new"]:
            self.builder.get_object(wname).set_visible(vis)
        self.builder.get_object("name_entry_dlg").grab_focus()
    
    def check_new_dlg_sanity(self, widget, data=None):
        '''Event handler. Disable Add Object dialog's Add button unless inputs make sense.'''
        haslbl = self.builder.get_object("name_entry_dlg").get_text() != ""
        ftext = self.from_dlg.get_text()
        ttext = self.to_dlg.get_text()
        
        hasnodes = True
        diffnodes = True
        nodes_exist = True
        obj_type = self.builder.get_object("newtypesel").get_active_text()
        if "Rel" in obj_type:
            hasnodes = ftext != '' and ttext != ''
            diffnodes = ftext != ttext
            nodes_exist = ftext in self.G and ttext in self.G
        
        sense = haslbl and hasnodes and diffnodes and nodes_exist        
        
        self.builder.get_object("new_ok").set_sensitive(sense)
    
    # Picks the appropriate object to paste into, then passes off to _paste_attrs.
    def do_paste(self, widget, data=None):
        '''Event handler. Trigger paste operation for selected item.'''
        if self.selection == None: return
        
        self._paste_attrs(self.selection)
        
        self.set_dirty(True)
    
    # Internal function to overwrite target object's attributes with those from
    # the clipboard.
    def _paste_attrs(self, obj):
        '''Paste copied attributes into obj, overwriting if necessary.'''
        #TODO paste
        #silently fail if no paste buffer
        self.show_dev_error()
    
    def center_on(self, obj):
        '''Center the graph on a specific drawn object.'''
        xyr = obj.get_xyr()
        x, y = self.canvas.convert_from_item_space(obj.parent, xyr['x'], xyr['y'])
        
        #get the visible window dimensions
        vis_w = self.hscroll.get_page_size()
        vis_h = self.vscroll.get_page_size()
        corner_x = x - vis_w/2
        corner_y = y - vis_h/2
        
        self.canvas.scroll_to(corner_x, corner_y)
    
    # Sees if a given node exists, and focuses on it if so.
    # Slightly different definition so that data is big enough to accept random
    # data from clicking the search icon.
    def find_node(self, widget, *data):
        '''Event handler. Search for the node whose label matches widget input.'''
        node = widget.get_text()
        if node not in self.G:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_NO)
            widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("No such node"))
            widget.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, False)
        else:
            #select node
            vertex = self.canvas.get_vertex(node)
            self.set_selection(vertex)
            self.center_on(vertex)
        widget.select_region(0, widget.get_text_length())
    
    def set_search_icon(self, widget, data=None):
        '''Event handler. Resets search box icon when user types.'''
        widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_FIND)
        widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("Search"))
        widget.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)
    
    def set_selection(self, selobj, obj=None, event=None):
        '''Event handler and standalone. Mark selobj as selected and update ui.'''
        #clear the old selection
        self.clear_select()
        
        if selobj == None:
            return
        
        self.selection = selobj
        self.seltype = selobj.type
        self.selection.set_selected(True)
        
        #grab data and update UI
        if self.seltype == 'node':
            self.seldata = selobj.node
            self.activate_node_controls()
        elif self.seltype == 'edge':
            #activate all edit controls
            self.activate_rel_controls()
            
            #automatically select the edge's most heavily weighted relationship
            self.seldata = selobj.get_heaviest()
            
            #populate self.rel_store from the edge
            for rel in self.selection.rels:
                self.rel_store.append((str(rel), str(rel.uid)))
            self.builder.get_object("rel_combo").set_active(0)
        
        self._refresh_edit_controls()
        self.builder.get_object("canvas_eventbox").grab_focus() #set keyboard focus
    
    def pick_rel(self, widget=None, data=None, relnum=None):
        '''Event handler. Select a specific relationship from an edge.'''
        if self.selection == None: return
        
        relid = widget.get_active() if widget != None else relnum
        rel = self.selection.rels[relid]
        if rel == self.seldata: return
        
        self.seldata = rel
        
        self._refresh_edit_controls()
    
    def _refresh_edit_controls(self):
        '''Update contents of edit box controls.'''
        if self.seltype == 'edge':
            #populate edit controls for that relationship
            weight = self.seldata.weight
            bidir = self.seldata.mutual
            tlbl = self.seldata.to_node
            flbl = self.seldata.from_node
            
            self.to_main.set_text(tlbl)
            self.from_main.set_text(flbl)
            self.builder.get_object("weight_spin").set_value(weight)
            self.builder.get_object("bidir").set_active(bidir)
    
        #populate common fields
        self.builder.get_object("name_entry").set_text(self.seldata.label)
        
        #populate self.attr_store from selected graph object's attributes
        self.attr_store.clear()
        for uid in self.seldata.attributes.iterkeys():
            attr = self.seldata.attributes[uid]
            self.attr_store.append((attr['name'], attr['value'], attr['visible'], uid))
    
    def clear_select(self, canvas=None, data=None):
        '''Event handler and standalone. Deselect object(s).'''
        if self.selection != None:
            self.selection.set_selected(False)        
            self.selection = None
            self.seltype = None
            self.seldata = None
            self.attr_store.clear()
            self.rel_store.clear()
        
        self.disable_all_controls()
    
    def delete_selection(self, widget=None, data=None):
        '''Event handler and standalone. Delete selected object.'''
        if self.selection == None:
            return
        
        if self.seltype == 'node':
            self.G.remove_node(self.seldata.label)
            self.selection.remove()
            self.clear_select()
        else:
            killed_edge = self.G.remove_rel(self.seldata)
            if not killed_edge:
                #in this case, we only need to refresh the graph, not redraw it
                self.refresh(self.seldata)
            else:
                self.selection.remove()
                self.clear_select()
                self.redraw()
        
        self.set_dirty(True)
    
    def activate_node_controls(self):
        '''Make only node-compatable selection-specific controls sensitive to input.'''
        #enable the enter sidebar and related controls
        self.activate_all_controls()
        
        #now explicitly disable relationship-only controls
        self.builder.get_object("relbox").set_sensitive(False)
        self.builder.get_object("frombox").set_sensitive(False)
        self.builder.get_object("tobox").set_sensitive(False)
        self.builder.get_object("weightbox").set_sensitive(False)
    
    def activate_rel_controls(self):
        '''Show relationship controls.'''
        self.activate_all_controls()
    
    def activate_all_controls(self):
        '''Make all selection-specific controls sensitive to input.'''
        self.builder.get_object("sidebarbox").set_sensitive(True)
        self.builder.get_object("add_attr").set_sensitive(True)
        self.builder.get_object("remove_attr").set_sensitive(True)
        
        #explicitly enable relationship-only controls, since they may have been previously explicitly disabled
        self.builder.get_object("relbox").set_sensitive(True)
        self.builder.get_object("frombox").set_sensitive(True)
        self.builder.get_object("tobox").set_sensitive(True)
        self.builder.get_object("weightbox").set_sensitive(True)
        
        #also enable selection-specific buttons and menu items
        self.builder.get_object("copy").set_sensitive(True)
        self.builder.get_object("paste").set_sensitive(True)
        self.builder.get_object("del").set_sensitive(True)
        self.builder.get_object("menu_copy").set_sensitive(True)
        self.builder.get_object("menu_paste").set_sensitive(True)
        self.builder.get_object("menu_delete").set_sensitive(True)
    
    def disable_all_controls(self):
        '''Make all selection-specific controls unresponsive to input and clear their values.'''
        self.builder.get_object("sidebarbox").set_sensitive(False)
        
        #clear values
        self.builder.get_object("name_entry").set_text('')       
        self.from_main.set_text('')
        self.to_main.set_text('')
        self.builder.get_object("weight_spin").set_value(5)
        
        #explicitly disable
        self.builder.get_object("frombox").set_sensitive(False)
        self.builder.get_object("tobox").set_sensitive(False)
        self.builder.get_object("weightbox").set_sensitive(False)
        self.builder.get_object("add_attr").set_sensitive(False)
        self.builder.get_object("remove_attr").set_sensitive(False)
        
        #disable buttons and menu items
        self.builder.get_object("copy").set_sensitive(False)
        self.builder.get_object("paste").set_sensitive(False)
        self.builder.get_object("del").set_sensitive(False)
        self.builder.get_object("menu_copy").set_sensitive(False)
        self.builder.get_object("menu_paste").set_sensitive(False)
        self.builder.get_object("menu_delete").set_sensitive(False)
    
    def node_clicked(self, selobj, obj=None, event=None):
        '''Event handler. Select and otherwise perform UI actions on node click.'''
        self.set_selection(selobj)
        btn = event.get_button()
        
        #TODO handle the right-click menu
        if btn[1] == 3L:
            self.show_dev_error()
            #use menu.popup function
    
    def line_clicked(self, selobj, obj=None, event=None):
        '''Event handler. Draw clicked edge as "selected".'''
        self.set_selection(selobj)
        btn = event.get_button()
        
        #TODO handle the right-click menu
        if btn[1] == 3L:
            self.show_dev_error()
            #use menu.popup function
    
    def canvas_clicked(self, canvas, obj=None, event=None):
        '''Event handler. Set keyboard focus and clear selection on canvas click.'''
        self.clear_select()
        self.builder.get_object("canvas_eventbox").grab_focus() #set keyboard focus
    
    def canvas_key_handler(self, widget, event=None):
        '''Event handler. Take actions based on keyboard input while a graph object is selected.'''
        
        kvn = Gdk.keyval_name(event.keyval)
        if kvn == '1':
            self.zoom_reset()
            return True
        elif kvn == 'plus':
            self.zoom_in_step()
            return True
        elif kvn == 'minus':
            self.zoom_out_step()
            return True
        elif kvn == 'Delete':
            self.delete_selection()
            return True
        elif kvn == 'Escape':
            self.clear_select()
            return True
        elif kvn == 'Right' or kvn == 'Left':
            val = self.hscroll.get_value()
            adj = self.hscroll.get_step_increment()
            if kvn == 'Right':
                self.hscroll.set_value(val+adj)
            else:
                self.hscroll.set_value(val-adj)
            return True
        elif kvn == 'Up' or kvn == 'Down':
            val = self.vscroll.get_value()
            adj = self.vscroll.get_step_increment()
            if kvn == 'Down':
                self.vscroll.set_value(val+adj)
            else:
                self.vscroll.set_value(val-adj)
            return True
    
    def scroll_handler(self, widget, event=None):
        '''Event handler. Change scroll action based on various contexts.'''
        #TODO get masks from prefs
        horiz_mask = Gdk.ModifierType.SHIFT_MASK
        zoom_mask = Gdk.ModifierType.CONTROL_MASK
        
        if event.state & horiz_mask:
            val = self.hscroll.get_value() #minus step increment, capped at zero
            adj = self.hscroll.get_step_increment()
            if event.direction == Gdk.ScrollDirection.UP:
                #scroll left
                self.hscroll.set_value(val-adj)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                #scroll right
                self.hscroll.set_value(val+adj)
            
            return True
        elif event.state & zoom_mask:
            if event.direction == Gdk.ScrollDirection.UP:
                self.zoom_in_step()
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.zoom_out_step()
            
            return True
        
        #unless we handled it, let the event flow along
        return False
    
    def update_zoom(self, widget, data=None):
        '''Event handler. Set scale to current adjustment value.'''
        val = self.scale_adj.get_value()
        self.canvas.set_scale(val / 100)
    
    def zoom_in_step(self, widget=None, data=None):
        '''Event handler. Enlarge scale by 20%.'''
        val = self.scale_adj.get_value()
        self.scale_adj.set_value(val + 20)
    
    def zoom_out_step(self, widget=None, data=None):
        '''Event handler. Shrink scale by 20%.'''
        val = self.scale_adj.get_value()
        self.scale_adj.set_value(val - 20)
    
    def zoom_reset(self, widget=None, data=None):
        '''Event handler. Set scale to 1.'''
        self.scale_adj.set_value(100)
    
    def zoom_fit(self, widget=None, data=None):
        '''Event handler and standalone. Calculate optimal scale value to show entire area at once.'''
        #get the visible window dimensions
        vis_w = self.hscroll.get_page_size()
        vis_h = self.vscroll.get_page_size()
        
        #add padding to the graph width and height to account for invisible spacing rings
        bounds = self.canvas.get_bounds()
        graph_w = bounds.x2 - bounds.x1 + 20
        graph_h = bounds.y2 - bounds.y1 + 20
        
        if graph_w == 0 or graph_h == 0:
            return
        
        xscale = vis_h / graph_h
        yscale = vis_w / graph_w
        
        #use the smaller of the two scales so we fit as much as possible
        scale = min(xscale, yscale) * 100
        
        self.scale_adj.set_value(scale)
    
    def check_label(self, widget, data=None):
        '''Event handler. Warn if edited label is already used.'''
        
        if widget == None or self.seltype != 'node':
            return
        
        newlbl = widget.get_text()
        if newlbl != self.seldata.label and newlbl in self.G:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_DIALOG_ERROR)
            widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("Label already used"))
            widget.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, False)
        else:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, None)
    
    def cancel_name_edit(self, widget, data=None):
        '''Event handler. Reset name field if Esc key pressed.'''
        kvn = Gdk.keyval_name(data.keyval)
        if kvn == 'Escape':
            widget.set_text(self.seldata.label)
    
    def update_lbl(self, widget, data=None):
        '''Event handler. Update selection's label and redraw it.'''
        if self.selection == None:
            return
        
        newlbl = widget.get_text()
        oldlbl = self.seldata.label
        if oldlbl == newlbl:
            return
        
        #reset field if it was submitted blank
        if newlbl == "":
            widget.set_text(oldlbl)
            return
        
        if self.seltype == 'node':
            #change the internal object's label
            self.seldata.label = newlbl
            
            #remove old label from the liststore and add the new one
            for row in self.node_lbl_store:
                if row[0] == oldlbl:
                    self.node_lbl_store.remove(row.iter)
                    break
            self.node_lbl_store.append([newlbl])
            
            #update internal relationship objects' to and from node labels
            for n in self.G[oldlbl]:
                for rel in self.G[oldlbl][n]['rels']:
                    if rel.from_node == oldlbl: rel.from_node = newlbl
                    if rel.to_node == oldlbl: rel.to_node = newlbl
            
            #change the graph node's key
            nx.relabel_nodes(self.G, {oldlbl:newlbl}, False)
        else:
            self.seldata.label = newlbl
            tlbl = self.seldata.to_node
            flbl = self.seldata.from_node
        
        self.refresh(self.seldata, oldlbl)
        self.set_dirty(True)
    
    def check_endpoint(self, widget, data=None):
        '''Event handler. Warn if desired endpoint does not exist.'''
        
        if widget == None or self.seltype != 'edge':
            return
        
        newlbl = widget.get_text()
        if newlbl not in self.G:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_DIALOG_ERROR)
            widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("No such node"))
            widget.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, False)
        else:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, None)
    
    def cancel_endpoint(self, widget, data=None):
        '''Event handler. Reset name field if Esc key pressed.'''
        kvn = Gdk.keyval_name(data.keyval)
        if kvn == 'Escape':
            widget.set_text(self.seldata.from_node)
    
    def update_origin(self, widget, data=None):
        '''Event handler. Update selected relationship's origin.'''
        if self.selection == None:
            return
        
        new_origin = widget.get_text()
        if new_origin == self.seldata.from_node:
            return
        
        #reset field if it was submitted blank
        if new_origin == "":
            widget.set_text(self.seldata.from_node)
            return
        
        #if our new origin is our old destination, swap the two
        if new_origin == self.seldata.to_node:
            self.G.move_rel(self.seldata, origin=new_origin, dest=self.seldata.from_node)
            #now that it's been updated, we can just assign the real to_node value
            self.to_main.set_text(self.seldata.to_node)
            #just refresh in this case
            self.refresh(self.seldata)
        else:
            #otherwise, change the origin only
            self.G.move_rel(self.seldata, origin=new_origin)
            self.redraw()
        self.set_dirty(True)
    
    def update_dest(self, widget, data=None):
        '''Event handler. Update selected relationship's destination.'''
        if self.selection == None:
            return
        
        new_dest = widget.get_text()
        if new_dest == self.seldata.to_node:
            return
        
        #reset field if it was submitted blank
        if new_dest == "":
            widget.set_text(self.seldata.to_node)
            return
        
        #if our new origin is our old destination, swap the two
        if new_dest == self.seldata.from_node:
            self.G.move_rel(self.seldata, origin=self.seldata.to_node, dest=new_dest)
            #now that it's been updated, we can just assign the real to_node value
            self.from_main.set_text(self.seldata.from_node)
            #just refresh in this case
            self.refresh(self.seldata)
        else:
            #otherwise, change the origin only
            self.G.move_rel(self.seldata, dest=new_dest)
            self.redraw()
        
        self.set_dirty(True)
    
    def update_weight(self, widget, data=None):
        '''Event handler. Update selected relationship's weight and redraw it.'''
        if self.selection == None: return
        
        oldw = self.seldata.weight
        neww = widget.get_value()
        
        if oldw == neww: return
        
        self.seldata.weight = neww
        #refresh instead of fully redrawing
        self.refresh(self.seldata)
        self.set_dirty(True)
    
    def update_bidir(self, widget, data=None):
        '''Event handler. Update selected relationship's bidir property and redraw it.'''
        if self.selection == None: return
        
        oldb = self.seldata.weight
        newb = widget.get_active()
        
        if oldb == newb: return
        
        self.seldata.mutual = newb
        #refresh instead of fully redrawing
        self.refresh(self.seldata)
        self.set_dirty(True)
    
    def toggle_widget(self, widget, data=None):
        '''Event handler and standalone. Toggle passed widget.'''
        # The widget arg is populated correctly in Glade using the Custom Data
        # field as the target, and marking the Switch attribute.
        widget.set_visible(not widget.get_visible())
    
    def toggle_fullscreen(self, widget, data=None):
        '''Event handler and standalone. Toggles the app's Fullscreen state.'''
        if self.is_fullscreen:
            self.window.unfullscreen()
        else:
            self.window.fullscreen()
    
    def track_fullscreen(self, widget, data=None):
        '''Event handler. Tracks the app's fullscreen state.'''
        mask = Gdk.WindowState.FULLSCREEN
        self.is_fullscreen = (widget.get_window().get_state() & mask) == mask
    
    def show_dlg(self, widget, data=None):
        '''Event handler and standalone. Run, then hide the dialog box passed as widget.'''
        # The widget arg is populated correctly in Glade using the Custom Data
        # field as the target dialog, and marking the Switch attribute.
        widget.run()
        widget.hide()
    
    def show_dup_node_error(self):
        '''Show the Duplicate Node error dialog.'''
        self.dup_err_dlg.run()
        self.dup_err_dlg.hide()
    
    def show_blank_err(self):
        '''Show the Blank Label error dialog.'''
        self.blank_err_dlg.run()
        self.blank_err_dlg.hide()
    
    def show_dev_error(self, widget=None, data=None, other=None):
        '''Event handler and standalone. Show the Not Implemented dialog.'''
        print widget
        self.not_implemented_box.run()
        self.not_implemented_box.hide()
    
    def redraw(self, widget=None, data=None):
        '''Event handler and standalone. Trigger a graph update and redraw.'''
        seltype = None
        if self.seltype == 'node':
            seltype = 'node'
            lbl = self.seldata.label
        elif self.seltype == 'edge':
            seltype = 'edge'
            rel = self.seldata
            #get edge selection data
            tlbl = self.seldata.to_node
            flbl = self.seldata.from_node
        
        self.canvas.scroll_to(0, 0)
        self.canvas.redraw(self.G)
        
        #reset the cursor
        rwin = self.builder.get_object("canvas_eventbox").get_window()
        rwin.set_cursor(None)
        
        #get back our selection
        if seltype != None:
            if seltype == 'node':
                self.set_selection(self.canvas.get_vertex(lbl))
            else:
                self.set_selection(self.canvas.get_edge(tlbl, flbl))
                if rel in self.selection.rels:
                    num = self.selection.rels.index(rel)
                    self.pick_rel(relnum = num)
                    self.builder.get_object("rel_combo").set_active(num)
            
            #center the selection
            self.center_on(self.selection)
    
    def refresh(self, touch, oldlbl=None):
        '''Redraw the diagram without updating node positions.'''
        self.selection.set_selected(False)
        self.canvas.refresh(touch, oldlbl)
        self.selection.set_selected(True)
    
def _(text):
    '''Get translated text where possible.'''
    #TODO grab translated text
    return text

def main():
    '''Enter Gtk.main().'''
    Gtk.main()
    return

if __name__ == "__main__":
    soc = Sociogram()
    main()
