from vtkmodules.vtkCommonColor import vtkNamedColors

from common import LabelColorWidget, LabelSetting


class BrainWebLabelColorWidget(LabelColorWidget):
    def __init__(self, parent=None, inject_ui=None):
        label_settings = [
            LabelSetting(
                label=0,
                name='Background',
                default_color=vtkNamedColors().GetColor3ub("Black")
            ),
            LabelSetting(
                label=1,
                name='Cerebrospinal Fluid',
                default_color=vtkNamedColors().GetColor3ub("Banana")
            ),
            LabelSetting(
                label=2,
                name='Gray Matter',
                default_color=vtkNamedColors().GetColor3ub("Gray"),
            ),
            LabelSetting(
                label=3,
                name='White Matter',
                default_color=vtkNamedColors().GetColor3ub("White"),
            ),
            LabelSetting(
                label=4,
                name='Fat',
                default_color=vtkNamedColors().GetColor3ub("Raspberry"),
            ),
            LabelSetting(
                label=5,
                name='Muscle',
                default_color=vtkNamedColors().GetColor3ub("Tomato"),
            ),
            LabelSetting(
                label=6,
                name='Muscle/Skin',
                default_color=vtkNamedColors().GetColor3ub("Flesh"),
            ),
            LabelSetting(
                label=7,
                name='Skull',
                default_color=vtkNamedColors().GetColor3ub("Wheat"),
            ),
            LabelSetting(
                label=8,
                name='Vessels',
                default_color=vtkNamedColors().GetColor3ub("Blue"),
            ),
            LabelSetting(
                label=9,
                name='Around Fat',
                default_color=vtkNamedColors().GetColor3ub("Mint"),
            ),
            LabelSetting(
                label=10,
                name='Dura Matter',
                default_color=vtkNamedColors().GetColor3ub("Peacock"),
            ),
            LabelSetting(
                label=11,
                name='Bone Marrow',
                default_color=vtkNamedColors().GetColor3ub("Salmon")
            )
        ]
        super().__init__(label_settings, parent, inject_ui=inject_ui)
