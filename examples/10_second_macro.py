import time

import directkeys

directkeys.start_recording()
time.sleep(10)
events = directkeys.stop_recording()
directkeys.replay(events)
