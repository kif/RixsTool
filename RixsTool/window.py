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
from os.path import splitext as OsPathSplitExt

from RixsTool.datahandling import QDirListModel

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

class FileSystemBrowser(qt.QWidget):
    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        uic.loadUi('C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\filesystembrowser.ui', self)
        # Set working directory
        self.workingDirCB.setModel(QDirListModel(self))
        self.workingDir = qt.QDir('C:\\Users\\tonn\\lab\\rixs\\Images')
        if not self.workingDir.isAbsolute():
            self.workingDir.makeAbsolute()

        # Monitor the creation/changing of new files
        self.watcher = qt.QFileSystemWatcher()
        self.watcher.addPath(self.workingDir.path())

        # Set up the FS model
        self.model = qt.QFileSystemModel() # Performant alternative to QDirModel
        self.model.setRootPath(self.workingDir.path())

        # QTreeView created from ui-file
        self.fsView.setModel(self.model)
        self.fsView.setRootIndex(self.model.index(self.workingDir.path()))

        # Connect
        self.watcher.fileChanged.connect(self._handleFileChanged)
        self.watcher.directoryChanged.connect(self._handleFileChanged)
        self.workingDirCB.currentIndexChanged.connect(self._handleWorkingDirectoryChanged)

        self.connectActions()

    def _handleWorkingDirectoryChanged(self, elem):
        if isinstance(elem, int):
            dirModel = self.workingDirCB.model()
            #elem = dirModel.data(dirModel.createIndex(elem, 0),
            #                     qt.Qt.DisplayRole)
            qdir = dirModel[elem]
        else:
            qdir = qt.QDir(elem)
        print(qdir.path())
        self.model.setRootPath(qdir.path())
        self.fsView.setRootIndex(self.model.index(qdir.path()))
        # Clear paths of the watch
        self.watcher.removePaths(self.watcher.directories())
        self.watcher.addPath(qdir.path())

    def _handleFileChanged(self, filePath):
        print('FileSystemBrowser._handleFileChanged called: %s'%str(filePath))
        return

    def _handleDirectoryChanged(self, dirPath):
        print('FileSystemBrowser._handleDirectoryChanged called: %s'%str(dirPath))
        return

    def connectActions(self):
        print('FileSystemBrowser.connectActions to be implemented..')
        pass

class DummyNotifier(qt.QObject):
    def signalReceived(self, val=None):
        print('DummyNotifier.signal received -- kw:\n',str(val))

if __name__ == '__main__':
    app = qt.QApplication([])
    #win = BandPassFilterWindow()
    notifier = DummyNotifier()
    win = RIXSMainWindow()
    #win = FileSystemBrowser()
    if isinstance(win, AbstractToolWindow):
        win.acceptSignal.connect(notifier.signalReceived)
    win.show()
    app.exec_()