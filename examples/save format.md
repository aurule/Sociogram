Sociogram Save File Format
==========================

Sociogram saves its data in XML, which allows for easy use by other programs. The RelaxNG file `soc.rnc` specifies how this xml is formatted. Once Sociogram sees its first gold release, all save files from that point on will validate against the latest version of `soc.rnc`. Until then, validation may break between development releases.

The XML of a save file is not validated when Sociogram loads it. Instead, unrecognized data is discarded.
