from IPython.kernel.zmq.kernelbase import Kernel

import rpy2.rinterface as ri
import rpy2.robjects as ro

import re

__version__ = '0.1'

version_pat = re.compile(r'version (\d+(\.\d+)+)')


class RKernel(Kernel):
    implementation = 'r2_kernel'
    implementation_version = __version__

    @property
    def language_version(self):
        v = self.r('R.version')
        return v.rx('major')[0][0] + '.' + v.rx('minor')[0][0]

    _banner = None

    @property
    def banner(self):
        if self._banner is None:
            self._banner = self.r('R.version.string')[0]
        return self._banner

    language_info = {'name': 'R',
                     'codemirror_mode': 'r',
                     'mimetype': 'text/x-rsrc',
                     'file_extension': '.r'}

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self.r = ro.r

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        if silent:
            ri.set_writeconsole(lambda output: None)
        else:
            def stream(output):
                content = {'name': 'stdout', 'text': output}
                self.send_response(self.iopub_socket, 'stream', content)
            ri.set_writeconsole(stream)

        interrupted = False
        try:
            self.r(code.rstrip())
        except KeyboardInterrupt:
            # TODO: this branch doesn't happen
            interrupted = True
        except ri.RRuntimeError as e:
            return {'status': 'error', 'execution_count': self.execution_count,
                    'ename': 'ERROR', 'evalue': e.args[0], 'traceback': []}

        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}
        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}
