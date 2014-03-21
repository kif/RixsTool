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
#
# Imports for GUI
#
from PyMca import PyMcaQt as qt
from PyQt4 import uic

#
# IMPORTS FROM RIXSTOOL
#   unique: In place removal of redundant elements in a sequence
#   FileContextMenu: Custom context menus for DirTree
#   AddFilesAction: Custom action in context menu
#   QDirListModel: Simple list model to manage directories
#
from RixsTool.Utils import unique as RixsUtilsUnique
from RixsTool.ContextMenu import FileContextMenu, AddFilesAction
from RixsTool.Models import QDirListModel

DEBUG = 1


class DirTree(qt.QTreeView):
    def __init__(self, parent):
        qt.QTreeView.__init__(self, parent)

        #
        # Model is qt.QFileSystemModel()
        #
        self.setModel(qt.QFileSystemModel())

        #
        # Set up monitor for the file system
        #
        self.watcher = qt.QFileSystemWatcher()
        self.watcher.fileChanged.connect(self.fileChanged)

        #
        # Context menu
        #
        self.setContextMenuPolicy(qt.Qt.DefaultContextMenu)
        if hasattr(parent, 'handleContextMenuAction'):
            self.callback = parent.handleContextMenuAction
        else:
            self.callback = None

    def fileChanged(self, **kw):
        # TODO: Implement auto update
        print('DirTree.fileChanged -- path:', kw)

    def updatePath(self, path):
        print('DirTree.updatePath -- called')
        model = self.model()
        model.setRootPath(path)
        newRoot = model.index(path)
        self.setRootIndex(newRoot)
        watcherDirs = self.watcher.directories()
        if len(watcherDirs) > 0:
            self.watcher.removePaths(watcherDirs)
        print('DirTree.updatePath -- watcherDirs:\n\t%s' % str(watcherDirs))
        self.watcher.addPath(path)

    def contextMenuEvent(self, event):
        print('DirTree.contextMenuEvent -- called')
        modelIndexList = self.selectedIndexes()
        RixsUtilsUnique(modelIndexList, "row")
        #modelIndexList = [self.indexAt(event.pos())]
        print('Length modelIndexList:', len(modelIndexList))

        model = self.model()
        fileInfoList = [model.fileInfo(idx) for idx in modelIndexList]

        if all([elem.isFile() for elem in fileInfoList]):
            menu = FileContextMenu(self)
            print('DirTree.contextMenuEvent -- All files!')
        else:
            print('DirTree.contextMenuEvent -- Not all files!')
            return
        menu.build()
        action = menu.exec_(event.globalPos())

        if action:
            if self.callback:
                self.callback(action, {'fileInfoList': fileInfoList})
            else:
                raise AttributeError("DirTree.contextMenuEvent -- callback not set")
        return

    def setModel(self, fsModel):
        if not isinstance(fsModel, qt.QFileSystemModel):
            raise ValueError('DirTree.setModel -- provided model must be of type QFileSystemModel')
        else:
            qt.QTreeView.setModel(self, fsModel)


