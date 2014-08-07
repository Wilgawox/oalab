# -*- python -*-
#
# OpenAlea.OALab: Multi-Paradigm GUI
#
#       Copyright 2013 INRIA - CIRAD - INRA
#
#       File author(s): Julien Coste <julien.coste@inria.fr>
#                       Guillaume Baty <guillaume.baty@inria.fr>
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

from openalea.vpltk.qt import QtGui, QtCore
from openalea.core.observer import AbstractListener
from openalea.vpltk.project import ProjectManager
from openalea.oalab.gui import resources_rc
from openalea.oalab.service.applet import get_applet
from openalea.oalab.gui.utils import qicon
from openalea.oalab.project.pretty_preview import ProjectSelectorScroll
from openalea.oalab.project.creator import CreateProjectWidget
from openalea.oalab.gui.utils import ModalDialog
from openalea.core.path import path
from openalea.core import settings
from openalea.oalab.session.session import Session
from openalea.file.files import start
from openalea.oalab.service.mimetype import encode
from openalea.vpltk.plugin import iter_plugins

from openalea.oalab.project.manager import SelectCategory, RenameModel

"""
TODO:
    - use project known categories instead of hard coded 'model', 'src', ...

"""

class ProjectManagerWidget(QtGui.QWidget, AbstractListener):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        AbstractListener.__init__(self)

        layout = QtGui.QVBoxLayout(self)
        self.view = ProjectManagerView()
        self.model = self.view.model()
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)

        self.projectManager = ProjectManager()
        self.projectManager.register_listener(self)

        self.paradigm_container = None
        self.menu_available_projects = QtGui.QMenu(u'Available Projects')



        self.actionNewProj = self.view.actionNewProj
        self.actionOpenProj = self.view.actionOpenProj

        group = "Project"
        self._actions = [[group, "Manage Project", self.view.actionNewProj, 0],
                         [group, "Manage Project", self.view.actionOpenProj, 0],
                         [group, "Manage Project", self.view.actionSaveProj, 0],
#                          [group, "Manage Project", self.view.actionSaveProjAs, 1],
                         [group, "Manage Project", self.view.actionCloseProj, 0],
#                          [group, "Manage Project", self.view.actionEditMeta, 1],
#                          ["Project", "Manage Project", self.actionRenameProject, 1],
        ]
        self._actions += self.view._actions

        # Menu used to display all available projects.
        # This menu is filled dynamically each time this menu is opened
        self.menu_available_projects = QtGui.QMenu(u'Available Projects')
        self.menu_available_projects.aboutToShow.connect(self._update_available_project_menu)
        self.action_available_project = {} # Dict used to know what project corresponds to triggered action
        self.session = Session()

    def initialize(self):
        self.paradigm_container = get_applet(identifier='EditorManager')
        self.view.initialize()

        # As default project has been defined before having connected this widget
        # We close it and open it again.
        pm = self.projectManager
        default = pm.cproject
        pm.cproject = None
        pm.cproject = default

    def close(self):
        config = settings.Settings()
        if self.project():
            config

    def actions(self):
        return self._actions

    def project(self):
        if self.projectManager:
            return self.projectManager.cproject

    def _update_available_project_menu(self):
        """
        Discover all projects and generate an action for each one.
        Then connect this action to _on_open_project_triggered
        """
        self.projectManager.discover()
        self.menu_available_projects.clear()
        self.action_available_project.clear()
        all_projects = {}
        for project in self.projectManager.projects:
            all_projects.setdefault(project.projectdir, []).append(project)

        for projectdir, projects in all_projects.iteritems():
            title = unicode(projectdir.name)
            if title == 'data':
                title = 'Examples'
            menu = QtGui.QMenu(title, self.menu_available_projects)
            for project in projects:
                icon_path = project.icon_path
                icon_name = icon_path if icon_path else ":/images/resources/openalealogo.png"
                action = QtGui.QAction(QtGui.QIcon(icon_name), project.name, self.menu_available_projects)
                action.triggered.connect(self._on_open_project_triggered)
                menu.addAction(action)
                self.action_available_project[action] = project
            self.menu_available_projects.addMenu(menu)
        return self.menu_available_projects

    def _on_open_project_triggered(self):
        project = self.action_available_project[self.sender()]
        self.projectManager.cproject = project

    def notify(self, sender, event=None):
        signal, data = event
        if signal == 'project_changed':
            project = self.projectManager.cproject
            self.view.set_project(project=project)
            self.session.world.clear()
        elif signal == 'project_updated':
            self.view.refresh()

        self.session.update_namespace()

    def set_project(self, project):
        self.view.set_project(project)

