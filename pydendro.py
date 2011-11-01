"""PyDendro GUI."""

import sys

from pydendro import PyDendroModel, PyDendroMainWindow, Stack
from PyQt4.QtGui import QApplication

# create application, model and form
app         = QApplication(sys.argv)
model       = PyDendroModel()
main_window = PyDendroMainWindow()

model.main_window = main_window
main_window.model = model

# add default stacks
stack = Stack('MASTER', False)
model.add_stack(stack)

stack = Stack('WORKING', False)
model.add_stack(stack)

main_window.add_stack_view()
main_window.update_stacks()

# fire up the ui
main_window.show()
app.exec_()
