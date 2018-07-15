#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Notifications Ticker Dock
# For Freedesktop (Linux / BSD / +)
#
# Depends: PyQt5

# core
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication
import sys

# includes
from PyQt5.QtCore import pyqtSlot, Q_CLASSINFO, pyqtSignal, QObject
from PyQt5.QtDBus import QDBusConnection, QDBusMessage, QDBusInterface, QDBusAbstractAdaptor
from PyQt5.QtWidgets import QScrollArea, QHBoxLayout, QVBoxLayout, QLabel, QLayout, QPushButton, QToolTip
from PyQt5.QtGui import QCursor

# fx
from PyQt5.QtWidgets import  QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QPropertyAnimation

# other includes
from PyQt5.QtCore import QPoint, QPointF, QTimer
from PyQt5.QtGui import QPainter

# logging
from PyQt5.QtCore import QDate

#===========================================================================================================
# probably the wrong fuckin' way to do globals
summaries = []  # Summary titles
widgers = {}    # Group widget list
s = ""          # Summary unique-izer buffer

class NX_Notifs_Signals(QObject):
    getNotification = pyqtSignal(str,str,str,dict)
c = NX_Notifs_Signals()

class NX_Notifs_Dbus(QDBusAbstractAdaptor):
    Q_CLASSINFO("D-Bus Interface", "org.freedesktop.Notifications")

    def __init__(self, qobject):
        '''
            Starts the d-bus service to watch for any stray notifications
        '''
        super().__init__(qobject);

        sb = QDBusConnection.sessionBus()
        print   ("Notifs_Dbus: Registering notif. service…")
        try:    sb.registerService("org.freedesktop.Notifications")
        except: print("Couldn't register freedesktop notifications service!")

        print   ("Notifs_Dbus: Registering notif. object…")
        try:    sb.registerObject("/org/freedesktop/Notifications", qobject)
        except: print("Couldn't register freedesktop notifications object!")

        # match string
        m = "eavesdrop='true', interface='org.freedesktop.Notifications', member='Notify', type='method_call'"
        i = QDBusInterface("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus")
        i.call("AddMatch", m)

        print("Notifs_Dbus: Listener should start by now.")

    @pyqtSlot(QDBusMessage)
    def Notify(bus, msg):
        '''
            PyQt d-bus slot, called when a standard notification occurs.
            The arguments are currently passed in this order:
            <app_name>, <summary>, <body>, <hints>
        '''
        # 0 = app_name      0
        # 1 = app_id
        # 2 = icon
        # 3 = summary       1
        # 4 = body          2
        # 5 = actions
        # 6 = hints         3
        args = msg.arguments()
        print("Notifs_Dbus: Got notification!",args[0:6])
        print("Logging to /tmp/!")
        c.getNotification.emit(args[0],args[3],args[4],args[6]) # ping signal w/ notification args
#===========================================================================================================

class NX_Notifs(QMainWindow):
    def __init__(self):
        super().__init__();

        self.setWindowTitle("Notification Dock")

        self.setStyleSheet("""
            *{
                background:transparent;
                color:white;
                font-family: "Franklin Gothic Medium";
                font-size:11px;
                padding:0;
                margin:0;
            }
            QMainWindow, QDockWidget > * {
                background-color:#2E5286;
            }
            QPushButton{
                background:black;
                border-radius:10px;
            }
            QScrollBar:vertical{width:5px;}
            QScrollBar:horizontal{height:0px;}
            QScrollBar::handle:horizontal,QScrollBar::handle:vertical{
                background:white;border:1px solid black;width:4px;height:4px;
            }
        """)

        mgr = NX_Notifs_Dbus(self)                 # create notification handler
        print("Notifs: Initialized Notifs_Dbus.")

        c.getNotification.connect(self.onNotify)    # add widgets upon notification

        self.b = QScrollArea()  # root widget
        self.a = QWidget()

        notifContainer = QVBoxLayout()
        notifContainer.setSizeConstraint(QLayout.SetMinAndMaxSize) # fixes scrolling I think
        notifContainer.setContentsMargins(5,5,5,5)
        notifContainer.setAlignment(Qt.AlignTop)

        # self.b.horizontalScrollBar().setEnabled(False)
        self.b.setWidgetResizable(False)

        self.a.setLayout(notifContainer)
        self.b.setWidget(self.a)

        self.setCentralWidget(self.b)
        print("Notifs: Successfully intialized.")

    def onNotify(self, app_name,summary,body,hints):
        '''
            This also logs notifications to /tmp/notifs-<current sys.date>.txt
            if the file exists, append to file - otherwise create
        '''
        with open("/tmp/notifs-"+QDate.currentDate().toString("yyyyMMdd")+".txt","a") as log:
            log.write(summary+":\n")
            log.write(body+"\n")
            log.write("-------------------------------------------------------\n")

        d = NX_Notifs_Widget(summary,body,app_name)            # add notification widget
        self.a.layout().addWidget(d)
        self.a.resize(self.a.sizeHint())
        self.b.verticalScrollBar().setMaximum(self.b.verticalScrollBar().maximum()+d.height())
        self.b.verticalScrollBar().setValue(self.b.verticalScrollBar().maximum())
