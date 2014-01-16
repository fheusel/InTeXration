import logging
from bottle import Bottle, request, abort, static_file
import os
import json
from intexration.loghandler import LogHandler
from intexration.task import Task


# Logger
logger = logging.getLogger('intexration')


class Server:
    def __init__(self, host, port, api_keys):
        self._host = host
        self._port = port
        self._api_keys = api_keys
        self._app = Bottle()
        self._route()

    def _route(self):
        self._app.route('/', method="GET", callback=self._index)
        self._app.route('/hook/<api_key>', method="POST", callback=self._hook)
        self._app.route('/out/<repo>', method="GET", callback=self._out)
        self._app.route('/log/<repo>', method="GET", callback=self._log)

    def start(self):
        self._app.run(host=self._host, port=self._port)

    def _hook(self, api_key):
        def validate(key_to_check):
            path = self._api_keys
            if not os.path.isfile(path):
                return False
            key_file = open(path, "r")
            for line in key_file.readlines():
                key = line.rstrip()
                if key_to_check == key:
                    return True
            return False

        if not validate(api_key):
            logger.warning("Request denied: API key invalid.")
            abort(401, 'Unauthorized: API key invalid.')
        payload = request.forms.get('payload')
        try:
            data = json.loads(payload)
            url = data['repository']['url']
            name = data['repository']['name']
            commit = data['after']
            task = Task(url, name, commit)
            task.run()
            return 'InTeXration task started.'
        except ValueError:
            logger.warning("Request denied: Could not decode request body.")
            abort(400, 'Bad request: Could not decode request body.')

    @staticmethod
    def _index():
        return 'InTeXration is up and running.'

    @staticmethod
    def _out(repo):
        path = os.path.join(os.getcwd(), 'out', repo)
        return static_file('main.pdf', path)

    @staticmethod
    def _log(repo):
        path = os.path.join(os.getcwd(), 'out', repo, 'main.log')
        log_handler = LogHandler(path)
        html = '<h1>Errors</h1>'
        for line in log_handler.get_errors():
            html += line.rstrip() + '<br/>'
        html += '<h1>Complete Log</h1>'
        for line in log_handler.get_all():
            html += line + '<br/>'
        return html