class ProjectManagerView(QtGui.QTreeView):
    def __init__(self):
        QtGui.QTreeView.__init__(self)
        self.paradigm_container = None

        self._model = ProjectManagerModel()
        self.projectManager = ProjectManager()
        self.setModel(self._model)

        self._model.dataChanged.connect(self._on_model_changed)

        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.connect(self, QtCore.SIGNAL('doubleClicked(const QModelIndex&)'), self.open)

        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setAcceptDrops(True)

        self._actions = []
        self._new_file_actions = {}
        self.paradigms_actions = []
        self.paradigms = {}

        self.actionEditMeta = QtGui.QAction(qicon("book.png"), "Edit Project Information", self)
        self.actionEditMeta.triggered.connect(self.edit_metadata)

        self.actionImportFile = QtGui.QAction(qicon("open.png"), "Import file", self)
        self.actionImportFile.triggered.connect(self.import_file)

        self.actionSaveProjAs = QtGui.QAction(qicon("save.png"), "Save As", self)
        self.actionSaveProjAs.triggered.connect(self.saveAs)

        self.actionSaveProj = QtGui.QAction(qicon("save.png"), "Save project", self)
        self.actionSaveProj.triggered.connect(self.save)

        self.actionCloseProj = QtGui.QAction(qicon("closeButton.png"), "Close project", self)
        self.actionCloseProj.triggered.connect(self.close)

        self.actionNewProj = QtGui.QAction(qicon("new.png"), "New Project", self)
        self.actionNewProj.setShortcut(
            QtGui.QApplication.translate("MainWindow", "Ctrl+N", None, QtGui.QApplication.UnicodeUTF8))
        self.actionOpenProj = QtGui.QAction(qicon("open.png"), "Open Project", self)
        self.actionOpenProj.setShortcut(
            QtGui.QApplication.translate("MainWindow", "Ctrl+O", None, QtGui.QApplication.UnicodeUTF8))

        self.actionNewProj.triggered.connect(self.new_project)
        self.actionOpenProj.triggered.connect(self.open_project)




    #  API

    def initialize(self):
        self.paradigm_container = get_applet(identifier='EditorManager')

    def set_project(self, project):
        self.projectManager.cproject = project
        # TODO: Dirty hack to remove asap. Close project selector if widget has been created
        if hasattr(self, "proj_selector"):
            del self.proj_selector

        self._model.set_project(project)

        if project:
            self.close_all_scripts()
            self.open_all_scripts_from_project(project)
            self.expandAll()
        else:
            self.close_all_scripts()


    def refresh(self):
        self._model.refresh()

    #  Convenience methods

    def getItem(self):
        index = self.getIndex()
        if index:
            return self._model.itemFromIndex(index)

    def getIndex(self):
        indices = self.selectedIndexes()
        for index in indices:
            return index

    def project(self):
        if self.projectManager:
            return self.projectManager.cproject

    def selected_data(self):
        index = self.getIndex()
        project = self.project()
        data = self._model.projectdata(index)
        if index is None or project is None or data is None:
            return (None, None, None)
        else:
            category, name = data
            return project, category, name

    #  Slots

    def _on_model_changed(self):
        self.expandAll()

    #  Contextual menu

    def add_new_file_actions(self, menu):
        for applet in self.paradigm_container.paradigms.values():
            action = QtGui.QAction(qicon(applet.icon), 'New %s' % applet.default_name, self)
            action.triggered.connect(self.new_file)
            self._new_file_actions[action] = applet.default_name
            menu.addAction(action)
        menu.addSeparator()

    def create_menu(self):
        menu = QtGui.QMenu(self)
        project, category, obj = self.selected_data()

        if category == 'category' and obj == 'model':
            self.add_new_file_actions(menu)

        elif category == 'category' and obj == 'data':
            import_data = QtGui.QAction(qicon('import.png'), 'Import data', self)
            import_data.triggered.connect(self.open)
            menu.addAction(import_data)

        elif category == 'category' and obj in ('startup', 'doc', 'lib'):
            new_startup = QtGui.QAction(qicon('filenew.png'), 'New file', self)
            new_startup.triggered.connect(self.new_file)
            menu.addAction(new_startup)

        if category == 'model':
            self.add_new_file_actions(menu)

        if category in ['model', 'src', 'startup', 'doc', 'data', 'lib']:
            editAction = QtGui.QAction(qicon('open.png'), 'Open "%s"' % obj, self)
            menu.addAction(editAction)
            editAction.triggered.connect(self.open)

            rename = QtGui.QAction(qicon('Crystal_Clear_device_floppy_unmount.png'), 'Save as', self)
            rename.triggered.connect(self.rename)
            menu.addAction(rename)

            remove = QtGui.QAction(qicon('Crystal_Clear_action_edit_remove.png'), 'Remove "%s"' % obj, self)
            remove.triggered.connect(self.remove)
            menu.addAction(remove)

            menu.addSeparator()

            deleteAction = QtGui.QAction(qicon('Crystal_Clear_action_stop.png'), 'Delete "%s"' % obj, self)
            menu.addAction(deleteAction)
            deleteAction.triggered.connect(self.delete)


        if category in ['project']:
            menu.addAction(self.actionEditMeta)
            menu.addAction(self.actionSaveProj)
            menu.addAction(self.actionSaveProjAs)
            menu.addAction(self.actionCloseProj)

        return menu



    def contextMenuEvent(self, event):
        if self.projectManager.cproject is None:
            return
        menu = self.create_menu()
        menu.exec_(event.globalPos())

    #  Action's slots

    def edit_metadata(self):
        project = self.project()
        if project:
            project_creator = CreateProjectWidget(project)
            dialog = ModalDialog(project_creator)
            if dialog.exec_():
                _proj = project_creator.project()
                project.projectdir = _proj.projectdir
                if _proj.name != project.name or _proj.projectdir != project.projectdir:
                    project.rename('project', project.name, _proj.name)
                project.metadata = project_creator.metadata()

    def open_project(self, name=False, path=None):
        """
        If name==false, display a widget to choose project to open.
        Then open project.
        """
        self.projectManager.discover()
        projects = self.projectManager.projects
        self.proj_selector = ProjectSelectorScroll(projects=projects, open_project=self.set_project)
        self.proj_selector.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.proj_selector.show()

    def new_project(self):
        project_creator = CreateProjectWidget()
        dialog = ModalDialog(project_creator)
        if dialog.exec_():
            _project = project_creator.project()
            project = self.projectManager.create(_project.name, _project.projectdir)
            project.metadata = _project.metadata

    def open_all_scripts_from_project(self, project):
        if self.paradigm_container is not None:
            for model in project._model:
                self.paradigm_container.open_project_data('model', model)

    def new_file(self, dtype=None):
        try:
            dtype = self._new_file_actions[self.sender()]
        except KeyError:
            dtype = None
        project, category, data = self.selected_data()
        code = ''

        if category == 'category':
            category = data
        if category is None:
            category = 'model'
            project = self.project()
        if dtype is None and category in ['startup', 'lib']:
            dtype = 'Python'

        if category in ['startup', 'lib']:
            d = {'startup': 'start.py', 'lib': 'algo.py'}
            name = d[category]
        elif dtype:
            name = '%s_%s' % (dtype, category)
        else:
            name = category
        category, name = self.paradigm_container.add(project, name, code, dtype=dtype, category=category)
        if name:
            self.paradigm_container.open_project_data(category, name)

    def open(self):
        project, category, name = self.selected_data()
        if project:
            if category == 'category' and name == 'data':
                p = QtGui.QFileDialog.getOpenFileName(self, 'Select File to open', project.path, "All (*)")
                if p:
                    p = path(p)
                    project.add(name, p.name, p)
            elif category == 'project':
                self.open_all_scripts_from_project(project)
            elif category == 'data':
                filepath = project.path / category / name
                start(filepath)
            elif category in ('startup', 'model', 'doc', 'lib'):
                self.paradigm_container.open_project_data(category, name)

    def _rename(self, project, category, name):
        if category in ('model', 'src'):
            models = project.models()
            if isinstance(models, list):
                list_models = [mod.name for mod in models]
            else:
                list_models = [models.name]
            renamer = RenameModel(list_models, name)
            dialog = ModalDialog(renamer)
            if dialog.exec_():
                old_name = renamer.old_name()
                new_name = renamer.new_name()
                project.rename(category, old_name, new_name)
        elif category == 'project':
            self.edit_metadata()

    def rename(self):
        project, category, name = self.selected_data()
        if project:
            self._rename(project, category, name)

    def remove(self):
        project, category, name = self.selected_data()
        if project:
            project.remove(category, name)

    def delete(self):
        project, category, name = self.selected_data()
        if project:
            if category == 'data':
                path = project.get(category, name)
            elif category == 'model':
                model = project.get(category, name)
                path = model.abspath(project.path / 'model')
            else:
                path = project.path / category / name

            confirm = QtGui.QLabel('Remove %s ?' % path)
            dialog = ModalDialog(confirm)
            if dialog.exec_():
                project.remove(category, name)
                path.remove()
                if self.paradigm_container:
                    self.paradigm_container.close_project_data(category, name)

    def save(self):
        project = self.project()
        if project:
            project.save()

    def saveAs(self):
        project = self.project()
        if project:
            name = self.showNewProjectDialog(default_name=None, text="Select name to save project")
            if name:
                project.rename(category="project", old_name=project.name, new_name=name)

    def close(self):
        self.projectManager.cproject = None

    def close_all_scripts(self):
        if self.paradigm_container is None:
            return
        self.paradigm_container.closeAll()

    def import_file(self):
        print 'import_file'

    def showNewProjectDialog(self, default_name=None, text=None, parent=None):
        my_path = path(settings.get_project_dir())
        if default_name:
            my_path = my_path / default_name
        if not text:
            text = 'Select name to create project'
        fname = QtGui.QFileDialog.getSaveFileName(parent, text,
                                                  my_path)
        return fname


    def showOpenProjectDialog(self, parent=None):
        my_path = path(settings.get_project_dir())
        fname = QtGui.QFileDialog.getExistingDirectory(parent, 'Select Project Directory',
                                                       my_path)
        return fname


    # Drag and drop

    def startDrag(self, supportedActions):
        index = self.getIndex()
        item = self.getItem()
        data = self._model.projectdata(index)
        if data is None:
            return
        category, obj = data
        # Check item in src
        # TODO move this part in dragEnterEvent with mimetype
        if category in ['src', 'model']:
            text = item.text()

            # name_without_ext = ".".join(text.split(".")[:-1])
            name_without_ext = text
            name_without_space = "_".join(name_without_ext.split())
            for sym in ["-", "+", "*", "/", "\""]:
                name_without_space = "_".join(name_without_space.split(sym))

            python_call_string = '%s = Model("%s")' % (name_without_space, name_without_ext)
            icon = item.icon()
            pixmap = icon.pixmap(20, 20)

            itemData = QtCore.QByteArray()
            dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.WriteOnly)
            model_id = name_without_ext
            dataStream.writeString(str(python_call_string))
            dataStream.writeString(str(model_id))

            mimeData = QtCore.QMimeData()
            mimeData.setText(python_call_string)
            mimeData.setData("openalealab/model", itemData)

            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setHotSpot(QtCore.QPoint(pixmap.width() / 2, pixmap.height() / 2))
            drag.setPixmap(pixmap)

            drag.start(QtCore.Qt.MoveAction)

        elif category == 'data':
            p = '%s/%r' % (category, str(obj))
            mimetype, mimedata = encode(p, mimetype='openalealab/data')
            qmime_data = QtCore.QMimeData()
            qmime_data.setData(mimetype, mimedata)
            qmime_data.setText(mimedata)
            drag = QtGui.QDrag(self)
            drag.setMimeData(qmime_data)
            drag.start()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("openalealab/model"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("openalealab/model"):
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        event.ignore()

class ProjectManagerModel(QtGui.QStandardItemModel):
    def __init__(self):
        QtGui.QStandardItemModel.__init__(self)
        self._data = {}
        self._root_item = None
        self._project = None

    def project_icon(self, project):
        # Propose icon by default.
        # If project have another one, use it
        icon_project = QtGui.QIcon(":/images/resources/openalea_icon2.png")
        icon = icon_project
        if hasattr(project, "icon"):
            icon_name = project.icon
            if len(icon_name):
                if icon_name[0] is not ":":
                    # local icon
                    icon_name = project.path / icon_name
                    # else native icon from oalab.gui.resources
                icon = QtGui.QIcon(icon_name)
        return icon

    def set_project(self, project):
        self._project = project
        self.refresh()

    def refresh(self):
        self.clear()
        project = self._project
        if project is None:
            return

        icons = dict(
            project=QtGui.QIcon(":/images/resources/openalea_icon2.png"),
            src=QtGui.QIcon(":/images/resources/filenew.png"),
            control=QtGui.QIcon(":/images/resources/node.png"),
            world=QtGui.QIcon(":/images/resources/plant.png"),
            startup=QtGui.QIcon(":/images/resources/editredo.png"),
            data=QtGui.QIcon(":/images/resources/fileopen.png"),
            doc=QtGui.QIcon(":/images/resources/book.png"),
            cache=QtGui.QIcon(":/images/resources/editcopy.png"),
            model=QtGui.QIcon(":/images/resources/new.png"),
            lib=QtGui.QIcon(":/images/resources/codefile-red.png"),
        )

        name = project.name
        parentItem = self.invisibleRootItem()
        item = QtGui.QStandardItem(name)
        self._root_item = name

        files = project.files

        item.setIcon(self.project_icon(project))
        parentItem.appendRow(item)


        categories = sorted(['model', 'startup', 'doc', 'data', 'lib'])
        for category in categories:
            item2 = QtGui.QStandardItem(category)
            item.appendRow(item2)

            if category in icons:
                item2.setIcon(icons[category])

            if not hasattr(project, category):
                continue


            if category == 'model':
                data_dict = project._model
            else:
                data_dict = getattr(project, category)

            names = data_dict.keys()
            for name in names:
                data = data_dict[name]
                item3 = QtGui.QStandardItem(name)
                if hasattr(data, 'icon'):
                    data_icon_path = data.icon
                else:
                    data_icon_path = ''
                item3.setIcon(QtGui.QIcon(data_icon_path))
                item3.setData((category, data))
                item2.appendRow(item3)


#         categories = files.keys()
#         for category in categories:
#             if hasattr(project, category):
#                 cat = getattr(project, category)
#                 if cat is not None:
#                     if len(cat) > 0:
#                         item2 = QtGui.QStandardItem(category)
#                         item.appendRow(item2)
#                         try:
#                             icon = eval(str("icon_" + category))
#                         except NameError:
#                             icon = QtGui.QIcon()
#                         item2.setIcon(icon)
#                 else:
#                     # hide name of category if we don't have object of this category
#                     pass
#
#                 if isinstance(cat, dict):
#                     for obj in cat.keys():
#                         l = obj.split(".")
#                         name = ".".join(l[:-1])
#                         ext = l[-1]
#                         item3 = QtGui.QStandardItem(obj)
#                         if category == "src":
#                             item3 = QtGui.QStandardItem(name)
#                             item3.setData((category, name))
#                             if ext in self.icons.keys():
#                                 item3.setIcon(QtGui.QIcon(self.icons[ext]))
#                         item2.appendRow(item3)
#                 else:
#                     # Useful for category "localized" which store a bool and not a list
#                     item3 = QtGui.QStandardItem(cat)
#                     item2.appendRow(item3)

    def projectdata(self, index):
        if index is None:
            return None
        if self._project is None:
            return

        if index.parent().data() in self._project.categories():
            return (index.parent().data(), index.data())
        elif index.data() in self._project.categories():
            return ('category', index.data())
        elif index.data() == self._root_item:
            return ('project', index.data())
        else:
            return None

