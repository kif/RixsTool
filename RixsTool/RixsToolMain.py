
from PyMca import PyMcaQt
from RixsTool.mainWindow import RIXSMainWindow

class RixsTool(object):

    def __init__(self, hasWindow=True):
        super(object, self).__init__()
        if hasWindow:
            self.initRixsToolWindow()

    def initRixsToolWindow(self):
        """
        Create RIXSMainWindow instance. In order for it to have
        a parent, RixsTool must be QObject. Consider that..

        Need to create an application before a paint device
        """
        QTAPPLICATION = PyMcaQt.QApplication([])
        window = RIXSMainWindow()
        window.show()
        QTAPPLICATION.exec_()

if __name__ == '__main__':
    rixsTool = RixsTool(hasWindow=True)