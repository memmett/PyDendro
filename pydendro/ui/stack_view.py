
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class PyDendroSampleListItem(QListWidgetItem):

  def __init__(self, name, model):
    super(PyDendroSampleListItem, self).__init__(name)
    self.name = name
    self.model = model
    self.update()

  def update(self):
    sample = self.model.get_sample(self.name)

    if sample.first_year != sample.original_first_year:
      self.setText(self.name + ' (' + str(sample.first_year-sample.original_first_year) + ')')
    else:
      self.setText(self.name)
      

class PyDendroSampleList(QListWidget):
  pass

class PyDendroStackView(QDockWidget):

  def __init__(self, ui, model):

    super(QDockWidget, self).__init__(ui)

    self.hold = False

    self.ui = ui
    self.model = model

    self.stacks = set()
    self.samples = set()
    self.stack_items = {}
    self.sample_items = {}

    self.create_stack_view()


  def closeEvent(self, ev):
    super(QDockWidget, self).closeEvent(ev)
    self.ui.delete_stack_view(self)


  @property
  def selected_stacks(self):
    # return [str(item.text(0)) for item in self.stack_list.selectedItems()]
    return [str(item.text()) for item in self.stack_list.selectedItems()]    


  @property
  def selected_samples(self):
    return [item.name for item in self.sample_list.selectedItems()]


  def set_color(self, color):
    """Set color."""
    
    self.color = color
    self.current_color.setStyleSheet("QLabel { background-color: rgba(%d, %d, %d, %d) }"
                                     % self.color.getRgb())

  def update(self):
    """Update stack view."""
    
    self.update_stacks()
    self.update_samples()


  def update_stacks(self):
    """Update stack list."""
    
    old_stacks = self.stacks
    new_stacks = set()
    
    for stack in self.model.stacks:
      new_stacks.add(stack)
      if stack not in self.stacks:
        self.stacks.add(stack)
        # self.stack_items[stack] = QTreeWidgetItem(self.stack_list)
        # self.stack_items[stack].setText(0, stack)
        # self.stack_list.addTopLevelItem(self.stack_items[stack])
        self.stack_items[stack] = QListWidgetItem(self.stack_list)
        self.stack_items[stack].setText(stack)
        self.stack_list.addItem(self.stack_items[stack])
        # if not self.model.get_stack(stack).immutable:
        self.destination_combo.addItem(stack)
          
    for stack in (old_stacks - new_stacks):
      self.stack_list.takeItem(self.stack_list.row(self.stack_items[stack]))

    self.stacks = new_stacks


  def update_samples(self):
    """Update sample list."""
    
    old_samples = self.samples
    new_samples = set()

    for stack in self.selected_stacks:
      samples = self.filter(self.model.samples_in_stack(stack))

      for sample in samples:
        new_samples.add(sample)
        if sample not in old_samples:
          self.sample_items[sample] = PyDendroSampleListItem(sample, self.model)
          self.sample_list.addItem(self.sample_items[sample])

    for sample in (old_samples - new_samples):
      self.sample_list.takeItem(self.sample_list.row(self.sample_items[sample]))

    self.samples = new_samples

    for name in self.sample_items:
      self.sample_items[name].update()


  ##
  ## actions
  ## 

  def on_stack_selection(self):
    self.update_samples()
    self.ui.on_draw()


  def on_sample_selection(self):
    self.ui.on_draw()


  def on_change_color(self):
    """Change color dialog."""
    
    color = QColorDialog.getColor(self.color, self, "Stack color", QColorDialog.ShowAlphaChannel)

    if QColor.isValid(color):
      self.set_color(color)
      self.ui.on_draw()

  def filter(self, samples):
    
    if self.hold:
      return list(set(samples) & self._filter)

    return samples


  def on_hold(self):
    """Hold/release action."""

    if self.hold:
      self.hold = False
      self.hold_button.setText('Hold')
      self._filter = set()
    else:
      self.hold = True
      self.hold_button.setText('Release')
      self._filter = set(self.selected_samples)

    self.update_samples()
    self.ui.on_draw()


  def on_commit(self):
    """Move/copy to action."""

    action = str(self.action_combo.currentText())

    if action == "Move to":
      action = self.model.move_sample
    elif action == "Copy to":
      action = self.model.copy_sample
    # elif action == "Delete":
    #   action = self.model.delete_sample
    else:
      return

    destination = str(self.destination_combo.currentText())
    for stack in self.selected_stacks:
      for sample in self.selected_samples:
        action(stack, sample, destination)

    self.ui.update_stacks()
      

  ##
  ## main frame
  ##

  def create_stack_view(self):
    """Create the stack view."""

    self.setWindowTitle("Stack view")
    splitter = QSplitter(Qt.Vertical)

    #### stacks group
    
    group = QGroupBox("Stacks")
    vbox  = QVBoxLayout()

    # stack list
    # self.stack_list = QTreeWidget(rootIsDecorated=False,
    #                               allColumnsShowFocus=True,
    #                               uniformRowHeights=True,
    #                               sortingEnabled=True,
    #                               )
    self.stack_list = QListWidget()
    self.stack_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    # self.stack_list.setColumnCount(1)
    # self.stack_list.setHeaderLabels(['Stack'])
    self.connect(self.stack_list, SIGNAL('itemSelectionChanged()'), self.on_stack_selection)

    vbox.addWidget(self.stack_list)

    # color button
    hbox = QHBoxLayout()

    change_color = QPushButton("Color")
    self.connect(change_color, SIGNAL("clicked()"), self.on_change_color)
    hbox.addWidget(change_color)

    # color label
    self.current_color = QLabel("")
    self.current_color.setAutoFillBackground(True)
    self.set_color(QColor.fromRgbF(0.0, 0.0, 1.0, 1.0))

    hbox.addWidget(self.current_color)

    vbox.addLayout(hbox)

    group.setLayout(vbox)
    splitter.addWidget(group)


    #### samples group

    group = QGroupBox("Samples")
    vbox  = QVBoxLayout()

    # filter button
    self.hold_button = QPushButton("Hold")
    vbox.addWidget(self.hold_button)
    self.connect(self.hold_button, SIGNAL("clicked()"), self.on_hold)

    # sample list
    self.sample_list = PyDendroSampleList()    
    self.sample_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    self.sample_list.setSortingEnabled(True)
    self.connect(self.sample_list, SIGNAL('itemSelectionChanged()'), self.on_sample_selection)

    vbox.addWidget(self.sample_list)

    # "move to"/"copy to" area
    hbox = QHBoxLayout()

    self.action_combo = QComboBox()
    self.action_combo.addItems(["Move to", "Copy to"]) #, "Delete"])
    hbox.addWidget(self.action_combo)

    self.destination_combo = QComboBox()
    self.destination_combo.addItem('TRASH')
    hbox.addWidget(self.destination_combo)

    commit_button = QPushButton("Commit")
    hbox.addWidget(commit_button)
    self.connect(commit_button, SIGNAL("clicked()"), self.on_commit)

    vbox.addLayout(hbox)
    
    group.setLayout(vbox)
    splitter.addWidget(group)

    #### done

    self.setWidget(splitter)
