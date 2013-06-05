## BlurNoti

*BlurNoti* is a simple Mac app that stays on your menu bar, and checks your feeds on [NewsBlur](http://www.newsblur.com) to give you a heads up of new items

How to use
------------
I'm still learning this Python Objective-C stuff, so the app isn't smart enough to have a preferences pane for your username and password yet - therefore you need to compile the app yourself, after adding your username and password (For that reason, don't distribute the compiled code!)

1. Grab the source
2. Edit blurnoti.py's line 16 and 17 to define your username and password
3. In terminal, change path to your checked out code, then run "python setup.py py2app" and wait
4. Grab the dist/BlurNoti.app application and move it to /Applications
5. Run! Be happy :)