# -*- python -*-
#
#       LPy manager applet.
#
#       OpenAlea.OALab: Multi-Paradigm GUI
#
#       Copyright 2013 INRIA - CIRAD - INRA
#
#       File author(s): Julien Coste <julien.coste@inria.fr>
#
#       File contributor(s):
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
###############################################################################
__revision__ = ""

from openalea.oalab.editor.text_editor import RichTextEditor as Editor
from openalea.oalab.editor.highlight import Highlighter
from openalea.oalab.editor.lpy_lexer import LPyLexer
from openalea.oalab.control.picklable_curves import geometry_2_piklable_geometry
from openalea.lpy import Lsystem
from openalea.lpy.__lpy_kernel__ import LpyParsing
from openalea.lpy.gui.objectmanagers import get_managers
from openalea.lpy.gui.scalar import ProduceScalar
from openalea.core import logger
from openalea.oalab.model.lpy import LPyModel
from openalea.oalab.service.help import display_help


def import_lpy_file(script):
    """
    Extract from an "old style" LPy file script part (str) and associated control (dict).
    Permit compatibility between LPy and OALab.

    :param: script to filter (str)
    :return: lpy script (str) without end begining with "###### INITIALISATION ######"
    and a dict which contain the control (dict)
    """
    control = dict()

    if script is None: script = ""
    beginTag = LpyParsing.InitialisationBeginTag
    if not beginTag in script:
        return str(script), control
    else:
        txts = str(script).split(beginTag)
        new_script = txts[0]
        context_to_translate = txts[1]
        context = Lsystem().context()
        context.initialiseFrom(beginTag + context_to_translate)

        managers = get_managers()
        visualparameters = []
        scalars = []
        functions = []
        curves = []
        geoms = []

        lpy_code_version = 1.0
        if context.has_key('__lpy_code_version__'):
            lpy_code_version = context['__lpy_code_version__']
        if context.has_key('__scalars__'):
            scalars_ = context['__scalars__']
            scalars = [ ProduceScalar(v) for v in scalars_ ]
        if context.has_key('__functions__') and lpy_code_version <= 1.0 :
            functions = context['__functions__']
            for n, c in functions: c.name = n
            functions = [ c for n, c in functions ]
            funcmanager = managers['Function']
            geoms += [(funcmanager, func) for func in functions]
        if context.has_key('__curves__') and lpy_code_version <= 1.0 :
            curves = context['__curves__']
            for n, c in curves: c.name = n
            curves = [ c for n, c in curves ]
            curvemanager = managers['Curve2D']
            geoms += [ (curvemanager, curve) for curve in curves ]
        if context.has_key('__parameterset__'):
            for panelinfo, objects in context['__parameterset__']:
                for typename, obj in objects:
                    visualparameters.append((managers[typename], obj))

        control["color map"] = context.turtle.getColorList()
        for scalar in scalars:
        	control[unicode(scalar.name)] = scalar
        for (manager, geom) in geoms:
            if geom != list():
                new_obj, new_name = geometry_2_piklable_geometry(manager, geom)
                control[new_name] = new_obj
        for (manager, geom) in visualparameters:
            if geom != list():
                new_obj, new_name = geometry_2_piklable_geometry(manager, geom)
                control[new_name] = new_obj

        return new_script, control