class FileSystemBrowser(qt.QWidget):
    addSignal = qt.pyqtSignal(object)

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        #uic.loadUi('C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\filesystembrowser.ui', self)
        #uic.loadUi('/Users/tonn/GIT/RixsTool/RixsTool/ui/filesystembrowser.ui', self)
        uic.loadUi('/home/truter/lab/RixsTool/RixsTool/ui/filesystembrowser.ui', self)

        #
        # Set start directory to qt.QDir.home()
        #
        workingDirModel = QDirListModel(self)
        self.workingDirCB.setModel(workingDirModel)

        #
        # Init addDir- and closeDirButtons
        #
        self.closeDirButton.setEnabled(False)

        #
        # Connect
        #
        self.fsView.watcher.fileChanged.connect(self.handleFileChangedSignal)
        #self.fsView.watcher.directoryChanged.connect(self.handleFileChanged)
        self.workingDirCB.currentIndexChanged.connect(self.handleWorkingDirectoryChanged)

        self.addDirButton.clicked[()].connect(self.addDir)
        self.closeDirButton.clicked[()].connect(self.closeDir)

        # TODO: change startDir = qt.QDir.home()
        startDir = qt.QDir.home()
        #startDir = qt.QDir('/home/truter/lab/mock_folder/')
        self.fsView.updatePath(startDir.absolutePath())

    #
    # Handler functions for various user interaction:
    #   fileChangedSignal
    #   directoryChanged
    #   currentIndexChanged
    #
    def handleFileChangedSignal(self, **kw):
        print('FileSystemBrowser.handleFileChangedSignal -- kw: %s' % str(kw))
        pass

    def handleWorkingDirectoryChanged(self, **kw):
        print(kw)
        pass

    def handleContextMenuAction(self, obj, param=None):
        # Change to treeCallback and except qfileinfos directly
        if not param:
            param = {}
        if isinstance(obj, AddFilesAction):
            fileInfoList = param.get('fileInfoList', None)
            if fileInfoList:
                self.addSignal.emit(fileInfoList)
        print('FileSystemBrowser.handleContextMenuAction -- finished!')

    #
    # Adding/Removing working directories
    #
    def closeDir(self, safeClose=True):
        if safeClose:
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setWindowTitle('Close directory')
            msg.setText('Are you shure you want to close the current working directory?')
            msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
            if msg.exec_() == qt.QMessageBox.Cancel:
                if DEBUG == 1:
                    print('FileSystemBrowser.closeDir -- Abort')
                return
        currentIdx = self.workingDirCB.currentIndex()
        print('currentIdx:', currentIdx)
        model = self.workingDirCB.model()
        print('model.rowCount:',model.rowCount())
        print('len(model):',len(model))
        if model.rowCount() > 0:
            model.removeDirs(row=currentIdx,
                             count=1)
        if model.rowCount() <= 0:
            self.closeDirButton.setEnabled(False)
            self.workingDirCB.setCurrentIndex(-1)
        else:
            self.workingDirCB.setCurrentIndex(0)

    def addDir(self, path=None):
        """
        :param path: New directory to be added
        :type path: str

        Path is added to working directory combo box and set as new root directory in the view.
        """
        if path is None:
            startDir = self.workingDirCB.currentText()
            if len(startDir) <= 0:
                startDir = qt.QDir.home().absolutePath()
            path = qt.QFileDialog.getExistingDirectory(parent=self,
                                                       caption='Add directory..',
                                                       directory=startDir,
                                                       options=qt.QFileDialog.ShowDirsOnly)
        path = str(path)
        if len(path) <= 0:
            if DEBUG == 1:
                print('FileSystemBrowser.addDir -- Received empty path. Return.')
            return

        newIdx = self.workingDirCB.currentIndex() + 1
        model = self.workingDirCB.model()
        model.insertDirs(newIdx, [path])
        # Update ComboBox and TreeView
        self.workingDirCB.setCurrentIndex(newIdx)
        self.fsView.updatePath(path)
        if not self.closeDirButton.isEnabled():
            self.closeDirButton.setEnabled(True)

    #
    # File selection
    #
    def getSelectedFiles(self):
        # QTreeView.selectedIndexes returns list
        # [Row1Col1, Row1Col2, ..., Row2Col1, ...].
        # Hence, there is redundant information
        modelIdxList = self.fsView.selectedIndexes()
        # Reduce modelIdxList to unique row numbers
        seen = {}
        insertPos = 0
        for item in modelIdxList:
            if item.row() not in seen:
                seen[item.row()] = True
                modelIdxList[insertPos] = item
                insertPos += 1
        del modelIdxList[insertPos:]
        # Get QFileInfo from model indexes
        fsModel = self.fsView.model()
        infoList = [fsModel.fileInfo(idx) for idx in modelIdxList]
        if DEBUG == 1:
            for elem in infoList:
                print('\t', elem.absoluteFilePath())
        return infoList

    def addFiles(self):
        # TODO: remove me
        current = self.getSelectedFiles()
        self.addSignal.emit(current)

    def _handleWorkingDirectoryChanged(self, elem):
        if isinstance(elem, int):
            dirModel = self.workingDirCB.model()
            if len(dirModel) > 0:
                qdir = dirModel[elem]
            else:
                qdir = qt.QDir.home()
        else:
            qdir = qt.QDir(elem)
        self.fsView.updatePath(qdir.path())


class DummyNotifier(qt.QObject):
    @staticmethod
    def signalReceived(**kw):
        print('DummyNotifier.signal received -- kw:\n', str(kw))


def unitTest_FileSystemBrowser():
    app = qt.QApplication([])
    browser = FileSystemBrowser()
    browser.show()
    app.exec_()


if __name__ == '__main__':
    unitTest_FileSystemBrowser()