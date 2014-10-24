#!/usr/bin/python2.7
from ROOT import TCanvas, TMultiGraph, TLegend, gPad

from data import DataErrors
from fitter import Fitter
from functions import setupROOT, loadCSVToList

from hanle import setMultiGraphTitle, TempToSeries, serieslabels, seriescolors, STEMP
import numpy as np


def loadTempDict():
    data = loadCSVToList('../calc/temp_pressure.txt')
    d = dict()
    for T, p, sp in data:
        d[T] = (p, sp)
    return d


def printGraph(datas, phi, name='', fit=False):
    # make graphs
    c = TCanvas('c_%d' % phi)
    graphs = TMultiGraph()
    for s, datalist in datas.iteritems():
        data = DataErrors.fromLists(*zip(*datalist))
        g = data.makeGraph('g_%d_%d' % (phi, s))
        g.SetMarkerColor(seriescolors[s])
        g.SetLineColor(seriescolors[s])
        graphs.Add(g)
    graphs.Draw('AP')
    gPad.Update()
    setMultiGraphTitle(graphs, 'Druck p / mPa', '#tau / ns')

    if fit:
        fit = Fitter('fit_%d' % phi, 'pol1(0)')
        fit.function.SetNpx(1000)
        fit.setParam(0, '#tau_{0}', 119)
        fit.setParam(1, 'm', 0.5)
        fit.fit(graphs, 0, 225, 'M')
        fit.saveData('../calc/fit_tau_%02d%s.txt' % (phi, name), 'w')

    if fit:
        l = TLegend(0.6, 0.15, 0.85, 0.5)
    else:
        l = TLegend(0.6, 0.15, 0.85, 0.3)
    for i, graph in enumerate(graphs.GetListOfGraphs()):
        l.AddEntry(graph, serieslabels[i], 'p')
    if fit:
        l.AddEntry(fit.function, 'Fit mit #tau(p) = #tau_{0} + m * p', 'l')
        fit.addParamsToLegend(l, [('%.1f', '%.1f'), ('%.2f', '%.2f')], chisquareformat='%.2f', advancedchi=True, units=['ns', 'ns / mPa'])
    l.Draw()

    c.Update()
    c.Print('../img/taus_%02d%s.pdf' % (phi, name), 'pdf')


def makeFit(datalist, phi, name=''):
    data = DataErrors.fromLists(*zip(*datalist))
    c = TCanvas('c_fit_%d' % phi, '', 1280, 720)
    g = data.makeGraph('g_fit_%d' % phi, 'Druck p / mPa', '#tau / ns')
    g.GetXaxis().SetLimits(0, max(data.getX()) * 1.1)
    g.Draw('AP')

    fit = Fitter('fit_%d' % phi, 'pol1(0)')
    fit.setParam(0, '#tau_{0}', 119)
    fit.setParam(1, 'm', 0.5)
    fit.fit(g, 0, 225, 'M')
    fit.saveData('../calc/fit_tau_%02d%s.txt' % (phi, name), 'w')

    l = TLegend(0.55, 0.15, 0.85, 0.4)
    l.SetTextSize(0.03)
    l.AddEntry(g, 'Lebensdauern (aus Fits)', 'p')
    l.AddEntry(fit.function, 'Fit mit #tau(p) = #tau_{0} + m * p', 'l')
    fit.addParamsToLegend(l, [('%.1f', '%.1f'), ('%.2f', '%.2f')], chisquareformat='%.2f', advancedchi=True, units=['ns', 'ns / mPa'])
    l.Draw()

    g.SetMinimum(min(fit.params[0]['value'], min(data.getY()) * 0.975))

    c.Update()
    c.Print('../img/taus_fit_%02d%s.pdf' % (phi, name), 'pdf')


def main():
    phis = [0, 45, 90]
    tempDict = loadTempDict()
    for phi in phis:
        # read data
        datalist = loadCSVToList('../calc/taus_%02d.txt' % phi)
        datas = {0: [], 1: [], 2: []}
        for T, tau, stau, fitphi, sfitphi in datalist:
            p, sp = tempDict[T]
            datas[TempToSeries(T)].append((p, tau, sp, stau))  # sort in right series list

        printGraph(datas, phi)
        printGraph(datas, phi, '_total', True)

        del datas[0]
        printGraph(datas, phi, '_day2', True)

        del datas[2]
        printGraph(datas, phi, '_partial', True)


if __name__ == '__main__':
    setupROOT()
    main()
