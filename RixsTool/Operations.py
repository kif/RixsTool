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

import time

import numpy

# Numeric routines from PyMca
from PyMca.Gefit import LeastSquaresFit as LSF
from PyMca import SpecfitFunctions as SF
from PyMca.SpecfitFuns import gauss as gaussianModel
from PyMca import SNIPModule as SNIP

# IO and Datahandling from RixsTool
from RixsTool.datahandling import RixsProject
from RixsTool.DataItem import AnalyticItem
from os.path import normpath as OsPathNormpath
from os.path import splitext as OsPathSplitext
from os.path import sep as OsPathSep
from os import walk as OsWalk

DEBUG = 1
MATPLOTLIBIMPORT = False
plt = None


class ImageOp(object):
    def __init__(self):
        object.__init__(self)
        self._ops = {}


class Filter(ImageOp):
    def __init__(self):
        ImageOp.__init__(self)
        self._ops = {
            'bandpass': self.bandPassFilter
        }

    #def bandPassFilter(self, image, params):
    @staticmethod
    def bandPassFilter(image, params):
        imMin = image.min()
        imMax = image.max()
        lo = params.get('low', imMin)
        hi = params.get('high', imMax)
        offset = params.get('offset', None)
        if offset:
            offset = numpy.asscalar(numpy.array([offset], dtype=image.dtype))

        out = numpy.where((lo <= image), image, imMin)
        out = numpy.where((image <= hi), out, imMin)
        if offset:
            out = numpy.where((image > offset), out, 0)

        #ddict = {
        #    'op': 'bandpass',
        #    'image': out
        #}
        #return ddict
        return out


