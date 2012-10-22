Sociogram
=========

A Gtk program to visualize social networks.

The source presented here is currently under heavy development and not suitable for serious use. It has only been tested on an Ubuntu 12.04 64-bit system.

Requirements
============

* Gtk+ 3.4 (or higher) with gobject-introspection (gi) libraries
* goocanvas 2.0.1
* networkx 1.6
* python 2.7.3
* python bindings for gtk, goocanvas, and networkx

Features
=======
I have a lot planned for this program, but it'll have to come in a bit at a time.

Planned for Release
-----------------
* arbitrary nodes and relationships
* arbitrary name:value attribute pairs on nodes and relationships
* rule-based styling for node appearance
* rule-based styling for relationship dropdowns, and maybe relationship appearance
* export to pdf, hopefully jpg, maybe other formats
* "highlight mode", where everything except the currently selected node, its links, and some number of connected nodes are grayed out
* search nodes by label
* save/load from xml

Finished
-------
* arbitrary nodes and relationships
* drawing! (except subgraph packing...)
* search nodes by label

The Future
---------
* attribute "tag cloud"
* determine/show shared, linked nodes between (connected) subgraphs (i.e. the AND of two subgraphs)
* determine/show shortest and longest paths between two connected nodes
* static node placement
* search nodes (and relationships) by attribute as well as label
* style key, with one-click enable/disable for individual rules
* style rule option to make a thing invisible
* image styles, like post-it and yarn, polaroids, etc.
* customizable images for each node
* background color/texture, with builtins like corkboard and paper

Documentation
============
Documentation will be added to the project's [wiki](https://github.com/aurule/Sociogram/wiki) here on github, once Sociogram is stable enough for documentation to be reliable.

Internationalization
==================
I'm planning to make the whole program compatable with i18n, but not until it's more complete.
