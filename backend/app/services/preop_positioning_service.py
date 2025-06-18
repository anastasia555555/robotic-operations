import vtk
import numpy as np
import SimpleITK as sitk
from vtkmodules.util import numpy_support
import random

positioning_handlers = {}

class PositioningHandler:
    def __init__(self, nrrd_path, axis="z", descending=True):
        self.bone_model_path = nrrd_path
        self.sort_axis = axis
        self.sort_descending = descending

        self.bone_model = None
        self.bone_actor = None
        self.surface_points = []
        self.registered_points = {}
        self.prediction_points = []
        self.predicted_world_coords = []
        self.prediction_registered = {}
        self.prediction_errors = None

        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.SetOffScreenRendering(True)
        self.render_window.AddRenderer(self.renderer)

        self.load_bone_model()
        if self.bone_actor:
            self.renderer.AddActor(self.bone_actor)
        self.renderer.SetBackground(14 / 255, 14 / 255, 15 / 255)
        self.set_camera("front")

    def load_bone_model(self):
        image = sitk.ReadImage(self.bone_model_path)
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

        contour_filter = vtk.vtkContourFilter()
        contour_filter.SetInputConnection(gaussian.GetOutputPort())
        contour_filter.SetValue(0, 0.5)
        contour_filter.Update()

        smoother = vtk.vtkSmoothPolyDataFilter()
        smoother.SetInputConnection(contour_filter.GetOutputPort())
        smoother.SetNumberOfIterations(50)
        smoother.SetRelaxationFactor(0.1)
        smoother.FeatureEdgeSmoothingOff()
        smoother.BoundarySmoothingOn()
        smoother.Update()

        center_transform = vtk.vtkTransform()
        bounds = smoother.GetOutput().GetBounds()
        center_transform.Translate(
            -0.5 * (bounds[0] + bounds[1]),
            -0.5 * (bounds[2] + bounds[3]),
            -0.5 * (bounds[4] + bounds[5])
        )

        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputConnection(smoother.GetOutputPort())
        transform_filter.SetTransform(center_transform)
        transform_filter.Update()

        self.bone_model = transform_filter.GetOutput()
        self.surface_points = self._sample_surface_points(
            10, axis=self.sort_axis, descending=self.sort_descending
        )

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.bone_model)
        mapper.ScalarVisibilityOff()

        self.bone_actor = vtk.vtkActor()
        self.bone_actor.SetMapper(mapper)
        self.bone_actor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.bone_actor.GetProperty().SetInterpolationToPhong()
        self.bone_actor.GetProperty().SetSpecular(0.4)
        self.bone_actor.GetProperty().SetSpecularPower(20)

    def _sample_surface_points(self, num, axis="z", descending=True):
        axis_map = {"x": 0, "y": 1, "z": 2}
        if axis not in axis_map:
            raise ValueError("axis must be one of: 'x', 'y', 'z'")
        axis_index = axis_map[axis]

        all_points = [
            np.array(self.bone_model.GetPoint(i))
            for i in range(self.bone_model.GetNumberOfPoints())
        ]

        sorted_points = sorted(
            all_points,
            key=lambda pt: pt[axis_index],
            reverse=descending
        )

        seen_keys = set()
        deduped = []
        for pt in sorted_points:
            if axis == "z":
                key = (int(round(pt[0])), int(round(pt[1])))
            elif axis == "y":
                key = (int(round(pt[0])), int(round(pt[2])))
            else:
                key = (int(round(pt[1])), int(round(pt[2])))
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(pt)

        cutoff = int(len(deduped) * 0.25)
        upper_quartile = deduped[:cutoff]
        if len(upper_quartile) < num:
            raise ValueError(
                f"Only {len(upper_quartile)} unique points; can't select {num}."
            )

        selected = random.sample(upper_quartile, num)
        return selected

    def _generate_predictions(self):
        self.prediction_points = [(10 + i, pt) for i, pt in enumerate(
            self._sample_surface_points(3, axis=self.sort_axis, descending=self.sort_descending)
        )]

        model_pts = np.array([self.surface_points[i] for i in self.registered_points_keys[:10]])
        world_pts = np.array([self.registered_points[k] for k in self.registered_points_keys[:10]])

        src = vtk.vtkPoints()
        tgt = vtk.vtkPoints()
        for m, w in zip(model_pts, world_pts):
            src.InsertNextPoint(m)
            tgt.InsertNextPoint(w)

        tfm = vtk.vtkLandmarkTransform()
        tfm.SetSourceLandmarks(src)
        tfm.SetTargetLandmarks(tgt)
        tfm.SetModeToRigidBody()
        tfm.Update()

        self.predicted_world_coords = [
            np.array(tfm.TransformPoint(pt)) for _, pt in self.prediction_points
        ]

    def _compute_prediction_errors(self):
        actual = [self.prediction_registered[idx] for idx, _ in self.prediction_points]
        self.prediction_errors = [
            float(np.linalg.norm(pred - act))
            for pred, act in zip(self.predicted_world_coords, actual)
        ]

    @property
    def registered_points_keys(self):
        return list(self.registered_points.keys())

    def register_point(self, index: int, world_coords: list[float]):
        world = np.array(world_coords)
        self.registered_points[index] = world

        if len(self.registered_points) == 10 and not self.prediction_points:
            self._generate_predictions()

        prediction_point_indices = [idx for idx, _ in self.prediction_points]
        if index in prediction_point_indices:
            self.prediction_registered[index] = world

    def check_and_compute_prediction_errors(self):
        if (
            len(self.prediction_registered) == len(self.prediction_points)
            and self.prediction_points
        ):
            self._compute_prediction_errors()

    def get_prediction_errors(self) -> list[float]:
        return self.prediction_errors

    def set_camera(self, view="front"):
        bounds = self.bone_model.GetBounds()
        center_x = 0.5 * (bounds[0] + bounds[1])
        center_y = 0.5 * (bounds[2] + bounds[3])
        center_z = 0.5 * (bounds[4] + bounds[5])
        center = (center_x, center_y, center_z)

        directions = {
            "front": (0, 250, 0),
            "back": (0, -250, 0),
            "other side": (250, 0, 0),
            "side": (-250, 0, 0),
            "top": (0, 0, 250),
            "bottom": (0, 0, -250),
        }
        rel_pos = directions.get(view, directions["front"])
        position = tuple(center[i] + rel_pos[i] for i in range(3))

        camera = vtk.vtkCamera()
        camera.SetPosition(*position)
        camera.SetFocalPoint(*center)
        camera.SetViewUp(0, 0, 1 if view in ["front", "back", "side", "other side"] else 0)

        self.renderer.SetActiveCamera(camera)
        self.renderer.ResetCameraClippingRange()

    def render_png_bytes(self) -> bytes:
        self.render_window.SetSize(1024, 1024)

        actors_to_remove = []
        for actor in self.renderer.GetActors():
            if actor != self.bone_actor:
                actors_to_remove.append(actor)
        for actor in actors_to_remove:
            self.renderer.RemoveActor(actor)

        for idx, pt in enumerate(self.surface_points):
            if idx in self.registered_points:
                color = (0.0, 1.0, 0.0)
            else:
                color = (1.0, 0.0, 0.0)
            self._add_sphere(pt, color, label=idx)

        for idx, pt in self.prediction_points:
            self._add_sphere(pt, (0.0, 0.0, 1.0), label=idx)

        self.render_window.Render()
        win2img = vtk.vtkWindowToImageFilter()
        win2img.SetInput(self.render_window)
        win2img.Update()

        writer = vtk.vtkPNGWriter()
        writer.SetInputConnection(win2img.GetOutputPort())
        writer.WriteToMemoryOn()
        writer.Write()
        return bytes(memoryview(writer.GetResult()))

    def _add_sphere(self, pt, color, label=None):
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(*pt)
        sphere.SetRadius(1.0)
        sphere.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(sphere.GetOutput())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        self.renderer.AddActor(actor)

        if label is not None:
            text_source = vtk.vtkVectorText()
            text_source.SetText(str(label))

            text_mapper = vtk.vtkPolyDataMapper()
            text_mapper.SetInputConnection(text_source.GetOutputPort())

            text_actor = vtk.vtkFollower()
            text_actor.SetMapper(text_mapper)
            text_actor.SetScale(3.0, 3.0, 3.0)
            text_actor.GetProperty().SetColor(*color)

            offset_pt = np.array(pt) + np.array([1.5, 1.5, 1.5])
            text_actor.SetPosition(*offset_pt)
            text_actor.SetCamera(self.renderer.GetActiveCamera())

            text_actor.GetProperty().SetOpacity(1.0)
            text_actor.GetProperty().SetRepresentationToSurface()
            text_actor.GetProperty().SetLighting(False)
            text_actor.GetProperty().SetAmbient(1.0)
            text_actor.GetProperty().SetDiffuse(0.0)
            text_actor.GetProperty().SetSpecular(0.0)
            text_actor.GetProperty().SetRenderLinesAsTubes(True)
            text_actor.GetProperty().SetLineWidth(1.5)

            self.renderer.AddActor(text_actor)

    def get_all_points_status(self) -> list[dict]:
        points_status = []

        for idx, pt in enumerate(self.surface_points):
            points_status.append({
                "index": idx,
                "type": "main",
                "model_coords": pt.tolist(),
                "world_coords": self.registered_points.get(idx).tolist() if idx in self.registered_points else None
            })

        for idx, pt in self.prediction_points:
            points_status.append({
                "index": idx,
                "type": "prediction",
                "model_coords": pt.tolist(),
                "world_coords": self.prediction_registered.get(idx).tolist() if idx in self.prediction_registered else None
            })

        return points_status

    def get_registered_main_points(self) -> list[tuple[int, np.ndarray, np.ndarray]]:
        result = []
        for idx, model_pt in enumerate(self.surface_points[:10]):
            if idx in self.registered_points:
                world_pt = self.registered_points[idx]
                result.append((idx, model_pt, world_pt))
        return result


def remove_positioning_handler(i_operation_plan: int) -> bool:
    if i_operation_plan in positioning_handlers:
        del positioning_handlers[i_operation_plan]
        return True
    return False