class Alignment(ImageOp):
    def __init__(self=None):
        ImageOp.__init__(self)
        self._ops = {
            'maxAlignment': self.maxAlignment,
            'fftAlignment': self.fftAlignment,
            'centerOfMassAlignment': self.centerOfMassAlignment
        }

    @staticmethod
    def maxAlignment(image, params):
        # TODO: Add normalization flag
        idx0 = params.get('idx0', 0)
        axis = params.get('axis', -1) # Axis defines direction of curves
        scale = params.get('scale', None)

        if axis < 0:
            rows, cols = image.shape
            if rows < cols:
                axis = 0
            else:
                axis = 1

        if axis == 0:
            nCurves, nPoints = image.shape
            curves = image
        elif axis == 1:
            nPoints, nCurves = image.shape
            curves = image.T
        else:
            raise ValueError('Alignment instance -- Axis must be either -1, 0 or 1')

        shiftList = [float('NaN')] * nCurves

        pos0 = curves[idx0].argmax()

        for idx, y in enumerate(curves):
            shift = pos0 - y.argmax()
            shiftList[idx] = shift

        shiftArray = numpy.asarray(shiftList)
        if scale:
            shiftArray *= numpy.average(numpy.diff(scale))

        #ddict = {
        #    'op': 'maxAlignment',
        #    'shiftList': shiftArray
        #}
        #return ddict
        return shiftArray

    @staticmethod
    def centerOfMassAlignment(image, params):
        idx0 = params.get('idx0', 0)
        axis = params.get('axis', -1) # Axis defines direction of curves
        portion = params.get('portion', .80)
        scale = params.get('scale', None)

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
            curves = image
        elif axis == 1:
            nPoints, nCurves = image.shape
            curves = image.T
        else:
            raise ValueError('Alignment instance -- Axis must be either -1, 0 or 1')

        shiftList = nCurves * [float('NaN')]

        y0 = curves[idx0]
        pos0 = y0.argmax()
        ymin0, ymax0 = y0.min(), y0.max()
        normFactor = ymax0-ymin0
        if float(normFactor) <= 0.:
            # Curve is constant
            raise ZeroDivisionError('Alignment.centerOfMass -- Trying to align on constant curve')
        ynormed0 = (y0-ymin0)/normFactor

        threshold = portion * float(ynormed0[pos0])
        left, right = pos0, pos0
        while  ynormed0[left] > threshold:
            left -= 1
        while  ynormed0[right] > threshold:
            right += 1
        if left < 0 or right >= nPoints:
            raise IndexError('Alignment.centerOfMassAlignment: 0-th index out of range (left: %d, right: %d)'%(left, right))
        mask = numpy.arange(left, right+1, dtype=int)
        pos0 = numpy.trapz(ynormed0[mask] * mask) / numpy.trapz(ynormed0[mask])

        for idx, y in enumerate(curves):
            # Normalize betw. zero an one
            ymin, ymax = y.min(), y.max()
            normFactor = ymax-ymin
            if float(normFactor) <= 0.:
                # Curve is constant
                continue
            ynormed = (y-ymin)/normFactor

            idxMax = ynormed.argmax()
            left, right = idxMax, idxMax
            while ynormed[left] > threshold:
                left -= 1
            while ynormed[right] > threshold:
                right += 1
            if left < 0 or right >= nPoints:
                raise IndexError('Alignment.centerOfMassAlignment: index out of range (left: %d, right: %d)'%(left, right))
            mask = numpy.arange(left, right+1, dtype=int)
            print('mask:', mask)
            shift = pos0 - numpy.trapz(ynormed[mask] * mask) / numpy.trapz(ynormed[mask])
            if DEBUG:
                print('\t%d\t%f'%(idx, shift))
            shiftList[idx] = shift

        shiftArray = numpy.asarray(shiftList)
        if scale:
            shiftArray *= numpy.average(numpy.diff(scale))
        #ddict = {
        #    'op': 'centerOfMassAlignment',
        #    'shiftList': shiftArray
        #}
        #return ddict
        return shiftArray

    @staticmethod
    def fftAlignment(image, params):
        idx0 = params.get('idx0', 0)
        axis = params.get('axis', -1)  # Axis defines direction of curves
        portion = params.get('portion', .80)
        scale = params.get('scale', None)

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
            curves = image
        elif axis == 1:
            nPoints, nCurves = image.shape
            curves = image.T
        else:
            raise ValueError('Alignment instance -- Axis must be either -1, 0 or 1')

        shiftList = nCurves * [float('NaN')]

        y0 = curves[idx0]
        fft0 = numpy.fft.fft(y0)

        for idx, y in enumerate(curves):
            print('fftAlignment -- y.shape: %s' % str(y.shape))
            ffty = numpy.fft.fft(y)
            shiftTmp = numpy.fft.ifft(fft0 * ffty.conjugate()).real
            shiftPhase = numpy.zeros(shiftTmp.shape, dtype=shiftTmp.dtype)
            m = shiftTmp.size//2
            shiftPhase[m:] = shiftTmp[:-m]
            shiftPhase[:m] = shiftTmp[-m:]

            # Normalize shiftPhase between 0 and 1 to standardize thresholding
            shiftPhaseMin = shiftPhase.min()
            shiftPhaseMax = shiftPhase.max()
            normFactor = shiftPhaseMax - shiftPhaseMin
            if float(normFactor) <= 0.:
                print('fftAlignment -- \tshiftPhaseMin: %f\n\t\t\tshiftPhaseMax: %f' %
                      (shiftPhaseMin, shiftPhaseMax))  # TODO
                continue
            shiftPhase = (shiftPhase-shiftPhaseMin)/normFactor

            # Thresholding
            idxMax = shiftPhase.argmax()
            left, right = idxMax, idxMax
            #threshold = portion * shiftPhaseMax
            threshold = portion
            while shiftPhase[left] >= threshold:
                left -= 1
            while shiftPhase[right] >= threshold:
                right += 1

            mask = numpy.arange(left, right+1, 1, dtype=int)
            print('fftAlignment -- mask: %s' % str(mask))
            # The shift is determined by center-of-mass around idxMax
            shiftTmp = numpy.sum((shiftPhase[mask] * mask/shiftPhase[mask].sum()))
            #shift = (shiftTmp - m) * (x[1] - x[0])
            # x-range is pixel count..
            print('fftAlignment -- shiftTmp: %s' % str(shiftTmp))
            shift = (shiftTmp - m)

            shiftList[idx] = shift
            if DEBUG:
                print('\t%d\t%f' % (idx, shift))

        #ddict = {
        #    'op': 'fftAlignment',
        #    'shiftList': shiftList
        #}
        #return ddict
        #return shiftList
        return numpy.ascontiguousarray(shiftList)

    @staticmethod
    def fitAlignment(image, params):
        idx0 = params.get('idx0', 0)
        axis = params.get('axis', -1) # Axis defines direction of curves
        snipWidth = params.get('snipWidth', None)
        peakSearch = params.get('peakSearch', False)

        #
        # Determine which axis defines curves
        # Make shure to convert image to float!!!
        #
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
            curves = numpy.float64(image)
        elif axis == 1:
            nPoints, nCurves = image.shape
            curves = numpy.float64(image.T)
        else:
            raise ValueError('Alignment instance -- Axis must be either -1, 0 or 1')

        #
        # Image preprocessing: Snip background
        #
        imRows, imCols = image.shape
        if snipWidth is None:
            snipWidth = max(imRows, imCols)//10
        print('snipWidth:', )
        specfitObj = SF.SpecfitFunctions()

        background = numpy.zeros(shape=curves.shape,
                                 dtype=numpy.float64)
        for idx, curve in enumerate(curves):
            background[idx] = SNIP.getSnip1DBackground(curve, snipWidth)
        subtracted = curves-background
        normResult = Normalization.zeroToOne(image=subtracted,
                                             params={})
        normalized = normResult['image']

        """
        print('curves.shape:', curves.shape)
        #print('background.shape:', background.shape)
        print('subtracted.shape:', subtracted.shape)

        plotImageAlongAxis(subtracted)
        """

        #
        # Loop through curves: Find peak (max..), Estimate fit params, Perform Gaussian fit
        #
        fitList = nCurves * [float('NaN')]
        if DEBUG == 1:
            print('Alignment.fitAlignment -- fitting..')
        for idx, y in enumerate(subtracted):
            #
            # Peak search
            #
            if peakSearch:
                try:
                    # Calculate array with all peak indices
                    peakIdx = numpy.asarray(specfitObj.seek(y, yscaling=100.),
                                            dtype=int)
                    # Extract highest feature
                    maxIdx = y[peakIdx].argsort()[-1]
                except IndexError:
                    if DEBUG == 1:
                        print('Alignment.fitAlignment -- No peaks found..')
                    return None
                except SystemError:
                    if DEBUG == 1:
                        print('Alignment.fitAlignment -- Peak search failed. Continue with y maximum')
                    peakIdx = [y.argmax()]
                    maxIdx = 0
            else:
                peakIdx = [y.argmax()]
                maxIdx = 0
            height = float(y[peakIdx][maxIdx]) + curves[idx].min()
            pos = float(peakIdx[maxIdx])

            #
            # Estimate FWHM
            #
            fwhmIdx = numpy.nonzero(y >= .5*normalized[idx])[0]
            # Underestimates FWHM, since carried out on normalized image
            fwhm = float(fwhmIdx.max()-fwhmIdx.min())

            #
            # Peak fit: Uses actual data
            #
            #xrange = numpy.arange(0, len(y), dtype=y.dtype) # Full range
            mask = numpy.nonzero(y >= .1*normalized[idx])[0]
            ydata = curves[idx,mask]
            #ydata -= ydata.min()
            try:
                fitp, chisq, sigma = LSF(gaussianModel,
                                         numpy.asarray([height, pos, fwhm]),
                                         xdata=mask,
                                         ydata=(ydata-ydata.min()))
                if DEBUG == 1:
                    print('\tCurve %d -- fitp: %s' % (idx, str(fitp)))
                    print('\tCurve %d -- chisq: %s' % (idx, str(chisq)))
                    print('\tCurve %d -- sigma: %s' % (idx, str(sigma)))
            except numpy.linalg.linalg.LinAlgError:
                fitp, chisq, sigma = [None, None, None],\
                                     float('Nan'),\
                                     float('Nan')
                if DEBUG == 1:
                    print('\tCurve %d -- Fit failed!' % idx)
            fitList[idx] = fitp # ftip is 3-tuple..


        posIdx = 1 # ..2nd argument of fitp is peak position
        shift0 = fitList[idx0][posIdx]
        shiftList = [shift0-fit[posIdx] for fit in fitList]

        #ddict = {
        #    'op': 'fitAlignment',
        #    'shiftList': shiftList
        #}
        #return ddict
        return shiftList


