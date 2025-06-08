import SimpleITK as sitk
import vtk
from vtkmodules.util import numpy_support
import numpy as np
from sqlalchemy.orm import Session
from app.models.bone_model import BoneModel
from app.models.prosthesis_model import ProsthesisModel
from app.models.opplan_model import OperationPlanBone, OperationPlanProsthesis
from app.models.opplan_scene_model import OperationPlanScenes
from vtkmodules.vtkCommonTransforms import vtkTransform


scene_handlers = {}

class ModelHandler:
    def __init__(self, bone_model_path: str):
        self.bone_model_path = bone_model_path
        self.prosthesis_model_path = None
        self.bone_model = None
        self.bone_actor = None
        self.prosthesis_model = None
        self.prosthesis_actor = None

        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        #self.render_window.SetOffScreenRendering(1)


        self.load_bone_model()
        if self.bone_actor:
            self.renderer.AddActor(self.bone_actor)
        self.renderer.SetBackground(14/255, 14/255, 15/255)
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

        bone_mapper = vtk.vtkPolyDataMapper()
        bone_mapper.SetInputData(self.bone_model)
        bone_mapper.ScalarVisibilityOff()

        self.bone_actor = vtk.vtkActor()
        self.bone_actor.SetMapper(bone_mapper)
        self.bone_actor.GetProperty().SetColor(1.0, 1.0, 1.0)

    def load_prosthesis_model(self, prosthesis_model_path: str):
        self.prosthesis_model_path = prosthesis_model_path
        reader = vtk.vtkOBJReader()
        reader.SetFileName(self.prosthesis_model_path)
        reader.Update()
        self.prosthesis_model = reader.GetOutput()

        prosthesis_mapper = vtk.vtkPolyDataMapper()
        prosthesis_mapper.SetInputData(self.prosthesis_model)

        self.prosthesis_actor = vtk.vtkActor()
        self.prosthesis_actor.SetMapper(prosthesis_mapper)
        self.prosthesis_actor.GetProperty().SetColor(0.0, 1.0, 0.0)

    def add_prosthesis_to_scene(self, prosthesis_model_path: str = None):
        if prosthesis_model_path and prosthesis_model_path != self.prosthesis_model_path:
            self.load_prosthesis_model(prosthesis_model_path)
        elif not self.prosthesis_actor and self.prosthesis_model_path:
            self.load_prosthesis_model(self.prosthesis_model_path)
        elif not self.prosthesis_model_path and prosthesis_model_path:
             self.load_prosthesis_model(prosthesis_model_path)

        if self.prosthesis_actor and self.prosthesis_actor not in self.renderer.GetActors():
            self.renderer.AddActor(self.prosthesis_actor)

    def remove_prosthesis_from_scene(self):
        if self.prosthesis_actor and self.prosthesis_actor in self.renderer.GetActors():
            self.renderer.RemoveActor(self.prosthesis_actor)
        self.prosthesis_model = None
        self.prosthesis_actor = None
        self.prosthesis_model_path = None


    def set_camera(self, view="front"):
        camera = vtk.vtkCamera()
        positions = {
            "front": (0, 500, 0),
            "back": (0, -500, 0),
            "left_side": (500, 0, 0),
            "right_side": (-500, 0, 0),
            "top": (0, 0, 500),
            "bottom": (0, 0, -500)
        }
        pos = positions.get(view, (0, 500, 0))
        camera.SetPosition(*pos)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        self.renderer.SetActiveCamera(camera)
        self.renderer.ResetCamera()

    def render_to_image(self, filepath: str):
        self.render_window.SetOffScreenRendering(1)
        self.render_window.Render()

        window_to_image_filter = vtk.vtkWindowToImageFilter()
        window_to_image_filter.SetInput(self.render_window)
        window_to_image_filter.ReadFrontBufferOff()
        window_to_image_filter.Update()

        writer = vtk.vtkPNGWriter()
        writer.SetFileName(filepath)
        writer.SetInputConnection(window_to_image_filter.GetOutputPort())
        writer.Write()

    def slide_prosthesis_up(self, value): self._translate_prosthesis(0, 0, value)
    def slide_prosthesis_down(self, value): self._translate_prosthesis(0, 0, -value)
    def slide_prosthesis_left(self, value): self._translate_prosthesis(-value, 0, 0)
    def slide_prosthesis_right(self, value): self._translate_prosthesis(value, 0, 0)
    def slide_prosthesis_forward(self, value): self._translate_prosthesis(0, value, 0)
    def slide_prosthesis_backward(self, value): self._translate_prosthesis(0, -value, 0)

    def _translate_prosthesis(self, x, y, z):
        if not self.prosthesis_actor:
            return
        current_transform = self.prosthesis_actor.GetUserTransform()
        if current_transform is None:
            current_transform = vtk.vtkTransform()
        transform = vtk.vtkTransform()
        transform.DeepCopy(current_transform)
        transform.Translate(x, y, z)

        self.prosthesis_actor.SetUserTransform(transform)

    def scale_prosthesis(self, scale_x: float, scale_y: float, scale_z: float):
        """
        Scales the prosthesis actor by the given factors.

        Args:
            scale_x (float): Scaling factor for the X-axis.
            scale_y (float): Scaling factor for the Y-axis.
            scale_z (float): Scaling factor for the Z-axis.
        """
        if not self.prosthesis_actor:
            print("Warning: Attempted to scale prosthesis, but no prosthesis actor is present.")
            return

        current_transform = self.prosthesis_actor.GetUserTransform()
        if current_transform is None:
            current_transform = vtk.vtkTransform()


        new_transform = vtk.vtkTransform()
        new_transform.DeepCopy(current_transform)
        new_transform.Scale(scale_x, scale_y, scale_z)


        self.prosthesis_actor.SetUserTransform(new_transform)

    def rotate_prosthesis(self, axis: str, angle: float):
        if not self.prosthesis_actor:
            raise ValueError("No prosthesis actor to rotate.")

        axis = axis.lower()
        if axis not in ["x", "y", "z"]:
            raise ValueError("Invalid axis. Use 'x', 'y', or 'z'.")

        current_transform = self.prosthesis_actor.GetUserTransform()
        if current_transform is None:
            current_transform = vtk.vtkTransform()

        new_transform = vtk.vtkTransform()
        new_transform.DeepCopy(current_transform)

        if axis == "x":
            new_transform.RotateX(angle)
        elif axis == "y":
            new_transform.RotateY(angle)
        elif axis == "z":
            new_transform.RotateZ(angle)

        self.prosthesis_actor.SetUserTransform(new_transform)

    def get_actor_matrix(self, actor: vtk.vtkActor) -> list[float]:
        transform = actor.GetUserTransform()
        if transform is None:

            return np.identity(4).flatten().tolist()

        matrix = transform.GetMatrix()

        return [matrix.GetElement(i, j) for i in range(4) for j in range(4)]


    def set_actor_matrix(self, actor: vtk.vtkActor, matrix_flat: list[float]):
        vtk_matrix = vtk.vtkMatrix4x4()
        for i in range(4):
            for j in range(4):
                vtk_matrix.SetElement(i, j, matrix_flat[i * 4 + j])
        transform = vtk.vtkTransform()
        transform.SetMatrix(vtk_matrix)
        actor.SetUserTransform(transform)

    def get_prosthesis_matrix(self) -> list[float]:
        if not self.prosthesis_actor:
            return None
        return self.get_actor_matrix(self.prosthesis_actor)

    def set_prosthesis_matrix(self, matrix: list[float]):
        if not self.prosthesis_actor:
            print("Warning: Attempted to set prosthesis matrix, but no prosthesis actor is present.")
            return
        self.set_actor_matrix(self.prosthesis_actor, matrix)


    def get_bone_matrix(self) -> list[float]:
        return self.get_actor_matrix(self.bone_actor)

    def set_bone_matrix(self, matrix: list[float]):
        self.set_actor_matrix(self.bone_actor, matrix)


