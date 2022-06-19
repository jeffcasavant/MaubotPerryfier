# MaubotPerryfier

MaubotPerryfier will edit a brown fedora into images if the right phrase is used (or on command).

If it hears `a <noun>?` (e.g. `a platypus?`) then it will add the fedora and repost the image.

It will also post the image when you ask it to with `!perryfy <noun>` (or just `!perryfy`).

It needs to be running when an image is posted (it keeps track of the most recent image post in every room it's in).  It keeps this info in memory so if it's restarted it won't respond until it sees anotherV

## Requirements

Perryfier depends on OpenCV to figure out where to put the hat.  Your Maubot instance must have access to the `python-opencv` Python lib.  I have a custom built `maubot` docker container at `jeffcasavant/maubot-maubot` which you're welcome to use.  It uses a [slightly modified version of the official Maubot Dockerfile.](https://github.com/jeffcasavant/public-containers/blob/master/maubot-maubot/Dockerfile)