class Interpolation(ImageOp):
    def __init__(self=None):
        ImageOp.__init__(self)
        self._ops = {
            'axisInterpolation': self.axisInterpolation
        }

    def axisInterpolation(self, image, params):
        axis = params.get('axis', -1)
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
    def __init__(self=None):
        ImageOp.__init__(self)
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
        #ddict = {
        #    'op': 'axisSum',
        #    'sum': numpy.sum(image, axis=axis)
        #}
        #return ddict
        return numpy.sum(image, axis=axis)

    #def sliceAndSum(self, image, params):
    @staticmethod
    def sliceAndSum(image, params):
        sumAxis = params.get('sumAxis', 1)
        sliceAxis = params.get('sliceAxis', 1)
        params['axis'] = sliceAxis
        slices = Manipulation.slice(image, params)
        #result = [slice_.sum(axis=sumAxis) for slice_ in slices]
        result = numpy.asarray([slice_.sum(axis=sumAxis) for slice_ in slices], dtype=image.dtype)
        #ddict = {
        #    'op': 'sliceAndSum',
        #    'summedSlices': result
        #}
        #return ddict
        return result


class Normalization(ImageOp):
    def __init__(self=None):
        ImageOp.__init__(self)
        self._ops = {
            'zeroToOne': self.zeroToOne
        }

    @staticmethod
    def zeroToOne(image, params):
        offset  = image.min()
        maximum = image.max()
        normFactor = maximum - offset

        print('zeroToOne, before -- min: %.3f, max: %.3f'%(offset, maximum))

        if normFactor == 0.:
            normalized = numpy.zeros(shape=image.shape,
                                     dtype=image.dtype)
        else:
            normalized = (image - offset)/normFactor
        print('zeroToOne, after  -- min: %.3f, max: %.3f' % (normalized.min(), normalized.max()))
        ddict = {
            'op': 'zeroToOne',
            'image': normalized
        }
        return ddict


