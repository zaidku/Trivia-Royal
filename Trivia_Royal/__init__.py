"""
The flask application package.
"""

from flask import Flask
app = Flask(__name__)
app.secret_key = "zk-this-is-super-secret-🔐"



import Trivia_Royal.views
