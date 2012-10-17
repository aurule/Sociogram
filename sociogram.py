#!/usr/bin/env python2

#import system libraries
from __future__ import division
from gi.repository import Gtk, GooCanvas
from gi.repository.Gdk import WindowState
import networkx as nx

#import local libraries
import Errors
import Graph
import Drawing

class Sociogram:
    #TODO:
    #nodes are stored in a networkx.Graph(node.label, node=node)
    #adding checks for the label in networkx.Graph.nodes()
    #removing uses G.remove_node(label)
    #   this *should* take care of object dereferencing, since the Graph is the only place with refs. Still, if that doesn't work properly, this method should do the trick:
    #   first iterates through neighbors using G[label] list
    #   gathers relationships from each link G[label][n]
    #   del each relationship, then the subject node
    #   finally, G.remove_node(label)
    
    #relationships are stored in the same nx graph using Graph.add_edge(node, node, rels=[rel1, rel2, ...])
    #updates:
    #   first, make sure label1 in G is true
    #   if G.has_edge(node, node), append or remove rels from the dict at G[node][node]['rels']
    #   if not, add_edge(node, node, rels)
    
    def __init__(self):
        '''Set up internals and instantiate/fix up GUI using Gtk.Builder.'''
        self.G = nx.Graph() # instantiate the graph for storage and positioning
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/sociogram.ui")

        #set default type for new objects
        self.builder.get_object("newtypesel").set_active(0)

        #populate from_combo, to_combo, attr_edit_name with liststore and renderer
        self.node_lbl_store = Gtk.ListStore(str)
        textcell = Gtk.CellRendererText()
        
        from_combo = self.builder.get_object("from_combo")
        from_combo.set_model(self.node_lbl_store)
        from_combo.pack_start(textcell, True)
        from_combo.add_attribute(textcell, 'text', 0)
        from_combo.set_id_column(0)
        
        to_combo = self.builder.get_object("to_combo")
        to_combo.set_model(self.node_lbl_store)
        to_combo.pack_start(textcell, True)
        to_combo.add_attribute(textcell, 'text', 0)
        to_combo.set_id_column(0)
        
        
        #populate from_combo_dlg and to_combo_dlg from the same model as above
        from_combo_dlg = self.builder.get_object("from_combo_dlg")
        from_combo_dlg.set_model(self.node_lbl_store)
        from_combo_dlg.pack_start(textcell, True)
        from_combo_dlg.add_attribute(textcell, 'text', 0)
        from_combo_dlg.set_id_column(0)
        
        to_combo_dlg = self.builder.get_object("to_combo_dlg")
        to_combo_dlg.set_model(self.node_lbl_store)
        to_combo_dlg.pack_start(textcell, True)
        to_combo_dlg.add_attribute(textcell, 'text', 0)
        to_combo_dlg.set_id_column(0)
        
        
        #populate attribute name dropdown from a global list
        attr_names = Gtk.ListStore(str)
        ane = self.builder.get_object("attr_edit_name")
        ane.set_model(attr_names)
        ane.pack_start(textcell, True)
        ane.add_attribute(textcell, 'text', 0)
        to_combo_dlg.set_id_column(0)
        
        
        #connect attribute view with attribute list, create columns, and make it all sortable
        self.attr_store = Gtk.ListStore(str, str, bool, str)
        adisp = self.builder.get_object("attrstree")
        adisp.set_model(self.attr_store)
        col1 = Gtk.TreeViewColumn("Name", textcell, text=0)
        col1.set_sort_column_id(0)
        col2 = Gtk.TreeViewColumn("Value", textcell, text=1)
        col2.set_sort_column_id(1)
        togglecell = Gtk.CellRendererToggle()
        togglecell.connect("toggled", self.show_dev_error) #TODO handle attr visibility change
        col3 = Gtk.TreeViewColumn("Visible", togglecell, active=2)
        col3.set_sort_column_id(2)
        adisp.append_column(col1)
        adisp.append_column(col2)
        adisp.append_column(col3)


        #create canvas object and add to the scroll window
        #VERY IMPORTANT. using the normal window.add() call fails, but setting the parent like this makes everything fine
        self.canvas = Drawing.Canvas(parent=self.builder.get_object("canvas_scroll"))
        #attach callbacks
        self.canvas.node_callback = self.show_dev_error;
        self.canvas.line_callback = self.show_dev_error;
        
        
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
        
        
        #initialize our fullscreen tracker
        self.fullscreen = False
        
        #show the main window
        self.window = self.builder.get_object("sociogram_main")
        self.window.show_all()
        
        # Attach handlers to signals described in the .ui file.
        # TODO once functionality is finalized, remove redundant signals
        handlers_main = {
            "app.quit": Gtk.main_quit,
            "app.newfile": self.show_dev_error,
            "app.openfile": self.show_dev_error,
            "app.savefile": self.show_dev_error,
            "app.saveas": self.show_dev_error,
            "app.do_export": self.show_dev_error,
            "app.help": self.show_dev_error,
            "app.undo": self.show_dev_error,
            "app.redo": self.show_dev_error,
            "app.search": self.find_node,
            "app.reset_search_icon": self.set_search_icon,
            "app.selattr": self.show_dev_error,
            "app.toggle_widget": self.toggle_widget,
            "app.toggle_fs": self.toggle_fullscreen,
            "app.track_fs": self.track_fullscreen,
            "app.hide_add_controls": self.hide_addbox_controls,
            "app.check_empty": self.check_new_empty,
            "app.deep_find": self.show_dev_error,
            "app.show_dlg": self.show_dlg,
            "app.show_add": self.show_add,
            "data.add": self.add_obj,
            "data.copyattrs": self.show_dev_error,
            "data.pasteattrs": self.do_paste,
            "data.delsel": self.show_dev_error,
            "data.update": self.redraw,
            "data.newattr": self.show_dev_error,
            "data.delattr": self.show_dev_error,
            "graph.toggle_highlight": self.show_dev_error,
            "graph.refresh": self.redraw
        }
        self.builder.connect_signals(handlers_main)
    
    def show_add(self, widget, data=None):
        '''Show Add Object dialog after resetting field defaults and ensuring sane Relationship availability.'''
        #clear the dialog's values
        self.builder.get_object("newtypesel").set_active(0)
        self.builder.get_object("name_entry_dlg").set_text('')
        self.builder.get_object("from_combo_dlg").set_active(-1)
        self.builder.get_object("to_combo_dlg").set_active(-1)
        self.builder.get_object("weight_spin_dlg").set_value(5)
        self.builder.get_object("bidir_new").set_active(False)
        self.builder.get_object("use_copied_attrs").set_active(False)
        
        #show the thing
        self.builder.get_object("new_type_box").set_sensitive(self.G.order() > 1) #disallow Relationships unless we have enough nodes
        #TODO disallow selecting the same node for both From and To
        self.builder.get_object("name_entry_dlg").grab_focus()
        self.add_item_dlg.run()
        self.add_item_dlg.hide()
    
    def hide_addbox_controls(self, widget, data=None):
        '''Event handler. Toggles visibility of Relationship-specific fields in the Add Object dialog based on selected Type.'''
        obj_type = widget.get_active_text()
        vis = "Rel" in obj_type
        for wname in ["frombox_dlg", "tobox_dlg", "weightbox_dlg", "bidir_new"]:
            self.builder.get_object(wname).set_visible(vis)
    
    def check_new_empty(self, widget, data=None):
        '''Event handler. Disable Add Object dialog's Add button unless Label field has text.'''
        sense = self.builder.get_object("name_entry_dlg").get_text() != ""
        self.builder.get_object("new_ok").set_sensitive(sense)
    
    #TODO move this into show_add with a conditional
    def add_obj(self, widget, data=None):
        '''Handles the outcome of the Add Object dialog.'''
        obj_type = self.builder.get_object("newtypesel").get_active_text()
        
        lbl = self.builder.get_object("name_entry_dlg").get_text()
        
        #get the rest of our data
        use_copied = self.builder.get_object("use_copied_attrs").get_active()
        if "Rel" in obj_type:
            #grab extra data fields
            fnode = self.builder.get_object("from_combo_dlg").get_active_id()
            tnode = self.builder.get_object("to_combo_dlg").get_active_id()
            weight = self.builder.get_object("weight_spin_dlg").get_value()
            bidir = self.builder.get_object("bidir_new").get_active()
            rel = self._add_rel(lbl, fnode, tnode, weight, bidir)
            if use_copied:
                self._paste_attrs(rel)
        else:
            node = self._add_node(lbl)
        if use_copied:
            self._paste_attrs(node)
        self.redraw()
    
    def _add_node(self, lbl):
        '''Internal function. Add a node and handle bookkeeping.'''
        #make sure the node doesn't already exist
        if lbl in self.G: 
            self.show_dup_node_error()
            return
        
        #create object and update data
        node = Graph.Node(lbl)
        self.G.add_node(lbl, {"node": node}) #add to graph
        self.node_lbl_store.append([lbl]) #update name list for the dropdowns
    
    def _add_rel(self, lbl, fname, tname, weight, bidir):
        '''Internal function. Add a relationship and handle bookkeeping.'''
        #make sure both nodes exist
        if fname not in self.G:
            raise Errors.MissingNode("Node %s not in graph." % fname)
        if tname not in self.G:
            raise Errors.MissingNode("Node %s not in graph." % tname)
        
        #create relationship object
        rel = Graph.Relationship(lbl, fname, tname, weight, bidir)
        #update existing edge if possible, otherwise add new edge
        if self.G.has_edge(fname, tname):
            self.G[fname][tname]['rels'].append(rel)
        else:
            self.G.add_edge(fname, tname, rels=[rel])
    
    # Picks the appropriate object to paste into, then passes off to _paste_attrs.
    def do_paste(self, widget, data=None):
        #TODO
        #silently fail if there's no selection
        #pick target from selected object in graph
        #call _paste_attrs
        
        self.show_dev_error()
    
    # Internal function to overwrite target object's attributes with those from
    # the clipboard.
    def _paste_attrs(self, obj):
        #TODO paste
        self.show_dev_error()
    
    # Sees if a given node exists, and focuses on it if so.
    # Slightly different definition so that data is big enough to accept random
    # crap from clicking the search icon.
    def find_node(self, widget, *data):
        node = widget.get_text()
        if node not in self.G:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_NO)
        else:
            #TODO select node and make sure it's visible in the canvas. if not, center it
            self.show_dev_error()
        widget.select_region(0, widget.get_text_length())
    
    def set_search_icon(self, widget, data=None):
        '''Event handler. Resets search box icon when new text is entered.'''
        widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_FIND)
    
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
        mask = WindowState.FULLSCREEN
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
        self.not_implemented_box.run()
        self.not_implemented_box.hide()
    
    def redraw(self, widget=None, data=None):
        '''Event handler and standalone. Trigger a graph update and redraw.'''
        self.canvas.redraw(self.G)

def main():
    '''Enter Gtk.main().'''
    Gtk.main()
    return

if __name__ == "__main__":
    soc = Sociogram()
    main()
