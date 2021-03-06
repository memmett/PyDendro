# Copyright (c) 2011, Matthew Emmett.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   1. Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import os
import os.path
import pydendro.rwl as rwl

from PyQt4.QtCore import *
from PyQt4.QtGui import *


###############################################################################

class PyDendroNormalizationDialog(QDialog):

  def __init__(self, parent, ui, model):

    import pydendro.normalize
    from textwrap import dedent

    super(QDialog, self).__init__(parent)

    self.ui = ui
    self.model = model
    self.setMinimumSize(800, 200)

    
    norms = [ (None, 'none', 'No normalization.') ]
    for name in dir(pydendro.normalize):
      attr = getattr(pydendro.normalize, name, None)
      if callable(attr):
        norms.append((attr, attr.__name__, dedent(attr.__doc__)))

    self.norms = norms

    self.create_dialog()


  def create_dialog(self):

    self.setWindowTitle("Normalization")

    self.norms_list = QListWidget(self)
    self.norms_list.setSelectionMode(QAbstractItemView.SingleSelection)
    for norm in self.norms:
      item = QListWidgetItem(norm[1])
      item.docstring = norm[2]
      item.callable  = norm[0]
      self.norms_list.addItem(item)

    self.connect(self.norms_list, SIGNAL('itemSelectionChanged()'), self.on_norm_selection)

    self.doc = QLabel()
    self.doc.setStyleSheet("QLabel { font-family: sans-serif; min-width: 500px; min-height: 100px; }")
    self.doc.setAlignment(Qt.AlignTop)

    hbox = QHBoxLayout()
    hbox.addWidget(self.norms_list)
    hbox.addWidget(self.doc)

    bbox = QDialogButtonBox()
    bbox.addButton(QDialogButtonBox.Save)
    bbox.addButton(QDialogButtonBox.Cancel)
    self.connect(bbox, SIGNAL("accepted()"), self.on_accepted)    
    self.connect(bbox, SIGNAL("rejected()"), self.on_rejected)
    
    vbox = QVBoxLayout()
    vbox.addWidget(QLabel("Select normalization method:"))
    vbox.addLayout(hbox)
    vbox.addWidget(bbox)
    self.setLayout(vbox)


  def on_norm_selection(self):

    items = self.norms_list.selectedItems()

    if len(items) == 1:
      self.doc.setText(items[0].docstring)
    

  def on_accepted(self):

    items = self.norms_list.selectedItems()

    if len(items) == 1:
      self.model.normalization = items[0].callable
      self.ui.on_draw()


  def on_rejected(self):

    self.reject()


###############################################################################

class PyDendroSaveStacksDialog(QDialog):

  def __init__(self, parent, ui, model):

    super(QDialog, self).__init__(parent)

    self.ui = ui
    self.model = model
    self.stack_items = {}

    self.create_dialog()


  def create_dialog(self):

    self.setWindowTitle("Save stacks")


    # directory
    directory_group = QGroupBox("Working directory")
    vbox = QVBoxLayout()
    
    vbox.addWidget(QLabel("Select working directory in which to save stacks:"))

    self.directory_button = QPushButton("Choose")
    self.connect(self.directory_button, SIGNAL("clicked()"), self.on_set_directory)
    self.directory = QLineEdit(self.ui.working_directory)
    self.directory.setFixedWidth(400)

    hbox = QHBoxLayout()
    hbox.addWidget(self.directory, stretch=1)
    hbox.addWidget(self.directory_button)
    vbox.addLayout(hbox)

    directory_group.setLayout(vbox)

    # stacks
    stacks_group = QGroupBox("Stacks to save")
    vbox = QVBoxLayout()
    
    vbox.addWidget(QLabel("Select stacks to save (will be overwritten):"))

    grid = QGridLayout()
    grid.addWidget(QLabel("Save"), 0, 0, Qt.AlignHCenter)
    grid.addWidget(QLabel("Stack"), 0, 1)
    grid.addWidget(QLabel("Filename"), 0, 2)

    for k, stack_name in enumerate(self.model.stacks):
      stack = self.model.get_stack(stack_name)

      save = QCheckBox()
      state = 2 if not stack.immutable else 0
      save.setCheckState(state)

      name = QLabel(stack.name)

      filename = QLineEdit(stack.name + '.rwl')

      self.stack_items[stack.name] = (save, name, filename)
      
      grid.addWidget(save, k+1, 0, Qt.AlignCenter)
      grid.addWidget(name, k+1, 1)
      grid.addWidget(filename, k+1, 2)

    vbox.addLayout(grid)

    stacks_group.setLayout(vbox)

    # button box
    bbox = QDialogButtonBox()
    bbox.addButton(QDialogButtonBox.Save)
    bbox.addButton(QDialogButtonBox.Cancel)
    self.connect(bbox, SIGNAL("accepted()"), self.on_accepted)    
    self.connect(bbox, SIGNAL("rejected()"), self.on_rejected)
    
    vbox = QVBoxLayout()
    vbox.addWidget(directory_group)
    vbox.addWidget(stacks_group)
    vbox.addWidget(bbox)

    self.setLayout(vbox)


  def on_set_directory(self):

    directory = str(QFileDialog.getExistingDirectory(
      parent=self, caption="Select working directory",
      directory=str(self.directory.text())))

    if directory:
      self.directory.setText(directory)


  def on_accepted(self):

    dirname = str(self.directory.text())

    for stack_name in self.stack_items:
      (save, name, filename) = self.stack_items[stack_name]

      if save.checkState() == 2:
        # save this stack

        stack = self.model.get_stack(stack_name)
        
        samples = []
        for sample_name in stack.samples:
          sample = self.model.get_sample(sample_name)
          samples.append(sample.to_plain())

        if samples:
          fullname = os.path.join(dirname, str(filename.text()))
          rwl.write(fullname, samples)

    self.accept()


  def on_rejected(self):

    self.reject()