class Manipulation(ImageOp):
    def __init__(self):
        ImageOp.__init__(self)
        self._ops = {
            'slice': self.slice
        }

    @staticmethod
    def skewAlongAxis(image, params):
        nRows, nCols = image.shape

        axis = params.get('foobar', None)
        # if axis is specified, skew along longer axis
        # i.e. loop along shorter axis
        if axis is None:
            if nRows > nCols:
                axis = 1
                longAxis = 0
                shortAxis = 1
            else:
                longAxis = 1
                shortAxis = 0

        shiftArray = params.get('shiftArray', None)
        if shiftArray is None:
            raise ValueError('Manipulation.skewAlongAxis -- must provide shiftArray')
        if not isinstance(shiftArray, numpy.ndarray):
            shiftArray = numpy.ascontiguousarray(shiftArray)

        oversampling = params.get('oversampling', 1)
        if shortAxis == 0:
            resultShape = (nRows, oversampling * nCols)
        else:
            resultShape = (oversampling * nRows, nCols)
        result = numpy.zeros(resultShape)
        interpRange = numpy.linspace(0, 2047, result.shape[longAxis])
        if shortAxis == 0:
            points = numpy.arange(0, image.shape[1], 1, dtype=numpy.uint16)
        else:
            points = numpy.arange(0, image.shape[0], 1, dtype=numpy.uint16)

        print(shortAxis)
        print(longAxis)
        print(image.shape)
        print(result.shape)
        print(len(interpRange))
        print(len(points))

        for idx in range(image.shape[shortAxis]):
            if shortAxis == 0:
                vector = image[idx, :]
            else:
                vector = image[:, idx]
            shift = shiftArray[idx]

            interpolated = numpy.interp(
                x=interpRange-shift,
                xp=points,
                fp=vector
            )

            if shortAxis == 0:
                result[idx, :] = interpolated
            else:
                result[:, idx] = interpolated

        return result

    @staticmethod
    def slice(image, params):
        binWidth = params.get('binWidth', 8)
        axis = params.get('axis', 1)
        mode = params.get('mode', 'strict')
        if axis:
            size = (image.shape[0], binWidth)
        else:
            size = (binWidth, image.shape[1])
        lim = image.shape[axis]
        if mode not in ['strict']:  # TODO: implement mode that puts surplus cols rows as last element in tmpList
            raise ValueError('Integration.binning: Unknown mode %s' % mode)
        if lim % binWidth and mode == 'relaxed':
            raise Warning('Binning neglects curves at the end')
        numberOfBins = lim//binWidth
        tmpList = numberOfBins*[numpy.zeros(size, dtype=image.dtype)]
        for idx in range(numberOfBins):
            lower = idx * binWidth
            upper = lower + binWidth
            if upper > lim:
                break
            if axis:
                # Slice along cols (axis==1)
                tmpList[idx] = numpy.copy(image[:, lower:upper])
            else:
                # Slice along rows (axis==0)
                tmpList[idx] = numpy.copy(image[lower:upper, :])
        #ddict = {
        #    'op': 'binning',
        #    'slices': tmpList
        #}
        #return ddict
        return tmpList


