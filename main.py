import random
import signal
import time


worker_state = "not_working"


def start_work(signum, frame):
    global worker_state
    worker_state = "working"


def stop_work(signum, frame):
    global worker_state
    print("stopping")
    worker_state = "stopping"


signal.signal(signal.SIGUSR1, start_work)
signal.signal(signal.SIGUSR2, stop_work)


def main():
    global worker_state

    while True:
        if worker_state == "working":
            break
        time.sleep(1)

    print("starting")

    for i in range(5):
        print("working", i + 1)

        if random.random() >= 0.5:
            print("crashing")
            raise Exception("crash")

        time.sleep(2)

        if worker_state == "stopping":
            print("stopped")
            break

    time.sleep(2)

    print("done")


main()
