from IPython.kernel.zmq.kernelapp import IPKernelApp
from .kernel import RKernel
IPKernelApp.launch_instance(kernel_class=RKernel)
