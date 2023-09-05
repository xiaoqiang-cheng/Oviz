from Controller.controller import Controller
import signal
from log_sys import _log_sys_init
from Utils.common_utils import *


dirname = os.path.dirname(GuiCoreLib.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

def main():
    _log_sys_init()
    obj = Controller()
    signal.signal(signal.SIGINT, obj.sigint_handler)
    obj.run()





if __name__=="__main__":
    main()