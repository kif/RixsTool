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
# Imports for GUI
from PyMca import PyMcaQt as qt
#from PyMca.widgets import ColormapDialog
#from PyMca import PyMcaFileDialogs # RETURNS '/' as seperator on windows!?
from PyMca import PyMcaDirs
from PyQt4 import uic

# Imports from RixsTool
from RixsTool.io import EdfInputReader
from RixsTool.io import InputReader

# Imports from os.path
from os.path import splitext as OsPathSplitext
from os.path import normpath as OsPathNormpath

from collections import OrderedDict
from RixsTool.datahandling import QDirListModel
from RixsTool.datahandling import RixsProject

DEBUG = 1

class AbstractToolWindow(qt.QDockWidget):
    acceptSignal = qt.pyqtSignal(object)
    editFinished = qt.pyqtSignal()
    editCancelled = qt.pyqtSignal()

    def __init__(self, uiPath=None, parent=None):
        super(AbstractToolWindow, self).__init__(parent)
        self._widget = qt.QWidget(parent)
        self._values = {}
        self.__uiLoaded = False
        self.__uiPath = uiPath

    def finished(self):
        if DEBUG == 1:
            print("AbstractToolWindow.finished -- To be implemented")
        self.editFinished.emit()
        self.destroy(bool_destroyWindow=True,
                     bool_destroySubWindows=True)

    def hasUI(self):
        return self.__uiLoaded

    def setUI(self, uiPath=None):
        if uiPath is None:
            uiPath = self.__uiPath
        try:
            uic.loadUi(uiPath, self._widget)
            self.__uiLoaded = True
        except FileNotFoundError:
            if DEBUG == 1:
                print('Something went wrong while reading the ui file')
            self.__uiLoaded = False
            FileNotFoundError("AbstractToolWindow.setUI -- failed to find ui-file: '%s'"%uiPath)
        if self.widget() is None:
            self.setWidget(self._widget)

    def getValues(self):
        ddict = {}
        sortedKeys = sorted(self._values.keys())
        for key in sortedKeys:
            obj = self._values[key]
            if isinstance(obj, qt.QPlainTextEdit) or\
               isinstance(obj, qt.QTextEdit):
                val = obj.getPlainText()
            elif isinstance(obj, qt.QLineEdit):
                val = obj.text()
            elif isinstance(obj, qt.QCheckBox) or\
                 isinstance(obj, qt.QRadioButton):
                val = obj.checkState()
            elif isinstance(obj, qt.QComboBox):
                val = obj.currentText()
            elif isinstance(obj, qt.QAbstractSlider) or\
                 isinstance(obj, qt.QSpinBox):
                val = obj.value()
            else:
                val = None
            ddict[key] = val
        return ddict

    def setValues(self, ddict):
        success = True
        for key, val in ddict.items:
            obj = self._values[key]
            if isinstance(obj, qt.QPlainTextEdit) or\
               isinstance(obj, qt.QTextEdit):
                obj.setPlainText(val)
            elif isinstance(obj, qt.QLineEdit):
                obj.setText(val)
            elif isinstance(obj, qt.QCheckBox) or\
                 isinstance(obj, qt.QRadioButton):
                obj.setCheckState(val)
            elif isinstance(obj, qt.QComboBox):
                idx = obj.findText(val)
                obj.setCurrentIndex(idx)
            elif isinstance(obj, qt.QAbstractSlider) or\
                 isinstance(obj, qt.QSpinBox):
                obj.setValue(val)
            else:
                if DEBUG == 1:
                    print("AbstractToolWindow.setValues -- Could not set value for key '%s'"%str(key))
                # TODO: Raise Exception here?
                success = False
        return success

class BandPassFilterWindow(AbstractToolWindow):
    def __init__(self, parent=None):
        uiPath = 'C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\bandpassfilter.ui'
        super(BandPassFilterWindow, self).__init__(uiPath=uiPath,
                                                   parent=parent)
        self.setUI()

        self._values = {
            'upper' : self._widget.upperThreshold,
            'lower' : self._widget.lowerThreshold,
            'offset' : self._widget.offsetValue
        }

        #
        # Connects
        #
        self._widget.buttonApply.clicked.connect(self._handleApply)

    def _handleApply(self):
        self.acceptSignal.emit(self.getValues())

