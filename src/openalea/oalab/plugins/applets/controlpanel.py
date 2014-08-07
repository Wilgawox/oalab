
from openalea.oalab.applets.plugin import PluginApplet

class ControlPanel(PluginApplet):

    name = 'ControlPanel'
    alias = 'Control'

    def __call__(self, mainwindow):
        # Load and instantiate graphical component that actually provide feature
        from openalea.oalab.control.controlpanel import ControlPanel

        self._applet = ControlPanel(mainwindow.session, mainwindow)
        self._fill_menu(mainwindow, self._applet)

        mainwindow.add_applet(self._applet, self.alias, area='inputs')
