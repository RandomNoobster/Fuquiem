from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    return "Your bot is alive!"

def run():
    app.run()

def keep_alive():
    server = Thread(target=run)
    server.start()          