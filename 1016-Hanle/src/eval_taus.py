#!/usr/bin/python2.7
"""Evaluate taus obtained by lorentz-fits"""

__author__ = "Benjamin Rottler (benjamin@dierottlers.de)"


from ROOT import TCanvas, TMultiGraph, TLegend, gPad

# ========================================================================
# make sure to add ../../lib to your project path or copy files from there
from data import DataErrors
from fitter import Fitter
from functions import setupROOT, loadCSVToList, avgerrors
from txtfile import TxtFile
# ========================================================================

from hanle import setMultiGraphTitle, TempToSeries, serieslabels, seriescolors
import numpy as np


def loadTempDict():
    """load temperature to pressure data (calculated with mathematica)"""
    data = loadCSVToList('../calc/temp_pressure.txt')
    d = dict()
    for T, p, sp in data:
        d[T] = (p, sp)
    return d


def printGraph(datas, phi, name='', fit=False):
    """make graph with measured taus for one specific angle phi

    Arguments:
    datas -- datalists (sorted by series in dictonary)
    phi   -- angle
    name  -- additional name for file name
    fit   -- if true fit data with linear model (default=False)
    """
    # setup canvas and legend
    c = TCanvas('c_%d' % phi, '', 1280, 720)
    if fit:
        l = TLegend(0.6, 0.15, 0.85, 0.5)
    else:
        l = TLegend(0.65, 0.15, 0.85, 0.35)
    l.SetTextSize(0.03)
    # make and draw graphs, graphs are organized by TMultiGraph
    graphs = TMultiGraph()
    for s, datalist in datas.iteritems():
        data = DataErrors.fromLists(*zip(*datalist))
        g = data.makeGraph('g_%d_%d' % (phi, s))
        g.SetMarkerColor(seriescolors[s])
        g.SetLineColor(seriescolors[s])
        l.AddEntry(g, serieslabels[s], 'p')
        graphs.Add(g)
    graphs.Draw('AP')
    gPad.Update()
    setMultiGraphTitle(graphs, 'Druck p / mPa', '#tau / ns')

    # fit data with linear fit
    if fit:
        fit = Fitter('fit_%d' % phi, 'pol1(0)')
        fit.function.SetNpx(1000)
        fit.setParam(0, '#tau_{0}', 119)
        fit.setParam(1, 'm', 0.5)
        fit.fit(graphs, 0, 225, 'M')
        fit.saveData('../calc/fit_tau_%02d%s.txt' % (phi, name), 'w')
        l.AddEntry(fit.function, 'Fit mit #tau(p) = #tau_{0} + m * p', 'l')
        fit.addParamsToLegend(l, [('%.1f', '%.1f'), ('%.2f', '%.2f')], chisquareformat='%.2f',
                              advancedchi=True, units=['ns', 'ns / mPa'])

    # draw legend and print canvas to file
    l.Draw()
    c.Update()
    c.Print('../img/taus_%02d%s.pdf' % (phi, name), 'pdf')

    # return required fit parameter
    if fit:
        return fit.params[0]['value'], fit.params[0]['error']


def main():
    phis = [0, 45, 90]
    tempDict = loadTempDict()
    avgphis = dict()
    taus = []
    for phi in phis:
        # read data
        datalist = loadCSVToList('../calc/taus_%02d.txt' % phi)
        datas = {0: [], 1: [], 2: []}
        for T, tau, stau, fitphi, sfitphi in datalist:
            p, sp = tempDict[T]
            datas[TempToSeries(T)].append((p, tau, sp, stau))  # sort in right series list

        # make graphs with different series
        printGraph(datas, phi)
        printGraph(datas, phi, '_total', True)

        del datas[0]
        taus.append(printGraph(datas, phi, '_day2', True))

        del datas[2]
        printGraph(datas, phi, '_partial', True)

        # calculate average fitted phi
        philist = zip(*datalist)[3]
        avgphis[phi] = np.average(philist), np.std(zip(*datalist)[3], ddof=1) / np.sqrt(len(philist))

    # print out average fittet phis
    with TxtFile('../calc/avgphis.txt', 'w') as f:
        for phi, avgphi in avgphis.iteritems():
            f.writeline('\t', str(phi), *map(str, avgphi))

    # print out extraplated taus as LaTeX table
    with TxtFile('../src/taus_final.tex', 'w') as f:
        f.write2DArrayToLatexTable(zip(phis, *zip(*taus)),
                                   ['$\\Phi$ / ${}^{\\circ}$', '$\\tau$ / ns', '$s_{\\tau}$ / ns'],
                                   ['%d', '%.1f', '%.1f'],
                                   'Extrapolierte mittlere Lebensdauern bei verschiedenen Winkeleinstellungen.',
                                   'tab:tau:final')

    # print out extrapolated taus as csv and calculate weighted average
    with TxtFile('../calc/taus_final.txt', 'w') as f:
        for tau, error in taus:
            f.writeline('\t', str(tau), str(error))
        f.writeline('weighted average')
        f.writeline('\t', *map(str, avgerrors(*zip(*taus))))


if __name__ == '__main__':
    setupROOT()
    main()
