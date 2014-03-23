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
from RixsTool.widgets.ToolWindows import BandPassFilterWindow, BandPassID32Window, ImageAlignmenWindow

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
from RixsTool.Models import ProjectModel
from RixsTool.Items import SpecItem, ScanItem, ImageItem
from RixsTool.Operations import Filter

# IMPORT FROM PyMca
from PyMca.widgets import MaskImageWidget

# For Debuggin purposes
from RixsTool.datahandling import unitTest_RixsProject

import numpy, platform

# Imports from os.path
from os.path import splitext as OsPathSplitExt

DEBUG = 1
PLATFORM = platform.system()


class RixsMaskImageWidget(MaskImageWidget.MaskImageWidget):
    def __init__(self, parent=None):
        MaskImageWidget.MaskImageWidget.__init__(
            self,
            parent=parent,
            rgbwidget=None,
            selection=True,
            colormap=True,  # Shows ColorMapDialog
            imageicons=True,
            standalonesave=False,  # No save for image..
            usetab=False,  # Inserts MaskImageWidget into a new QTabWidget
            profileselection=True,
            scanwindow=None,
            aspect=True,
            polygon=False
        )

        self.dockWidgetArea = self.graphWidget.graph.dockWidgetArea

        self.graphWidget.colormapToolButton.clicked.connect(self.dummySlot)

    def addImage(self, data,
                 legend=None,
                 info=None,
                 replace=True,
                 replot=True,
                 xScale=None,
                 yScale=None,
                 z=0,
                 selectable=False,
                 draggable=False,
                 colormap=None, **kw):

        #
        # Use plotWindow.addImage to display the image in the plotting utility
        #
        plotWindow = self.graphWidget.graph #.addImage(
        plotWindow.addImage(
            data,
            legend=None,
            info=None,
            replace=True,  # Always replace existing images
            replot=True,
            xScale=None,
            yScale=None,
            z=0,
            selectable=False,
            draggable=False,
            colormap=None,
            **kw
        )

        #
        # Set as image data to allow masking, color mapping, ..
        #
        self.setImageData(
            data=data,
            clearmask=False,
            xScale=None,
            yScale=None
        )

    def addDockWidget(self, area, widget, orientation=qt.Qt.Vertical):
        self.graphWidget.graph.addDockWidget(area, widget, orientation)

    def dummySlot(self):
        print('RixsMaskImageWidget.dummySlot -- something happened!')


class RIXSMainWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        if PLATFORM == 'Linux':
            uic.loadUi('/home/truter/lab/RixsTool/RixsTool/ui/mainwindow.ui', self)
        elif PLATFORM == 'Windows':
            uic.loadUi('C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\mainwindow.ui', self)
        elif PLATFORM == 'Darwin':
            uic.loadUi('/Users/tonn/GIT/RixsTool/RixsTool/ui/mainwindow_imageView.ui', self)
        else:
            raise OSError('RIXSMainWindow.__init__ -- Unknown system type')

        #
        # Set up MaskImageWidget separately
        #
        #self.imageView = MaskImageWidget.MaskImageWidget(
        #    parent=self,
        #    rgbwidget=None,
        #    selection=True,
        #    colormap=True,  # Shows ColorMapDialog
        #    imageicons=True,
        #    standalonesave=False,  # No save for image..
        #    usetab=False,  # Inserts MaskImageWidget into a new QTabWidget
        #    profileselection=True,
        #    scanwindow=None,
        #    aspect=True,
        #    polygon=False
        #)
        #if self.__useTab:
        #    self.mainLayout.addWidget(self.mainTab)
        #else:
        #    self.mainLayout.addWidget(self.graphWidget)
        self.imageView.sigMaskImageWidgetSignal.connect(self.handleMaskImageSignal)

        self.connectActions()

        print('RIXSMainWindow -- type(self.imageView) = %s' % str(type(self.imageView)))

        # TODO: Can be of type ProjectView...
        self.projectDict = {
            '<current>': None,
            '<default>': ProjectModel()
        }
        self.currentProject = self.setCurrentProject()
        # Connect is independent from the project (model)
        self.projectBrowser.showSignal.connect(self._handleShowSignal)

        #
        # FILTERS
        #
        self.filterDict = {
            'bandpass': BandPassFilterWindow(),
            'bandpassID32': BandPassID32Window()
        }
        self.filterWidget = None
        self.setCurrentFilter('bandpass')

        #
        # ALIGNMENT
        #
        self.alignmentWidget = ImageAlignmenWindow()
        self.alignmentWidget.valuesChangedSignal.connect(self.filterValuesChanged)
        self.addAlignmentFilter()

        #self.imageView.toggleLegendWidget()
        self.specView.toggleLegendWidget()

    def handleMaskImageSignal(self, ddict):
        print("RIXSMainWindow.handleMaskImageSignal -- ddict: %s" % str(ddict))

    def handleToolStateChangedSignal(self, state, tool):
        print("RIXSMainWindow.handleToolStateChangedSignal -- state: %d" % state)
        print("\t%s" % str(tool))

    def setCurrentFilter(self, key):
        if self.filterWidget:
            #
            # There is an acitve filter, disconnect its actions
            #
            self.filterWidget.valuesChangedSignal.disconnect(self.filterValuesChanged)
            self.filterWidget.toolStateChangedSignal.connect(self.handleToolStateChangedSignal)
            dockWidgetArea = self.imageView.dockWidgetArea(self.filterWidget)
            self.filterWidget.hide()
        else:
            dockWidgetArea = qt.Qt.RightDockWidgetArea

        currentFilter = self.filterDict[key]
        currentFilter.valuesChangedSignal.connect(self.filterValuesChanged)
        currentFilter.toolStateChangedSignal.connect(self.handleToolStateChangedSignal)

        #
        # Positioning
        #
        self.imageView.addDockWidget(dockWidgetArea,
                                     currentFilter)
        currentFilter.show()
        self.filterWidget = currentFilter

    def addAlignmentFilter(self):
        self.imageView.addDockWidget(qt.Qt.RightDockWidgetArea,
                                     self.alignmentWidget)

    def filterValuesChanged(self, ddict):
        key = self.imageView.getActiveImage(just_legend=True)
        print("RIXSMainWindow.filterValuesChanged -- key: '%s'" % key)

        try:
            container = self.currentProject[key]
        except KeyError:
            print('RIXSMainWindow.filterValuesChanged -- Unable to find key')
            ids = self.currentProject.getIdDict()
            for key, value in ids.items():
                print("\t%s: %s" % (str(key), str(value)))
            return

        item = container.item()
        if item is None:
            print('RIXSMainWindow.filterValuesChanged -- Received None item')
            return
        else:
            print('RIXSMainWindow.filterValuesChanged -- Received item: %s' % str(item))

        #filtered = Filter.bandPassFilter(item.array, ddict)
        filtered = self.filterWidget.process(item.array, ddict)

        #self.imageView.addImage(
        self.addImage(
            data=filtered,
            legend=item.key(),
            replace=True
        )

    def addImage(self, data, legend, replace):
        print('RIXSMainWindow.addImage -- adding image..')
        #plotWindow = self.imageView.graphWidget.graph
        #plotWindow.addImage(
        self.imageView.addImage(
            data=data,
            legend=legend,
            replace=replace
        )

    def setCurrentProject(self, key='<default>'):
        #project = self.projectDict.get(key, None)
        model = self.projectDict['<default>']
        if not model:
            print('RIXSMainWindow.setCurrentProject -- project not found')
            return self.projectDict['<default>']
        else:
            model = ProjectModel()
        self.fileBrowser.addSignal.connect(model.addFileInfoList)
        #self.projectBrowser.showSignal.connect(self._handleShowSignal)
        self.projectBrowser.setModel(model)
        self.projectDict[key] = model
        return model

    def _handleShowSignal(self, itemList):
        for item in itemList:
            if isinstance(item, ImageItem):
                print('RIXSMainWindow._handleShowSignal -- Received ImageItem')
                #self.imageView.addImage(
                self.addImage(
                    data=item.array,
                    legend=item.key(),
                    replace=True
                )
            elif isinstance(item, ScanItem):
                print('RIXSMainWindow._handleShowSignal -- Received SpecItem')
                if hasattr(item, 'scale'):
                    scale = item.scale()
                else:
                    numberOfPoints = len(item.array)
                    scale = numpy.arange(numberOfPoints)  # TODO: Lift numpy dependency here
                # def addCurve(self, x, y, legend, info=None, replace=False, replot=True, **kw):
                self.specView.addCurve(
                    x=scale,
                    y=item.array,
                    legend=item.key(),
                    replace=False,
                    replot=True
                )
            elif isinstance(item, SpecItem):
                raise NotImplementedError('RIXSMainWindow._handleShowSignal -- Received ScanItem')
        print('RIXSMainWindow._handleShowSignal -- Done!')

    def connectActions(self):
        actionList = [(self.openImagesAction, self.openImages),
                      (self.saveAnalysisAction, self.saveAnalysis),
                      (self.histogramAction, self.showHistogram),
                      (self.bandPassFilterAction, self.openBandPassTool),
                      (self.bandPassFilterID32Action, self.openBandPassID32Tool)]
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

    def openBandPassTool(self):
        self.setCurrentFilter('bandpass')

    def openBandPassID32Tool(self):
        self.setCurrentFilter('bandpassID32')

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