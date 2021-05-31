import signal
import time

stop_working = False


def interrupt_handler(signum, frame):
    global stop_working
    if not stop_working:
        # This is the first time we've received SIGINT. Set a flag to gracefully
        # stop working before exiting.
        print("stopping")
        stop_working = True
    else:
        # This is the second time we've received SIGINT so call the default
        # handler which will forcefully exit the process.
        signal.default_int_handler(signum, frame)


signal.signal(signal.SIGINT, interrupt_handler)

print("starting")

for i in range(10):
    print("working", i + 1)
    time.sleep(2)
    if stop_working:
        print("stopped")
        break

print("done")
