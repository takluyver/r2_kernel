library(evaluate)

namedlist <- function() {
    # create an empty named list
    return(setNames(list(), character(0)))
}

plot_options=new.env()

#'Set options for plotting
#'
#'IRkernel displays plots in the notebook with calls to png().
#'This function allows to set the variables that will be passed on to
#'png(), for example width or height, see help(png).
#' @param ... options that will be passed to  png()
#' @export
set_plot_options <- function(...){
    options <- list(...)
    for(opt in names(options)){
        assign( opt, options[[opt]], plot_options )
    }
}

#'Get options for plotting
#'
#'Use set_plot_options() for modifying.
#' @export
get_plot_options <- function(){
    return(as.list(plot_options))
}

handle_error = function(e) {
    .report_error(toString(e))
}

silent_output_handler = new_output_handler(text=identity, graphics=identity,
    message=identity, warning=identity, value=identity, error=handle_error)

handle_value = function (obj) {
    data = list()
    data['text/plain'] = paste(capture.output(print(obj)), collapse="\n")
    iopub("execute_result", list(data=data, metadata=namedlist(),
              execution_count=.execution_count))
}
stream = function(output, streamname) {
    iopub("stream", list(name=streamname, text=paste(output, collapse="\n")))
}
handle_graphics = function(plotobj) {
    tf = tempfile(fileext='.png')
    do.call(png, c(list(filename=tf), get_plot_options()))
    replayPlot(plotobj)
    dev.off()
    display_png(filename=tf)
}
handle_message = function(o){
  stream(paste(o$message, collapse = ''), 'stderr')
}
handle_warning = function(o){
  call = if (is.null(o$call)) '' else {
   call = deparse(o$call)[1]
   paste('In', call)
  }
stream(sprintf('Warning message:\n%s: %s', call, o$message), 'stderr')
}

output_handler = new_output_handler(
    text=function(o) {stream(o, 'stdout')},
    graphics = handle_graphics,
    message = handle_message,
    warning = handle_warning,
    error = handle_error,
    value = handle_value
)

# Set the pager function to display help output
options(pager=function(files, header, title, delete.file) {
  text=title
  for (path in files) {
    text = c(text, header, readLines(path))
  }
  if (delete.file) file.remove(files)
  data = namedlist()
  data['text/plain'] = paste(text, collapse="\n")
  .add_payload('page', list(data=data))
})

.base_display  = function(data, metadata=NULL) {
    if (is.null(metadata)) {
        metadata = namedlist()
    }
    iopub("display_data", list(data=data, metadata=metadata)
        )
    invisible(T)
}

# Push the display function into the IRdisplay namespace
library(IRdisplay)
displayenv = environment(display)
unlockBinding("base_display", displayenv)
assign('base_display', .base_display, pos=displayenv)
rm(displayenv)
