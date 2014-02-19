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

class RIXSMainWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)
        uic.loadUi('C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\mainwindow.ui', self)
        self.connectActions()

    def connectActions(self):
        actionList = [(self.openImagesAction, self.openImages),
                      (self.saveAnalysisAction, self.saveAnalysis),
                      (self.histogramAction, self.showHistogram)]
        for action, function in actionList:
            action.triggered[()].connect(function)
        print('All Actions connected..')

    def openImages(self):
        # Open file dialog
        names = qt.QFileDialog.getOpenFileNames(parent=self,
                                                caption='Load Image Files',
                                                directory=PyMcaDirs.inputDir,
                                                filter=('EDF Files (*.edf *.EDF);;'
                                                       +'Tiff Files (*.tiff *.TIFF);;'
                                                       +'All Files (*.*)'))
        if len(names) == 0:
            # Nothing to do..
            return
        fileName, fileType = OsPathSplitExt(names[-1])
        print('Filetype:',fileType)
        if fileType.lower() == '.edf':
            reader = EdfInputReader()
        else:
            reader = InputReader()
        reader.refresh(names)
        #for idx, im in enumerate(flatten(reader['Image'])):
        for idx, im in enumerate(reader['Images']):
            self.imageView.addImage(im)
            print('Added image:',idx,' ',type(im))

    def saveAnalysis(self):
        print('MainWindow -- saveAnalysis: to be implemented')

    def showHistogram(self):
        print('MainWindow -- showHistogram: to be implemented')

if __name__ == '__main__':
    app = qt.QApplication([])
    win = RIXSMainWindow()
    #win = FileSystemBrowser()
    win.show()
    app.exec_()