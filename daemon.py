import argparse
import os
import signal
import subprocess
import sys
import threading

from client import Client


def on_connect(client):
    print("connected")
    client.send("hello")


def on_message(client, message):
    print("received message", message)
    if message == "start":
        start_worker(client)
    elif message == "stop":
        stop_worker()
    else:
        print("unknown message", message)


worker_process = None


def worker_reader(client):
    global worker_process
    print("worker_reader thread started")
    for line in iter(worker_process.stdout.readline, b""):
        message = line.decode("ascii").strip()
        print('received "{}" from worker_process'.format(message))
        if client.state == "connected":
            client.send(message)
        else:
            print("cannot send message because client state is {}".format(client.state))
    print("worker_reader thread exiting")
    worker_process = None


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
    reader_thread = threading.Thread(target=worker_reader, args=(client,))
    reader_thread.start()


def stop_worker():
    global worker_process
    if not worker_process:
        print("worker not started")
        return
    worker_process.send_signal(signal.SIGINT)
    # We trust that sending SIGINT will eventually close the subprocess. If we
    # wanted to forcibly terminate the subprocess after a timeout, we could do
    # that on a separate thread.
    worker_process = None


parser = argparse.ArgumentParser(description="daemon")
parser.add_argument("host", type=str, help="host")
parser.add_argument("port", type=int, help="port")
args = parser.parse_args()

client = Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect((args.host, args.port))
client.loop_forever()
