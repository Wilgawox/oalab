# -*- coding: utf-8 -*-
# -*- python -*-
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

__all__ = ['Session']

import os, sys
import warnings
from openalea.vpltk.shell.shell import get_interpreter_class
from openalea.oalab.package.manager import package_manager
from openalea.vpltk.project.manager import ProjectManager
from openalea.oalab.control.manager import ControlManager
from openalea.core.settings import get_openalea_tmp_dir
from openalea.oalab.config.main import MainConfig
from openalea.oalab.world.world import World
from openalea.core.singleton import Singleton
from openalea.core.path import path



class Session(object):
    """
    Session is a non graphical class that centralize managers for ...

      - application settings (:class:`~openalea.oalab.config.main.MainConfig`)
      - projects (:class:`~openalea.oalab.project.manager.ProjectManager`)
      - world (:class:`~openalea.oalab.world.world.World`)
      - interpreter (see :mod:`~openalea.vpltk.shell.shell`)

    """

    __metaclass__ = Singleton

    def __init__(self):
        self._project = None
        self._is_proj = False

        self.tmpdir = path(get_openalea_tmp_dir())

        self._config = MainConfig()
        self.extension = None

        self.package_manager = package_manager
        self.control_manager = ControlManager()
        self.project_manager = ProjectManager()

        self.world = World()

        interpreter_class = get_interpreter_class()
        self.interpreter = interpreter_class()
        if hasattr(self.interpreter.shell, "events"):
            self.interpreter.shell.events.register("post_execute", self.add_to_history)
        else:
            print("You are using a version of ipython < 2. History is not implemented for this version.")

        self.project_manager.set_shell(self.interpreter.shell)

        self.interpreter.locals['session'] = self
        self.debug_plugins = ''
        self.debug = False

        self.gui = True

        self.old_syspath = sys.path

    @property
    def project(self):
        """
        :return: current project if one is opened. Else return None.
        """
        return self.project_manager.cproject

    def load_config_file(self, filename, path=None):
        self._config.load_config_file(filename=filename, path=path)

    def update_namespace(self):
        """ Stub method from allwidgets. CPL: TODO

        Definition: Update namespace
        """
        self.interpreter.locals['project_manager'] = self.project_manager
        self.interpreter.locals['control_manager'] = self.control_manager
        self.interpreter.locals['package_manager'] = self.package_manager
        self.interpreter.locals['world'] = self.world
        self.interpreter.locals['follow'] = self.control_manager.register_follower
        self.interpreter.locals['unfollow'] = self.control_manager.unregister_follower

        if self.project:
            if self.project.path.exists():
                os.chdir(self.project.path)
                sys.path.insert(0, str(self.project.path / 'lib'))
            else:
                os.chdir(self.tmpdir)
                sys.path.insert(0, str(self.tmpdir / 'lib'))
            self.interpreter.locals['project'] = self.project
            self.interpreter.locals['Model'] = self.project.get_model
            self.interpreter.locals['data'] = self.project.path / 'data'
        else:
            # close
            sys.path = self.old_syspath

    def add_to_history(self, *args, **kwargs):
        """
        Send the last sent of history to the components that display history
        """
        from openalea.oalab.service.history import display_history
        records = self.interpreter.shell.history_manager.get_range()

        input_ = ''
        # loop all elements in iterator to get last one.
        # TODO: search method returning directly last input
        for session, line, input_ in records:
            pass
        display_history(input_)

    config = property(fget=lambda self:self._config.config)


