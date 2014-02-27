from PyMca import PyMcaQt as qt

def initRixsIconDictionary():
    iconDir = 'C:\\Users\\tonn\\lab\\RixsTool\\RixsTool\\icons\\'
    iconNames = {
        'plus':   'plus.ico',
        'minus':  'minus.ico',
        'rixs':   'rixs.ico',
        'target': 'target.ico'
    }
    iconDict = {}
    for key, filename in iconNames.items():
        iconDict[key] = qt.QImage(iconDir + filename)
    return iconDict

RixsIconDict = initRixsIconDictionary()