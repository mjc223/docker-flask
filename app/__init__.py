"""A simple flask web app"""
from flask import Flask, render_template
import os
import datetime
import time
from flask import g, request
from rfc3339 import rfc3339

from app.context_processors import utility_text_processors
from app.simple_pages import simple_pages
from flask import render_template, Flask, has_request_context, request
from app.db.models import User
import logging
from flask.logging import default_handler


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super(record).format(record) #"""changed this"""

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
    app.register_blueprint(simple_pages)
    app.context_processor(utility_text_processors)

    # Deactivate the default flask logger so that log messages don't get duplicated
    app.logger.removeHandler(default_handler)

    # get root directory of project
    root = os.path.dirname(os.path.abspath(__file__))
    # set the name of the apps log folder to logs
    logdir = os.path.join(root, 'logs')
    # make a directory if it doesn't exist
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    # set name of the log file
    log_file = os.path.join(logdir, 'info.log')

    handler = logging.FileHandler(log_file)
    # Create a log file formatter object to create the entry in the log
    formatter = RequestFormatter(
        '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
        '%(levelname)s in %(module)s: %(message)s'
    )
    # set the formatter for the log entry
    handler.setFormatter(formatter)
    # Set the logging level of the file handler object so that it logs INFO and up
    handler.setLevel(logging.INFO)
    # Add the handler for the log entry
    app.logger.addHandler(handler)

    @app.before_request
    def start_timer():
        g.start = time.time()

    @app.after_request
    def log_request(response):
        if request.path == '/favicon.ico':
            return response
        elif request.path.startswith('/static'):
            return response
        elif request.path.startswith('/bootstrap'):
            return response

        now = time.time()
        duration = round(now - g.start, 2)
        dt = datetime.datetime.fromtimestamp(now)
        timestamp = rfc3339(dt, utc=True)

        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        host = request.host.split(':', 1)[0]
        args = dict(request.args)

        log_params = [
            ('method', request.method),
            ('path', request.path),
            ('status', response.status_code),
            ('duration', duration),
            ('time', timestamp),
            ('ip', ip),
            ('host', host),
            ('params', args)
        ]

        request_id = request.headers.get('X-Request-ID')
        if request_id:
            log_params.append(('request_id', request_id))

        parts = []
        for name, value in log_params:
            part = name + ': ' + str(value) + ', '
            parts.append(part)
        line = " ".join(parts)
        #this triggers a log entry to be created with whatever is in the line variable
        app.logger.info('this is the plain message')

        return response

    return app



@login_manager.user_loader
def user_loader(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None
