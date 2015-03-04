from os.path import dirname, join as pjoin
from IPython.kernel.zmq.kernelbase import Kernel

import rpy2.rinterface as ri
import rpy2.robjects as ro

from rpy2.robjects.packages import importr
evaluate = importr('evaluate')

import re

__version__ = '0.1'

def pre_json_convert(robj):
    if not isinstance(robj, ri.Sexp):
        return robj
    try:
        names = robj.do_slot('names')
    except LookupError:
        # Vector - if length is one, treat as scalar
        if len(robj) == 1:
            return pre_json_convert(robj[0])

        return [pre_json_convert(e) for e in robj]

    else:
        # Named list - convert to dict
        return {k: pre_json_convert(v) for (k,v) in zip(names, robj)}


class RKernel(Kernel):
    implementation = 'r2_kernel'
    implementation_version = __version__

    @property
    def language_version(self):
        v = ro.r('R.version')
        return v.rx('major')[0][0] + '.' + v.rx('minor')[0][0]

    _banner = None

    @property
    def banner(self):
        if self._banner is None:
            self._banner = ro.r('R.version.string')[0]
        return self._banner

    language_info = {'name': 'R',
                     'codemirror_mode': 'r',
                     'mimetype': 'text/x-rsrc',
                     'file_extension': '.r'}

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)

        # Set up output handlers
        ri.globalenv['iopub'] = ri.rternalize(self.iopub)
        ri.globalenv['.report_error'] = ri.rternalize(self.report_error)
        with open(pjoin(dirname(__file__), 'init.r'), 'r') as f:
            ro.r(f.read())

        self.silent_output_handler = ri.globalenv['silent_output_handler']
        self.output_handler = ri.globalenv['output_handler']

    def iopub(self, msg_type, content):
        content = pre_json_convert(content)
        self.send_response(self.iopub_socket, msg_type[0], content)

    error = None
    silent = False

    def report_error(self, e):
        self.error = e[0]
        if not self.silent:
            import sys
            print(self.error, file=sys.__stdout__)
            msg_content =  {'ename': 'ERROR',
                            'evalue': self.error,
                            'traceback': [self.error],
                            'execution_count': self.execution_count
                           }
            self.send_response(self.iopub_socket, 'error', msg_content)

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}

        self.silent = silent
        ro.globalenv['.execution_count'] = self.execution_count

        oh = self.silent_output_handler if silent else self.output_handler

        self.error = None
        interrupted = False
        try:
            evaluate.evaluate(code, envir=ri.globalenv, output_handler=oh)
        except KeyboardInterrupt:
            # TODO: this branch doesn't happen
            interrupted = True
        except ri.RRuntimeError as e:
            self.report_error(e.args[0])

        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}
        elif self.error is not None:
            return {'status': 'error', 'execution_count': self.execution_count,
                    'ename': 'ERROR', 'evalue': self.error, 'traceback': [self.error]}
        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}
