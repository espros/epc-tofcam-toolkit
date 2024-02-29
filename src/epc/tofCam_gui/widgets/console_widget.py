from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager

WELCOME_MESSAGE = """Welcome to the espros TOFcam Console!

This console provides interactive access to the espros Time-of-Flight (TOF) camera functionalities. 

To get started:
1. An instance of the camera is available as 'cam'.
2. Use Python's built-in help function to view detailed information about any object, method, or module. For example, 'help(cam)'.
3. Use the TAB key for auto-completion. For instance, typing 'cam.' followed by the TAB key will display a list of all available methods and attributes of the 'cam' object.

Enjoy exploring and controlling your espros TOF camera!
"""

class Console_Widget(RichJupyterWidget):
    def __init__(self, parent=None):
        super(Console_Widget, self).__init__()
        self.kernel_manager = QtInProcessKernelManager()

    def startup_kernel(self, cam):
        self.kernel_manager.start_kernel()
        self.kernel_manager.kernel.gui = 'qt'
        self.kernel_manager.kernel.shell.banner1 = WELCOME_MESSAGE
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()
        self.kernel_client.namespace = {'widget': self}

        self.kernel_manager.kernel.shell.push({'cam': cam})
        self.show()
