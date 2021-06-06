Mobile Lucene: A Lucene Fork for Android and iOS
================================================

This is an experimental fork of Lucene. The aim is to make Lucene run on
Android, and then use Google's [j2objc](http://j2objc.org) to translate the
Java code into Objective-C, thus porting Lucene to iOS and OS X.

There have been various Lucene ports, but most of them are several releases
behind the mainline (5.x as of August 2015). This project strives to make
its porting strategy *repeated applicable* to subsequent versions of Lucene.
Since I started working on this project, Lucene 5.2.1 and Lucene 5.3 have
been released, and I was able to track Lucene 5.3 by first rebasing the
current tree and then tackling the changes between the two releases.

This is still an experiment and it requires a lot of work ahead. Below is
a high-level overview.


Quick Start
-----------

To build the JARs, use the commands:

```bash
cd lucene
ant -Dmobilejars=../build/<destination> clean mobile-build-modules-without-test
```

Where `<destination>` is a directory of your choice. The prefix `../build/`
is a trick to gather JARs to a unified folder under `lucene/build/`

Currently, the original Lucene tests don't run with this fork. Many `ant`
tasks are also potentially broken.


Porting Lucene to Android
-------------------------

Lucene 5.x makes use of many JDK 1.7-only APIs, most notably NIO.2. Android
does not have NIO.2, and therefore I've made a library to "backport" those
NIO.2 classes. The library, `org.lukhnos.portmobile`, also comes with some
other classes missing in Android. This is a very crude backport and there is
currently no test.

Because it's cumbersome to load Java resources in Android, and combining
metadata in JAR files when DEXing is also a complicated task, I've also made
changes to the SPI loading mechanism in Lucene so that it uses a hard-coded
list of "loaded" classes.

There are a few more changes needed. I'll try to document them in detail when
I find the time.


Use Source Code Transformation to Port
--------------------------------------

A `transform.py` script is provided to transform the Lucene source code. This
is to make sure that our changes are systematic. This also enforces us to
keep Android-specific changes to a minimum. More importantly, you may still
want to develop your Lucene app in the latest Java, NIO.2 and all, then
create an automated fork using this transformation tool that imports the
mobile version of Lucene.

This script _transforms_ the java code to make it compatible with j2objc.

Porting to Objective-C
----------------------

Once we have made the code Android-compatible, it is then possible to use
j2objc to translate Java to Objective-C. Since Objective-C does not have
garbage collection, we need to break a few cyclic references using j2objc's
weak reference annotations (Java `WeakReference` is not used to minimize
source code changes).

First, set up the J2ObjC dependencies. If you haven't installed it,
[download version 2.8](https://github.com/google/j2objc/releases/tag/2.8) from
its GitHub releases page. After you have made sure that the command `j2objc`
exists in your `PATH`, run within the `lucene` directory:

```bash
cd lucene
./setup-j2objc.sh
```

Then run the `translate.py` script to generate new obj-c classes. The classes
are generated within the folder: `./build/objc/`.

```bash
./translate.py
```

Ported Packages
---------------

* lucene-analyzers-common (but without those that need `BreakIterator`, and
  `org.apache.lucene.analysis.hunspell.ISO8859_14Decoder` is not available
  in the Objective-C translation)
* lucene-core
* lucene-highlighter
* lucene-join
* lucene-memory
* lucene-misc (but no `org.apache.lucene.store.*`)
* lucene-queries
* lucene-queryparser
* lucene-sandbox
* lucene-suggest


To Do
-----

* Currently portmobile only ports the absolute minimum of NIO.2 that Lucene
  uses. Since it does not have everything, Lucene test framework cannot be
  built. There are a number of things in NIO.2 that may not be backportable
  using pre-JDK 7 APIs, and so whether we can make Lucene tests run is an
  open question.
* Only a very small portion of Lucene is used and tested in sample mobile
  apps.
* The transform and translate scripts need a lot of clean-up.
* ant tasks need working.
* The project needs a lot of documentation.
