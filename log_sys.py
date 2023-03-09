

def _log_sys_init():
    global ui_tips_log_msg
    ui_tips_log_msg = []


def send_log_msg(color_code, msg):
    global ui_tips_log_msg
    ui_tips_log_msg.append([color_code, msg])


def ret_log_msg():
    global ui_tips_log_msg
    ret = ui_tips_log_msg[:]
    ui_tips_log_msg = []
    return ret
