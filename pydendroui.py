"""PyDendro GUI."""

import os
import sys

try:
    sys.path.append(os.environ['PYDENDRO'])
except:
    pass

from pydendro.stack import Stack
from pydendro.ui.model import PyDendroModel
from pydendro.ui.ui import PyDendroMainWindow
from PyQt4.QtGui import QApplication

# create application, model and form
app   = QApplication(sys.argv)
model = PyDendroModel()
ui    = PyDendroMainWindow()

model.ui = ui
ui.model = model

# add default stacks
stack = Stack('MASTER', False)
model.add_stack(stack)

stack = Stack('WORKING', False)
model.add_stack(stack)

ui.add_stack_view()
ui.update_stacks()

# fire up the ui
ui.show()
app.exec_()
