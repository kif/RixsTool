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
# Imports for GUI
from PyMca import PyMcaQt as qt
#from PyMca.widgets import ColormapDialog
#from PyMca import PyMcaFileDialogs # RETURNS '/' as seperator on windows!?
from PyQt4 import uic

# Imports from RixsTool
from RixsTool.ContextMenu import FileContextMenu, AddFilesAction

# Imports from os.path

from RixsTool.Models import QDirListModel
from RixsTool.Models import ProjectModel
from RixsTool.Utils import unique as RixsUtilsUnique
from RixsTool.ContextMenu import ProjectContextMenu, RemoveAction, RemoveItemAction, RemoveContainerAction,\
    ShowAction, ExpandAction, RenameAction
from RixsTool.datahandling import ItemContainer

DEBUG = 1


class AbstractToolTitleBar(qt.QWidget):

    #__uiPath = 'C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\abtractTitleToolBar.ui'
    #__uiPath = '/Users/tonn/GIT/RixsTool/RixsTool/ui/abtracttitletoolbar.ui'
    __uiPath = '/home/truter/lab/RixsTool/RixsTool/ui/abtracttitletoolbar.ui'

    def __init__(self, title):
        super(AbstractToolTitleBar, self).__init__()
        uic.loadUi(self.__uiPath, self)
        self.closeButton.setFlat(True)
        self.setWindowTitle(title)


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
        except FileNotFoundError:
            self.__uiLoaded = False
            raise FileNotFoundError("AbstractToolWindow.setUI -- failed to find ui-file: '%s'"%uiPath)
        self.__uiLoaded = True
        if self.widget() is None:
            self.setWidget(self._widget)
            #
            # Set the title bar
            #
            title = self.windowTitle()
            titleBar = AbstractToolTitleBar(title)
            self.setTitleBarWidget(titleBar)

    def getValues(self):
        ddict = {}
        sortedKeys = sorted(self._values.keys())
        for key in sortedKeys:
            obj = self._values[key]
            if isinstance(obj, qt.QPlainTextEdit) or isinstance(obj, qt.QTextEdit):
                val = obj.getPlainText()
            elif isinstance(obj, qt.QLineEdit):
                val = obj.text()
            elif isinstance(obj, qt.QCheckBox) or isinstance(obj, qt.QRadioButton):
                val = obj.checkState()
            elif isinstance(obj, qt.QComboBox):
                val = obj.currentText()
            elif isinstance(obj, qt.QAbstractSlider) or isinstance(obj, qt.QSpinBox):
                val = obj.value()
            else:
                val = None
            ddict[key] = val
        return ddict

    def setValues(self, ddict):
        success = True
        for key, val in ddict.items:
            obj = self._values[key]
            if isinstance(obj, qt.QPlainTextEdit) or isinstance(obj, qt.QTextEdit):
                obj.setPlainText(val)
            elif isinstance(obj, qt.QLineEdit):
                obj.setText(val)
            elif isinstance(obj, qt.QCheckBox) or isinstance(obj, qt.QRadioButton):
                obj.setCheckState(val)
            elif isinstance(obj, qt.QComboBox):
                idx = obj.findText(val)
                obj.setCurrentIndex(idx)
            elif isinstance(obj, qt.QAbstractSlider) or isinstance(obj, qt.QSpinBox):
                obj.setValue(val)
            else:
                if DEBUG == 1:
                    print("AbstractToolWindow.setValues -- Could not set value for key '%s'"%str(key))
                # TODO: Raise Exception here?
                success = False
        return success


class BandPassFilterWindow(AbstractToolWindow):
    def __init__(self, parent=None):
        #uiPath = 'C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\bandpassfilter.ui'
        #uiPath = '/Users/tonn/GIT/RixsTool/RixsTool/ui/bandpassfilter.ui'
        uiPath = '/home/truter/lab/RixsTool/RixsTool/ui/bandpassfilter.ui'
        super(BandPassFilterWindow, self).__init__(uiPath=uiPath,
                                                   parent=parent)
        self.setUI()

        self._values = {
            'upper': self._widget.upperThreshold,
            'lower': self._widget.lowerThreshold,
            'offset': self._widget.offsetValue
        }


class DirTree(qt.QTreeView):
    def __init__(self, parent):
        super(DirTree, self).__init__(parent)
        self.setContextMenuPolicy(qt.Qt.DefaultContextMenu)
        self.watcher = qt.QFileSystemWatcher()
        self.setModel(qt.QFileSystemModel())
        self.watcher.fileChanged.connect(self.fileChanged)
        if hasattr(parent, 'handleContextMenuAction'):
            self.callback = parent.handleContextMenuAction
        else:
            self.callback = None

    def fileChanged(self, path):
        # TODO: Implement auto update
        print('DirTree.fileChanged -- path:', path)

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