###############################################################################

class PyDendroDeleteStacksDialog(QDialog):

  def __init__(self, parent, ui, model):

    super(QDialog, self).__init__(parent)

    self.ui = ui
    self.model = model

    self.create_dialog()


  def create_dialog(self):

    self.setWindowTitle("Delete stacks")
    vbox = QVBoxLayout()

    # stacks
    vbox.addWidget(QLabel("Select stacks to delete:"))

    self.stack_list = QListWidget()
    self.stack_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    
    for stack in self.model.stacks:
      item = QListWidgetItem(self.stack_list)
      item.setText(stack)
      self.stack_list.addItem(item)

    vbox.addWidget(self.stack_list)

    # button box
    bbox = QDialogButtonBox()
    bbox.addButton(QDialogButtonBox.Ok)
    bbox.addButton(QDialogButtonBox.Cancel)
    self.connect(bbox, SIGNAL("accepted()"), self.on_accepted)    
    self.connect(bbox, SIGNAL("rejected()"), self.on_rejected)
    
    vbox.addWidget(bbox)

    self.setLayout(vbox)


  def on_accepted(self):

    for item in self.stack_list.selectedItems():
      stack = str(item.text())
      self.model.remove_stack(stack)
      
    self.ui.update_stacks()
    self.accept()


  def on_rejected(self):

    self.reject()


###############################################################################

class PyDendroRenameStackDialog(QDialog):

  def __init__(self, parent, ui, model):

    super(QDialog, self).__init__(parent)

    self.ui = ui
    self.model = model

    self.setWindowTitle("Rename stack")

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel("Rename stack"))

    hbox = QHBoxLayout()

    hbox.addWidget(QLabel("Rename "))
    self.stack_combo = QComboBox()
    for stack in self.model.stacks:
      self.stack_combo.addItem(stack)

    hbox.addWidget(self.stack_combo)
    hbox.addWidget(QLabel(" to "))

    self.new_name_input = QLineEdit()
    hbox.addWidget(self.new_name_input)

    vbox.addLayout(hbox)


    bbox = QDialogButtonBox()
    bbox.addButton(QDialogButtonBox.Ok)
    bbox.addButton(QDialogButtonBox.Cancel)
    self.connect(bbox, SIGNAL("accepted()"), self.on_accepted)    
    self.connect(bbox, SIGNAL("rejected()"), self.on_rejected)

    vbox.addWidget(bbox)

    self.setLayout(vbox)

  def on_accepted(self):

    old_name = str(self.stack_combo.currentText())
    new_name = str(self.new_name_input.text())
    
    stack = self.model.rename_stack(old_name, new_name)
    self.ui.update_stacks()

    self.accept()


  def on_rejected(self):

    self.reject()
