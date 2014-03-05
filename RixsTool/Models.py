#/*##########################################################################
# Copyright (C) 2014 European Synchrotron Radiation Facility
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

from RixsTool.Utils import unique as RixsUtilsUnique
#from RixsTool.datahandling import
from PyMca import PyMcaQt as qt

from os.path import splitext as OsPathSplitext
from os import walk as OsWalk

DEBUG = 1

class QContainerTreeModel(qt.QAbstractItemModel):
    __doc__ = """
    Structure of RixsProject.groups:

      +---- Ims --+---- Group0: All images per default
      |           |
    --+---- Sps   +---- Group1: empty
      |
      +---- Sts
    """

    def __init__(self, root, parent=None):
        super(QContainerTreeModel, self).__init__(parent)
        self.rootItem = root

    def getContainer(self, modelIndex):
        """
        :param modelIndex: Model index of a container in the model
        :type modelIndex: QModelIndex
        :returns: ItemContainer instance at modelIndex.
        :rtype: ItemContainer
        """
        if modelIndex.isValid():
            item = modelIndex.internalPointer()
            if item:
                return item
        return self.rootItem

    def data(self, modelIndex, role=qt.Qt.DisplayRole):
        """
        :param modelIndex: Model index of a container in the model
        :type modelIndex: QModelIndex
        :param role: Determines which data is extracted from the container
        :type role: Qt.ItemDataRole (int)
        :returns: Requested data or None
        :rtype: str, QSize, None, ...
        """
        if not modelIndex.isValid():
            return None
        item = self.getContainer(modelIndex)
        if role == qt.Qt.DisplayRole:
            return str(item.data(modelIndex.column()))

    def rowCount(self, parentIndex=qt.QModelIndex(), *args, **kwargs):
        """
        :param modelIndex: Model index of a container in the model
        :type modelIndex: QModelIndex
        :returns: Number of rows
        :rtype: int
        """
        parent = self.getContainer(parentIndex)
        return parent.childCount()

    def columnCount(self, parentIndex=qt.QModelIndex(), *args, **kwargs):
        """
        :param modelIndex: Model index of a container in the model
        :type modelIndex: QModelIndex
        :returns: Number of columns (i.e. attributes) shown
        :rtype: int
        """
        parent = self.getContainer(parentIndex)
        #return self.rootItem.columnCount()
        return parent.columnCount()

    def flags(self, modelIndex):
        """
        :param modelIndex: Model index of a container in the model
        :type modelIndex: QModelIndex
        :returns: Flag indicating how the view can interact with the model
        :rtype: Qt.ItemFlag
        """
        if modelIndex.isValid():
            return qt.Qt.ItemIsEditable | qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable
        else:
            return 0

    def index(self, row, col, parentIndex=qt.QModelIndex(), *args, **kwargs):
        """
        :param row: Row in the table of parentIndex
        :type row: int
        :param col: Column in the table of parentIndex
        :type col: int
        :param parentIndex: Determines the table
        :type parentIndex: QModelIndex
        :returns: (Possibly invalid) model index of a container in the model. Invalid model indexes refer to the root
        :rtype: QModelIndex
        """
        if parentIndex.isValid() and parentIndex.column() > 0:
            return qt.QModelIndex()
        parent = self.getContainer(parentIndex)
        try:
            child = parent.children[row]
        except IndexError:
            return qt.QModelIndex()
        if child:
            return self.createIndex(row, col, child)
        else:
            return qt.QModelIndex()

    def parent(self, modelIndex=qt.QModelIndex()):
        """
        :param modelIndex: Model index of a container in the model
        :type modelIndex: QModelIndex
        :returns: (Possibly invalid) model index of the parent container. Invalid model indexes refer to the root
        :rtype: QModelIndex
        """
        if not modelIndex.isValid():
            return qt.QModelIndex()

        child = self.getContainer(modelIndex)
        parent = child.parent

        if parent == self.rootItem:
            return qt.QModelIndex()

        return self.createIndex(parent.childNumber(), 0, parent)

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
    unitTest_RixsProjectModel()