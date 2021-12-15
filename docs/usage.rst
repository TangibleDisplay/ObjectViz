Usage
=====

Entering use mode
------------------

To use ObjectViz with another software, you must switch to `use` mode,
by touching the button labeled `use`.

This makes the Detection zone full screen, and allow detection on every
part of the screen. If you enabled the `hide window in use mode` option,
the window will turn invisible until you exit `use` mode.


Exiting use mode
----------------

To exit use mode, you can use the button at the top-left button
of the screen, to avoid accidental exit while using another application,
the button requires a long touch, then to touch the buttons that appear
temporarily. Alternatively, you can press the `escape` key on the
computer's keyboard.


About TUIO
----------

ObjectViz uses TUIO as a way to communicate Object events to client
applications. TUIO is a simple yet powerful network protocol used to send touch
and objects events for multitouch and tangible applications. A specification of
the format can be found at http://tuio.org/?specification. Most programming
environment have a TUIO implementation, if yours doesn't have one, an OSC
(https://en.wikipedia.org/wiki/Open_Sound_Control) implementation (even
more common) should give you most of what's needed to implement TUIO server (to
parse events from ObjectViz) quickly.