class ProjectView(qt.QTreeView):
    showSignal = qt.pyqtSignal(object)
    #showSpecSignal = qt.pyqtSignal(object)
    #showStackSignal = qt.pyqtSignal(object)

    def __init__(self, parent=None):
        super(ProjectView, self).__init__(parent)
        # TODO: Check if project is instance of RixsProject
        #self.project = project
        self.setSelectionMode(qt.QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(qt.Qt.DefaultContextMenu)
        #self.customContextMenuRequested.connect(self.contextMenuRequest)

    def _emitShowSignal(self, containerList):
        """
        :param list containerList: Contains items selected in the view

        Filters the containers in container list for such that contain a :py:class::`DataItem.DataItem` and emits
        a list of references to the items.
        """
        itemList = [ItemContainer.item(container) for container in filter(ItemContainer.hasItem, containerList)]
        for item in itemList:
            print('%s: %s %s' % (item.key(), str(item.shape()), type(item.array)))
        self.showSignal.emit(itemList)

    def contextMenuEvent(self, event):
        print('ProjectView.contextMenuEvent -- called')
        model = self.model()
        if not model:
            print('ProjectView.contextMenuEvent -- Model is none. Abort')
            return

        modelIndexList = self.selectedIndexes()
        RixsUtilsUnique(modelIndexList, "row")
        containerList = [model.containerAt(idx) for idx in modelIndexList]
        print('ProjectView.contextMenuEvent -- Received %d element(s)' % len(modelIndexList))
        for idx in modelIndexList:
            print('\t', idx.row(), idx.column())

        menu = ProjectContextMenu()
        if not any([container.hasItem() for container in containerList]):
            # No DataItem in selection, deactivate actions aimt at DataItems
            for action in menu.actionList:
                if isinstance(action, ShowAction) or isinstance(action, RemoveItemAction):
                    action.setEnabled(False)
        else:
            #if not any([container.childCount() for container in containerList]):
            # No containers in selection, deactivate actions aimt at containers
            for action in menu.actionList:
                if isinstance(action, ExpandAction)\
                        or isinstance(action, RemoveContainerAction)\
                        or isinstance(action, RenameAction):
                    action.setEnabled(False)
        menu.build()
        action = menu.exec_(event.globalPos())

        print("ProjectView.contextMenuEvent -- received action '%s'" % str(type(action)))
        if isinstance(action, RemoveAction):
            print("\tRemoving item(s)")
            for idx in modelIndexList:
                model.removeContainer(idx)
        elif isinstance(action, ShowAction):
            self._emitShowSignal(containerList)
        elif isinstance(action, RenameAction):
            # TODO: Call visualization here
            pass
        elif isinstance(action, ExpandAction):
            for modelIndex in modelIndexList:
                self.expand(modelIndex)
        else:
            return


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
        # TODO: change startDir = qt.QDir.home()
        startDir = qt.QDir('/home/truter/lab/mock_folder/')
        workingDirModel = QDirListModel(self)
        self.workingDirCB.setModel(workingDirModel)
        self.fsView.updatePath(startDir.absolutePath())

        #
        # Init addDir- and closeDirButtons
        #
        self.closeDirButton.setEnabled(False)

        #
        # Connect
        #
        self.fsView.watcher.fileChanged.connect(self._handleFileChanged)
        self.fsView.watcher.directoryChanged.connect(self._handleFileChanged)
        self.workingDirCB.currentIndexChanged.connect(self._handleWorkingDirectoryChanged)

        self.addDirButton.clicked[()].connect(self.addDir)
        self.closeDirButton.clicked[()].connect(self.closeDir)

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
        print('DummyNotifier.signal received -- kw:\n', str(val))


if __name__ == '__main__':
    from RixsTool.Models import ProjectModel

    directory = '/home/truter/lab/mock_folder'
    proj = ProjectModel()
    proj.crawl(directory)

    app = qt.QApplication([])
    #win = BandPassFilterWindow()
    #win = FileSystemBrowser()
    win = ProjectView()
    win.setModel(proj)

    notifier = DummyNotifier()
    if isinstance(win, AbstractToolWindow):
        win.acceptSignal.connect(notifier.signalReceived)
    elif isinstance(win, ProjectView):
        win.showSignal.connect(notifier.signalReceived)
    win.show()
    app.exec_()