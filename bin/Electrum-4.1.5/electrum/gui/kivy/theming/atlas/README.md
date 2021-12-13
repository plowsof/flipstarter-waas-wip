# electrum-kivy-atlas

This repository contains a frozen image atlas for [Electrum](https://github.com/spesmilo/electrum),
specifically its kivy GUI, used for reproducible/deterministic builds.

Note: we did not investigate whether the atlas could be built reproducibly;
this repository exists to avoid having to install the dependencies to build the atlas
(when building Electrum).

## Note for maintainer:

To update these, from electrum root folder, run:
```
$ (cd contrib/android/; make theming)
$ cd electrum/gui/kivy/theming/atlas
$ git commit -m "update atlas"
$ git push
```
