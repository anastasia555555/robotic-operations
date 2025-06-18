import vtk
import SimpleITK as sitk
from vtkmodules.util import numpy_support
import numpy as np

def load_nrrd_as_actor(nrrd_path):
    image = sitk.ReadImage(nrrd_path)
    np_array = sitk.GetArrayFromImage(image).astype(np.float32)
    np_array = np.transpose(np_array, (2, 1, 0))

    vtk_image = vtk.vtkImageData()
    vtk_image.SetSpacing(image.GetSpacing())
    vtk_image.SetOrigin(image.GetOrigin())
    vtk_image.SetExtent(0, np_array.shape[0] - 1,
                        0, np_array.shape[1] - 1,
                        0, np_array.shape[2] - 1)

    vtk_array = numpy_support.numpy_to_vtk(
        num_array=np_array.ravel(order='F'),
        deep=True,
        array_type=vtk.VTK_FLOAT
    )
    vtk_image.GetPointData().SetScalars(vtk_array)

    gaussian = vtk.vtkImageGaussianSmooth()
    gaussian.SetInputData(vtk_image)
    gaussian.SetRadiusFactors(1.5, 1.5, 1.5)
    gaussian.SetStandardDeviations(1.0, 1.0, 1.0)
    gaussian.Update()

    contour = vtk.vtkContourFilter()
    contour.SetInputConnection(gaussian.GetOutputPort())
    contour.SetValue(0, 0.5)
    contour.Update()

    smoother = vtk.vtkSmoothPolyDataFilter()
    smoother.SetInputConnection(contour.GetOutputPort())
    smoother.SetNumberOfIterations(50)
    smoother.SetRelaxationFactor(0.1)
    smoother.BoundarySmoothingOn()
    smoother.Update()

    bounds = smoother.GetOutput().GetBounds()
    center_transform = vtk.vtkTransform()
    center_transform.Translate(
        -0.5 * (bounds[0] + bounds[1]),
        -0.5 * (bounds[2] + bounds[3]),
        -0.5 * (bounds[4] + bounds[5])
    )

    transform_filter = vtk.vtkTransformPolyDataFilter()
    transform_filter.SetInputConnection(smoother.GetOutputPort())
    transform_filter.SetTransform(center_transform)
    transform_filter.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(transform_filter.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(1.0, 1.0, 1.0)

    return actor

def render_nrrd(nrrd_path):
    actor = load_nrrd_as_actor(nrrd_path)

    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(14/255, 14/255, 15/255)

    camera = vtk.vtkCamera()
    camera.SetPosition(0, 500, 0)
    camera.SetFocalPoint(0, 0, 0)
    camera.SetViewUp(0, 0, 1)
    renderer.SetActiveCamera(camera)
    renderer.ResetCamera()

    window = vtk.vtkRenderWindow()
    window.AddRenderer(renderer)
    window.SetSize(800, 800)

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(window)

    window.Render()
    interactor.Start()

if __name__ == "__main__":
    nrrd_path = ""
    render_nrrd(nrrd_path)
