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
from RixsTool.BandPassFilterWindow import BandPassFilterWindow
from RixsTool.Models import ProjectModel
from RixsTool.Items import SpecItem, ScanItem, ImageItem, StackItem

import numpy

# Imports from os.path
from os.path import splitext as OsPathSplitExt
from os.path import normpath as OsPathNormpath

DEBUG = 1


class RIXSMainWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)
        #uic.loadUi('C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\mainwindow.ui', self)
        #uic.loadUi('/Users/tonn/GIT/RixsTool/RixsTool/ui/mainwindow.ui', self)
        uic.loadUi('/home/truter/lab/RixsTool/RixsTool/ui/mainwindow.ui', self)
        self.connectActions()

        self.filterWidget = None
        self.openFilterTool()

        # TODO: Can be of type ProjectView...
        self.projectDict = {
            '<current>': None,
            '<default>': ProjectModel()
        }
        self.setCurrentProject()
        # Connect is independent from the project (model)
        self.projectBrowser.showSignal.connect(self._handleShowSignal)
        self.imageView.toggleLegendWidget()

    def setCurrentProject(self, key='<default>'):
        project = self.projectDict.get(key, None)
        if not project:
            print('RIXSMainWindow.setCurrentProject -- project not found')
            return
        model = ProjectModel()
        self.fileBrowser.addSignal.connect(model.addFileInfoList)
        #self.projectBrowser.showSignal.connect(self._handleShowSignal)
        self.projectBrowser.setModel(model)
        self.projectDict[key] = model

    def _handleShowSignal(self, itemList):
        for item in itemList:
            if isinstance(item, ImageItem):
                print('RIXSMainWindow._handleShowSignal -- Received ImageItem')
                self.imageView.addImage(
                    data=item.array,
                    legend=item.key(),
                    replace=True
                )
            elif isinstance(item, SpecItem):
                print('RIXSMainWindow._handleShowSignal -- Received SpecItem')
                if hasattr(item, 'scale'):
                    scale = item.scale
                else:
                    numberOfPoints = len(item.array)
                    scale = numpy.arange(numberOfPoints)  # TODO: Lift numpy dependency here
                # def addCurve(self, x, y, legend, info=None, replace=False, replot=True, **kw):
                self.specView.addPlot(
                    x=scale,
                    y=item.array,
                    legend=item.key(),
                    replace=False,
                    replot=True
                )
            elif isinstance(item, ScanItem):
                raise NotImplementedError('RIXSMainWindow._handleShowSignal -- Received ScanItem')
        print('RIXSMainWindow._handleShowSignal -- Done!')

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
                                                filter=('EDF Files (*.edf *.EDF);;' +
                                                        'Tiff Files (*.tiff *.TIFF);;' +
                                                        'All Files (*.*)'))
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
        print('DummyNotifier.signal received -- kw:\n', str(val))

if __name__ == '__main__':
    app = qt.QApplication([])
    win = RIXSMainWindow()
    win.show()
    app.exec_()