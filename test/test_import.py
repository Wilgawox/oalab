def test_import():
    from openalea.core.pkgmanager import PackageManager
    from openalea.oalab.control.controlpanel import ControlPanel, ControlPanelManager
    from openalea.oalab.control.observerpanel import ObserverPanel
    from openalea.oalab.gui.logger import Logger
    from openalea.oalab.gui.help import Help
    from openalea.oalab.scene.view3d import Viewer
    from openalea.oalab.gui.menu import PanedMenu
    from openalea.vpltk.shell.shell import get_interpreter_class, get_shell_class
    from openalea.oalab.applets.container import AppletContainer
    from openalea.oalab.scene.view3d import Viewer
    from openalea.oalab.project.manager import ProjectManager
    from openalea.oalab.project.treeview import ProjectTreeView, ProjectLayoutWidget
    from openalea.oalab.package import PackageViewWidget, PackageCategorieViewWidget, PackageSearchWidget
    from openalea.oalab.gui.store import Store
    from openalea.vpltk.qt import QtCore, QtGui
