import copy

from openalea.core.observer import Observed, AbstractListener
from openalea.core.singleton import Singleton
from openalea.oalab.control.control import Control

class ControlContainer(Observed, AbstractListener):

    def __init__(self):
        Observed.__init__(self)
        AbstractListener.__init__(self)
        self._controls = set()

    def control(self, name=None, uid=None):
        if name is None and uid is None:
            return [control for control in self._controls]
        elif name is None and uid:
            for control in self._controls:
                if id(control) == uid:
                    return control
        elif name and uid is None:
            controls = []
            for control in self._controls:
                if control.name == name:
                    controls.append(control)
            if len(controls) == 0:
                return None
            elif len(controls) == 1:
                return controls[0]
            else:
                return controls
        else:
            return self.control(None, uid)

    def add_control(self, control):
        """
        :param control: Control object or tuple(name, interface, widget). widget can be None
        :param tag: If tag is specified, link control to this tag, else control is global to all tags in current project.
        """
        assert isinstance(control, Control)
        self._controls.add(control)
        control.register_listener(self)
        self.notify_listeners(('state_changed', (control)))

    def remove_control(self, control):
        """
        :param control: Control object or tuple(name, interface, widget). widget can be None
        :param tag: If tag is specified, link control to this tag, else control is global to all tags in current project.
        """
        assert isinstance(control, Control)
        if control in self._controls:
            self._controls.remove(control)
            control.unregister_listener(self)
            self.notify_listeners(('state_changed', (control)))

    def namespace(self, interface=None):
        """
        Returns namespace (dict control name -> value).
        :param tag: returns namespace corresponding to given tag. Default, returns global namespace
        """
        ns = {}
        for control in self.controls():
            if interface is None:
                ns[control.name] = copy.deepcopy(control.value)
            else:
                from openalea.oalab.service.interface import get_name
                if get_name(control.interface) == interface:
                    ns[control.name] = copy.deepcopy(control.value)
        return ns

    def controls(self):
        return self._controls

    def notify(self, sender, event):
        if isinstance(sender, Control):
            signal, data = event
            if signal == 'value_changed':
                self.notify_listeners(('control_value_changed', (sender, data)))
            if signal == 'name_changed':
                self.notify_listeners(('control_name_changed', (sender, data)))


    def __contains__(self, key):
        for control in self.controls():
            if key == control.name:
                return True
        return False


class ControlManager(ControlContainer):
    __metaclass__ = Singleton

def control_dict():
    """
    Get the controls from the control manager in a dictionary (key = name, value = object)

    :return: dict of controls
    """
    cm = ControlManager()
    controls = cm.namespace()
    return controls
