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
from openalea.core.compositenode import CompositeNodeFactory


class VisualeaModel(Model):
    default_name = "Workflow"
    default_file_name = "workflow.wpy"
    pattern = "*.wpy"
    extension = "wpy"
    icon = ":/images/resources/openalealogo.png"

    def __init__(self, name="workflow.wpy", code="", filepath="", inputs=[], outputs=[]):
        super(VisualeaModel, self).__init__(name=name, code=code, filepath=filepath, inputs=inputs, outputs=outputs)
        _name = self.name.split('.wpy')[0]
        if (code is None) or (code is ""):
            self._workflow = CompositeNodeFactory(_name).instantiate()
        elif isinstance(code, CompositeNodeFactory):
            # hakishhh
            code.instantiate_node = monkey_patch_instantiate_node
            self._workflow = code.instantiate()
        else:
            # Access to the current project
            # 
            cnf = eval(code, globals(), locals())
            # hakishhh
            cnf.instantiate_node = monkey_patch_instantiate_node
            self._workflow = cnf.instantiate()



    def repr_code(self):
        """
        :return: a string representation of model to save it on disk
        """
        name = self.name

        if name[-3:] in '.py':
            name = name[-3:]
        elif name[-4:] in '.wpy':
            name = name[-4:]
        cn = self._workflow
        cnf = CompositeNodeFactory(name)
        cn.to_factory(cnf)

        repr_wf = repr(cnf.get_writer())
        # hack to allow eval rather than exec...
        # TODO: change the writer

        repr_wf = (' = ').join(repr_wf.split(' = ')[1:])
        return repr_wf

    def run(self, interpreter=None):
        """
        execute model thanks to interpreter
        """
        return self._workflow.eval()

    def reset(self, interpreter=None):
        """
        go back to initial step
        """
        return self._workflow.reset()

    def step(self, interpreter=None):
        """
        execute only one step of the model
        """
        return self._workflow.eval_as_expression(step=True)

    def stop(self, interpreter=None):
        """
        stop execution
        """
        # TODO : to implement
        pass

    def animate(self, interpreter=None):
        """
        run model step by step
        """
        return self._workflow.eval()

def monkey_patch_instantiate_node(cnf, vid, call_stack=None):

    from openalea.oalab.model.model import ModelFactory

    self = cnf

    (package_id, factory_id) = self.elt_factory[vid]
    
    # my temporary patch
    if package_id in (None, ":projectmanager.current"):
        factory = ModelFactory(fatory_id)
    else:
        pkgmanager = PackageManager()
        pkg = pkgmanager[package_id]
        factory = pkg.get_factory(factory_id)
    
    node = factory.instantiate(call_stack)

    attributes = copy.deepcopy(self.elt_data[vid])
    ad_hoc     = copy.deepcopy(self.elt_ad_hoc.get(vid, None))
    self.load_ad_hoc_data(node, attributes, ad_hoc)

    # copy node input data if any
    values = copy.deepcopy(self.elt_value.get(vid, ()))

    for vs in values:
        try:
            #the two first elements are the historical
            #values : port Id and port value
            #the values beyond are not used.
            port, v = vs[:2]
            node.set_input(port, eval(v))
            node.input_desc[port].get_ad_hoc_dict().set_metadata("hide",
                                                                 node.is_port_hidden(port))
        except:
            continue

    return node
