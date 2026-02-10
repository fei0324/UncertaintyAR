from paraview.simple import *

import vtk
import vtk.util.numpy_support as VN
import numpy as np
import json
import sys


def getMSCfromIVT():
    inputIVT_path = sys.argv[1]
    sim_threshold = sys.argv[2]
    cp_savepath = sys.argv[3]
    msc_savepath = sys.argv[4]

    inputIVT = XMLImageDataReader(registrationName='inputIVT', FileName=[inputIVT_path])
    inputIVT.TimeArray = 'None'
    UpdatePipeline(time=0.0, proxy=inputIVT)

    ttkSimp = TTKTopologicalSimplificationByPersistence(registrationName='TTKSimp', Input=inputIVT)
    # set active source
    SetActiveSource(ttkSimp)
    ttkSimp.PersistenceThreshold = float(sim_threshold)
    ttkSimp.InputArray = ['POINTS', 'ivt_magnitude']

    UpdatePipeline(time=0.0, proxy=ttkSimp)

    # create a new 'TTK MorseSmaleComplex'
    ttkMSC = TTKMorseSmaleComplex(registrationName='TTKMorseSmaleComplex',
                                                 Input=ttkSimp)
    # Properties modified on tTKMorseSmaleComplex1
    ttkMSC.ScalarField = ['POINTS', 'ivt_magnitude']
    ttkMSC.Descending1Separatrices = 0
    ttkMSC.SaddleConnectors = 0
    ttkMSC.DescendingSegmentation = 0

    UpdatePipeline(time=0.0, proxy=ttkMSC)

    # save critical points data
    SaveData(cp_savepath, proxy=ttkMSC,
             PointDataArrays=['CellDimension', 'CellId', 'IsOnBoundary', 'ManifoldSize', 'ivt_magnitude',
                              'ttkVertexScalarField'],
             DataMode='Binary')

    # get active source
    ttkMSC_1_sep = GetActiveSource()
    # save 1-separatrices
    SaveData(msc_savepath,
             proxy=OutputPort(ttkMSC_1_sep, 1),
             PointDataArrays=['CellDimension', 'CellId', 'ttkMaskScalarField'],
             CellDataArrays=['DestinationId', 'NumberOfCriticalPointsOnBoundary', 'SeparatrixFunctionDifference',
                             'SeparatrixFunctionMaximum', 'SeparatrixFunctionMinimum', 'SeparatrixId', 'SeparatrixType',
                             'SourceId'],
             DataMode='Binary')


if __name__ == "__main__":
    getMSCfromIVT()