class LPyModelController(object):
    default_name = LPyModel.default_name
    default_file_name = LPyModel.default_file_name
    pattern = LPyModel.pattern
    extension = LPyModel.extension
    icon = LPyModel.icon

    def __init__(self, name="", code="", model=None, filepath=None, interpreter=None, editor_container=None, parent=None):
        self.name = name
        self.interpreter = interpreter
        self.filepath = filepath
        if model:
            self.model = model
        else:
            self.model = LPyModel(name=name, code=code)
        self.parent = parent
        self.editor_container = editor_container
        self._widget = None

        self.lsystem = self.model.lsystem
        self.axialtree = self.model.axialtree
        #todo get controls
        """
        if self.session.project is not None:
            self.session.project.control.update(control)
            # for parameter in self.model.parameters:
                # if hasattr(self.model.parameters[parameter], "value"):
                    # self.model.parameters[parameter] = self.model.parameters[parameter].value
            controller.project_manager._load_control()

        # Link with color map from application
        if hasattr(self.session.project, "control"):
            if self.session.project.control.has_key("color map"):
                i = 0
                for color in self.session.project.control["color map"] :
                    self.lsystem.context().turtle.setMaterial(i, color)
                    i += 1"""

        self.interpreter.locals['lsystem'] = self.lsystem

    def instanciate_widget(self):
        # todo register viewer
        """
        if hasattr(self.controller, "_plugins"):
            if self.controller._plugins.has_key('Viewer3D'):
                registerPlotter(self.controller._plugins['Viewer3D'].instance())
        else:
            if self.controller.applets.has_key('Viewer3D'):
                registerPlotter(self.controller.applets['Viewer3D'])"""

        self._widget = Editor(parent=self.parent)
        Highlighter(self._widget.editor, lexer=LPyLexer())
        self.widget().applet = self

        self.widget().set_text(self.model.code)
        return self.widget()

    def focus_change(self):
        """
        Set doc string in Help widget when focus changed
        """
        doc = self.model.get_documentation()
        display_help(doc)

    def run_selected_part(self):
        """
        Run selected code like a PYTHON code (not LPy code).
        If nothing selected, run like LPy (not Python).
        """
        code = self.widget().get_selected_text()
        if len(code) == 0:
            return self.model()
        else:
            interp = self.interpreter
            return interp.runcode(code)

    def run(self):
        code = self.widget().get_text()
        self.model.code = code

        #todo get control
        """ # Get control
        if hasattr(self.session.project, "control"):
            self.model.parameters.update(self.session.project.control)
        for parameter in self.model.parameters:
            if hasattr(self.model.parameters[parameter], "value"):
                self.model.parameters[parameter] = self.model.parameters[parameter].value
        self.lsystem.setCode(code, self.model.parameters)"""

        self.axialtree = self.model()
        new_scene = self.lsystem.sceneInterpretation(self.axialtree)
        scene_name = self.context["scene_name"]
        # todo: put result in the world
        # self.session.world[scene_name] = new_scene
        return self.axialtree, new_scene, scene_name

    def step(self, i=None):
        code = self.widget().get_text()
        if code != self.code:
            #todo set controls
            """
            # /!\ setCode method set the getLastIterationNb to zero
            # So, if you change code, next step will do a 'reinit()'
            self.model.parameters.update(self.session.project.control)
            for parameter in self.model.parameters:
                if hasattr(self.model.parameters[parameter], "value"):
                    self.model.parameters[parameter] = self.model.parameters[parameter].value"""
            self.lsystem.setCode(code, self.model.parameters)

            self.model.code = code
        self.axialtree = self.model.step(i=i)

        new_scene = self.lsystem.sceneInterpretation(self.axialtree)
        scene_name = self.context["scene_name"]
        # todo: put result in the world
        """
        if new_scene:
            self.controller.scene[self.context["scene_name"]] = new_scene"""

        return self.axialtree, new_scene, scene_name

    def stop(self):
        return self.model.stop()

    def animate(self):
        code = self.widget().get_text()

        #todo set controls
        """
        # /!\ setCode method set the getLastIterationNb to zero
        # So, if you change code, next step will do a 'reinit()'
        self.model.parameters.update(self.session.project.control)
        for parameter in self.model.parameters:
            if hasattr(self.model.parameters[parameter], "value"):
                self.model.parameters[parameter] = self.model.parameters[parameter].value"""
        self.lsystem.setCode(code, self.model.parameters)

        self.model.code = code

        self.axialtree = self.model.animate()

        new_scene = self.lsystem.sceneInterpretation(self.axialtree)
        scene_name = self.context["scene_name"]
        # todo: put result in the world
        """
        if new_scene:
            self.controller.scene[self.context["scene_name"]] = new_scene"""

        return self.axialtree, new_scene, scene_name

    def reinit(self):
        code = self.widget().get_text()
        self.model.code = code

        self.axialtree = self.model.init()

        new_scene = self.lsystem.sceneInterpretation(self.axialtree)
        scene_name = self.context["scene_name"]
        # todo: put result in the world
        """
        if new_scene:
            self.controller.scene[self.context["scene_name"]] = new_scene"""

        return self.axialtree, new_scene, scene_name

    def widget(self):
        """
        :return: the edition widget
        """
        return self._widget

    def save(self, name=None):
        code = self.widget().get_text()
        if name:
            self.model.filepath = name
        self.model.code = code
        self.widget().save(name=self.model.filepath)
