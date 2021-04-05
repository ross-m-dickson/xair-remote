# xair-control

The XAir Control is an extension to the XAir remote that extends the remote with
a GUI interface that runs full screen on a Raspberry Pi with PiTFT display. It
uses the control buttons to start or stop the XAir Control, start or stop a
recording to USB stick using sox, and eventually blank the screen, configure
wifi, and start an autogain model once implemented.

## Installing

Follow the instructions for XAir Remote found in README.md then from the X
display on your Pi, either via the touch screen or remotely via VNC:

1. Open the Raspberry menu
2. Preferences->Main Menu Editor
3. New Item
4. Fill in Name: XAir Control, Command [path]/xair-remote/control.sh
5. Click on the icon and choose /usr/share/icons/gnome/48x48/apps/volume-knob.png
6. Click OK
7. Right Click on the title bar
8. Add/Remote Panel Items
9. Choose Aplication Launch Bar
10. Click Preferences
11. Select Other->XAir Control from the right and click Add
12. Click close
13. Edit paths in xair-remote files as necessary

## Running

To run from a termin or ssh session:

	$ sudo python3 [path]/xair-remote/xair_control.py

to run from an xwindows terminal

    $ [path]/xair-remote/control.sh

to run from the GUI simply click the new icon.
