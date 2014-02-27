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
from RixsTool.RixsUtils import unique as RixsUtilsUnique
from RixsTool.calculations import *
import RixsTool.io as IO
from PyMca import PyMcaQt as qt
from os.path import split as OsPathSplit
from os import access as OsAccess
from os import R_OK as OS_R_OK
from os import listdir as OsListDir
from os.path import isfile as OsPathIsFile, join as OsPathJoin
from os.path import normpath as OsPathNormpath


DEBUG == 1

class RixsProject(qt.QObject):
    __IMAGES = 'images'
    __SPECTRA = 'spectra'
    __ANALYSIS = 'analysis'

    __SPEC_TYPE = 'spec'
    __EDF_TYPE = 'edf'
    __RAW_TYPE = 'raw'

    defaultWorkingDirectory = 'C:\\Users\\tonn\\lab\\rixs\\Images'

    def __init__(self, workingDir=''):
        super(RixsProject, self).__init__()
        #
        # Set working directory
        #
        if len(workingDir) <= 0:
            self.workingDir = qt.QDir(self.defaultWorkingDirectory)
        else:
            self.workingDir = qt.QDir(workingDir)

        #
        # Spec readers
        #
        # TODO: Have readers for specfiles..
        self.specReaders = {
            self.__SPEC_TYPE : None
        }

        #
        # Image readers
        #
        self.imageReaders = {
            self.__EDF_TYPE : IO.EdfInputReader(),
            self.__RAW_TYPE : IO.RawTextInputReader()
        }

    def readImage(self, filename, fileType):
        try:
            reader = self.imageReaders[fileType]
        except KeyError:
            return False
        reader.append(filename)
        return True

    def readImages(self, filelist, fileType):
        try:
            reader = self.imageReaders[fileType]
        except KeyError:
            return False
        reader.refresh(filelist)
        return True

    def getImage(self, reader, key, index):
        #if key not in reader.getFileList():
        #    raise IndexError("RixsProject.getImage -- Key '%s' not found "%key)
        return reader['Images']

    def addFileInfoList(self, fileInfoList):
        if DEBUG == 1:
            print('RixsProject.addFileInfoList -- received fileInfoList (len: %d)'%\
                  len(fileInfoList))
        for info in fileInfoList:
            name = OsPathNormpath(info.completeSuffix())
            suffix = str(info.completeSuffix())
            if suffix.lower not in self.imageReaders.keys():
                raise ValueError("Unknown filetype: '%s'"%suffix)
            reader = self.imageReaders[suffix]
            reader.append(name)
            print(reader)

    def getFileNames(self):
        llist = [reader.getFileList() for reader in self.imageReaders.values()]
        return sum(llist, [])

class QDirListModel(qt.QAbstractListModel):
    def __init__(self, parent=None):
        super(QDirListModel, self).__init__(parent)
        self.__directoryList = []

    def __getitem__(self, idx):
        """
        :param idx: Return idx-th element in the model
        :type idx: int
        """
        return self.__directoryList[idx]

    def flags(self, modelIndex):
        if modelIndex.isValid():
            return qt.Qt.ItemIsSelectable | qt.Qt.ItemIsEditable | qt.Qt.ItemIsEnabled
        else:
            if DEBUG == 1:
                print('QDirListModel.flags -- received invalid modelIndex')
            return 0

    def __len__(self):
        return len(self.__directoryList)

    def rowCount(self, modelIndex = qt.QModelIndex()):
        return len(self.__directoryList)

    def insertDirs(self, row, directoryList):
        """
        :param row: Determines after which row the items are inserted
        :type row: int
        :param directoryList: Carries the new legend information
        :type directoryList: list of either strings or QDirs
        """
        modelIndex = self.createIndex(row,0)
        count = len(directoryList)
        qt.QAbstractListModel.beginInsertRows(self,
                                              modelIndex,
                                              row,
                                              row+count)
        head = self.__directoryList[0:row]
        tail = self.__directoryList[row:]
        new  = [qt.QDir()] * count
        for idx, elem in enumerate(directoryList):
            if isinstance(elem, str):
                newDir = qt.QDir(elem)
            elif isinstance(elem, qt.QDir):
                # Call copy ctor
                newDir = qt.QDir(elem)
            else:
                if DEBUG == 1:
                    print('QDirListModel.insertDirs -- Element %d: Neither instance of str nor QDir'%idx)
                continue
            new[idx] = newDir
        self.__directoryList = head + new + tail
        # Reduce self.__directoryList to unique elements..
        RixsUtilsUnique(self.__directoryList, 'absolutePath')
        qt.QAbstractListModel.endInsertRows(self)
        return True

    def insertRows(self, row, count, modelIndex = qt.QModelIndex()):
        raise NotImplementedError('Use LegendModel.insertLegendList instead')

    def removeDirs(self, row, count, modelIndex = qt.QModelIndex()):
        length = len(self.__directoryList)
        if length == 0:
            # Nothing to do..
            return True
        if row < 0 or row >= length:
            raise IndexError('Index out of range -- '
                            +'idx: %d, len: %d'%(row, length))
        if count == 0:
            return False
        qt.QAbstractListModel.beginRemoveRows(self,
                                              modelIndex,
                                              row,
                                              row+count)
        del(self.__directoryList[row:row+count])
        qt.QAbstractListModel.endRemoveRows(self)
        return True

    def removeRows(self, row, count, modelIndex = qt.QModelIndex()):
        raise NotImplementedError('QDirListModel.removeRows -- Not implemented, use QDirListModel.removeDirs instead')

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

def unitTest_QDirListModel():
    inp = ['foo/dir','bar\\dir','baz']
    listModel = QDirListModel()
    listModel.insertDirs(0, inp)

    print('datahandling.unitTest_QDirListModel -- Input string list:', str(inp))

    first = (len(listModel) == 3) and (listModel.rowCount() == 3)
    second, third = True, True
    for idx in range(len(listModel)):
        modelIndex = listModel.createIndex(idx, 0)
        displayRole = listModel.data(modelIndex, qt.Qt.DisplayRole)
        flag = listModel.flags(modelIndex)
        qdir = listModel[idx]

        second &= isinstance(displayRole, str)
        third  &= isinstance(qdir, qt.QDir)

        print('\t%d: %s\t%s\t%s\t%s'%\
              (idx, str(displayRole), type(displayRole), int(flag), str(qdir)))

    if first and second and third:
        print('datahandling.unitTest_QDirListModel -- Success')
        return True
    else:
        print('datahandling.unitTest_QDirListModel -- Failure')
        return False


if __name__ == '__main__':
    unitTest_QDirListModel()
    #rixsImageDir = 'C:\\Users\\tonn\\lab\\rixs\\Images'
    #proj = RixsProject()
    #edfImageList = [OsPathJoin(rixsImageDir,fn) for fn in OsListDir(rixsImageDir)\
    #             if OsPathIsFile(OsPathJoin(rixsImageDir,fn))][1:]
    #proj.readImages(edfImageList, 'edf')