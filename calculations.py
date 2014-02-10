#/*##########################################################################
# Copyright (C) 2004-2013 European Synchrotron Radiation Facility
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
__author__ = "Tonn Rueter - ESRF Data Analysis"

from PyMca import PyMcaQt as qt
import time
import numpy

DEBUG = 1

class OpDispatcher(qt.QObject):
    sigOperationFinished = qt.pyqtSignal(object)

    def __init__(self, key, idx, parent):
        qt.QObject.__init__(self, parent)
        self.__key = key
        self.__idx = idx
        self._ops = {}

    def refresh(self, image, key, idx, operation=None):
        if key != self.__key or idx != self.__idx:
            return False
        if operation is None:
            for operation, func in self._ops.items():
                startTime = time.time()
                ddict = func(image)
                endTime = time.time()
                deltaT = endTime - startTime
                print('ImageOp.refresh -- performed %s in %.3f'%
                      (operation, deltaT))
                self.sigOperationFinished.emit(ddict)
        else:
            func = self._ops[operation]
            startTime = time.time()
            ddict = func(image)
            endTime = time.time()
            deltaT = endTime - startTime
            print('ImageOp.refresh -- performed %s in %.3f'%
                  (operation, deltaT))
            self.sigOperationFinished.emit(ddict)
        return True

class ImageOp(object):
    def __init__(self, key, idx, parent):
        object.__init__(self)
        self.__key = key
        self.__idx = idx
        self.__parent = parent
        self._ops = {}

    def refreshAll(self, key, idx, image, params=None):
        if (key != self.__key) or (idx != self.__idx):
            return {}
        if not params:
            params = {}
        ddict = {}
        opsList = len(self._ops) * ['']
        startTime = time.time()
        for cnt, (operation, func) in enumerate(self._ops.items()):
            tmpDict = func(image, params)
            ddict.update(tmpDict)
            opsList[cnt] = tmpDict['op']
        endTime = time.time()
        deltaT = endTime - startTime
        print('ImageOp.refreshAll -- performed %s in %.3f'%
              (operation, deltaT))
        # Remove 'op' key/value since it is meaningless after loop
        del(ddict['op'])
        # Use ops list instead
        ddict['ops'] = opsList
        return ddict

    def refresh(self, operation, key, idx, image, params):
        if (key != self.__key) or (idx != self.__idx):
            return {}
        func = self._ops[operation]
        startTime = time.time()
        ddict = func(image, params)
        endTime = time.time()
        deltaT = endTime - startTime
        print('ImageOp.refresh -- performed %s in %.3f'%
              (operation, deltaT))
        return ddict

class Alignment(ImageOp):
    def __init__(self, key, idx, parent=None):
        ImageOp.__init__(self, key, idx, parent)
        self._ops = {
            'fftAlignment': self.fftAlignment
        }

    def fftAlignment(self, image, params):
        idx0 = params.get('idx0', 0)
        axis = params.get('axis', -1)
        portion = params.get('portion', .95)
        # Determine which axis defines curves
        if axis < 0:
            # If axis not specified..
            rows, cols = image.shape
            # ..align along smaller axis
            if rows < cols:
                axis = 0
            else:
                axis = 1

        if axis == 0:
            nCurves, nPoints = image.shape
        elif axis == 1:
            nPoints, nCurves = image.shape
        else:
            raise ValueError('Invalid axis: %d'%axis)

        # Aquire memory to store shifts
        shiftList = nCurves * [0.]

        if nCurves < 2:
            raise ValueError('At least 2 curves needed')

        # Sets the curve to which every other
        # curve is compared to..
        if axis:
            y0 = image[idx0,:]
        else:
            y0 = image[:,idx0]

        # Normalize before fft?
        #y0 = self.normalize(y0)
        fft0 = numpy.fft.fft(y0)

        # Perform fft Alignment for every other curves
        if axis:
            curves = image
        else:
            curves = image.T
        for idx, y in enumerate(curves):
            ffty = numpy.fft.fft(y)
            shiftTmp = numpy.fft.ifft(fft0 * ffty.conjugate()).real
            shiftPhase = numpy.zeros(shiftTmp.shape, dtype=shiftTmp.dtype)
            m = shiftTmp.size//2
            shiftPhase[m:] = shiftTmp[:-m]
            shiftPhase[:m] = shiftTmp[-m:]
            # Normalize shiftPhase between 0 and 1 to standardize thresholding
            #shiftPhase = self.normalize(shiftPhase)
            shiftPhaseMin = shiftPhase.min()
            shiftPhaseMax = shiftPhase.max()
            if not (shiftPhaseMax-shiftPhaseMin > 0):
                print('Error') # TODO
                return {}
            shiftPhase = (shiftPhase-shiftPhaseMin)/(shiftPhaseMax-shiftPhaseMin)

            # Thresholding
            xShiftMax = shiftPhase.argmax()
            left, right = xShiftMax, xShiftMax
            threshold = portion * shiftPhaseMax()
            while (shiftPhase[left] > threshold)&\
                  (shiftPhase[right] > threshold):
                left  -= 1
                right += 1
            mask = numpy.arange(left, right+1, 1, dtype=int)
            # The shift is determined by center-of-mass around shiftMax
            shiftTmp = (shiftPhase[mask] * idx/shiftPhase[mask].sum()).sum()
            #shift = (shiftTmp - m) * (x[1] - x[0])
            # x-range is pixel count..
            shift = (shiftTmp - m)

            shiftList[idx] = shift
            if DEBUG:
                print('\t%d\t%f'%(idx,shift))
        ddict = {
            'op': 'fftAlignment',
            'shiftList': shiftList
        }
        return ddict


