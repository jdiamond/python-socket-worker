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
    print("received message", message)
    if message == "start":
        worker_process.send_signal(signal.SIGUSR1)
    elif message == "stop":
        stop_worker()
    else:
        print("unknown message", message)


def worker_reader(client, my_worker):
    global worker_process
    print("worker_reader thread started")
    for line in iter(my_worker.stdout.readline, b""):
        message = line.decode("ascii").strip()
        print('received "{}" from worker'.format(message))
        if message == "stopped":
            worker_process = None
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
        worker_process = None
        start_worker(client)
    print("worker_reader thread exiting")


def start_worker(client):
    global worker_process
    if worker_process:
        print("worker already started")
        return
    # -u is to avoid buffering output or we won't receive messages printed to
    # stdout until the process exits.
    worker_process = subprocess.Popen(
        args=[sys.executable, "-u", "main.py"],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,  # This allows us to read what the process prints to stdout.
    )
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
    global worker_process
    if not worker_process:
        print("worker not started")
        return
    worker_process.send_signal(signal.SIGUSR2)
    worker_process = None


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
