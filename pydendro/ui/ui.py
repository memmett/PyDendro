"""PyDendro GUI."""

# Copyright 2011 Andria Dawson and Matthew Emmett.  All rights reserved.

# 

import sys, os, os.path, string

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from pydendro.model.stack import Stack
from pydendro.ui.stack_view import PyDendroStackView #, PyDendroFrozenStackList
from pydendro.ui.dialogs import PyDendroSaveStacksDialog

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure


class PyDendroMainWindow(QMainWindow):


  def __init__(self, parent=None):
    QMainWindow.__init__(self, parent)
    self.setWindowTitle('PyDendro')

    self.hold = False
    self.stack_views = []
    # self.frozen_stack_list = None

    self.create_menu()
    self.create_main_frame()
    self.create_tool_bar()
    self.create_status_bar()


  @property
  def selected_stacks(self):
    stacks = []
    for stack_view in self.stack_views:
      stacks += stack_view.selected_stacks
    return stacks


  @property
  def selected_samples(self):
    samples = set()
    for stack_view in self.stack_views:
      samples |= set(stack_view.selected_samples)
    return list(samples)


  @property
  def non_frozen_selected_samples(self):
    samples = set()
    for stack_view in self.stack_views:
      samples |= set(stack_view.selected_samples)
    for stack_name in self.model.stacks:
      stack = self.model.get_stack(stack_name)
      if stack.frozen:
        samples -= set(self.model.samples_in_stack(stack_name))
    return list(samples)


  def update_stacks(self):
    for stack_view in self.stack_views:
      stack_view.update()

    # if self.frozen_stack_list:
    #   self.frozen_stack_list.update()


  ##
  ## actions
  ##

  def on_about(self):
    """About dialog."""
    
    msg = """PyDendro - Copyright 2011 Andria Dawson and Matthew Emmett.  All rights reserved."""
    QMessageBox.about(self, "About PyDendro", msg.strip())


  def on_import_rwl(self):
    """Import RWL dialog."""

    filename = str(QFileDialog.getOpenFileName(
      parent=self, caption="Import samples from RWL file"))

    if filename:
      stack = self.model.add_stack_from_rwl(filename)
      self.status_text.setText("Loaded %d samples from %s" % (len(stack.samples), filename))
      self.update_stacks()


  def on_save_stacks(self):
    """Save stacks dialog."""

    dialog = PyDendroSaveStacksDialog(self, self, self.model)
    dialog.exec_()


  def on_save_plot(self):
    """Save plot dialog."""

    path = str(QFileDialog.getSaveFileName(
      self, "Save file", "", "PNG (*.png)|*.png"))

    if path:
      self.canvas.print_figure(path, dpi=self.dpi)
      self.statusBar().showMessage("Plot saved to %s" % path, 2000)


  def on_new_stack(self):
    """New stack dialog."""    
    
    new_stack, ok = QInputDialog.getText(self, "New stack", "New stack name")

    if ok:
      stack = Stack(str(new_stack), False)
      self.model.add_stack(stack)
      self.update_stacks()


  def on_rename_stack(self):
    """Rename stack dialog."""    
    
    stack, new_name = PyDendroDialog.renameStack(self)


  def on_new_stack_view(self):
    """Create new stack view."""
    
    self.add_stack_view()
    self.update_stacks()


  def on_pick(self, event):
    """Pick a transect."""
    
    line = event.artist
    sample_name = line.get_label()

    self.hold = True

    for stack_view in self.stack_views:
      for item in stack_view.sample_list.findItems(sample_name, Qt.MatchExactly):
        # XXX: depending on keys currently pressed?        
        selected = not stack_view.sample_list.isItemSelected(item)
        stack_view.sample_list.setItemSelected(item, selected)

    self.hold = False
    self.on_draw()


  def on_move_left(self):
    """Move selected sample(s) to the left."""
    
    for sample in self.non_frozen_selected_samples:
      s = self.model.get_sample(sample)
      s.first_year -= 1

    self.on_draw()


  def on_move_right(self):
    """Move selected sample(s) to the right."""
    
    for sample in self.non_frozen_selected_samples:
      s = self.model.get_sample(sample)
      s.first_year += 1

    self.on_draw()


  def on_draw(self):
    """Redraw the plot."""

    if self.hold:
      return

    self.axes.clear()    

    # get list of selected stacks
    # XXX: don't plot the same sample more than once!

    if self.plot_stacks.isChecked():
      for stack_view in self.stack_views:
        selected_stacks  = stack_view.selected_stacks
        selected_samples = stack_view.selected_samples

        color = stack_view.color.getRgbF()

        for stack in selected_stacks:
          samples = self.model.samples_in_stack(stack)

          for sample in samples:
            if sample not in selected_samples:
              s = self.model.get_sample(sample)
              self.axes.plot(s.years, s.ring_widths, '-', color=color,
                             picker=5, label=sample)

          for sample in samples:
            if sample in selected_samples:
              s = self.model.get_sample(sample)
              self.axes.plot(s.years, s.ring_widths, '.-r',
                             linewidth=2, picker=10, label=sample)
    else:
      for stack_view in self.stack_views:
        selected_stacks  = stack_view.selected_stacks
        selected_samples = stack_view.selected_samples        

        color = stack_view.color.getRgbF()

        for stack in selected_stacks:
          samples = self.model.samples_in_stack(stack)

          for sample in samples:
            if sample in selected_samples:
              s = self.model.get_sample(sample)
              self.axes.plot(s.years, s.ring_widths, '-', color=color,
                             picker=5, label=sample)

      
    
    self.canvas.draw()


  def on_plot_stacks_toggled(self, checked):
    """Trigger redraw."""

    self.on_draw()


  ##
  ## main frame
  ##

  def add_stack_view(self):
    """Add a new stack view."""

    # # frozen stack list
    # if not self.frozen_stack_list:
    #   self.frozen_stack_list = PyDendroFrozenStackList(self, self.model)    
    #   self.addDockWidget(Qt.LeftDockWidgetArea, self.frozen_stack_list)

    dock = PyDendroStackView(self, self.model)    
    self.addDockWidget(Qt.LeftDockWidgetArea, dock)
    self.stack_views.append(dock)


  def create_main_frame(self):
    """Create main frame."""
    
    # plot window
    vbox = QVBoxLayout()

    hbox = QHBoxLayout()
    hbox.addWidget(QLabel("Plot:"))

    self.plot_stacks = QRadioButton("entire stack")
    self.plot_stacks.toggle()
    self.connect(self.plot_stacks, SIGNAL('toggled(bool)'), self.on_plot_stacks_toggled)

    self.plot_samples = QRadioButton("selected samples")

    hbox.addWidget(self.plot_stacks)
    hbox.addWidget(self.plot_samples)
    hbox.addStretch()
    vbox.addLayout(hbox)
    
    plot_frame = QWidget()
    fig = Figure((5.0, 4.0), dpi=100)
    self.canvas = FigureCanvas(fig)
    self.canvas.setParent(plot_frame)
    self.axes = fig.add_subplot(111,axis_bgcolor=(1.0, 1.0, 1.0, 1.0))
    self.canvas.mpl_connect('pick_event', self.on_pick)
    vbox.addWidget(self.canvas)

    mpl_toolbar = NavigationToolbar(self.canvas, plot_frame)
    vbox.addWidget(mpl_toolbar)

    plot_frame.setLayout(vbox)
    self.setCentralWidget(plot_frame)


  def create_status_bar(self):
    """Create status bar."""
    
    self.status_text = QLabel("Welcome to PyDendro")
    self.statusBar().addWidget(self.status_text, 1)


  def create_tool_bar(self):
    """Create tool bar."""

    left_action = self.create_action(
      "Move left", shortcut="-", icon="pydendro/icons/left.png",
      slot=self.on_move_left, tip="Move selected sample(s) to the left")

    right_action = self.create_action(
      "Move right", shortcut="=", icon="pydendro/icons/right.png",
      slot=self.on_move_right, tip="Move selected sample(s) to the right")

    self.tool_bar = self.addToolBar("Main toolbar")
    self.tool_bar.addAction(left_action)
    self.tool_bar.addAction(right_action)


  def create_menu(self):
    """Create menus."""
    
    # file menu
    self.file_menu = self.menuBar().addMenu("&File")

    import_rwl_action = self.create_action(
      "&Import RWL...", shortcut="Ctrl+I",
      slot=self.on_import_rwl, tip="Import samples from an RWL file")

    save_stacks_action = self.create_action(
      "&Save stacks...", shortcut="Ctrl+S",
      slot=self.on_save_stacks, tip="Save stacks")

    save_plot_action = self.create_action(
      "Save plot...", 
      slot=self.on_save_plot, tip="Save current plot")
    
    quit_action = self.create_action(
      "&Quit", shortcut="Ctrl+Q",
      slot=self.close, tip="Close the application")
    
    self.add_actions(self.file_menu, 
      (import_rwl_action, save_stacks_action, save_plot_action, None, quit_action))

    # stacks menu
    self.stacks_menu = self.menuBar().addMenu("&Stacks")

    new_stack_window_action = self.create_action(
      "New stack &window", shortcut="Ctrl+W",
      slot=self.on_new_stack_view, tip="Create a new stack window")

    new_stack_action = self.create_action(
      "&New stack...", shortcut="Ctrl+N",
      slot=self.on_new_stack, tip="Create new stack")

    rename_stack_action = self.create_action(
      "&Rename stack...",
      slot=self.on_rename_stack, tip="Rename a stack")

    self.add_actions(self.stacks_menu,
                     (new_stack_window_action, new_stack_action, rename_stack_action))
    
    # help menu
    self.help_menu = self.menuBar().addMenu("&Help")

    about_action = self.create_action(
      "&About", shortcut='F1',
      slot=self.on_about, tip='About PyDendro')
    
    self.add_actions(self.help_menu, (about_action,))


  def add_actions(self, target, actions):
    """Add action helper."""
    
    for action in actions:
      if action is None:
        target.addSeparator()
      else:
        target.addAction(action)


  def create_action(self, text,
                    slot=None, shortcut=None, 
                    icon=None, tip=None, checkable=False, 
                    signal="triggered()"):
    """Create action helper."""
    
    action = QAction(text, self)
    if icon is not None:
      action.setIcon(QIcon(icon))
    if shortcut is not None:
      action.setShortcut(shortcut)
    if tip is not None:
      action.setToolTip(tip)
      action.setStatusTip(tip)
    if slot is not None:
      self.connect(action, SIGNAL(signal), slot)
    if checkable:
      action.setCheckable(True)
    return action



