Calibration
===========

To use ObjectViz, you must train it to recognize your objects:

- Put a phymark on the table, in the detection zone, so that your object is
  oriented upward, after calibration, the current position will indicate an
  angle of 0.

.. Figure:: images/calib_1.png
    :scale: 50%

    Object's touches (here represented by red dots) must be in the calibration
    zone. Touches status will indicate 3 available touches.

- The detection zone cursor should position itself to the object id selector,
  as soon as exactly 3 free touches (see touch status zone in the interface
  description) are detected in the calibration zone, you can select an
  available ID here.

.. Figure:: images/calib_1_bis.png
    :scale: 50%

    Status zone will indicate that you can select an identifier.


.. Figure:: images/calib_2.png
    :scale: 50%

    Select an identifier

.. Figure:: images/calib_3.png

    This identifier is now assigned to the phymark.

- Once a ID is selected, the object's position and orientation is
  indicated on the screen, under the phymark, in yellow.

.. Figure:: images/calib_4.png
    :scale: 50%

    This object needs some slow motions to improve ObjectViz knowledges about it.

- Rotate the phymark slowly until the display under it turns blue.

- The object is now known, and will be recognized every time it's put in
  the detection zone.

.. Figure:: images/calib_5.png
    :scale: 50%

    This object has completed its calibration process.

- You may get a message at the top of the screen advising about adjusting
  tolerance parameters. This indicate that the values collected during the
  calibration varied more than the current tolerance parameters account for,
  the advised value correspond to two standard deviations from the collected
  data set. If the object was moved too fast during calibration, the value may
  be way more than what you need, so be sure to do the calibration in a gentle
  way. These values can be adjusted in the `settings` screen.

.. Figure:: images/calib_warning.png
    :scale: 50%

    Either the frame is not precise enough for the current values, or the calibration step was done slightly too fast.
