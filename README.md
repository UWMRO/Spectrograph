# Spectrograph
Spectrograph control software for MRO


## Installing drivers
Go through the INSTALL.txt file in this repository.

## API Documentation

The camera object used during scripts is as follows:

![alt text][apogeeClasses]

[apogeeClasses]: https://github.com/UWMRO/Spectrograph/blob/master/doc/apogeeClasses.png "PyLibapogee Hierarchy"

There is no clear documentation for the Python functions themselves, but there is class documentation for the C++ drivers.

Take a look at TestSpecCam.py, and then move into the provided example Python programs in "examples" (these are from
the apogee drivers).  This will give you a feel for the basic functions and how programming the Alta F is like.  Also take
a look at the Python source code in /usr/local/lib/python2.7/site-packages/pylibapogee (files pylibapogee.py and pylibapogee_setup.py).

For more extensive documentation you will need to look in the classDocs folder in the doc directory.  This gives you great
detail in the C++ classes and functions that are DIRECTLY mapped into Python using SWIG.  All the functions across C++ and Python will
be named the same, only the arguements that you pass in are different.

Go ahead and start one of the *.html files and move over to the classes section and pay closest attention to the classes ApogeeCam, which
is inherited by CamGen2Base, which is inherited by AltaF.  This means all the functions you will be able to use in Python are documented
in these 3 classes.  Make sure you know what inheritance is; that is the main class you will work with is AltaF which has access to the functions
of CamGen2Base and ApogeeCam because of inheritance.  See the float chart above to get a visual of the layout.

As for the functions you will read in the class documentation they are types in C++.  You will need to verify, but the translated type to Python
is relatively intuitive and simpler.  Here are a list of types I found in the documentation and what I believe they will translate to in
the Python functions:
    `C++` -> `Python`

    `uint16`(unsigned 16 bit integer) -->  `int`