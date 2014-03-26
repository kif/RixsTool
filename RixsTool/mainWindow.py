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
from RixsTool.widgets.ToolWindows import BandPassFilterWindow, BandPassID32Window, ImageAlignmenWindow,\
    SumImageTool, EnergyScaleTool
from RixsTool.datahandling import ItemContainer

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
from RixsTool.Utils import unique as RixsUtilsUnique

# IMPORT FROM PyMca
from PyMca.widgets import MaskImageWidget

# For Debuggin purposes
from RixsTool.datahandling import unitTest_RixsProject

import numpy
import platform

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

        #
        # Data handling: only one image at a time is shown
        #
        self.currentImageItem = None

        #
        # ATTRIBUTES CONCERNING DATA MANIPULATION

        # FILTER: General preprocessing
        self.filterDict = {
            'bandpass': BandPassFilterWindow(),
            'bandpassID32': BandPassID32Window()
        }
        self.filterWidget = None
        self.setCurrentFilter('bandpass')

        # ALIGNMENT: Shift image along columns
        self.alignmentWidget = ImageAlignmenWindow()
        self.alignmentWidget.valuesChangedSignal.connect(self.toolWindowValuesChanged)
        self.showAlignmentFilter()

        # EXPORT: Sum up shifted images along an axis and export
        # the resulting spectra to the project
        self.exportWidget = SumImageTool()
        self.showExportWidget()

        #
        # ORDER: Operations must happen in fixed order
        #
        self.toolList = [
            self.filterWidget,
            self.alignmentWidget
        ]

        self.EnergyScaleTool = EnergyScaleTool()
        self.showEnergyScaleTool()

    #
    # METHODS CONCERNING DATA MANIPULATION TOOLS
    #
    def setCurrentFilter(self, key):
        if self.filterWidget:
            #
            # There is an acitve filter, disconnect its actions
            #
            self.filterWidget.valuesChangedSignal.disconnect(self.toolWindowValuesChanged)
            #self.filterWidget.toolStateChangedSignal.connect(self.handleToolStateChangedSignal)
            #self.filterWidget.toolStateChangedSignal.connect(self.toolWindowValuesChanged)
            dockWidgetArea = self.dockWidgetArea(self.filterWidget)
            self.filterWidget.hide()
        else:
            dockWidgetArea = qt.Qt.LeftDockWidgetArea

        currentFilter = self.filterDict[key]
        currentFilter.valuesChangedSignal.connect(self.toolWindowValuesChanged)
        #currentFilter.toolStateChangedSignal.connect(self.handleToolStateChangedSignal)
        #currentFilter.toolStateChangedSignal.connect(self.toolWindowValuesChanged)

        #
        # Positioning
        #
        self.addDockWidget(dockWidgetArea,
                           currentFilter)
        currentFilter.show()
        self.filterWidget = currentFilter

    def toolWindowValuesChanged(self, ddict):
        #key = self.imageView.getActiveImage(just_legend=True)

        #
        # AVOID RECALCULATION: If change occured in tool at position idx,
        # perform recalculation for self.toolList[idx:] ...
        #

        key = self.currentImageItem.key()
        imageData = self.currentImageItem.array

        for tool in self.toolList:
            if not tool.active():
                continue
            parameters = tool.getValues()
            imageData = tool.process(imageData, parameters)

        print("RIXSMainWindow.filterValuesChanged -- key: '%s'" % key)
        self.addImage(
            data=imageData,
            legend=key,
            replace=True
        )

    def getActiveImage(self, just_legend=True):
        plotWindow = self.graphWidget.graph
        legend = plotWindow.getActiveImage(just_legend=just_legend)
        if DEBUG >= 1:
            print("RixsMaskImageWidget.getActiveImage -- legend: '%s'" % legend)
        return legend

    def setImageItem(self, projectItem):
        self.currentImageItem = projectItem
        imageData = self.currentImageItem.array

        self.setImageData(
            data=imageData,
            clearmask=False,
            xScale=None,
            yScale=None
        )

        if DEBUG >= 1:
            print('RixsMaskImageWidget.setImageItem -- finished!')

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
        plotWindow = self.graphWidget.graph  #.addImage(
        plotWindow.addImage(
            data,
            legend=legend,
            info=info,
            replace=True,  # Always replace existing images
            replot=True,
            xScale=None,
            yScale=None,
            z=0,
            selectable=False,
            draggable=False,
            colormap=None,  # Temperature is default
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

        if DEBUG >= 1:
            print('RixsMaskImageWidget.addImage -- finished!')

    def showAlignmentFilter(self):
        self.addDockWidget(qt.Qt.LeftDockWidgetArea,
                           self.alignmentWidget)

    def showExportWidget(self):
        self.addDockWidget(qt.Qt.LeftDockWidgetArea,
                           self.exportWidget)

    def showEnergyScaleTool(self):
        self.addDockWidget(qt.Qt.LeftDockWidgetArea,
                           self.energyScaleTool)

    def addDockWidget(self, area, widget, orientation=qt.Qt.Vertical):
        self.graphWidget.graph.addDockWidget(area, widget, orientation)

    def dummySlot(self):
        print('RixsMaskImageWidget.dummySlot -- something happened!')


class RIXSMainWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)

        if PLATFORM == 'Linux':
            uic.loadUi('/home/truter/lab/RixsTool/RixsTool/ui/mainwindow_imageView.ui', self)
        elif PLATFORM == 'Windows':
            uic.loadUi('C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\ui\\mainwindow_imageView.ui', self)
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
        #self.filterDict = {
        #    'bandpass': BandPassFilterWindow(),
        #    'bandpassID32': BandPassID32Window()
        #}
        #self.filterWidget = None
        #self.setCurrentFilter('bandpass')

        #
        # ALIGNMENT
        #
        #self.alignmentWidget = ImageAlignmenWindow()
        #self.alignmentWidget.valuesChangedSignal.connect(self.filterValuesChanged)
        #self.showAlignmentFilter()

        #self.imageView.toggleLegendWidget()
        #self.specView.toggleLegendWidget()

        #
        # INTEGRATION
        #
        self.imageView.exportWidget.exportSelectedSignal.connect(self.exportSelectedImage)
        self.imageView.exportWidget.exportCurrentSignal.connect(self.exportCurrentImage)

        #
        # ENERGY SCALE
        #
        self.imageView.energyScaleTool.energyScaleSignal.connect(self.setEnergyScale)


    def setEnergyScale(self):
        scale = self.imageView.energyScaleTool.energyScale()
        print('RIXSMainWindow.setEnergyScale -- scale: %s' % str(scale))

    def exportSelectedImage(self):
        #items = self.projectBrowser.selectedItems()
        items = self.projectBrowser.selectedContainers()
        self.exportingImages(items)

    def exportCurrentImage(self):
        #item = self.imageView.currentImageItem
        imageItem = self.imageView.currentImageItem
        if not imageItem:
            return
        try:
            container = self.currentProject[imageItem.key()]
        except KeyError:
            print('RIXSMainWindow.exportCurrentImage -- Image not found in project!')
        #if not container:
            return
        self.exportingImages([container])

    def exportingImages(self, itemContainerList):
        #def imageToSpectrum(self, imageItemList):
        print('ProjectView.exportingImages -- Received %d item' % len(itemContainerList))
        toolList = self.imageView.toolList
        exportWidget = self.imageView.exportWidget
        specContainer = self.currentProject['Spectra']

        for container in filter(ItemContainer.hasItem, itemContainerList):
            if container in self.currentProject:
                item = container.item()
                data = item.array

                print('ProjectView.exportingImages -- Found it! %s' % container.label)
                for step in toolList:
                    #
                    # HERE BE PROCESSING.. Apply filter and alignment to all images
                    #
                    if not step.active():
                        continue
                    parameters = step.getValues()
                    data = step.process(data, parameters)

                #
                # Build new tree item
                #
                result = exportWidget.process(data, {})
                print(result.shape)

                key = item.key()
                newKey = key.replace('.edf', '.dat')

                newItem = SpecItem(
                    key=newKey,
                    header=item.header,
                    array=result,
                    fileLocation=''
                )

                #newContainer = ItemContainer(
                #    item=newItem,
                #    parent=specContainer,
                #    label=None  # is set automatically
                #)

                self.currentProject.addItem(newItem)

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
            dockWidgetArea = qt.Qt.LeftDockWidgetArea

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

    def showAlignmentFilter(self):
        self.imageView.addDockWidget(qt.Qt.LeftDockWidgetArea,
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
                #self.addImage(
                #self.imageView.addImage(
                #    data=item.array,
                #    legend=item.key(),
                #    replace=True
                #)
                self.imageView.setImageItem(item)
                print('RIXSMainWindow._handleShowSignal -- Received ImageItem')
            elif isinstance(item, ScanItem) or isinstance(item, SpecItem):
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
                #raise NotImplementedError('RIXSMainWindow._handleShowSignal -- Received ScanItem')
        print('RIXSMainWindow._handleShowSignal -- Done!')

    def connectActions(self):
        actionList = [(self.colormapAction, self.imageView.selectColormap),
                      (self.bandPassFilterAction, self.openBandPassTool),
                      (self.integrationAction, self.imageView.showExportWidget),
                      (self.bandPassFilterID32Action, self.openBandPassID32Tool),
                      (self.energyScaleAction, self.imageView.energyScaleTool.show),
                      (self.saveSpectraAction, self.saveSpectra),
                      (self.projectBrowserShowAction, self.openBandPassID32Tool)]
        for action, function in actionList:
            action.triggered[()].connect(function)
        print('All Actions connected..')

    def saveSpectra(self):
        print('RIXSMainWindow.saveSpectra')

    def openBandPassTool(self):
        self.imageView.setCurrentFilter('bandpass')

    def openBandPassID32Tool(self):
        self.imageView.setCurrentFilter('bandpassID32')


class DummyNotifier(qt.QObject):
    def signalReceived(self, val=None):
        print('DummyNotifier.signal received -- kw:\n', str(val))

if __name__ == '__main__':
    app = qt.QApplication([])
    win = RIXSMainWindow()
    win.show()
    app.exec_()