# -*- python -*-
#
#       OpenAlea.OALab: Multi-Paradigm GUI
#
#       Copyright 2014 INRIA - CIRAD - INRA
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
from openalea.oalab.model.model import Model
from openalea.oalab.model.parse import parse_doc, parse_lpy, OutputObj
from openalea.oalab.control.picklable_curves import geometry_2_piklable_geometry
from openalea.lpy import Lsystem, AxialTree
from openalea.lpy.__lpy_kernel__ import LpyParsing
from openalea.lpy.gui.objectmanagers import get_managers
from openalea.lpy.gui.scalar import ProduceScalar
from openalea.lpy.gui import documentation as doc_lpy
import collections
import types


def get_default_text():
    return """Axiom:

derivation length: 1

production:

interpretation:

endlsystem
"""


def adapt_axialtree(axialtree, lsystem):
    """
    Adapat an axialtree to be viewable in the world (add a method _repr_geom_)

    :param axialtree: axialtree to adapt
    :param lsystem: lsystem that can be used to create the 3d representation of axialtree
    :return: adapted axialtree
    """
    def repr_geom(self):
        return self.__scene

    scene = lsystem.sceneInterpretation(axialtree)
    axialtree.__scene = scene
    axialtree._repr_geom_ = types.MethodType(repr_geom, axialtree)

    return axialtree


class LsysObj(object):
    def __init__(self, lsystem, axialtree, name=""):
        """
        Object that can be interpreted in the world.

        It contain the lsystem, the resulting axiatree and a name.
        The lsysytem and the axialtree are used to convert object into PlantGL scene with _repr_geom_ method.
        """
        self.lsystem = lsystem
        self.axialtree = axialtree
        self.name = name

    def _repr_geom_(self):
        return self.lsystem.sceneInterpretation(self.axialtree)


