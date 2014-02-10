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
__author__ = "Tonn Rueter - ESRF Data Analysis Unit"

import numpy, time

DEBUG = 1

class ImageOp(object):
    def __init__(self, key, idx, parent):
        object.__init__(self)
        self.__key = key
        self.__idx = idx
        self.__parent = parent
        self._ops = {}

    def key(self):
        return self.__key

    def index(self):
        return self.__idx

    def parent(self):
        return self.__parent

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
        print('ImageOp.refreshAll -- performed in %.3f'%deltaT)
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
            'axisSum': self.axisSum,
            'sliceAndSum': self.sliceAndSum
        }

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

    def sliceAndSum(self, image, params):
        sumAxis = params.get('sumAxis', 1)
        sliceAxis = params.get('sliceAxis', 1)
        params['axis'] = sliceAxis
        sliceObj = Manipulation(self.key(),
                                self.index(),
                                self.parent())
        slices = sliceObj.slice(image, params)['slices']
        for slice in slices:
            print(slice.shape)
        result = [slice.sum(axis=sumAxis) for slice in slices]
        ddict = {
            'op': 'sliceAndSum',
            'summedSlices': result
        }
        return ddict

class Manipulation(ImageOp):
    def __init__(self, key, idx, parent):
        ImageOp.__init__(self, key, idx, parent)
        self._ops = {
            'slice': self.slice
        }

    def slice(self, image, params):
        binWidth = params.get('binWidth', 8)
        axis = params.get('axis',1)
        mode = params.get('mode','strict')
        if axis:
            size = (image.shape[0],binWidth)
        else:
            size = (binWidth,image.shape[1])
        lim = image.shape[axis]
        if mode not in ['strict']: # TODO: implement mode that puts surplus cols rows as last element in tmpList
            raise ValueError('Integration.binning: Unknown mode %s'%mode)
        if lim%binWidth and mode == 'relaxed':
            raise Warning('Binning neglects curves at the end')
        numberOfBins = lim//binWidth
        tmpList = numberOfBins*[numpy.zeros(size, dtype=image.dtype)]
        for idx in range(numberOfBins):
            lower = idx * binWidth
            upper = lower + binWidth
            if upper >= lim:
                break
            if axis:
                # Slice along cols (axis==1)
                tmpList[idx] = numpy.copy(image[:,lower:upper])
            else:
                # Slice along rows (axis==0)
                tmpList[idx] = numpy.copy(image[lower:upper,:])
        ddict = {
            'op': 'binning',
            'slices': tmpList
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


def run_test():
    import RixsTool.io as io
    from matplotlib import pyplot as plt
    a = io.run_test()
    im = a[15][2][0] # 15th data blob (i.e. [2]), first image
    if 1:
        im = im - im.min()
        im = numpy.where(im <= 140, im, 0)
    print('im.shape:',im.shape)
    b = Integration('foo',0)
    #for elem in b.sliceAndSum(im, {'sumAxis':1, 'binWidth':128})['summedSlices']:
    #    plt.plot(elem)
    plt.plot(b.axisSum(im, {})['sum'])
    plt.show()


if __name__ == '__main__':
    run_test()