class Interpolation(ImageOp):
    def __init__(self, key, idx, parent=None):
        ImageOp.__init__(self, key, idx, parent)
        self._ops = {
            'axisInterpolation': self.axisInterpolation
        }

    def axisInterpolation(self, image, params):
        axis = params.get('axis',-1)
        if axis < 0:
            # If axis not specified..
            rows, cols = image.shape
            # ..sum along larger axis
            if rows < cols:
                axis = 1
            else:
                axis = 0
        ddict = {}
        print('Interpolation.axisInterpolation -- not implemented')
        return ddict

class Integration(ImageOp):
    def __init__(self, key, idx, parent=None):
        ImageOp.__init__(self, key, idx, parent)
        self._ops = {
            'axisSum': self.axisSum
        }

    def bin(self, image, params):
        binWidthe = params.get('binWidth',10)
        axis = params.get('axis',-1)
        print('Integration.binning -- not implemented')
        ddict = {}
        return ddict

    def axisSum(self, image, params):
        axis = params.get('axis', -1)
        if axis < 0:
            # If axis not specified..
            rows, cols = image.shape
            # ..sum along smaller axis
            if rows < cols:
                axis = 0
            else:
                axis = 1
        ddict = {
            'op': 'axisSum',
            'sum': numpy.sum(image, axis=axis)
        }
        return ddict


class Stats2D(ImageOp):
    def __init__(self, key, idx, parent=None):
        ImageOp.__init__(self, key, idx, parent)
        self._minVal = float('NaN')
        self._maxVal = float('NaN')
        self._avgVal = float('NaN')
        self._medVal = float('NaN')
        self._ops = {
            'basics': self.basics,
            'histogram': self.histogram
        }

    def normalize(self, image, params):
        print('Stats2D.normalize -- not implemented')
        ddict = {}
        return ddict

    def basics(self, image, params):
        flat = numpy.sort(image.reshape(-1), kind='mergesort')
        #flat = sorted(image.reshape(-1)) # 10x slower than above
        if len(flat) > 0:
            self._minVal = flat[0]
            self._maxVal = flat[-1]
            if len(flat) % 2:
                middle = len(flat)//2
                self._medVal = .5 * (flat[middle-1] + flat[middle])
            else:
                self._medVal = flat[len(flat)//2 - 1]
            self._avgVal = numpy.average(flat)
        else:
            self._minVal = float('NaN')
            self._maxVal = float('NaN')
            self._avgVal = float('NaN')
            self._medVal = float('NaN')
        ddict = {
            'op': 'basics',
            'min': self._minVal,
            'max': self._maxVal,
            'average': self._medVal,
            'median': self._medVal
        }
        return ddict

    def histogram(self, image, params):
        y, x = numpy.histogram(image.reshape(-1),
                               bins=1000)
        ddict = {
            'op': 'histogram',
            'bins': .5*(x[:-1]+x[1:]),
            'counts': y
        }
        return ddict


class Notifiyer(qt.QObject):
    def __init__(self):
        qt.QObject.__init__(self)

    def signalReceived(self, ddict):
        obj = self.sender()
        print('Signal received:',ddict)
        #print('%s : %s'%(str(obj),str(kwargs)))

if __name__ == '__main__':
    n = Notifiyer()
    for idx in range(10):
        key = 'Dummy %d'%idx
        im = numpy.random.random((2048, 512))
        s = Stats2D(key, idx)
        #s.sigOperationFinished.connect(n.signalReceived)
        s.refresh(im, key, idx)