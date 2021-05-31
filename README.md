This is an example of how to implement a simple client/server system where clients perform work on behalf of events received from a server in Python.

The `Client` class in [client.py](client.py) is a generic, line-based protocol client that can send and receive messages ending with newlines across a TCP socket. It takes care of reconnecting, buffering, encoding, decoding, and other miscellaneous details. Its API is roughly inspired by the [Eclipse Paho MQTT Python Client](https://github.com/eclipse/paho.mqtt.python#client) but its implemenation is much simpler.

[daemon.py](daemon.py) uses the `Client` class to implement a simple protocol:

- When daemon connects (including reconnects), it sends a "hello" message to server.
- When server sends "start" message, daemon launches new worker process.
- Messages written to stdout by worker process get sent to server via daemon's existing connection.
- When server sends "stop" message, daemon sends SIGINT to worker process.
- If daemon's connection is broken while worker process is running, work can continue while daemon reconnects.

The work done by the worker could be done in a thread to avoid spawning a new process, but a nice advantage of separating the daemon and the worker into separate processes is it becomes really easy to test the worker without having to connect to a server and wait for it to send "start" commands. Just run main.py directly from a shell and press Ctrl+C to simulate the SIGINT signal the daemon would send when it receives a "stop" command from the server. This would be unsuitable for high-throughput workloads, but it is fine for work that takes several seconds to run and the max number of workers is limited.

The worker in [main.py](main.py) doesn't do any real work other than printing to stdout which, when spawned from the daemon, is converted into messages to send to the server. The key to being able to react to the "stop" command sent from the server to the daemon is to install a new handler for SIGINT. Anything written to stderr by main.py goes to the daemon's stderr.

To test the daemon, you will need a server for it to connect to. It's really easy to use netcat as a simple test server:

```
nc -l 127.0.0.1 12345 -k
```

This only supports one client at a time but is nice for testing line-based protocols because it prints what it receives to stdout and lets you type in lines of text in stdin to send to the currently connected client.

Start the daemon like this:

```
python3 daemon.py 127.0.0.1 12345
```

You should see "hello" in the server terminal right away. That message was sent by the daemon when it connected.

Type "start" in the server terminal and hit RETURN to send a message to the daemon to start a new worker process and "stop" to stop it. If you're typing while the worker is sending messages, it will make a mess on the screen but you can ignore that.

Press Ctrl+D in the server terminal to kill the connection and the daemon will reconnect after 1 second and send "hello" again but it should not affect a running worker process. Press Ctrl+C in the server terminal to kill netcat and daemon.py will try reconnecting forever.

I haven't tried writing a server in Python yet, but might try with the [socketserver](https://docs.python.org/3/library/socketserver.html) module.