class Fit(object):
    @staticmethod
    def secondOrderPolynom(fitvalues, x=None):
        """
        :param ndarray fitvalues: Values on which the fit is carried out
        :param ndarray x: x-range of the fitvalues (default: None)

        :raises numpy.RankWarning: In case the least squares fit is badly conditioned.
        """
        if x is None:
            x = numpy.arange(
                start=0,
                stop=len(y)
            )
        par = numpy.polyfit(
            x=x,
            y=fitvalues,
            deg=2)
        function = AnalyticItem('some fit', 'noheader')
        expression = lambda x, a, b, c: a * x**2 + b * x + c
        parameters = {
            'a': par[0],
            'b': par[1],
            'c': par[2],
        }
        function.setExpression(expression)
        function.setParameters(parameters)
        print('Fit.secondOrderPolynom -- consistency check succeeded: %s' % str(function.consistencyCheck()))
        return function


class Stats2D(ImageOp):
    def __init__(self=None):
        ImageOp.__init__(self)
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


def importMatplotLib():
    global MATPLOTLIBIMPORT, plt
    try:
        from matplotlib import pyplot as plt
        MATPLOTLIBIMPORT = True
    except ImportError:
        MATPLOTLIBIMPORT = False
        print('showImage -- Module matplotlib not found! Abort')


def showImage(image):
    global MATPLOTLIBIMPORT, plt
    if not MATPLOTLIBIMPORT:
        importMatplotLib()
    plt.imshow(image)
    plt.show()


def plotImageAlongAxis(image, axis=-1, offset=False, returnPlot=False):
    global MATPLOTLIBIMPORT, plt
    if not MATPLOTLIBIMPORT:
        importMatplotLib()
    if (axis > 1) or (len(image.shape) > 2):
        raise ValueError('Image must be 2D and axis must be either -1, 0 or 1')

    # If axis is default value, take longer axis to be x
    # and loop along smaller axis
    if axis < 0:
        loop = numpy.argmax(image.shape)

    yOffset = 0.
    for idx in range(8):
        if axis:
            # axis == 1
            curve = image[idx, :]
        else:
            # axis == 0
            curve = image[:, idx]
        if offset:
            yOffset += (curve.max() - curve.min())
        plt.plot(curve + yOffset)

    if returnPlot:
        return plt
    else:
        plt.show()


