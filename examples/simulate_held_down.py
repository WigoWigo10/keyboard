import time

import directkeys

# Sends 20 "key down" events in 0.1 second intervals, followed by a single
# "key up" event.
for i in range(20):
    directkeys.press('a')
    time.sleep(0.1)
directkeys.release('a')
