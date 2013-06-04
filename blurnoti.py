import objc, re, os, urllib, urllib2, hashlib, sys, time, json, webbrowser
from Foundation import *
from AppKit import *
from PyObjCTools import NibClassBuilder, AppHelper

status_images = {'no-unread':'no-unread.png', 'unread':'unread.png'}

start_time = NSDate.date()

class Timer(NSObject):
  images = {}
  username = ''
  password = ''
  statusbar = None
  auth_cookie = ''
  last_count = 0
  state = 'no-unread'

  def applicationDidFinishLaunching_(self, notification):
    global app
    statusbar = NSStatusBar.systemStatusBar()
    # Create the statusbar item
    self.statusitem = statusbar.statusItemWithLength_(NSVariableStatusItemLength)
    # Load all images
    for i in status_images.keys():
      self.images[i] = NSImage.alloc().initByReferencingFile_(status_images[i])
    # Set initial image
    self.statusitem.setImage_(self.images['no-unread'])
    # Let it highlight upon clicking
    self.statusitem.setHighlightMode_(1)
    # Set a tooltip
    self.statusitem.setToolTip_('Sync Trigger')
    
    # Setup notification sound
    # Thanks to http://www.freesound.org/people/NenadSimic/sounds/171696/ for the sound! - Creative commons licensed
    self.notifysound = NSSound.alloc()
    self.notifysound.initWithContentsOfFile_byReference_("notify.wav", True)

    # Build a very simple menu
    self.menu = NSMenu.alloc().init()
    # Sync event is bound to sync_ method
    menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Open NewsBlur', 'open:', '')
    self.menu.addItem_(menuitem)
    menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Check Now...', 'tick:', '')
    self.menu.addItem_(menuitem)
    # Default event
    menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
    self.menu.addItem_(menuitem)
    # Bind it to the status item
    self.statusitem.setMenu_(self.menu)
    
    self.growlImage = NSImage.alloc().initWithContentsOfFile_('newsblur-icon.png').TIFFRepresentation()
    
    # Login, get cookie.
    login = {'username': self.username, 'password': self.password}
    data = urllib.urlencode(login)
    req = urllib2.Request('https://www.newsblur.com/api/login',data)
    response = urllib2.urlopen(req)
    
    data = json.loads(response.read())

    if data['code'] == 1:
      headers = response.info().dict
      cookies = headers['set-cookie']
      
      
      parts = cookies.split(';')
      self.auth_cookie = parts[0]
  
      # Get the timer going
      self.timer = NSTimer.alloc().initWithFireDate_interval_target_selector_userInfo_repeats_(start_time, 300.0, self, 'tick:', None, True)
      NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)
    else:
      self.statusitem.setImage_(self.images['error'])
      alert("Unable to login", "We were unable to login with the credentials provided", ["OK"]) 
      print "failed to login"
      app.terminate_(self)
    
  def open_(self, notification):
    webbrowser.open('https://www.newsblur.com/folder/everything')

  def tick_(self, notification):
    
    req = urllib2.Request('https://www.newsblur.com/reader/refresh_feeds')
    req.add_header('Cookie',self.auth_cookie)
    response = urllib2.urlopen(req)
    data = json.loads(response.read())
    
    unread = 0;
    
    for feed_id, feed_data in data['feeds'].items():
      unread += feed_data['nt']
      
    print "Total unread: "+str(unread)
    
    if unread > 0:
      self.state = 'unread'
      self.statusitem.setImage_(self.images['unread'])
      self.statusitem.setTitle_(str(unread))
      if unread > self.last_count:
        self.notifysound.play()
        new = unread - self.last_count
        if new == 1:
          plural = ''
          are = 'is'
        else:
          plural = 's'
          are = 'are'
        GrowlApplicationBridge.notifyWithTitle_description_notificationName_iconData_priority_isSticky_clickContext_(
            u'BlurNoti',str(new)+' new unread article'+plural+' on NewsBlur\nThere are now '+str(unread)+' unread items',u'notification',self.growlImage,0,False,time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime()))
        
      self.last_count = unread 
    else:
      self.state = 'no-unread'
      self.statusitem.setImage_(self.images['no-unread'])
      self.statusitem.setTitle_('')


 
class Alert(object):
    
    def __init__(self, messageText):
        super(Alert, self).__init__()
        self.messageText = messageText
        self.informativeText = ""
        self.buttons = []
    
    def displayAlert(self):
        alert = NSAlert.alloc().init()
        alert.setMessageText_(self.messageText)
        alert.setInformativeText_(self.informativeText)
        alert.setAlertStyle_(NSInformationalAlertStyle)
        for button in self.buttons:
            alert.addButtonWithTitle_(button)
        NSApp.activateIgnoringOtherApps_(True)
        self.buttonPressed = alert.runModal()
    
def alert(message="Default Message", info_text="", buttons=["OK"]):    
    ap = Alert(message)
    ap.informativeText = info_text
    ap.buttons = buttons
    ap.displayAlert()
    return ap.buttonPressed
 
def cocoa_dialogs(fn):
    class MainRunner(object):
        def runWithShutdown_(self, timer):
            fn()
            NSApp.stop_(None)
 
        def run(self):
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(1, self, 'runWithShutdown:', "", False)                    
                    
    def wrapped():
        NSApplication.sharedApplication()
        MainRunner().run()
        NSApp.run()
        
    return wrapped
    
    


# load Growl.framework
myGrowlBundle=objc.loadBundle("GrowlApplicationBridge", globals(), bundle_path=objc.pathForFramework(
    u'./Growl.framework'))

# growl delegate
class rcGrowl(NSObject):

    def rcSetDelegate(self):

        GrowlApplicationBridge.setGrowlDelegate_(self)

    def registrationDictionaryForGrowl(self):

        return {u'ApplicationName':u'BlurNoti',u"AllNotifications":[u'notification'],u"DefaultNotifications":[u'notification']}

    # don't know if it is working or not
    def applicationNameForGrowl(self):
        return u'BlurNoti'

    # the method below is called when notification is clicked
    def growlNotificationWasClicked_(self,clickContextS):
      webbrowser.open('https://www.newsblur.com/folder/everything')

    # the method below is called when notification is timed out
    #def growlNotificationTimedOut_(self,clickContextS):
      #print 'Growl timed out'

if __name__ == "__main__":
  app = NSApplication.sharedApplication()
  delegate = Timer.alloc().init()
  app.setDelegate_(delegate)

  # set up growl delegate
  rcGrowlDelegateO=rcGrowl.new()
  rcGrowlDelegateO.rcSetDelegate()
    
  AppHelper.runEventLoop()