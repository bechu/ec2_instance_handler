# -*- coding: utf8 -*-
#!/usr/bin/python2

import sys
from PyQt4 import QtGui, QtCore
import boto.ec2
import os
import config

class SystemTrayIcon(QtGui.QSystemTrayIcon):

  def __init__(self, parent):
    icon = QtGui.QIcon(self.getPath() + "/aws.png")
    QtGui.QSystemTrayIcon.__init__(self, icon, parent)
    self.parent = parent
    self.instance_id = None
    self.action = ''
    self.updateMenu()

  def updateMenu(self):

    menu = QtGui.QMenu(self.parent)
    self.setContextMenu(menu)

    exitAction = menu.addAction("Exit")
    exitAction.triggered.connect(self.quit)

    self.mapper = QtCore.QSignalMapper()
    self.conn = boto.ec2.connect_to_region(config.REGION,
      aws_access_key_id=config.ACCESS_KEY,
      aws_secret_access_key=config.SECRET_ACCESS_KEY)
    reservations = self.conn.get_all_reservations()
    instances = []
    done = False
    for reservation in reservations:
      for instance in reservation.instances:
        instances.append(instance)
    self.instances = {}
    for instance in instances:
      if instance.id == self.instance_id:
        if instance.state == 'stopped' and self.action == 'stop':
          done = True
        if instance.state == 'running' and self.action == 'start':
          done = True
      if instance.state == 'stopped':
        action = menu.addAction("Start %s" % instance.key_name)
      elif instance.state == 'running':
        action = menu.addAction("Stop %s" % instance.key_name)
      self.mapper.setMapping(action, str(instance.id))
      self.instances[str(instance.id)] = instance
      action.triggered.connect(self.mapper.map)

    self.mapper.mapped['QString'].connect(self.instanceManage)
    if self.instance_id == None or done == True:
      self.setIcon(QtGui.QIcon(self.getPath() + "/aws.png"))
      self.instance_id = None
      QtCore.QTimer.singleShot(200000, self.updateMenu)
    else:
      QtCore.QTimer.singleShot(1000, self.updateMenu)


  def instanceManage(self, instance_name):
    instance = self.instances[str(instance_name)]
    if instance.state == 'stopped':
      self.conn.start_instances(instance.id)
      self.action = 'start'
    else:
      self.conn.stop_instances(instance.id)
      self.action = 'stop'
    self.setContextMenu(None)
    self.instance_id = instance.id
    self.setIcon(QtGui.QIcon(self.getPath() + "/aws_red.png"))
    QtCore.QTimer.singleShot(1000, self.updateMenu)

  def getPath(self):
    return os.path.dirname(os.path.abspath(__file__))

  def quit(self):
    QtGui.QApplication.quit()

def main():

  app = QtGui.QApplication(sys.argv)

  w = QtGui.QWidget()
  trayIcon = SystemTrayIcon(w)

  trayIcon.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()

