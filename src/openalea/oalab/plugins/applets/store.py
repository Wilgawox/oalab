
from openalea.oalab.plugins.applets import PluginApplet

class Store(PluginApplet):

    name = 'Store'
    alias = 'Store'

    def __call__(self, mainwindow):
        from openalea.oalab.gui.store import Store as StoreWidget

        self._applet = StoreWidget(mainwindow.session, mainwindow)
        self._fill_menu(mainwindow, self._applet)

        mainwindow.add_applet(self._applet, self.alias, area='inputs')
