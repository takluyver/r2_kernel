An IPython wrapper kernel for R

This requires IPython 3 and rpy2, and a couple of R packages:

    install.packages(c('evaluate', 'devtools'))
    devtools::install_github("takluyver/IRdisplay")

To test it, install with ``setup.py``, then::

    ipython qtconsole --kernel r2