class LPyModel(Model):
    default_name = "LSystem"
    default_file_name = "script.lpy"
    pattern = "*.lpy"
    extension = "lpy"
    icon = ":/images/resources/logo.png"

    def __init__(self, name="script.lpy", code=None, filepath="", inputs=[], outputs=[]):
        super(LPyModel, self).__init__(name=name, code=code, filepath=filepath, inputs=inputs, outputs=outputs)
        self.temp_axiom = None
        if code == "":
            code = get_default_text()

        # dict is mutable... It is useful if you want change scene_name inside application
        self.context = dict()
        self.scene_name = self.name + "_scene"
        self.context["scene_name"] = self.scene_name
        self.lsystem = Lsystem()
        self.axialtree = AxialTree()
        self.code, control = import_lpy_file(code)

        self.axialtree = adapt_axialtree(self.axialtree, self.lsystem)
        # TODO: update control of the project with new ones

        from openalea.lpy import registerPlotter
        from openalea.oalab.service.plot import get_plotters

        plotters = get_plotters()
        if len(plotters):
            registerPlotter(plotters[0])
        # print "p: ", plotters

        # for plotter in plotters:
        #     print "plotter: ", plotter
        #     registerPlotter(plotter)

    def get_documentation(self):
        """
        :return: a string with the documentation of the model
        """
        if self._doc:
            return self._doc
        else:
            return """
<H1><IMG SRC=""" + str(self.icon) + """
 ALT="icon"
 HEIGHT=25
 WIDTH=25
 TITLE="LPy logo">L-Py</H1>""" + doc_lpy.getSpecification()[13:]

    def repr_code(self):
        """
        :return: a string representation of model to save it on disk
        """
        return self.code

    def run(self, *args, **kwargs):
        """
        execute model thanks to interpreter
        """
        # TODO: get control from application and set them into self.context
        self.inputs = args
        self.context.update(self.inputs)

        self.lsystem.setCode(str(self.code), self.context)
        if self.temp_axiom is not None:
            self.lsystem.axiom = self.temp_axiom
            self.temp_axiom = None

        self.axialtree = self.lsystem.iterate()

        self.lsystem.context().getNamespace(self.context)

        self._set_output_from_ns(self.context)

        # new_scene = self.lsystem.sceneInterpretation(self.axialtree)
        if "scene_name" in self.context:
            self.scene_name = self.context["scene_name"]

        self.axialtree = adapt_axialtree(self.axialtree, self.lsystem)

        return self.outputs

    def init(self, *args, **kwargs):
        """
        go back to initial step
        """
        self.step(i=0, *args, **kwargs)
        return self.outputs

    def step(self, i=None, *args, **kwargs):
        """
        execute only one step of the model
        """
        self.inputs = args
        self.context.update(self.inputs)

        # if you are at derivation length, re-init
        if self.lsystem.getLastIterationNb() >= self.lsystem.derivationLength - 1:
            i = 0
        # clasical case: evolve one step
        if i is None:
            # Warning: getLastIterationNb return 0,0,1,2,3,4,...
            # Hack: here step 0 -> step 2, 3, 4
            # Warning: TODO: step 1 !
            # Hack
            self.axialtree = self.lsystem.iterate(self.lsystem.getLastIterationNb() + 2)
        # if you set i to a number, directly go to this step.
        # it is used with i=0 to reinit
        else:
            self.axialtree = self.lsystem.iterate(i)

        self.lsystem.context().getNamespace(self.context)

        self._set_output_from_ns(self.context)

        # new_scene = self.lsystem.sceneInterpretation(self.axialtree)
        if "scene_name" in self.context:
            self.scene_name = self.context["scene_name"]

        self.axialtree = adapt_axialtree(self.axialtree, self.lsystem)

        return self.outputs

    def stop(self, *args, **kwargs):
        """
        stop execution
        """
        # TODO : to implement
        self.axialtree = adapt_axialtree(self.axialtree, self.lsystem)

        return self.outputs

    def animate(self, *args, **kwargs):
        """
        run model step by step
        """
        self.inputs = args
        self.context.update(self.inputs)
        self.step(*args, **kwargs)
        self.axialtree = self.lsystem.animate()

        self.lsystem.context().getNamespace(self.context)

        self._set_output_from_ns(self.context)

        if "scene_name" in self.context:
            self.scene_name = self.context["scene_name"]

        self.axialtree = adapt_axialtree(self.axialtree, self.lsystem)

        return self.outputs

    def _set_output_from_ns(self, namespace):
        # get outputs from namespace
        if self.outputs_info:
            self.outputs = []
            if len(self.outputs_info) > 0:
                for outp in self.outputs_info:
                    if outp.name in namespace:
                        self._outputs.append(namespace[outp.name])
                    elif outp.name.lower() in ["axialtree", "lstring"]:
                        self._outputs.append(self.axialtree)
                    elif outp.name.lower() == "lsystem":
                        self._outputs.append(self.lsystem)
                    elif outp.name.lower() == "scene":
                        self._outputs.append(self.lsystem.sceneInterpretation(self.axialtree))

    @property
    def inputs(self):
        """
        List of inputs of the model.

        :use:
            >>> model.inputs = 4, 3
            >>> rvalue = model.run()
        """
        return self._inputs

    @inputs.setter
    def inputs(self, *args):
        self._inputs = dict()
        if args:
            # inputs = args
            inputs = list(args)
            if len(inputs) == 1:
                if isinstance(inputs, collections.Iterable):
                    inputs = inputs[0]
                if isinstance(inputs, collections.Iterable):
                    inputs = list(inputs)
                else:
                    inputs = [inputs]
            inputs.reverse()

            if not self.inputs_info:
                if len(inputs) == 1:
                    # If we have no input declared but we give one, it must be the axiom!
                    axiom = inputs[0]
                    self.temp_axiom = axiom
            else:
                for input_info in self.inputs_info:
                    if len(inputs):
                        inp = inputs.pop()
                    elif input_info.default:
                        inp = eval(input_info.default)
                    else:
                        raise Exception("Model %s have inputs not setted. Please set %s ." % (self.name, input_info.name))

                    if input_info.name:
                        if input_info.name.lower() in ["axiom", "lstring"]:
                            # If one of the declared input is "axiom" or "lstring" set the lsystem axiom
                            self.temp_axiom = inp
                        else:
                            self._inputs[input_info.name] = inp

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, code=""):
        self._code = code
        docstring = parse_lpy(code)
        if docstring is not None:
            model, self.inputs_info, self.outputs_info = parse_doc(docstring)

            # Dafault output
            if not self.outputs_info:
                self.outputs_info = [OutputObj("lstring:IStr")]


def get_default_text():
    return """Axiom:

derivation length: 1

production:

interpretation:

endlsystem
"""


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
