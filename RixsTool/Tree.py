from PyMca import PyMcaQt as qt

class ItemContainer(object):
    def __init__(self, data=None, parent=None):
        self._data = data if data is not None else [] # Dict or OrderedDict here?
        self.parent = parent
        self.children = []

    def childNumber(self):
        if self.parent:
            siblings = self.parent.children
            idx = siblings.index(self)
        else:
            idx = -1
        return idx

    def childCount(self):
        return len(self.children)

    def columnCount(self):
        return len(self._data)

    def data(self, colIdx):
        return self._data[colIdx]

    def setData(self, colIdx, data):
        if (colIdx < 0) or colIdx >= len(self._data):
            return False
        self._data[colIdx] = data
        return True

    """
    def insertChildren(self, pos, count, cols):
        # Modifies self.children
        if (pos < 0) or (pos > len(self.children)):
            return False

        head = self.children[0:pos]
        tail = self.children[pos:]
        new  = [ItemContainer(data=([None]*cols), parent=self)] * count
        self.children = head + new + tail
        return True
    """

    def insertChildren(self, pos, new):
        # Modifies self.children
        # Insert ItemContainer instances
        if (pos < 0) or (pos > len(self.children)):
            return False
        if False in [isinstance(child, ItemContainer) for child in new]:
            return False

        head = self.children[0:pos]
        tail = self.children[pos:]
        self.children = head + new + tail
        return True

    def removeChildren(self, pos, count):
        # Modifies self.children
        if (pos < 0) or (pos >= len(self.children)):
            return False

        del(self.children[pos:pos+count])
        return True

    def insertColumns(self, pos, count):
        # Modifies self._data
        if (pos < 0) or (pos >= len(self.children)):
            return False

        head = self._data[0:pos]
        tail = self._data[pos:]
        new  = [None] * count
        self._data = head + new + tail
        return True

    def removeColumns(self, pos, count):
        pass

class TreeModel(qt.QAbstractItemModel):
    def __init__(self, root, parent=None):
        super(TreeModel, self).__init__(parent)
        #self.rootItem = ItemContainer(data=[],parent=None)
        self.rootItem = root

    def data(self, modelIndex, role=qt.Qt.DisplayRole):
        if not modelIndex.isValid():
            return None
        item = self.getItem(modelIndex)
        if role == qt.Qt.DisplayRole:
            return item.data(modelIndex.column())

    def getItem(self, modelIndex):
        if modelIndex.isValid():
            item = modelIndex.internalPointer()
            if item:
                return item
        return self.rootItem

    def rowCount(self, parentIndex=qt.QModelIndex(), *args, **kwargs):
        parent = self.getItem(parentIndex)
        return parent.childCount()

    def columnCount(self, parentIndex=qt.QModelIndex(), *args, **kwargs):
        # TODO: Do all items contain the same amount of data?
        return self.rootItem.columnCount()

    def flags(self, modelIndex):
        if modelIndex.isValid():
            return qt.Qt.ItemIsEditable | qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable
        else:
            return 0

    def index(self, row, col, parentIndex=qt.QModelIndex(), *args, **kwargs):
        if parentIndex.isValid() and parentIndex.column() > 0:
            return qt.QModelIndex()
        parent = self.getItem(parentIndex)
        try:
            child = parent.children[row]
        except IndexError:
            return qt.QModelIndex()
        if child:
            return self.createIndex(row, col, child)
        else:
            return qt.QModelIndex()

    def parent(self, modelIndex=qt.QModelIndex()):
        if not modelIndex.isValid():
            return qt.QModelIndex()

        child = self.getItem(modelIndex)
        parent = child.parent

        if parent == self.rootItem:
            return qt.QModelIndex()

        return self.createIndex(parent.childNumber(), 0, parent)

def unitTest_ItemContainer():
    root = buildTree()
    print('---- Traversal ----')
    traverse(root)
    print('-------------------')

    app = qt.QApplication([])
    win = qt.QTreeView()
    model = TreeModel(root)
    win.setModel(model)
    win.show()
    app.exec_()


def buildTree(root=None):
    import os

    directory = root.data(0) if root else r'C:\Users\tonn\lab\mockFolder'
    lsdir = ['\\'.join([directory,name]) for name in os.listdir(directory)]
    dirs  = [path for path in lsdir if os.path.isdir(path)]
    files = [path.split('\\')[-1] for path in lsdir if os.path.isfile(path)]
    root = root if root else ItemContainer([directory, files], None)
    for idx, direct in enumerate(dirs):
        lsdir = ['\\'.join([directory,name]) for name in os.listdir(direct)]
        files = [path.split('\\')[-1] for path in lsdir if os.path.isfile(path)]
        child = buildTree(ItemContainer([direct, files], None))
        child.parent = root
        root.insertChildren(root.childCount(), [child])
    return root

def traverse(root):
    print(root.data(0),'  --contains->  ', root.data(1))
    print('childNumber:',root.childNumber())
    for child in root.children:
        traverse(child)





if __name__ == '__main__':
    unitTest_ItemContainer()