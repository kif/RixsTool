from PyMca import PyMcaQt as qt

class DataHandler(qt.QObject):
    sigRefresh = qt.pyqtSignal(str, int)

    def __init__(self, reader, parent=None):
        qt.QObject.__init__(self, parent)
        self.db = reader
        self.getStatistics()

    def __len__(self):
        return len(self.db)

    def _handleSigScalarUpdate(self, ddict):
        print('DataHandler._handleSigScalarUpdate -- ddict:',ddict)

    def ready(self):
        return not self.db.refreshing

    def getStatistics(self):
        if not self.ready():
            print('DataHandler.getStatistics -- not ready')
        for idx, key in enumerate(self.db.keys()):
            numImages = self.db['numImages'][idx]
            imageBlob = self.db['Images']
            for jdx in range(numImages):
                image = imageBlob[jdx]
                stats = Stats2D(key, jdx, self)
                self.sigRefresh.connect(stats.refresh)
                stats.sigScalarUpdate.connect(
                            self._handleSigScalarUpdate)
                stats.basics(image)
        return True