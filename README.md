Sociogram
=========

A Gtk program to visualize social networks.

The source presented here is currently under heavy development and not suitable for serious use. It has only been tested on an Ubuntu 12.10 64-bit system.

Requirements
============

* Gtk+ 3.4 (or higher) with gobject-introspection (gi) libraries
* goocanvas 2.0.1 (or higher)
* networkx 1.6
* python 2.7.3
* python bindings for gtk, goocanvas, and networkx

Features
=======
I have a lot planned for this program, but it'll have to come in a bit at a time.

First Preview Release
---------------------
This release is a preview showcasing the basic features of Sociogram. Most features are not yet implemented. This is what does work:
* add, remove, and edit arbitrary nodes and relationships
* add, remove and edit arbitrary name:value attribute pairs on nodes and relationships
* diagrams are correctly drawn
* diagrams can be zoomed and panned
    * zooming uses Ctrl + mouse scroll wheel
    * panning uses the scroll handles on the diagram
    * vertical panning can be done with the mouse scroll wheel
    * horizontal panning can be done with Shift + mouse scroll wheel
* search for nodes by their label (only from the main window)
* save and load data from custom xml files

Planned for Version 1.0
-----------------
These are what's left to implement before the first gold release.
* rule-based styling for node appearance
* rule-based styling for relationship dropdowns, and maybe relationship appearance
* export to pdf, hopefully jpg, maybe other formats
* "highlight mode", where everything except the currently selected node, its links, and some number of connected nodes are grayed out
* search for nodes and relationships by label using the Find popup
* unlimited undo/redo for changes to the diagram
* basic in-app help docs
* attribute copy/paste between nodes and relationships

The Future
---------
* attribute "tag cloud"
* determine/show shared, linked nodes between (connected) subgraphs (i.e. the AND of two subgraphs)
* determine/show shortest and longest paths between two connected nodes
* pin nodes in place to prevent automatic rearrangement
* search by attribute as well as label
* style key, with one-click enable/disable for individual rules
* style rule option to make a thing invisible
* image styles, like post-it and yarn, polaroids, etc.
* customizable images for each node
* background color/texture, with builtins like corkboard and paper
* relationships with one or both endpoints being other relationships, like in a family tree
* import graph data from other formats (DOT file, csv, anything supported by networkx, etc.)
* add notes to each node, relationship, and the diagram as a whole

Documentation
============
Documentation will be added to the project's [wiki](https://github.com/aurule/Sociogram/wiki) here on github, once Sociogram is stable enough for documentation to be reliable.

Helping Out
==========
There a tons of ways that you can help, though some of them might have to wait until the program is more stable and complete.

Code
----
Pull requests are always welcome and I'd be happy to collaborate with anyone interested in development.

Testing
------
Adding to the project's Issues is a great way to help me out. I have my own development checklist, but seeing other people's issues helps refine my efforts.

Art
---
Sociogram could really use some custom icons, especially one for the program itself. If you have skills in this direction, please do send icons my way! They're very, very likely to be added.

Internationalization
-----------------
I'm planning to make the whole program compatable with i18n, but not until it's more complete. If you'd like to help translate, watch this space! Or you can send me a message to that effect and I'll let you know when it's ready.
