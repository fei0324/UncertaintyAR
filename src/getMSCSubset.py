from paraview.simple import *

import vtk
import vtk.util.numpy_support as VN
import numpy as np
import json
import sys


def getMSCSubset(msc, AR_cp, jsonDir):
    """
    Get the subset of MSC that start or end at the critical points inside of the AR boundaries
    :param msc: msc vtp file saved from Paraview
    :param AR_cp: critical points inside of AR boundaries
    :param jsonDir: json directory to save the edge data
    :return: the MSC saved in a json file with edge endpoints being the critical sources and destinations
    """

    edges = []

    # the cp here are CellId, different from Cell ID in Paraview
    for cp in AR_cp:
        # check for cps that are destinations first (a cp cannot be both destination and source???)
        # print('(DestinationId == ' + str(cp) + ')')
        SetActiveSource(msc)
        QuerySelect(QueryString='(DestinationId == ' + str(cp) + ')', FieldType='CELL', InsideOut=0)
        extractSelection_cp_target = ExtractSelection(Input=msc)
        cpData_t = paraview.servermanager.Fetch(extractSelection_cp_target)
        if cpData_t.GetCellData().GetNumberOfArrays() > 0:
            sourceList = set(VN.vtk_to_numpy(cpData_t.GetCellData().GetArray("SourceId")))
            # print(sourceList)
            # every pair of (source, target) is one edge in the graph model of msc
            for source in sourceList:
                edge_dict = {'source': int(source), 'target': int(cp)}
                SetActiveSource(msc)
                querySourceTarget = '(DestinationId == ' + str(cp) + ')&(SourceId == ' + str(source) + ')'
                # print(querySourceTarget)
                QuerySelect(QueryString=querySourceTarget, FieldType='CELL', InsideOut=0)
                lines = ExtractSelection(Input=msc)
                lineData = paraview.servermanager.Fetch(lines)
                numOfLines = lineData.GetNumberOfCells()
                # print("number of lines in the edge", numOfLines)

                # each line in lineData is a cell in an edge
                edge_cells = []
                cellIds = vtk.vtkIdList() # cell ids store to
                for i in range(numOfLines):
                    lineData.GetCellPoints(i, cellIds) # get ids of points of a given cell
                    assert cellIds.GetNumberOfIds() == 2 # every line has two end points
                    edge_cells.append([lineData.GetPoint(cellIds.GetId(0)), lineData.GetPoint(cellIds.GetId(1))])

                edge_dict['cells'] = edge_cells
                edges.append(edge_dict)

        # check for cps that are sources
        # print('(SourceId == ' + str(cp) + ')')
        SetActiveSource(msc)
        QuerySelect(QueryString='(SourceId == ' + str(cp) + ')', FieldType='CELL', InsideOut=0)
        extractSelection_cp_source = ExtractSelection(Input=msc)
        cpData_s = paraview.servermanager.Fetch(extractSelection_cp_source)
        if cpData_s.GetCellData().GetNumberOfArrays() > 0:
            targetList = set(VN.vtk_to_numpy(cpData_s.GetCellData().GetArray("DestinationId")))
            # print(targetList)
            # every pair of (source, target) is one edge in the graph model of msc
            for target in targetList:
                edge_dict = {'source': int(cp), 'target': int(target)}
                SetActiveSource(msc)
                querySourceTarget = '(DestinationId == ' + str(target) + ')&(SourceId == ' + str(cp) + ')'
                # print(querySourceTarget)
                QuerySelect(QueryString=querySourceTarget, FieldType='CELL', InsideOut=0)
                lines = ExtractSelection(Input=msc)
                lineData = paraview.servermanager.Fetch(lines)
                numOfLines = lineData.GetNumberOfCells()
                # print("number of lines in the edge", numOfLines)

                # each line in lineData is a cell in an edge
                edge_cells = []
                cellIds = vtk.vtkIdList()  # cell ids store to
                for i in range(numOfLines):
                    lineData.GetCellPoints(i, cellIds)  # get ids of points of a given cell
                    assert cellIds.GetNumberOfIds() == 2  # every line has two end points
                    edge_cells.append(
                        [lineData.GetPoint(cellIds.GetId(0)), lineData.GetPoint(cellIds.GetId(1))])

                edge_dict['cells'] = edge_cells
                edges.append(edge_dict)

    data = {}
    for i, edge in enumerate(edges):
        data[i] = edge

    with open(jsonDir, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def getMSCSubsetWrapper():

    msc_filename = sys.argv[1]
    cp_outdir = sys.argv[2]
    AR_id = sys.argv[3]
    outdir = sys.argv[4]

    cpInAR_cellid_file = cp_outdir + "ARCP_cellid_" + str(AR_id) + ".npy"

    msc_name = msc_filename.split("/")[-1]
    print(msc_name)

    mscvtp = XMLPolyDataReader(registrationName=msc_name, FileName=[msc_filename])
    mscvtp.CellArrayStatus = ['SourceId', 'DestinationId', 'SeparatrixId', 'SeparatrixType',
                                             'SeparatrixFunctionMaximum', 'SeparatrixFunctionMinimum',
                                             'SeparatrixFunctionDifference', 'NumberOfCriticalPointsOnBoundary',
                                             'vtkOriginalCellIds']
    mscvtp.PointArrayStatus = ['ttkMaskScalarField', 'CellDimension', 'CellId', 'vtkOriginalPointIds']

    AR_cp = np.load(cpInAR_cellid_file)
    # print(AR_cp)

    getMSCSubset(mscvtp, AR_cp, outdir)


if __name__ == "__main__":
    getMSCSubsetWrapper()
    # create a new 'XML Unstructured Grid Reader'
    # aRCatalog_1996_shape_364_0vtu = XMLUnstructuredGridReader(registrationName='ARCatalog_1996_shape_364_0.vtu', FileName=['/Users/misskoala/Documents/Research/Summer2022/ARCatalog/ARCatalog_1996/shape/ARCatalog_1996_shape_364_0.vtu'])
    # aRCatalog_1996_shape_364_0vtu.PointArrayStatus = ['AR_shape']

    # create a new 'XML PolyData Reader'
    # ivt_1996_364_0_mscvtp = XMLPolyDataReader(registrationName='ivt_1996_364_0_msc.vtp', FileName=['/Users/misskoala/Documents/Research/Summer2022/MSCData/msc_1996_364_0.vtp'])
    # ivt_1996_364_0_mscvtp.CellArrayStatus = ['SourceId', 'DestinationId', 'SeparatrixId', 'SeparatrixType', 'SeparatrixFunctionMaximum', 'SeparatrixFunctionMinimum', 'SeparatrixFunctionDifference', 'NumberOfCriticalPointsOnBoundary', 'vtkOriginalCellIds']
    # ivt_1996_364_0_mscvtp.PointArrayStatus = ['ttkMaskScalarField', 'CellDimension', 'CellId', 'vtkOriginalPointIds']

    # create a new 'XML Image Data Reader'
    # ivt_1996_364_0vti = XMLImageDataReader(registrationName='ivt_1996_364_0.vti', FileName=['/Users/misskoala/Documents/Research/Summer2022/MERRA2IVT/ivt_1996/ivt_1996_364_0.vti'])
    # ivt_1996_364_0vti.PointArrayStatus = ['ivt_x', 'ivt_y', 'ivt_magnitude']

    # Properties modified on ivt_1996_364_0vti
    # ivt_1996_364_0vti.TimeArray = 'None'

    # UpdatePipeline(time=0.0, proxy=ivt_1996_364_0vti)

    # set active source
    # SetActiveSource(ivt_1996_364_0_mscvtp)
    #
    # AR_cp = np.load("IntermediateFiles/AR_3_cp_sim.npy")
    # print(AR_cp)
    #
    # getMSCSubset(ivt_1996_364_0_mscvtp, AR_cp, "IntermediateFiles/AR_3_edges_sim.json")
    #
    # for cp in AR_cp:
    #     print('(DestinationId == ' + str(cp) + ')')
    #     SetActiveSource(ivt_1996_364_0_mscvtp)
    #     QuerySelect(QueryString='(DestinationId == ' + str(cp) + ')', FieldType='CELL', InsideOut=0)
    #     extractSelection_cp = ExtractSelection(Input=ivt_1996_364_0_mscvtp)
    #     selectionData_cp = paraview.servermanager.Fetch(extractSelection_cp)
    #     print(selectionData_cp.GetCellData().GetArray("SourceId"))

    # create a query selection
    # QuerySelect(QueryString='(DestinationId == 273245)', FieldType='CELL', InsideOut=0)
    # QuerySelect(QueryString='(DestinationId == 273245)&(SourceId == 339259)', FieldType='CELL', InsideOut=0)

    # create a query selection
    # QuerySelect(QueryString='(id == 92763)', FieldType='CELL', InsideOut=0)

    # create a new 'Extract Selection'
    # extractSelection1 = ExtractSelection(registrationName='ExtractSelection1', Input=ivt_1996_364_0_mscvtp)

    # Access Query Selection!!!!!!!
    # selectionData = paraview.servermanager.Fetch(extractSelection1)
    # print(selectionData)
    # CellId = VN.vtk_to_numpy(selectionData.GetCellData().GetArray("SourceId"))
    # print(CellId)
    # print(VN.vtk_to_numpy(selectionData.GetPoints().GetData()))