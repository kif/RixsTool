# Imports for GUI
from PyMca import PyMcaQt as qt
#from PyMca.widgets import ColormapDialog
#from PyMca import PyMcaFileDialogs # RETURNS '/' as seperator on windows!?
from PyMca import PyMcaDirs
from PyQt4 import uic

# Imports from os.path
from os.path import splitext as OsPathSplitExt

class RIXSMainWindow(qt.QMainWindow):
    def __init__(self, parent=None):
        qt.QMainWindow.__init__(self, parent)
        uic.loadUi('C:\\Users\\tonn\\lab\\rixs\\RIXS_ui\\mainwindow.ui', self)
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
        for idx, im in enumerate(flatten(reader['Image'])):
            self.imageView.addImage(im)
            print('Added image:',idx,'\n',im)

    def saveAnalysis(self):
        print('MainWindow -- saveAnalysis: to be implemented')

    def showHistogram(self):
        print('MainWindow -- showHistogram: to be implemented')

if __name__ == '__main__':
    app = qt.QApplication([])
    win = RIXSMainWindow()
    win.show()
    app.exec_()