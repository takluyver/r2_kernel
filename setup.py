from distutils.core import setup
from distutils.command.install import install
from distutils import log
import json
import os
import sys

kernel_json = {"argv":[sys.executable,"-m","r2_kernel", "-f", "{connection_file}"],
 "display_name":"R",
 "language":"R",
}

class install_with_kernelspec(install):
    def run(self):
        # Regular installation
        install.run(self)

        # Now write the kernelspec
        from IPython.kernel.kernelspec import install_kernel_spec
        from IPython.utils.tempdir import TemporaryDirectory
        with TemporaryDirectory() as td:
            os.chmod(td, 0o755) # Starts off as 700, not user readable
            with open(os.path.join(td, 'kernel.json'), 'w') as f:
                json.dump(kernel_json, f, sort_keys=True)
            # TODO: Copy resources

            log.info('Installing IPython kernel spec')
            install_kernel_spec(td, 'r2', user=self.user, replace=True)

with open('README.rst') as f:
    readme = f.read()

svem_flag = '--single-version-externally-managed'
if svem_flag in sys.argv:
    # Die, setuptools, die.
    sys.argv.remove(svem_flag)

setup(name='r2_kernel',
      version='0.1',
      description='An R wrapper kernel for IPython',
      long_description=readme,
      author='Thomas Kluyver',
      author_email='thomas@kluyver.me.uk',
      url='https://github.com/takluyver/r2_kernel',
      packages=['r2_kernel'],
      cmdclass={'install': install_with_kernelspec},
      install_requires=['IPython>=3', 'rpy2'],
      classifiers = [
          'Framework :: IPython',
          'License :: OSI Approved :: BSD License',
      ]
)