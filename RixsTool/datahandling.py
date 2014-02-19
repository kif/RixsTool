#/*##########################################################################
# Copyright (C) 2004-2014 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# This toolkit is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# PyMca is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# PyMca; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# PyMca follows the dual licensing model of Riverbank's PyQt and cannot be
# used as a free plugin for a non-free program.
#
# Please contact the ESRF industrial unit (industry@esrf.fr) if this license
# is a problem for you.
#############################################################################*/
__author__ = "Tonn Rueter - ESRF Data Analysis Unit"
from RixsTool.calculations import *
from PyMca import PyMcaQt as qt

DEBUG == 1

class QDirListModel(qt.QAbstractListModel):
    def __init__(self, parent=None):
        super(QDirListModel, self).__init__(parent)
        #self.__directoryList = []
        self.__directoryList = [qt.QDir('C:\\Users\\tonn\\lab\\rixs\\Images'),
                                qt.QDir('C:\\Users\\tonn\\lab\\rixs')]

    def __getitem__(self, idx):
        return self.__directoryList[idx]

    def rowCount(self, modelIndex):
        return len(self.__directoryList)

    def data(self, modelIndex, role):
        if modelIndex.isValid():
            idx = modelIndex.row()
        else:
            if DEBUG == 1:
                print('WorkingDirModel.data -- received invalid index')
            return None
        if idx >= len(self.__directoryList):
            raise IndexError('WorkingDirModel.data -- list index out of range')

        qdir = self.__directoryList[idx]
        if role == qt.Qt.DisplayRole:
            dirPath = qdir.absolutePath()
            return qt.QDir.toNativeSeparators(dirPath)
        else:
            if DEBUG == 1:
                #print('WorkingDirModel.data -- received invalid index')
                pass
            return None

class DataHandler(qt.QObject):
    sigRefresh = qt.pyqtSignal(str, int)

    def __init__(self, reader, parent=None):
        qt.QObject.__init__(self, parent)
        self.db = reader

    def ready(self):
        return not self.db.refreshing

    def getStatistics(self):
        if not self.ready():
            print('DataHandler.getStatistics -- not ready')
        for idx, key in enumerate(self.db.keys()):
            numImages = self.db['numImages'][idx]
            imageBlob = self.db['Images']
            for jdx in range(numImages):
                image = imageBlob[jdx]
                stats = Stats2D(key, jdx, self)
                self.sigRefresh.connect(stats.refresh)
                stats.basics(image)
        return True


class OpDispatcher(qt.QObject):
    sigOpFinished = qt.pyqtSignal(object)

    def __init__(self, key, idx, parent):
        qt.QObject.__init__(self, parent)


class DummyNotifiyer(qt.QObject):
    def __init__(self):
        qt.QObject.__init__(self)

    def signalReceived(self, ddict):
        obj = self.sender()
        print('Signal received:',ddict)
        #print('%s : %s'%(str(obj),str(kwargs)))