def slopeCorrection(itemList):
    from matplotlib import pyplot as plt
    imageList = [None] * len(itemList)
    clist = ['b', 'g', 'r']
    for idx, item in enumerate(itemList):
        color = clist[idx % len(clist)]
        im = item.array

        oversampling = 2
        nRows, nCols = im.shape
        final = numpy.zeros(
            shape=(oversampling * nRows, nCols)
        )

        imageList[idx] = im
        filtered = Filter.bandPassFilter(im, {'low': im.min(),
                                              'high': im.min()+140})

        sliced = numpy.asarray(Integration.sliceAndSum(filtered, {'sumAxis': 1, 'binWidth': 64}))
        ffts = Alignment.fftAlignment(sliced, {})
        x = numpy.arange(len(ffts)) * 64
        #plt.plot(x, ffts, 'x'+color)
        #par = numpy.polyfit(
        #    x=x,
        #    y=ffts,
        #    deg=2)
        #print par
        #x = numpy.linspace(0, len(ffts), 50)
        #poly = lambda x: par[0] * x**2 + par[1] * x + par[2]
        poly = Fit.secondOrderPolynom(
            fitvalues=ffts,
            x=x
        )
        shiftArray = poly.sample(numpy.arange(min(filtered.shape)))
        #plt.plot(x, poly(x), '--'+color)
        #print im.shape  # (2048, 512)
        #for row in [128*elem for elem in [0,1,2,3]]:
        #for row in range(im.shape[-1]):
        #    shift = poly(row)
        #    #rowVals = im[row, :]
        #    rowVals = filtered[:, row]
        #    print shift
        #    interpX = numpy.linspace(0, 2047, oversampling * len(rowVals))
        #    points = numpy.arange(0, 2048, 1, dtype=im.dtype)
        #    #interpX = numpy.where(interpX < 2048)
        #    interpY = numpy.interp(interpX-shift, points, rowVals)
        #    final[:, row] = interpY
        #Normalization.zeroToOne(filtered)

        corrected = Manipulation.skewAlongAxis(
            image=filtered,
            params={
                'oversampling': 1,
                'shiftArray': shiftArray
            }
        )
        #plt.imshow(filtered)
        #plt.imshow(corrected)
        final = numpy.sum(corrected, axis=1)

        f = open('/home/truter/lab/rixs_own/own%d.dat' % idx, 'w')
        #llist = final.tolist()
        #llist.reverse()
        #for elem in llist:
        #    f.write('%.3f\n' % elem)
        final[::-1].tofile(f, sep='\n')
        f.close()
        #plt.plot(final)
    #plt.show()
    # Scherung


def run_test():

    directory = '/home/truter/lab/mock_folder/Images'
    project = RixsProject()
    project.crawl(directory)
    #return
    #im = a['Images'][0][:,1:]
    #print('run_test -- slice.shape:', sliced.shape)
    itemList = [
        project['LBCO0483.edf'].item(),
        project['LBCO0484.edf'].item(),
        project['LBCO0485.edf'].item(),
        project['LBCO0486.edf'].item(),
        project['LBCO0487.edf'].item(),
        project['LBCO0488.edf'].item(),
        project['LBCO0489.edf'].item(),
        project['LBCO0490.edf'].item(),
        project['LBCO0491.edf'].item(),
        project['LBCO0492.edf'].item(),
        project['LBCO0493.edf'].item(),
        project['LBCO0494.edf'].item(),
        project['LBCO0495.edf'].item(),
        project['LBCO0496.edf'].item(),
        project['LBCO0497.edf'].item(),
        project['LBCO0498.edf'].item()
    ]

    itemList = [child.item() for child in project['Images'].children]


    slopeCorrection(itemList)


    #im = numpy.asarray([[0,0,0,.25,.5,2,.5,.25], [0,.5,1,.5,0,0,0,0]])
"""
    alignmentObj = Alignment(key, idx)
    #shiftList = alignmentObj.centerOfMassAlignment(normed, {})
    shiftList = alignmentObj.maxAlignment(im, {})
    print('shiftList:', shiftList)
    shiftList = alignmentObj.centerOfMassAlignment(im, {})
    print('shiftList:', shiftList)
    shiftList = alignmentObj.fftAlignment(im, {})
    print('shiftList:', shiftList)
    #for elem in shiftList
#    for elem in normed:
#        plt.plot(elem)
    #plt.plot(b.axisSum(im, {})['sum'])
#    plt.show()
"""


if __name__ == '__main__':
    run_test()
    print('io.run_test -- Done')