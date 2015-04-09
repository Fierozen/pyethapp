"""
Essential parts borrowed from https://github.com/ipython/ipython/pull/1654
"""

import code
import signal
from devp2p.service import BaseService
import gevent
from gevent.event import Event
import IPython
import IPython.core.shellapp
from IPython.lib.inputhook import InputHookBase, inputhook_manager, GlutInputHook, stdin_ready


GUI_GEVENT = 'gevent'


def inputhook_gevent():
    while not stdin_ready():
        gevent.sleep(0.05)
    return 0


@inputhook_manager.register('gevent')
class GeventInputHook(InputHookBase):

    def enable(self, app=None):
        """Enable event loop integration with gevent.
        Parameters
        ----------
        app : ignored
            Ignored, it's only a placeholder to keep the call signature of all
            gui activation methods consistent, which simplifies the logic of
            supporting magics.
        Notes
        -----
        This methods sets the PyOS_InputHook for gevent, which allows
        gevent greenlets to run in the background while interactively using
        IPython.
        """
        self.manager.set_inputhook(inputhook_gevent)
        self._current_gui = GUI_GEVENT
        return app

    def disable(self):
        """Disable event loop integration with gevent.
        This merely sets PyOS_InputHook to NULL.
        """
        self.manager.clear_inputhook()


# ipython needes to accept "--gui gevent" option
IPython.core.shellapp.InteractiveShellApp.gui.values += ('gevent',)


class Console(BaseService):

    """A service starting an interactive ipython session when receiving the
    SIGSTP signal (e.g. via keyboard shortcut CTRL-Z).
    """

    name = 'console'

    def __init__(self, app):
        super(Console, self).__init__(app)
        self.interrupt = Event()
        gevent.signal(signal.SIGTSTP, self.interrupt.set)
        self.console_locals = []

    def start(self):
        super(Console, self).start()
        self.console_locals = {}
        self.console_locals.update(self.app.services)
        self.console_locals['app'] = self.app

    def _run(self):
        while True:
            self.interrupt.wait()
            IPython.start_ipython(argv=['--gui', 'gevent'], user_ns=self.console_locals)
            self.interrupt.clear()
