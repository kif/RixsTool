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
from PyMca import PyMcaDirs
from PyQt4 import uic

# Imports from RixsTool
from RixsTool.IO import EdfReader
from RixsTool.IO import InputReader
from RixsTool.window import BandPassFilterWindow

# Imports from os.path
from os.path import splitext as OsPathSplitExt
from os.path import normpath as OsPathNormpath

DEBUG = 1

class RIXSMainWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)
        #uic.loadUi('C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\mainwindow.ui', self)
        uic.loadUi('/Users/tonn/GIT/RixsTool/RixsTool/ui/mainwindow.ui', self)
        self.connectActions()

        self.filterWidget = None

        self.projectDict = {}

    def _handleAddSignal(self, fileInfoList):
        fileNames = [OsPathNormpath(elem.absoluteFilePath()) for elem in fileInfoList]
        current = self.projectList['Foo Project']
        current.readImages(fileNames, 'edf')
        imList = current.getImage(reader=current.imageReaders['edf'],
                                  key='foo',
                                  index=0)
        for im in imList:
            print(im[0].shape)
            self.imageView.addImage(im[0])
        #print('RIXSMainWindow._handleAddSignal -- Received addSignal:\n\t',fileNames)

    def connectActions(self):
        actionList = [(self.openImagesAction, self.openImages),
                      (self.saveAnalysisAction, self.saveAnalysis),
                      (self.histogramAction, self.showHistogram),
                      (self.filterAction, self.openFilterTool)]
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
            reader = EdfReader()
        else:
            reader = InputReader()
        reader.refresh(names)
        #for idx, im in enumerate(flatten(reader['Image'])):
        for idx, im in enumerate(reader['Images']):
            self.imageView.addImage(im)
            print('Added image:',idx,' ',type(im))

    def openFilterTool(self):
        if self.tabWidget.currentWidget() is not self.imageView:
            self.tabWidget.setCurrentWidget(self.imageView)
        if self.filterWidget is None:
            self.filterWidget = BandPassFilterWindow()
        w = self.centerWidget.width()
        h = self.centerWidget.height()
        if w > (1.25 * h):
            self.imageView.addDockWidget(qt.Qt.RightDockWidgetArea,
                                         self.filterWidget)
        else:
            self.imageView.addDockWidget(qt.Qt.BottomDockWidgetArea,
                                         self.filterWidget)

    def saveAnalysis(self):
        print('MainWindow -- saveAnalysis: to be implemented')

    def showHistogram(self):
        print('MainWindow -- showHistogram: to be implemented')

class DummyNotifier(qt.QObject):
    def signalReceived(self, val=None):
        print('DummyNotifier.signal received -- kw:\n',str(val))

if __name__ == '__main__':
    app = qt.QApplication([])
    win = RIXSMainWindow()
    win.show()
    app.exec_()