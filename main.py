from Controller.controller import Controller
import signal
from log_sys import _log_sys_init


def main():
    _log_sys_init()
    obj = Controller()
    signal.signal(signal.SIGINT, obj.sigint_handler)
    obj.run()


if __name__=="__main__":
    main()