#===========================================================================================================

class NX_Notifs_Widget(QWidget):
    '''
        Notifications widget class, crap code ahead
        Supports notification grouping.
    '''
    def __init__(self, summary,body,tooltip):
        super().__init__()
        self.setMouseTracking(True)

        global s

        from random import random
        self.setCont = False                    # determines if notification is a continuation

        nw_layout = QVBoxLayout()
        nw_layout.setContentsMargins(0,0,0,0)
        self.setLayout(nw_layout)

        summaries.append(summary)

        if len(summaries) >= 2:
            if summaries[len(summaries)-1] == summaries[len(summaries)-2]:
                self.summary = ""   # XXX should this be here?
                widgers[s].append(self)                     # group notification appropriately
                self.setCont = True
            else:
                self.summary = summary
                s = summary + str(int(random()*1000000))    # assign unique summary number

                b = QWidget()
                x = QHBoxLayout()
                x.setContentsMargins(0,0,0,0)
                a = self.addXbutton(s)                      # s is the target group
                x.addWidget(a)
                y = MarqueeLabel(self.summary)              # scrolling summary
                x.addWidget(y)
                b.setLayout(x)
                self.layout().addWidget(b)

                widgers[s] = []                             # clear group list
                self.setCont = False                        # mark as header
        else:                                               # XXX same code copy-pasted from above
            self.summary = summary
            s = summary + str(int(random()*1000000))
            b = QWidget()
            x = QHBoxLayout()
            x.setContentsMargins(0,0,0,0)
            a = self.addXbutton(s)
            x.addWidget(a)
            y = MarqueeLabel(self.summary)
            x.addWidget(y)
            b.setLayout(x)
            self.layout().addWidget(b)
            widgers[s] = []
            self.setCont = False

        self.body = body
        self.tooltip = tooltip

        a = MarqueeLabel(self.body)                         # add notif. contents

        self.x = QGraphicsDropShadowEffect()                # add glow effect
        self.x.setBlurRadius(6)                             #
        self.x.setColor(QColor(255,255,255,255))            #
        self.x.setOffset(0)                                 #

        self.y = QPropertyAnimation(self.x, b"blurRadius")  # make text
        self.y.setDuration(1000)                            # "flash in"
        self.y.setStartValue(6)                             #
        self.y.setEndValue(0)                               #
        self.y.start()                                      #

        a.setGraphicsEffect(self.x)

        self.layout().addWidget(a)

    def mouseMoveEvent(self, e):
        QToolTip.showText(QCursor.pos(),"")
        QToolTip.showText(QCursor.pos(),self.tooltip)

    def deleteGroup(self):
        self.deleteLater()                                  # delete self
        for i in widgers[self.sender().toolTip()]:
            i.deleteLater()                                 # delete all group widgets
        widgers[self.sender().toolTip()].clear()            # clear deleted widgets
        summaries.clear()

    def addXbutton(self,s):
        a = QPushButton("x")
        a.clicked.connect(self.deleteGroup)
        a.setFixedSize(16,16)
        a.setToolTip(s)                                     # probably not a good idea
        return a
#===========================================================================================================

class MarqueeLabel(QLabel): # reminds me of a news ticker
    def __init__(self, text):
        super().__init__()
        self.width_px = 100
        self.pad = "   ⛒   "
        self.text_ = ""
        self.lentextwithpad = text+self.pad
        self.pos_ = 0
        self.x = 0

        self.setFixedSize(self.width_px,self.fontMetrics().height())

        self.actualTextWidth = self.fontMetrics().width(text)

        print(self.actualTextWidth,self.width())

        if (self.actualTextWidth <= self.width()):
            self.pad = ""
        else:
            self.pad = self.pad + text
        self.text_ = text + self.pad
        self.setText(self.text_)

        self.y = QTimer()
        self.y.start(3000)
        self.y.timeout.connect(self.e_run)

    def paintEvent(self,e):
        p = QPainter(self)
        p.setPen(p.pen());
        p.setFont(p.font());
        p.drawText(QPointF(self.x, (self.height() + self.fontMetrics().height()) / 2) + QPoint(2, -4),self.text_)

    def e_step(self):
        #self.pos_ = (self.pos_ + 1) % (len(self.actual_text_))
        #self.setText(self.actual_text_[self.pos_:self.pos_+10])
        if self.x > (self.fontMetrics().width(self.lentextwithpad))*-1:
            self.x = self.x - 1
        else:
            self.x = 0
        self.update()

    def e_run(self):
        if self.actualTextWidth > self.width():
            self.y.setInterval(33)
            self.y.timeout.connect(self.e_step)
            self.y.timeout.disconnect(self.e_run)
        else:
            self.y.stop()
#===========================================================================================================

def main(args):
    return 0
#===========================================================================================================

if __name__ == '__main__':
    a = QApplication(sys.argv)
    w = NX_Notifs()
    w.show()
    sys.exit(a.exec_())
