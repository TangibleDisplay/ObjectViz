Settings
========

A number of settings can be used to alter the behavior of ObjectViz, they are
organised in the following sections.

General
-------

Here are a few options about general behavior of ObjectViz as an application,
saving, exiting, mode to start into…


Auto use
++++++++

Will trigger the "use" mode at the startup of the application, which is
important if the software and client applications are set to start themselves
unattended, usually at OS startup. This option will not work if the license is
not present or is expired, as the software will first ask for a license, and
allow for the time-limited demo, to be activated manually.


Start minimized (windows only)
++++++++++++++++++++++++++++++

If this option is activated, ObjectViz will hide itself in the taskbar on
startup, leaving the screen unobstructed. Since ObjectViz works with TUIO
input, it doesn't need to be visible to work, so this option allow for easier
integration, you probably want to activate the "auto use" option if you
activate this one.


Hide ObjectViz in use mode (windows only)
+++++++++++++++++++++++++++++++++++++++++

This option makes ObjectViz practically invisible in use mode, allowing to let
it full screen, on top of other applications, this allows to use ObjectViz when
only HID/wm_touch/native touch is available (instead of TUIO) on windows, since
the ObjectViz needs to be on top to receive touch events in this situation,
this allow to see the client application despite this requirement. 

.. note::
    Not all applications may allow or react well to being "masked" in this way,
    if your client application/framework requires to be fullscreen, or stop
    refreshing parts of the screen supposedly hidden, you may be unable to use
    this option, and have to use TUIO instead.

.. warning::
    This setting will cause a flickering of the application at startup or first
    activation, this doesn't cause any other issue, aside being graphically
    unpleasant, we appologize for the inconvenience.

Auto save
+++++++++

Save objects configuration when exiting application. This avoids losing
confirmation when exiting the application without saving, usually useful while
developing your setup, you may want to deactivate it in production, to avoid
bad manipulation to permanently modify your setup.


Confirm exit
++++++++++++

This option allows to ask for confirmation before exiting, and will display
a message indicating if saving will automatically occur when doing so. 


TUIO
----

Allow to configure how to send TUIO events.


Tuio events ip
++++++++++++++


All the tuio events will be sent to this ip, if your application is running on
the same computer, you can let the default "localhost" or "127.0.0.1", if you
have name resolution, you can use it.


Tuio events port
++++++++++++++++

The port your client application listen for events on, you can give a list of
ports, separated by commas, or a range, begin and end ports separated by
dashes, or even list of ranges and values.

examples:

    3337

    3337,4444

    3334-3340

    3334-3338,3350-3360,5000

.. warning::
    - Avoid putting unnecessary values, however, as it may slow down the
      program.
    - Don't try to send to port 3333, which is the one ObjectViz listens on,
      that would cause an infinite feedback loop.


TUIO flush interval
+++++++++++++++++++

For performance reasons, events are queued and sent to clients at regular
intervals, the default interval between two events being `0.05` second, this
value can be tweaked to lower delay between physical interactions and result in
client program. The value is in seconds.


Detection
---------

These settings allow to tweak detection and reaction to various events about
the lifetime of objects.


Screen width and Screen height
++++++++++++++++++++++++++++++

These options are here to allow correctly detecting objects on screens with
a different ratio than the default 16/9, because in such configuration objects
appear differently depending on their orientation, as long as your screen ratio
is 16/9, you shouldn't need to change these values, but if needed, please give
the physical properties of your screen.


Surface tolerance/Angle tolerance
+++++++++++++++++++++++++++++++++

These two options allow to tweak the difficulty of recognizing objects,
depending on your hardware/drivers/setup, the multitouch points may be more or
less precise, the more precise, the less you need these values to be large for
reliable detection, allowing for more objects to be recognized. On the other
hand, if there are big variations in reading of the touches, you'll need to
increase these values to get more reliable detections of objects, but it will
also increase the risk of mis detection, i.e, the wrong object being detected,
rather than no object.


Point box size
++++++++++++++

This value allows to set a limit to the size of objects being searched for, any
potential combination of points that has two points further apart than this
value will be dismissed, and even a known object will be dismissed if its
points drift further apart. This value will grow automatically when you
configure new objects, but may require to be tweaked if you lose objects when
moving them too fast, or if you configured unrealistically big objects, and
ObjectViz now tries to detect them and look for very large combinations.


Number of samples for calibration
+++++++++++++++++++++++++++++++++

The calibration routine allows to know more about the variation of values
detected for an object, depending on the quality of your setup, you may want to
increase the default value to try to get more representative variations of
objects, but it'll increase the time the user has to spend moving the object in
the calibration routine.


Display touches
+++++++++++++++

This option simply display all the existing touches using a simple circle
representation, allowing to understand if an object is not detected because
some of its point are simply not detected by the screen, or if the observed
position is different than the actual position. Additionally, touch identifiers
are displayed besides them, which allows to see when they change (lost
touches).


Display candidates matching score
+++++++++++++++++++++++++++++++++

When a set of points is considered a potential object, this option will display
its score values against known objects, to allow user to understand the cause
of a mismatch or failure to detect.

The set of points in a candidate are linked together using lines of the same
color (uniquely determined by the set of points), and a box contains the
scores, ordered from better to worse.

The first line indicates the current surface, and angles (min, max) for the
object, until it matches against an object, at this point the values ceases to
be updated.

- The first value is the id the score matches against.
- The second value is the score, the lower, the better (inf indicates an
  impossible match, for example, if the object has already been detected
  elsewhere, or the values falls outside of the tolerance values).
- The third value is the surface difference with the matched object.
- The fourth and fifth values indicates the differences between the matched
  angles of the matched object.

.. Figure:: images/candidates.png
    :scale: 50%

    No candidate matched this particular set of points, if we expected it to
    match object 5, we may need to increase surface (to more than 157) or angle
    (to more than 4.7) tolerance.


When multiple matched objects fall within the tolerance values, the best match
will be selected.
If no object match, the potential object will keep being updated until a match
is found.

If you find that your object are consistently not detected, these values will
indicate by how much you will want to adjust the surface and angle tolerance to
improve your matching, the lower scores will indicate up to how much you can
increase without risking a false positive with them.


Keep missing touches
++++++++++++++++++++

When a touch is lost by the frame, ObjectViz can keep its last position, until
it's found again, to improve its position/rotation values. You may try to
disable this  option and see if the results suits you more, if you favor
reactivity to movement over precision, for example.


Keep angle when object is incomplete
++++++++++++++++++++++++++++++++++++

When set, this option prevents any angle change while an object is incomplete,
this gives more stability to observed object in a noisy environment (weak
detection solution or too many objects near of each others).


Lost objects timeout
++++++++++++++++++++

If all of the touches of an object disappear, the object will be removed after
this time, this time gives a possibility to detect the object again, without
sending any event to the application, which won't see the object was
temporarily lost.

Base detection interval
+++++++++++++++++++++++

The delay between each object detection is dynamic, to limit slowdown in
situations with numerous combinations of touches in close proximity, most of
the time, however, the base delay will be applied, you can tweak this value, if
you want to detect new objects faster. The default value is `0.1` second.


Retain touch
------------

When touches are lost, and new touches appears near of them in a short time
after, they can be considered to be the same touch, this allows for more
reliability in noisy environments, when the lost objects timeout and keep
missing touches options are not enough.


Retain distance
+++++++++++++++

Maximum distance between the lost touch and the new touch to consider them the
same (in pixel).


Retain time
+++++++++++

Maximum time to consider a potential match for new touch before discarding it
(in milli seconds).

