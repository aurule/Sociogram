#!/usr/bin/env python2

#import system libraries
from __future__ import division
from gi.repository import Gtk, GooCanvas, Gdk
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
        #placeholders for selecting objects
        self.selection = None
        self.seltype = None
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/sociogram.ui")

        #set default type for new objects
        self.builder.get_object("newtypesel").set_active(0)
        
        self.node_lbl_store = Gtk.ListStore(str)
        textcell = Gtk.CellRendererText()
        
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
        #from_combo.pack_start(textcell, True)
        #from_combo.add_attribute(textcell, 'text', 0)
        #from_combo.set_id_column(0)
        
        to_combo = self.builder.get_object("to_combo")
        to_combo.set_model(self.node_lbl_store)
        self.to_main = self.builder.get_object("to_combo_entry")
        self.to_main.set_completion(completions[1])
        #to_combo.pack_start(textcell, True)
        #to_combo.add_attribute(textcell, 'text', 0)
        #to_combo.set_id_column(0)
        
        #populate from_combo_dlg and to_combo_dlg from the same model as above
        from_combo_dlg = self.builder.get_object("from_combo_dlg")
        from_combo_dlg.set_model(self.node_lbl_store)
        self.from_dlg = self.builder.get_object("from_combo_dlg_entry")
        self.from_dlg.set_completion(completions[2])
        #from_combo_dlg.pack_start(textcell, True)
        #from_combo_dlg.add_attribute(textcell, 'text', 0)
        #from_combo_dlg.set_id_column(0)
        
        to_combo_dlg = self.builder.get_object("to_combo_dlg")
        to_combo_dlg.set_model(self.node_lbl_store)
        self.to_dlg = self.builder.get_object("to_combo_dlg_entry")
        self.to_dlg.set_completion(completions[3])
        #to_combo_dlg.pack_start(textcell, True)
        #to_combo_dlg.add_attribute(textcell, 'text', 0)
        #to_combo_dlg.set_id_column(0)
        
        #add completion to toolbar node search field
        searchbar = self.builder.get_object("search_entry")
        searchbar.set_completion(completions[4])
        
        
        #connect attribute view with attribute list, create columns, and make it all sortable
        editme = Gtk.CellRendererText()
        editme.set_property("editable", True)
        editme.connect("edited", self.update_attrs)
        
        self.attr_store = Gtk.ListStore(str, str, bool, str)
        adisp = self.builder.get_object("attrstree")
        adisp.set_model(self.attr_store)
        col1 = Gtk.TreeViewColumn("Name", editme, text=0)
        col1.set_sort_column_id(0)
        col2 = Gtk.TreeViewColumn("Value", editme, text=1)
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
        self.canvas.node_callback = self.node_clicked
        self.canvas.line_callback = None
        self.canvas.key_handler = self.canvas_key_handler
        self.canvas.connect("button-press-event", self.canvas_clicked)
        self.canvas.connect("scroll-event", self.scroll_handler)
        
        
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
            "app.deep_find": self.show_dev_error,
            "app.show_dlg": self.show_dlg,
            "app.show_add": self.show_add,
            "app.dlg_sanity": self.check_new_dlg_sanity,
            "app.set_highlight_radius": self.show_dev_error,
            "app.check_name": self.check_label,
            "app.canvas_keys": self.canvas_key_handler,
            "app.zoom_in": self.zoom_in_step,
            "app.zoom_out": self.zoom_out_step,
            "app.zoom_reset": self.zoom_reset,
            "app.zoom_fit": self.zoom_fit,
            "app.cancel_newname": self.cancel_name_edit,
            "data.add": self.show_dev_error,
            "data.copyattrs": self.show_dev_error,
            "data.pasteattrs": self.do_paste,
            "data.delsel": self.delete_selection,
            "data.update_lbl": self.update_lbl,
            "data.update_terminus": self.update_terminus,
            "data.update_weight": self.update_weight,
            "data.update_bidir": self.update_bidir,
            "data.newattr": self.show_dev_error,
            "data.delattr": self.show_dev_error,
            "graph.toggle_highlight": self.show_dev_error,
            "graph.refresh": self.redraw
        }
        self.builder.connect_signals(handlers_main)
        
        #disable sidebar programmatically, so that labels will be drawn correctly
        self.builder.get_object("sidebarbox").set_sensitive(False)
    
    def nothing(self, a=None, b=None):
        print 'nothing'
    
    def show_add(self, widget, data=None):
        '''Show Add Object dialog after resetting field defaults and ensuring sane Relationship availability.'''
        #clear the dialog's values
        self.builder.get_object("newtypesel").set_active(0)
        self.builder.get_object("name_entry_dlg").set_text('')
        self.from_dlg.set_text('')
        self.to_dlg.set_text('')
        self.builder.get_object("weight_spin_dlg").set_value(5)
        self.builder.get_object("bidir_new").set_active(False)
        self.builder.get_object("use_copied_attrs").set_active(False)
        
        #show the thing
        self.builder.get_object("new_type_box").set_sensitive(self.G.order() > 1) #disallow Relationships unless we have enough nodes
        self.builder.get_object("name_entry_dlg").grab_focus() #focus on the label field
        response = self.add_item_dlg.run()
        self.add_item_dlg.hide()
        
        #don't add anything unless the OK button was pressed
        if response != 4:
            return
        
        #otherwise, add a new object
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
            rel = self._add_rel(lbl, fnode, tnode, weight, bidir, paste)
        else:
            node = self._add_node(lbl, paste)
        
        self.redraw()
        if "Rel" in obj_type:
            #TODO get selectable relationship
            obj = None
        else:
            obj = self.canvas.get_vertex(lbl)
        self.set_selection(obj)
    
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
    
    def _add_node(self, lbl, paste=False):
        '''Internal function. Add a node and handle bookkeeping.'''
        #make sure the node doesn't already exist
        if lbl in self.G: 
            self.show_dup_node_error()
            return
        
        #create object and update data
        node = Graph.Node(lbl)
        self.G.add_node(lbl, {"node": node}) #add to graph
        self.node_lbl_store.append([lbl]) #update name list for the dropdowns
        
        if paste:
            self._paste_attrs(node)
    
    def _add_rel(self, lbl, fname, tname, weight, bidir, paste):
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
        
        if paste:
            self._paste_attrs(node)
    
    # Picks the appropriate object to paste into, then passes off to _paste_attrs.
    def do_paste(self, widget, data=None):
        '''Event handler. Trigger paste operation for selected item.'''
        if self.selection != None:
            self._paste_attrs(self.selection)
    
    # Internal function to overwrite target object's attributes with those from
    # the clipboard.
    def _paste_attrs(self, obj):
        '''Paste copied attributes into obj, overwriting if necessary.'''
        #TODO paste
        #silently fail if no paste buffer
        self.show_dev_error()
    
    # Sees if a given node exists, and focuses on it if so.
    # Slightly different definition so that data is big enough to accept random
    # crap from clicking the search icon.
    def find_node(self, widget, *data):
        node = widget.get_text()
        if node not in self.G:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_NO)
            widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("No such node"))
            widget.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, False)
        else:
            #select node
            vertex = self.canvas.get_vertex(node)
            self.set_selection(vertex)
        widget.select_region(0, widget.get_text_length())
    
    def set_search_icon(self, widget, data=None):
        '''Event handler. Resets search box icon when user types.'''
        widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_FIND)
        widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("Search"))
        widget.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)
    
    def set_selection(self, selobj, obj=None, event=None):
        '''Event handler and standalone. Mark selobj as selected and update ui.'''
        #make sure the old selection is cleared, since we can't guarantee clear_select() has already been run
        if self.selection != None:
            self.selection.set_selected(False)
        
        if selobj == None:
            return
        
        self.selection = selobj
        self.seltype = selobj.type
        self.selection.set_selected(True)
        self.canvas.grab_focus(selobj)
            
        #TODO make sure it's visible in the canvas. if not, center it
        
        #TODO grab data and update UI
        self.builder.get_object("name_entry").set_text(selobj.label)
        if selobj.type == 'node':
            self.activate_node_controls()
        else:
            self.activate_all_controls()
            #TODO populate from a single relationship object, not the aggline
            self.from_combo.set_text(selobj.origin.label)
            self.from_combo.set_text(selobj.dest.label)
            self.builder.get_object("weight_spin").set_value(selobj.weight)
            self.builder.get_object("").set_active(selobj.bidir)
        
        #TODO populate attribute list
        self.builder.get_object("canvas_eventbox").grab_focus() #set keyboard focus
    
    def clear_select(self, canvas=None, data=None):
        '''Event handler and standalone. Deselect object(s).'''
        if self.selection != None:
            self.selection.set_selected(False)        
            self.selection = None
            self.seltype = None
        
        self.disable_all_controls()
    
    def delete_selection(self, widget=None, data=None):
        if self.selection != None:
            self.G.remove_node(self.selection.label)
            self.selection.remove()
            self.clear_select()
            self.redraw()
    
    def activate_node_controls(self):
        '''Make only node-compatable selection-specific controls sensitive to input.'''
        #enable the enter sidebar and related controls
        self.activate_all_controls()
        
        #now explicitly disable relationship-only controls
        self.builder.get_object("frombox").set_sensitive(False)
        self.builder.get_object("tobox").set_sensitive(False)
        self.builder.get_object("weightbox").set_sensitive(False)
    
    def activate_all_controls(self):
        '''Make all selection-specific controls sensitive to input.'''
        self.builder.get_object("sidebarbox").set_sensitive(True)
        self.builder.get_object("add_attr").set_sensitive(True)
        self.builder.get_object("remove_attr").set_sensitive(True)
        
        #explicitly enable relationship-only controls, since they may have been previously explicitly disabled
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
    
    def canvas_clicked(self, canvas, obj=None, event=None):
        '''Event handler. Set keyboard focus and clear selection on canvas click.'''
        self.clear_select()
        self.builder.get_object("canvas_eventbox").grab_focus() #set keyboard focus
    
    def canvas_key_handler(self, widget, event=None):
        '''Event handler. Take actions based on keyboard input while a graph object is selected.'''
        
        kvn = Gdk.keyval_name(event.keyval)
        if kvn == '1':
            self.canvas.set_scale(1)
            return True
        elif kvn == 'plus':
            self.zoom_in()
        elif kvn == 'minus':
            self.zoom_out()
        elif kvn == 'Delete':
            self.delete_selection()
            return True
        elif kvn == 'Escape':
            self.clear_select()
            return True
    
    def scroll_handler(self, widget, event=None):
        '''Event handler. Change scroll action based on various contexts.'''
        horiz_mask = Gdk.ModifierType.SHIFT_MASK
        zoom_mask = Gdk.ModifierType.CONTROL_MASK
        
        if event.state & horiz_mask:
            val = self.builder.get_object("horiz_scroll_adj").get_value() #minus step increment, capped at zero
            adj = self.builder.get_object("horiz_scroll_adj").get_step_increment()
            if event.direction == Gdk.ScrollDirection.UP:
                #scroll left
                self.builder.get_object("horiz_scroll_adj").set_value(val-adj)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                #scroll right
                self.builder.get_object("horiz_scroll_adj").set_value(val+adj)
            
            return True
        elif event.state & zoom_mask:
            #TODO get scale from settings
            if event.direction == Gdk.ScrollDirection.UP:
                self.zoom_in_step()
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.zoom_out_step()
            
            return True
        
        #unless we handled it, let the event flow along
        return False
    
    def zoom_in_step(self, widget, data=None):
        '''Event handler. Enlarge scale by prefs factor.'''
            #TODO get scale from settings
        self.canvas.set_scale(self.canvas.scale * 1.2)
    
    def zoom_out_step(self, widget, data=None):
        '''Event handler. Shrink scale by prefs factor.'''
            #TODO get scale from settings
        self.canvas.set_scale(self.canvas.scale * 0.8)
    
    def zoom_reset(self, widget, data=None):
        '''Event handler. Set scale to 1.'''
        self.canvas.set_scale(1)
    
    def zoom_fit(self, widget=None, data=None):
        '''Event handler and standalone. Calculate optimal scale value to show entire area at once.'''
        #TODO figure out the best fit, for real
        pass
    
    def check_label(self, widget, data=None):
        '''Event handler. Warn if edited label is already used.'''
        
        if widget == None or self.selection == None:
            return
        
        newlbl = widget.get_text()
        if newlbl != self.selection.label and newlbl in self.G:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_DIALOG_ERROR)
            widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("Label already used"))
            widget.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, False)
        else:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, None)
    
    def cancel_name_edit(self, widget, data=None):
        '''Event handler. Reset name field if Esc key pressed.'''
        kvn = Gdk.keyval_name(data.keyval)
        if kvn == 'Escape':
            widget.set_text(self.selection.label)
    
    def update_lbl(self, widget, data=None):
        '''Event handler. Update selection's label and redraw it.'''
        if self.selection == None:
            return
        
        newlbl = widget.get_text()
        oldlbl = self.selection.label
        if oldlbl == newlbl:
            return
        
        #change the internal object's label
        self.G.node[oldlbl]['node'].label = newlbl
        
        #remove old label from the liststore and add the new one
        for row in self.node_lbl_store:
            if row[0] == oldlbl:
                self.node_lbl_store.remove(row.iter)
        self.node_lbl_store.append([newlbl])
        
        #update internal relationship objects' to and from node labels
        for n in self.G[oldlbl]:
            for rel in self.G[oldlbl][n]['rels']:
                if rel.from_node == oldlbl: rel.from_node = newlbl
                if rel.to_node == oldlbl: rel.to_node = newlbl
        
        #change the graph node's key
        nx.relabel_nodes(self.G, {oldlbl:newlbl}, False)
        
        #redraw and reselect the new node
        self.canvas.redraw(self.G)
        self.set_selection(self.canvas.get_vertex(newlbl))
    
    def update_terminus(self, widget, data=None):
        '''Event handler. Update selected relationship's endpoints and redraw it.'''
        pass
    
    def update_weight(self, widget, data=None):
        '''Event handler. Update selected relationship's weight and redraw it.'''
        pass
    
    def update_bidir(self, widget, data=None):
        '''Event handler. Update selected relationship's bidir property and redraw it.'''
        pass
    
    def update_attrs(self, widget, path, text):
        #TODO update visible attrs
        #   update selection's attributes
        #   redraw selection
        
        #self.attrstore[path][???] = text
        
        pass
    
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
        self.not_implemented_box.run()
        self.not_implemented_box.hide()
    
    def redraw(self, widget=None, data=None):
        '''Event handler and standalone. Trigger a graph update and redraw.'''
        self.canvas.redraw(self.G)
        #TODO maintain selection

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