class DirTree(qt.QTreeView):
    def __init__(self, parent=None):
        super(DirTree, self).__init__(parent)
        self.setContextMenuPolicy(qt.Qt.DefaultContextMenu)
        self.__contextMenu = None
        self.watcher = qt.QFileSystemWatcher()
        self.setModel(qt.QFileSystemModel())
        self.watcher.fileChanged.connect(self.fileChanged)

    def fileChanged(self, path):
        # TODO: Implement auto update
        print('DirTree.fileChanged -- path:',path)

    def setContextMenu(self, menu):
        """
        :param menu: Contains
        :type menu: QMenu
        Sets the context menu of the DirTree that is triggered
        by a right click on the widget.
        """
        self.__contextMenu = menu

    def updatePath(self, path):
        model = self.model()
        model.setRootPath(path)
        newRoot = model.index(path)
        self.setRootIndex(newRoot)
        watcherDirs = self.watcher.directories()
        if len(watcherDirs) > 0:
            self.watcher.removePaths(watcherDirs)
        self.watcher.addPath(path)

    def contextMenuEvent(self, event):
        print('DirTree.contextMenuEvent called')
        if self.__contextMenu:
            self.__contextMenu.exec_(event.globalPos())

    def setModel(self, fsModel):
        if not isinstance(fsModel, qt.QFileSystemModel):
            raise ValueError('DirTree.setModel -- provided model must be of type QFileSystemModel')
        else:
            qt.QTreeView.setModel(self, fsModel)

class FileSystemBrowser(qt.QWidget):
    addSignal = qt.pyqtSignal(object)

    def __init__(self, parent=None, project=None):
        qt.QWidget.__init__(self, parent)
        uic.loadUi('C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\filesystembrowser.ui', self)

        if project is None:
            self.project = RixsProject()
        else:
            self.project = project

        # Set default working directory
        self.workingDirCB.setModel(QDirListModel(self))

        #
        # Connect
        #
        self.fsView.watcher.fileChanged.connect(self._handleFileChanged)
        self.fsView.watcher.directoryChanged.connect(self._handleFileChanged)
        self.workingDirCB.currentIndexChanged.connect(self._handleWorkingDirectoryChanged)

        #
        # Init and connect context menu for DirTree
        #
        treeContextMenu = qt.QMenu(title='File System Context Menu',
                                   parent=self)
        addFilesAction = qt.QAction('Add to session', self)
        addFilesAction.triggered.connect(self.addFiles)
        treeContextMenu.addAction(addFilesAction)
        self.fsView.setContextMenu(treeContextMenu)

    def setDir(self, path):
        """
        :param path: Path is added to working directory combo box
        :type path: str
        """
        model = self.workingDirCB.model()
        #self.workingDir = qt.QDir('C:\\Users\\tonn\\lab\\rixs\\Images')
        #if not self.workingDir.isAbsolute():
        #    self.workingDir.makeAbsolute()
        #self.fsView.updatePath(self.workingDir.path())

    def setProject(self, newProject):
        # Make sure to disconnect addSignal
        if self.project is not None:
            self.addSignal.disconnect(self.project)
            if DEBUG == 1:
                print('FileSystemBrowser.setProject -- Disconnected addSignal from current project')
        newDir = qt.QDir.absoluteFilePath(newProject.workingDir)
        if DEBUG == 1:
            print('FileSystemBrowser.setProject -- Setting project. New WD:', newDir)
        #self.fsView.updatePath(newDir)
        self.setDir(newDir)
        self.addSignal.connect(newProject.addFileInfoList)
        self.project = newProject

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
                print('\t',elem.absoluteFilePath())
        return infoList

    def addFiles(self):
        current = self.getSelectedFiles()
        self.addSignal.emit(current)

    def _handleWorkingDirectoryChanged(self, elem):
        if isinstance(elem, int):
            dirModel = self.workingDirCB.model()
            qdir = dirModel[elem]
        else:
            qdir = qt.QDir(elem)
        self.fsView.updatePath(qdir.path())

    def _handleActivated(self, modelIdx):
        print('FileSystemBrowser.activated')
        return

    def _handleMouseClick(self, foo):
        print('FileSystemBrowser._handleLeftClick')
        return

    def _handleRightClick(self, foo):
        print('FileSystemBrowser._handleLeftClick')
        return

    def _handleDoubleClick(self, foo):
        print('FileSystemBrowser._handleDoubleClick')
        return

    def _handleFileChanged(self, filePath):
        print('FileSystemBrowser._handleFileChanged called: %s'%str(filePath))
        return

    def _handleDirectoryChanged(self, dirPath):
        print('FileSystemBrowser._handleDirectoryChanged called: %s'%str(dirPath))
        return

class DummyNotifier(qt.QObject):
    def signalReceived(self, val=None):
        print('DummyNotifier.signal received -- kw:\n',str(val))

if __name__ == '__main__':
    app = qt.QApplication([])
    #win = BandPassFilterWindow()
    notifier = DummyNotifier()
    win = FileSystemBrowser()
    if isinstance(win, AbstractToolWindow):
        win.acceptSignal.connect(notifier.signalReceived)
    win.show()
    app.exec_()