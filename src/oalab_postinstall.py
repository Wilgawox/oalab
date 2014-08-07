# Postinstall scripts
__license__ = "Cecill-C"
__revision__ = " $Id: $"

def install():
    from openalea.deploy.shortcut import create_win_shortcut, set_win_reg, create_fd_shortcut
    from openalea.deploy import get_base_dir
    import sys
    from os.path import join as pj

    # Get the location of the installed egg
    base_dir = get_base_dir('openalea.oalab')
    share_dir = pj(base_dir, 'share')
    
    winexe = sys.executable
    winexe = winexe.replace('python.exe', 'pythonw.exe')
    
    prefix = base_dir.lower().split("lib")[0]

    create_win_shortcut(name = 'OALab',
                        target = winexe,
                        arguments = '"'+pj(sys.prefix, 'Scripts', 'oalab-script.pyw')+'"',
                        startin = "", 
                        icon = pj(share_dir, 'openalea_icon.ico'),
                        description = "OpenAlea Laboratory",
                        menugroup = "OpenAlea")

def uninstall():
    pass

if __name__ == '__main__':
	install()