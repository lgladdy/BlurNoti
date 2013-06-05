from Foundation import *
from AppKit import *
from PyObjCTools import NibClassBuilder, AppHelper

# load Growl.framework
myGrowlBundle=objc.loadBundle("GrowlApplicationBridge", globals(), bundle_path=objc.pathForFramework(u'./Growl.framework'))
    
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