def create_model_handler(i_operation_plan: int, db: Session):
    if i_operation_plan in scene_handlers:
        return scene_handlers[i_operation_plan]

    op_bone = db.query(OperationPlanBone).filter_by(i_operation_plan=i_operation_plan).first()
    if not op_bone:
        raise ValueError("No bone found for this operation plan")

    bone_model_db = db.query(BoneModel).filter_by(i_3d_bone_model=op_bone.i_3d_bone_model).first()
    if not bone_model_db:
        raise ValueError("Bone model not found")

    handler = ModelHandler(bone_model_db.path_to_model)

    op_prosthesis = db.query(OperationPlanProsthesis).filter_by(i_operation_plan=i_operation_plan).first()
    if op_prosthesis:
        prosthesis_model_db = db.query(ProsthesisModel).filter_by(i_3d_prosthesis_model=op_prosthesis.i_3d_prosthesis_model).first()
        if prosthesis_model_db:
            handler.add_prosthesis_to_scene(prosthesis_model_db.path_to_model)

    scene_handlers[i_operation_plan] = handler
    return handler

def remove_model_handler(i_operation_plan: int):
    if i_operation_plan in scene_handlers:
        del scene_handlers[i_operation_plan]


def restore_positions(i_operation_plan: int, db: Session):
    try:
        handler = create_model_handler(i_operation_plan, db)
    except Exception as e:
        raise ValueError(f"Failed to prepare model handler for operation plan {i_operation_plan}: {str(e)}")


    scene = db.query(OperationPlanScenes).filter_by(i_operation_plan=i_operation_plan).first()
    if not scene:
        handler.remove_prosthesis_from_scene()
        raise ValueError(f"No saved scene data found for operation plan {i_operation_plan}.")

    bone_matrix = compose_matrix(
        [scene.bone_translation_x, scene.bone_translation_y, scene.bone_translation_z],
        [scene.bone_rotation_x, scene.bone_rotation_y, scene.bone_rotation_z],
        [scene.bone_scale_x, scene.bone_scale_y, scene.bone_scale_z]
    )
    handler.set_bone_matrix(bone_matrix)

    if scene.prosthesis_translation_x is not None:
        op_prosthesis = db.query(OperationPlanProsthesis).filter_by(i_operation_plan=i_operation_plan).first()

        if not op_prosthesis:
            print(f"Warning: Saved prosthesis data for plan {i_operation_plan} but no prosthesis assigned in OperationPlanProsthesis. Removing existing prosthesis from scene.")
            handler.remove_prosthesis_from_scene()
        else:
            prosthesis_model_db = db.query(ProsthesisModel).filter_by(i_3d_prosthesis_model=op_prosthesis.i_3d_prosthesis_model).first()
            if not prosthesis_model_db:
                print(f"Warning: Prosthesis model ID {op_prosthesis.i_3d_prosthesis_model} not found for operation plan {i_operation_plan}. Cannot restore prosthesis.")
                handler.remove_prosthesis_from_scene()
            else:
                handler.add_prosthesis_to_scene(prosthesis_model_db.path_to_model)

                prosthesis_matrix = compose_matrix(
                    [scene.prosthesis_translation_x, scene.prosthesis_translation_y, scene.prosthesis_translation_z],
                    [scene.prosthesis_rotation_x, scene.prosthesis_rotation_y, scene.prosthesis_rotation_z],
                    [scene.prosthesis_scale_x, scene.prosthesis_scale_y, scene.prosthesis_scale_z]
                )
                handler.set_prosthesis_matrix(prosthesis_matrix)
    else:
        handler.remove_prosthesis_from_scene()

    return {"status": "positions restored"}

from scipy.spatial.transform import Rotation as R
import numpy as np

def decompose_matrix(matrix: list[float]):
    m = np.array(matrix).reshape(4, 4)
    translation = m[:3, 3].tolist()
    scale = [np.linalg.norm(m[:3, i]) for i in range(3)]

    if np.any(np.isclose(scale, 0)):
        rotation_matrix = np.eye(3)
    else:
        rotation_matrix = np.array([m[:3, i] / scale[i] for i in range(3)]).T

    r = R.from_matrix(rotation_matrix)
    euler_deg = r.as_euler('xyz', degrees=True).tolist()
    return translation, euler_deg, scale


def compose_matrix(translation, rotation_deg, scale):
    r = R.from_euler('xyz', rotation_deg, degrees=True)
    rotation_matrix = r.as_matrix()
    rotation_scaled = rotation_matrix * scale

    composed = np.eye(4)
    composed[:3, :3] = rotation_scaled
    composed[:3, 3] = translation
    return composed.flatten().tolist()

