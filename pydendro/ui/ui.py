"""PyDendro GUI."""
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
import string
import sys

import ConfigParser as configparser

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from pydendro.stack import Stack
from pydendro.ui.stack_view import PyDendroStackView
from pydendro.ui.dialogs import *

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from pydendro.ui.cursor import Cursor
from matplotlib.figure import Figure


class PyDendroMainWindow(QMainWindow):

  def __init__(self, parent=None):
    QMainWindow.__init__(self, parent)
    self.setWindowTitle('PyDendro')

    self.hold = False
    self.stack_views = []

    try:
      path = os.environ['PYDENDRO']
    except:
      path = os.getcwd()

    self.config = configparser.ConfigParser()
    try:
      self.config.read(os.path.expanduser('~/.pydendrorc'))
      self.working_directory = self.config.get('ui', 'working_directory')
    except:
      try:
        self.config.add_section('ui')
      except:
        pass
      self.config.set('ui', 'working_directory', os.getcwd())

    self.working_directory = self.config.get('ui', 'working_directory')

    self.icon_path = os.path.sep.join([ path, 'pydendro', 'ui', 'icons' ]) + os.path.sep

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


  def update_stacks(self):
    for stack_view in self.stack_views:
      stack_view.update()


  def delete_stack_view(self, stack_view):
    self.stack_views.remove(stack_view)
    self.update_stacks()
    self.on_draw()


  ##
  ## actions
  ##

  def on_about(self):
    """About dialog."""
    
    msg = """PyDendro - Copyright 2011 Andria Dawson and Matthew Emmett.  All rights reserved."""
    QMessageBox.about(self, "About PyDendro", msg.strip())


  def on_set_directory(self):

    directory = str(QFileDialog.getExistingDirectory(
      parent=self, caption="Select working directory",
      directory=self.working_directory))

    if directory:
      self.working_directory = directory
      try:
        self.config.add_section('ui')
      except:
        pass

      self.config.set('ui', 'working_directory', directory)
      with open(os.path.expanduser('~/.pydendrorc'), 'wb') as configfile:
        self.config.write(configfile)


  def on_import_rwl(self):
    """Import RWL dialog."""

    filenames = QFileDialog.getOpenFileNames(
      self, caption="Import samples from RWL file(s)",
      directory=self.working_directory)

    for filename in filenames:
      filename = str(filename)
      stack = self.model.add_stack_from_rwl(filename)
      self.status_text.setText("Loaded %d samples from %s" % (len(stack.samples), filename))

    if filenames:
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
      try:
        stack = Stack(str(new_stack), False)
        self.model.add_stack(stack)
        self.update_stacks()
      except:
        pass


  def on_delete_stacks(self):
    """Delete stacks dialog."""    
    
    dialog = PyDendroDeleteStacksDialog(self, self, self.model)
    dialog.exec_()


  def on_rename_stack(self):
    """Rename stack dialog."""    
    
    dialog = PyDendroRenameStackDialog(self, self, self.model)
    dialog.exec_()


  def on_new_stack_view(self):
    """Create new stack view."""
    
    self.add_stack_view()
    self.update_stacks()


  def on_normalization(self):

    dialog = PyDendroNormalizationDialog(self, self, self.model)
    dialog.exec_()


  def on_pick(self, event):
    """Pick a transect."""

    self.hold = True
    
    line = event.artist
    sample_name = line.get_label()

    for stack_view in self.stack_views:
      for item in stack_view.sample_list.findItems(sample_name, Qt.MatchExactly):
        selected = not stack_view.sample_list.isItemSelected(item)
        stack_view.sample_list.setItemSelected(item, selected)

    self.hold = False
    self.on_draw()


  def on_move_left(self):
    """Move selected sample(s) to the left."""
    
    for sample in self.selected_samples:
      s = self.model.get_sample(sample)
      s.first_year -= 1

    self.on_draw()

    for stack_view in self.stack_views:
      stack_view.update_samples()



  def on_move_right(self):
    """Move selected sample(s) to the right."""
    
    for sample in self.selected_samples:
      s = self.model.get_sample(sample)
      s.first_year += 1

    self.on_draw()

    for stack_view in self.stack_views:
      stack_view.update_samples()


  def on_draw(self):
    """Redraw the plot."""

    if self.hold:
      return

    self.axes.clear()

    ymin = 9999
    ymax = 0

    # XXX: don't plot the same sample more than once!

    for stack_view in self.stack_views:
      selected_stacks  = stack_view.selected_stacks
      selected_samples = stack_view.selected_samples

      color = stack_view.color.getRgbF()

      for stack in selected_stacks:
        samples = stack_view.filter(self.model.samples_in_stack(stack))

        for sample in samples:
          if sample not in selected_samples:
            s = self.model.get_sample(sample)
            self.axes.plot(s.years, s.ring_widths, '-', color=color,
                           picker=5, label=sample)

            if max(s.years) > ymax:
              ymax = max(s.years)

            if min(s.years) < ymin:
              ymin = min(s.years)

        for sample in samples:
          if sample in selected_samples:
            s = self.model.get_sample(sample)
            self.axes.plot(s.years, s.ring_widths, '.-r',
                           linewidth=2, picker=10, label=sample)

            if max(s.years) > ymax:
              ymax = max(s.years)

            if min(s.years) < ymin:
              ymin = min(s.years)


    ymin = (ymin/10)*10
    ymax = (ymax/10+1)*10

    try:
      xlim = self.axes.get_xlim()
      self.cursor.x = range(int(xlim[0]), int(xlim[1])+1)
    except:
      pass

    # self.axes.set_xlim([ymin, ymax])
    self.axes.xaxis.grid(color='gray')#, linestyle='dashed')
    self.axes.yaxis.grid(color='gray')#, linestyle='dashed')    
    self.canvas.draw()


  def on_plot_stacks_toggled(self, checked):
    """Trigger redraw."""

    self.moveable_stacks = set()
    self.on_draw()


  ##
  ## main frame
  ##

  def add_stack_view(self):
    """Add a new stack view."""

    dock = PyDendroStackView(self, self.model)    
    self.addDockWidget(Qt.LeftDockWidgetArea, dock)
    self.stack_views.append(dock)
    #dock.index = len(self.stack_views)-1


  def create_main_frame(self):
    """Create main frame."""
    
    # plot window
    vbox = QVBoxLayout()

    plot_frame = QWidget()
    fig = Figure((5.0, 4.0), dpi=100)
    self.canvas = FigureCanvas(fig)
    self.canvas.setParent(plot_frame)
    self.axes = fig.add_subplot(111,axis_bgcolor=(1.0, 1.0, 1.0, 1.0))
    self.cursor = Cursor(self.axes, color='grey', useblit=True)
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
      "Move left", shortcut="-", icon=self.icon_path+"left.png",
      slot=self.on_move_left, tip="Move selected sample(s) to the left")

    right_action = self.create_action(
      "Move right", shortcut="=", icon=self.icon_path+"right.png",
      slot=self.on_move_right, tip="Move selected sample(s) to the right")

    self.tool_bar = self.addToolBar("Main toolbar")
    self.tool_bar.addAction(left_action)
    self.tool_bar.addAction(right_action)


  def create_menu(self):
    """Create menus."""
    
    # file menu
    self.file_menu = self.menuBar().addMenu("&File")

    set_directory_action = self.create_action(
      "Set working &directory...", shortcut="Ctrl+D",
      slot=self.on_set_directory, tip="Set the working directory")

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
      (set_directory_action, import_rwl_action, save_stacks_action, save_plot_action, None, quit_action))

    # stacks menu
    self.stacks_menu = self.menuBar().addMenu("&Stacks")

    new_stack_window_action = self.create_action(
      "New stack &window", shortcut="Ctrl+W",
      slot=self.on_new_stack_view, tip="Create a new stack window")

    new_stack_action = self.create_action(
      "&New stack...", shortcut="Ctrl+N",
      slot=self.on_new_stack, tip="Create new stack")

    delete_stacks_action = self.create_action(
      "Delete stacks...",
      slot=self.on_delete_stacks, tip="Delete stacks")

    rename_stack_action = self.create_action(
      "&Rename stack...",
      slot=self.on_rename_stack, tip="Rename a stack")

    self.add_actions(self.stacks_menu,
                     (new_stack_window_action, new_stack_action, delete_stacks_action, rename_stack_action))


    # tools menu
    self.tools_menu = self.menuBar().addMenu("&Tools")

    normalization_action = self.create_action(
      "Normali&zation...",
      slot=self.on_normalization, tip="Configure normalization options")

    self.add_actions(self.tools_menu,
                     (normalization_action,))
    
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



