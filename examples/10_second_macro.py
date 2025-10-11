import directkeys
import time

directkeys.start_recording()
time.sleep(10)
events = directkeys.stop_recording()
directkeys.replay(events)
