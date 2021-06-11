import argparse
import os
import signal
import subprocess
import sys
import threading

from client import Client


worker_process = None


def on_connect(client):
    print("connected")
    client.send("hello")


def on_message(client, message):
    global worker_process

    print("received message from socket client: {}".format(message))

    if message == "start":
        worker_process.send_signal(signal.SIGUSR1)
    elif message == "stop":
        stop_worker()
    else:
        print("unknown message", message)


def worker_reader(client, my_worker):
    global worker_process

    print("worker_reader thread started for pid {}".format(my_worker.pid))

    for line in iter(my_worker.stdout.readline, b""):
        message = line.decode("ascii").strip()

        print(
            "received message from worker process pid {}: {}".format(
                my_worker.pid, message
            )
        )

        if message == "stopped":
            start_worker(client)
        if client.state == "connected":
            client.send(message)
        else:
            print("cannot send message because client state is {}".format(client.state))

    # When we get here, the child process has exited. If it exited cleanly, it
    # would have sent "stopped" and we would have already started a replacement.
    # If the global worker_process is the same as my_worker, that means we did
    # not receive "stopped" so did not start a new worker process.
    if worker_process == my_worker:
        print("pid {} did not exit cleanly".format(my_worker.pid))

        start_worker(client)

    print("worker_reader thread for pid {} is exiting".format(my_worker.pid))


def start_worker(client):
    global worker_process

    print("starting new worker_process")

    # -u is to avoid buffering output or we won't receive messages printed to
    # stdout until the process exits.
    worker_process = subprocess.Popen(
        args=[sys.executable, "-u", "main.py"],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,  # This allows us to read what the process prints to stdout.
    )

    print("new worker_process pid: {}".format(worker_process.pid))

    # This function gets called from the thread running `client.loop_forever` so
    # it can't block or we will stop receiving messages. Start a new thread to
    # read from the subprocess.
    reader_thread = threading.Thread(
        target=worker_reader,
        args=(
            client,
            worker_process,
        ),
    )

    reader_thread.start()


def stop_worker():
    if not worker_process:
        print("worker not started")
        return

    print("sending signal to stop to pid {}".format(worker_process.pid))

    worker_process.send_signal(signal.SIGUSR2)


parser = argparse.ArgumentParser(description="daemon")
parser.add_argument("host", type=str, help="host")
parser.add_argument("port", type=int, help="port")
args = parser.parse_args()

client = Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect((args.host, args.port))
start_worker(client)
client.loop_forever()
