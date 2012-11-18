Sociogram Save File Format
==========================

Sociogram saves its data in XML, which allows for easy use by other programs. The RelaxNG schema `saves.rnc` specifies how this xml is formatted. Although the schema isn't (currently) used to validate savefiles during load, required elements *must* be present. Additional unrecognized elements, however, are ignored.

Once Sociogram sees its first gold release, all save files from that point on will validate against the latest version of `saves.rnc`. Until then, **validation may break between development releases**.
