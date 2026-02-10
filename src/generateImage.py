#### import the simple module from the paraview
from paraview.simple import *

#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

import glob
import os

def generateImage(algo_name, year, date, hour):
    """
    Generate paraview images automatically based on algorithm type
    :param algo_name: algorithm folder name
    :param year: year e.g. 1996
    :param date: date e.g. 364 (0 - 165)
    :param hour: 0 - 3
    :return:
    """

    # get active view
    renderView1 = GetActiveViewOrCreate('RenderView')
    # get layout
    layout1 = GetLayout()
    # split cell
    layout1.SplitVertical(0, 0.5)
    # set active view
    SetActiveView(None)

    ivt_name = "ivt_" + str(year) + "_" + str(date) + "_" + str(hour) + ".vti"
    ivt_path = "MERRA2IVT/ivt_" + str(year) + "/" + ivt_name

    # Visualize IVT
    # create a new 'XML Image Data Reader'
    ivt_vti = XMLImageDataReader(registrationName=ivt_name, FileName=[ivt_path])
    # Properties modified on ivt_1996_364_0vti
    ivt_vti.TimeArray = 'None'
    # Create a new 'Render View'
    renderView2 = CreateView('RenderView')
    renderView2.AxesGrid = 'GridAxes3DActor'
    renderView2.StereoType = 'Crystal Eyes'
    renderView2.CameraFocalDisk = 1.0
    # show data in view
    ivtDisplay = Show(ivt_vti, renderView2, 'UniformGridRepresentation')
    # trace defaults for the display properties.
    ivtDisplay.Representation = 'Slice'
    # add view to a layout so it's visible in UI
    AssignViewToLayout(view=renderView2, layout=layout1, hint=2)
    # get color transfer function/color map for 'ivt_x'
    ivt_xLUT = GetColorTransferFunction('ivt_x')
    ivt_xPWF = GetOpacityTransferFunction('ivt_x')
    # reset view to fit data
    renderView2.ResetCamera(False)
    # changing interaction mode based on data extents
    renderView2.InteractionMode = '2D'
    renderView2.CameraPosition = [287.5, 180.0, 10000.0]
    renderView2.CameraFocalPoint = [287.5, 180.0, 0.0]
    # show color bar/color legend
    ivtDisplay.SetScalarBarVisibility(renderView2, True)
    # update the view to ensure updated data information
    renderView2.Update()
    # change representation type
    ivtDisplay.SetRepresentationType('Surface')
    # set scalar coloring
    ColorBy(ivtDisplay, ('POINTS', 'ivt_magnitude'))
    # Hide the scalar bar for this color map if no visible data is colored by it.
    HideScalarBarIfNotNeeded(ivt_xLUT, renderView2)
    # rescale color and/or opacity maps used to include current data range
    ivtDisplay.RescaleTransferFunctionToDataRange(True, False)
    # show color bar/color legend
    ivtDisplay.SetScalarBarVisibility(renderView2, False)

    # Add land lines
    # create a new 'XML MultiBlock Data Reader'
    coastline0360_transformvtm = XMLMultiBlockDataReader(registrationName='coastline0-360_transform.vtm',
                                                         FileName=['coastline0-360_transform.vtm'])
    # show data in view
    coastline0360_transformvtmDisplay = Show(coastline0360_transformvtm, renderView2, 'UnstructuredGridRepresentation')
    # trace defaults for the display properties.
    coastline0360_transformvtmDisplay.Representation = 'Surface'
    # update the view to ensure updated data information
    renderView2.Update()
    # set scalar coloring
    ColorBy(coastline0360_transformvtmDisplay, ('FIELD', 'vtkBlockColors'))
    # show color bar/color legend
    coastline0360_transformvtmDisplay.SetScalarBarVisibility(renderView2, True)
    # get color transfer function/color map for 'vtkBlockColors'
    vtkBlockColorsLUT = GetColorTransferFunction('vtkBlockColors')
    # turn off scalar coloring
    ColorBy(coastline0360_transformvtmDisplay, None)
    # Hide the scalar bar for this color map if no visible data is colored by it.
    HideScalarBarIfNotNeeded(vtkBlockColorsLUT, renderView2)
    # change solid color
    coastline0360_transformvtmDisplay.AmbientColor = [1.0, 0.6666666666666666, 0.0]
    coastline0360_transformvtmDisplay.DiffuseColor = [1.0, 0.6666666666666666, 0.0]
    # Properties modified on coastline0360_transformvtmDisplay
    coastline0360_transformvtmDisplay.LineWidth = 2.0

    # Visualize AR topological axes in the pacific/north American region
    axes_dir = "Algorithms/" + algo_name + "/GraphAxis/" + "GraphAxis_" + str(year) + "_" + str(date) + "_" + str(
        hour) + "/"
    print(axes_dir)
    axes_list = glob.glob(axes_dir + 'axis_*.vtp')
    print(axes_list)
    for axis_path in axes_list:
        axis_file = axis_path.split("/")[-1]
        print(axis_file)
        axis_vtp = XMLPolyDataReader(registrationName=axis_file, FileName=[axis_path])
        axis_vtp.TimeArray = 'None'
        axis_vtpDisplay = Show(axis_vtp, renderView2, 'GeometryRepresentation')
        axis_vtpDisplay.Representation = 'Surface'
        renderView2.Update()
        SetActiveSource(axis_vtp)
        axis_vtpDisplay.AmbientColor = [1.0, 1.0, 0.0]
        axis_vtpDisplay.DiffuseColor = [1.0, 1.0, 0.0]
        axis_vtpDisplay.LineWidth = 5.0

    # Visualize catalog AR Shape
    AR_shape_name = "ARCatalog_" + str(year) + "_shape_" + str(date) + "_" + str(hour) + ".vtu"
    AR_shape_path = "Algorithms/" + algo_name + "/ARCatalog/ARCatalog_" + str(year) + "/shape/" + AR_shape_name
    # create a new 'XML Unstructured Grid Reader'
    AR_shape_vtu = XMLUnstructuredGridReader(registrationName=AR_shape_name, FileName=[AR_shape_path])
    # Properties modified on aRCatalog_1996_shape_364_0vtu
    AR_shape_vtu.TimeArray = 'None'
    # show data in view
    AR_shape_Display = Show(AR_shape_vtu, renderView2, 'UnstructuredGridRepresentation')
    # trace defaults for the display properties.
    AR_shape_Display.Representation = 'Surface'
    # show color bar/color legend
    AR_shape_Display.SetScalarBarVisibility(renderView2, True)
    # update the view to ensure updated data information
    renderView2.Update()
    # get color transfer function/color map for 'AR_shape'
    aR_shapeLUT = GetColorTransferFunction('AR_shape')
    # get opacity transfer function/opacity map for 'AR_shape'
    aR_shapePWF = GetOpacityTransferFunction('AR_shape')
    # turn off scalar coloring
    ColorBy(AR_shape_Display, None)
    # Hide the scalar bar for this color map if no visible data is colored by it.
    HideScalarBarIfNotNeeded(aR_shapeLUT, renderView2)

    # Visualize guan_waliser catalog axis
    if algo_name == 'guan_waliser_v3':
        gw_axis_name = "ARCatalog_" + str(year) + "_axis_" + str(date) + "_" + str(hour) + ".vtu"
        gw_axis_dir = "Algorithms/" + algo_name + "/ARCatalog/ARCatalog_" + str(year) + "/axis/"
        gw_axis_vtu = XMLUnstructuredGridReader(registrationName=gw_axis_name, FileName=[gw_axis_dir + gw_axis_name])
        gw_axis_vtu.TimeArray = 'None'
        gw_axis_Display = Show(gw_axis_vtu, renderView2, 'UnstructuredGridRepresentation')
        gw_axis_Display.Representation = 'Surface'
        gw_axis_Display.SetScalarBarVisibility(renderView2, True)
        renderView2.Update()
        gw_axisLUT = GetColorTransferFunction('AR_axis')
        ColorBy(gw_axis_Display, None)
        HideScalarBarIfNotNeeded(gw_axisLUT, renderView2)
        gw_axis_Display.AmbientColor = [1.0, 0.0, 0.0]
        gw_axis_Display.DiffuseColor = [1.0, 0.0, 0.0]
        gw_axis_Display.PointSize = 5.0

    # Save screenshot with appropriate zoom level
    # layout/tab size in pixels
    layout1.SetSize(1930, 1609)

    # current camera placement for renderView2
    renderView2.InteractionMode = '2D'
    renderView2.CameraPosition = [349.91251759520014, 251.9356232868754, 10000.0]
    renderView2.CameraFocalPoint = [349.91251759520014, 251.9356232868754, 0.0]
    renderView2.CameraParallelScale = 73.81967774882307

    # save screenshot
    screenshot_dir = "figures/Algorithms/" + str(year) + "_" + str(date) + "_" + str(hour) + "/"
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_name = algo_name + "_" + str(year) + "_" + str(date) + "_" + str(hour) + ".png"
    SaveScreenshot(screenshot_dir + screenshot_name, renderView2, ImageResolution=[1930, 804])


# ================================================================
# addendum: following script captures some of the application
# state to faithfully reproduce the visualization during playback
# ================================================================

# --------------------------------
# saving layout sizes for layouts

# layout/tab size in pixels
# layout1.SetSize(1930, 1611)

# -----------------------------------
# saving camera placements for views

# current camera placement for renderView2
# renderView2.InteractionMode = '2D'
# renderView2.CameraPosition = [349.91251759520014, 251.9356232868754, 10000.0]
# renderView2.CameraFocalPoint = [349.91251759520014, 251.9356232868754, 0.0]
# renderView2.CameraParallelScale = 73.81967774882307

# --------------------------------------------
# uncomment the following to render all views
# RenderAllViews()
# alternatively, if you want to write images, you can use SaveScreenshot(...).


if __name__ == "__main__":
    dates = [306, 308, 310]
    for date_i in dates:
        for hour_i in range(0, 2):
            # generateImage("guan_waliser_v3", 2006, date_i, hour_i)
            # generateImage("ar_connect", 2006, date_i, hour_i)
            # generateImage("mundhenk_v3", 2006, date_i, hour_i)
            generateImage("teca_bard_v1.0.1", 2006, date_i, hour_i)
