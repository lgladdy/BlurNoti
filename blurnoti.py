import objc, re, os, urllib, urllib2, hashlib, sys, time, json, webbrowser, pprint
from Foundation import *
from AppKit import *
from PyObjCTools import NibClassBuilder, AppHelper

from alert import *
from rcGrowl import *

status_images = {'no-unread':'no-unread.png', 'unread':'unread.png'}

start_time = NSDate.date()


class BlurNotiApp(NSObject):
  images = {}
  username = ''
  password = ''
  statusbar = None
  auth_cookie = ''
  latest_count = 0
  previous_count = 0
  state = 'no-unread'
  feeds = []
  first_run = True
  previous_stories = []

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
    
    # Do login
    self.login()

    # Build a very simple menu
    self.buildMenu()
    
    # Setup the feed list used for displaying new items
    self.updateFeedsList()
    
    self.growlImage = NSImage.alloc().initWithContentsOfFile_('newsblur-icon.png').TIFFRepresentation()
      
  
  def login(self):
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
  
      # Get the BlurNotiApp going 
      self.BlurNotiApp = NSTimer.alloc().initWithFireDate_interval_target_selector_userInfo_repeats_(start_time, 300.0, self, 'tick:', None, True)
      NSRunLoop.currentRunLoop().addTimer_forMode_(self.BlurNotiApp, NSDefaultRunLoopMode)
    else:
      self.statusitem.setImage_(self.images['error'])
      alert("Unable to login", "We were unable to login with the credentials provided. The program will now exit", ["OK"]) 
      print "failed to login"
      app.terminate_(self)    
  
  def openItem_(self, notification):
    url = notification.toolTip()
    # Find the story id from self.previous_stories so we can mark it as read. Also, because the user is going to expect things to change instantly, decrease the unread count by one as we mark it as read, then fire a tick
    for story in self.previous_stories:
      if story['story_permalink'] == url:
        found_story = story
        break
    
    self.latest_count = self.latest_count - 1
    self.statusitem.setTitle_(str(self.latest_count))
    webbrowser.open(url)
    self.markAsRead(story)
    self.BlurNotiAppRun()
    
  def markAsRead(self, story):
    markasread = {'story_id': story['id'], 'feed_id': story['story_feed_id']}
    data = urllib.urlencode(markasread)
    req = urllib2.Request('https://www.newsblur.com/reader/mark_story_as_read',data)
    req.add_header('Cookie',self.auth_cookie)
    response = urllib2.urlopen(req)
    
    data = json.loads(response.read())
    
  def open_(self, notification):
    webbrowser.open('https://www.newsblur.com/folder/everything')

  def tick_(self, notification):
    self.BlurNotiAppRun()
  
  def BlurNotiAppRun(self):
    req = urllib2.Request('https://www.newsblur.com/reader/refresh_feeds')
    req.add_header('Cookie',self.auth_cookie)
    response = urllib2.urlopen(req)
    data = json.loads(response.read())
    
    unread = 0;
    self.unread_feeds = []
    
    for feed_id, feed_data in data['feeds'].items():
      unread += feed_data['nt']
      if feed_data['nt'] > 0:
        self.unread_feeds.append(str(feed_data['id']))
    
    print "Total unread: "+str(unread)
    
    
    self.previous_count = self.latest_count
    self.latest_count = unread 
    self.buildMenu()
    
    if unread > 0:
      self.state = 'unread'
      self.statusitem.setImage_(self.images['unread'])
      self.statusitem.setTitle_(str(unread))
      
      if self.first_run:
        self.first_run = False
        if unread > self.previous_count:
          new = unread - self.previous_count
          if new == 1:
            plural = ''
            are = 'is'
          else:
            plural = 's'
            are = 'are'
          self.notifysound.play()
          GrowlApplicationBridge.notifyWithTitle_description_notificationName_iconData_priority_isSticky_clickContext_(
              u'BlurNoti',str(new)+' new unread article'+plural+' on NewsBlur',u'notification',self.growlImage,0,False,'https://www.newsblur.com/folder/everything')
        
    else:
      self.state = 'no-unread'
      self.statusitem.setImage_(self.images['no-unread'])
      self.statusitem.setTitle_('')
      
  def updateFeedsList(self):
    
    req = urllib2.Request('https://www.newsblur.com/reader/feeds')
    req.add_header('Cookie',self.auth_cookie)
    response = urllib2.urlopen(req)
    data = json.loads(response.read())
    self.feeds = data['feeds']
    
    
  def getUnreadItems(self):
  
    feed_params = '&feeds='.join(self.unread_feeds)
    url = 'https://www.newsblur.com/reader/river_stories?read_filter=unread&feeds='+feed_params
    req = urllib2.Request(url)
    req.add_header('Cookie',self.auth_cookie)
    response = urllib2.urlopen(req)
    
    data = json.loads(response.read())
    return data['stories']
    
      
  def buildMenu(self):
  
    self.menu = NSMenu.alloc().init()
    # Sync event is bound to sync_ method
    if self.latest_count > 0:
      menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Open NewsBlur ('+str(self.latest_count)+' unread)', 'open:', '')
    else:
      menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Open NewsBlur', 'open:', '')
    
    self.menu.addItem_(menuitem)
    menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Check Now...', 'tick:', '')
    self.menu.addItem_(menuitem)
    
    menuitem = NSMenuItem.separatorItem()
    self.menu.addItem_(menuitem)
    
    #If we have some unread items, display them in the list
    if self.latest_count > 0:
      stories = self.getUnreadItems()
      
      if len(stories) > 0:
        for story in stories:
          feed = self.feeds[str(story['story_feed_id'])]
          feedname = feed['feed_title']
          title = feedname+': '+story['story_title']
          menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, 'openItem:', '')
          string = NSAttributedString.alloc().initWithString_attributes_(title,{ NSForegroundColorAttributeName: NSColor.grayColor() })          
          menuitem.setAttributedTitle_(string)
          menuitem.setToolTip_(story['story_permalink'])
          self.menu.addItem_(menuitem)
          
        if len(stories) < self.latest_count:
          remaining = self.latest_count - len(stories);
          if remaining == 1:
            stories_plural = 'story'
          else:
            stories_plural = 'stories'
          menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('+'+str(remaining)+' more '+stories_plural+'...', 'open:', '')
          self.menu.addItem_(menuitem)
      
        
    
        menuitem = NSMenuItem.separatorItem()
        self.menu.addItem_(menuitem)
        
        if self.first_run == False:
          diff = [x for x in stories if x not in self.previous_stories]
          if len(diff) > 0:
            count = 0
            for story in diff:
              count += 1
              if count == 5 and len(diff) > 5:
                remain = len(diff) - count
                GrowlApplicationBridge.notifyWithTitle_description_notificationName_iconData_priority_isSticky_clickContext_(
                  'BlurNoti','There are '+str(remain)+' additional unread articles on NewsBlur',u'notification',self.growlImage,0,False,story['story_permalink'])
                break;
              else:
                self.notifysound.play()
                feed = self.feeds[str(story['story_feed_id'])]
                feedname = feed['feed_title']
                GrowlApplicationBridge.notifyWithTitle_description_notificationName_iconData_priority_isSticky_clickContext_(
                  feedname,story['story_title'],u'notification',self.growlImage,0,False,story['story_permalink'])
          
        self.previous_stories = stories
      else:
        self.previous_stories = []
    
    # Default event
    menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
    self.menu.addItem_(menuitem)
    # Bind it to the status item
    self.statusitem.setMenu_(self.menu)

if __name__ == "__main__":
  app = NSApplication.sharedApplication()
  delegate = BlurNotiApp.alloc().init()
  app.setDelegate_(delegate)

  # set up growl delegate
  rcGrowlDelegateO=rcGrowl.new()
  rcGrowlDelegateO.rcSetDelegate()
    
  AppHelper.runEventLoop()