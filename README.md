ObjectViz
=========

ObjectViz is a multitouch object detection solution, enabling you to create
physical markers out of any reliable multitouch solution.

It's easily configurable and pluggable, using TUIO as a communication protocol
with client applications.


Documentation
-------------

To build the documentation (on ubuntu) you need
- texlive-base
- texlive-fonts-extra

go to the docs directory and run `make latexpdf`


Build & Package
---------------

A makefile in `packaging` is used for the various operations:

to install the dependencies, ensure python3.6 or newer is installed then:

```
make -f packaging/Makefile Deps
```

To run without packaging

```
python src/main.py
```

To package the application as an installer for your current platform (though mostly tested on Windows)

```
make -f packaging/Makefile all
```

/!\ Make sure you don't have any uncommited change before running this, as it'll make a lot of local changes you'll want to revert later.
