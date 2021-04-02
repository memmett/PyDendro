#
# Simple GUI to record measurements from VRO
#

import collections
import datetime
import random
import serial
import serial.threaded
import sys
import time
import threading

import pandas as pd

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize, Qt, QPersistentModelIndex
from PyQt5.QtGui import QStandardItemModel, QIcon

from pathlib import Path as path

top = path(__file__).resolve().parent

sys.path.append(str(top))

import pydendro.csv
import pydendro.rwl

class NewCoreDialog(QDialog):

    def __init__(self, *args, **kwargs):
        super(NewCoreDialog, self).__init__(*args, **kwargs)

        self.setWindowTitle("New core")
        self.core = QLineEdit()
        self.lyog = QLineEdit()

        now = datetime.datetime.now()
        self.lyog.setText(str(now.year))

        vbox = QVBoxLayout()

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Core name:"))
        hbox.addWidget(self.core)
        vbox.addLayout(hbox)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Last year of growth:"))
        hbox.addWidget(self.lyog)
        vbox.addLayout(hbox)

        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        vbox.addWidget(bbox)

        self.setLayout(vbox)

Measurement = collections.namedtuple('Measurement', ['core', 'year', 'width', 'measurement'])

class Measurements:

    def __init__(self):
        self.measurements = collections.defaultdict(list)

    def append(self, core, year, width, value):
        self.measurements[core].append(Measurement(core, year, width, value))

    def remove_core(self, core):
        if core not in self.measurements:
            return
        try:
            del self.measurements[core]
        except:
            pass

    def remove_last_measurement(self, core):
        if core not in self.measurements:
            return
        try:
            del self.measurements[core][-1]
        except:
            pass

    def write(self, fname):
        data = sum(self.measurements.values(), [])
        if data:
            df = pd.DataFrame([x._asdict() for x in data])
            df.to_csv(fname, index=False)

            samples = pydendro.csv.read(fname)
            pydendro.rwl.write(path(fname).with_suffix('.rwl'), samples)

    def load(self, fname):
        data = pd.read_csv(fname, dtype=str)
        for row in data.itertuples():
            self.measurements[row.core].append(Measurement(row.core, row.year, row.width, row.measurement))

class VROMainWindow(QMainWindow):

    CORE, YEAR, WIDTH, MEASUREMENT = range(4)
    model = None

    def __init__(self):
        QMainWindow.__init__(self)

        self.setWindowTitle("VRO")
        self.setWindowIcon(QIcon(str(top / "leaf-fill.svg")))
        self.setCentralWidget(QWidget())

        self.measurements = Measurements()

        self.model = QStandardItemModel(0, 4, self)
        self.model.setHeaderData(self.CORE, Qt.Horizontal, "Core")
        self.model.setHeaderData(self.YEAR, Qt.Horizontal, "Year")
        self.model.setHeaderData(self.WIDTH, Qt.Horizontal, "Width")
        self.model.setHeaderData(self.MEASUREMENT, Qt.Horizontal, "Measurement")

        self.file = QLabel()
        self.core = QLabel()
        self.year = QLineEdit()
        self.measurements_table = QTableView()
        self.measurements_table.setAlternatingRowColors(True)
        self.measurements_table.setModel(self.model)

        self.load_button = QPushButton('Load')
        self.load_button.clicked.connect(self.load_file)

        self.new_button = QPushButton('New')
        self.new_button.clicked.connect(self.new_file)

        self.delete_button = QPushButton('Delete last measurement')
        self.delete_button.clicked.connect(self.delete_last_measurement)

        self.new_core_button = QPushButton('New core')
        self.new_core_button.clicked.connect(self.new_core)

        self.delete_core_button = QPushButton('Delete core')
        self.delete_core_button.clicked.connect(self.delete_core)

        self.core_list_widget = QListWidget()
        self.core_list_widget.itemClicked.connect(self.core_clicked)

        file_group = QGroupBox("File")
        file_group_box = QHBoxLayout()
        file_group_box.addWidget(self.load_button)
        file_group_box.addWidget(self.new_button)
        file_group_box.addWidget(QLabel("File:"))
        file_group_box.addWidget(self.file)
        file_group.setLayout(file_group_box)

        core_info_box = QHBoxLayout()
        core_info_box.addWidget(QLabel("Core:"))
        core_info_box.addWidget(self.core)
        core_info_box.addWidget(QLabel("Year:"))
        core_info_box.addWidget(self.year)

        measurement_group = QGroupBox("Measurements")
        measurement_group_box = QVBoxLayout()
        measurement_group_box.addLayout(core_info_box)
        measurement_group_box.addWidget(self.measurements_table)
        measurement_group_box.addWidget(self.delete_button)
        measurement_group.setLayout(measurement_group_box)

        core_group = QGroupBox("Cores")
        core_group_box = QVBoxLayout()
        core_group_box.addWidget(self.core_list_widget)
        core_group_box.addWidget(self.new_core_button)
        core_group_box.addWidget(self.delete_core_button)
        core_group.setLayout(core_group_box)

        vbox = QVBoxLayout()
        vbox.addWidget(file_group)
        hbox = QHBoxLayout()
        hbox.addWidget(core_group)
        hbox.addWidget(measurement_group)
        vbox.addLayout(hbox)

        self.centralWidget().setLayout(vbox)


    def add_measurement(self, value, units):
        if self.model is None:
            return
        if self.measurements is None:
            return
        if len(self.file.text()) == 0:
            return
        if len(self.core.text()) == 0:
            return

        if self.model.rowCount() <= 0:
            current = "0.0"
        else:
            last_core = self.model.item(0, self.CORE).text()
            current_core = self.core.text()
            if last_core != current_core:
                current = "0.0"
            else:
                current = self.model.item(0, self.MEASUREMENT).text()
        digits  = len(value.split('.')[-1])
        fmt     = "{:.0" + str(digits) + "f}"
        width   = fmt.format(float(value) - float(current))

        self.measurements.append(self.core.text(), self.year.text(), width, value)
        self.write()
        self.update_measurements()


    def write(self):
        if len(self.file.text()) == 0:
            return
        self.measurements.write(self.file.text())


    def update_measurements(self):
        self.model.removeRows(0, self.model.rowCount())

        if len(self.core.text()) > 0:
            measurements = self.measurements.measurements[self.core.text()]
            for r, row in enumerate(measurements):
                self.model.insertRow(0)
                self.model.setData(self.model.index(0, self.CORE), row.core)
                self.model.setData(self.model.index(0, self.YEAR), row.year)
                self.model.setData(self.model.index(0, self.WIDTH), row.width)
                self.model.setData(self.model.index(0, self.MEASUREMENT), row.measurement)
            if measurements:
                last = measurements[-1]
                self.year.setText(str(int(last.year)-1))

        cores = sorted(self.measurements.measurements.keys())
        selected = self.core_list_widget.selectedItems()
        if selected:
            selected = self.core_list_widget.selectedItems()[0].text()
        self.core_list_widget.clear()
        self.core_list_widget.addItems(cores)
        if selected:
            try:
                idx = cores.index(selected)
                self.core_list_widget.setCurrentRow(idx)
            except:
                pass


    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Load CSV file')
        if not fname:
            return

        self.file.setText(fname)
        self.core.setText('')
        self.measurements.load(fname)
        self.update_measurements()


    def new_file(self):
        fname, _ = QFileDialog.getSaveFileName(self, 'Create CSV file')
        if not fname:
            return

        self.file.setText(fname)
        self.core.setText('')
        self.measurements = Measurements()
        self.update_measurements()


    def delete_last_measurement(self):
        self.measurements.remove_last_measurement(self.core.text())
        self.write()
        self.update_measurements()


    def new_core(self):
        dlg = NewCoreDialog(self)
        if dlg.exec_():
            core = dlg.core.text()
            self.core.setText(core)
            self.year.setText(dlg.lyog.text())
            self.measurements.measurements[core] = []
            # core = QListWidgetItem(self.core.text())
            # self.core_list_widget.addItem(core)
            self.update_measurements()


    def delete_core(self):
        c = self.core_list_widget.selectedItems()
        if c:
            c = c[0].text()
            self.core.setText("")
            self.measurements.remove_core(c)
            self.write()
            self.update_measurements()


    def core_clicked(self):
        c = self.core_list_widget.selectedItems()[0].text()
        self.core.setText(c)
        self.update_measurements()


class VRO(serial.threaded.LineReader):
    model = None
    def set_model(self, model):
        self.model = model
    def handle_line(self, data):
        _, value, units = data.strip().split()
        if self.model is not None:
            self.model.add_measurement(value, units)


class FakeVRO(threading.Thread):
    model = None
    def set_model(self, model):
        self.model = model
    def run(self):
        v = 0.0
        while True:
            v += random.randrange(1, 10000) / 10000
            self.model.add_measurement(f'{v:.4f}', 'mm')
            time.sleep(random.randrange(2, 10))


def find_vro():
    usbs = [ f'/dev/ttyUSB{i}' for i in range(10) ] + [ f'COM{i}' for i in range(10) ]
    for usb in usbs:
        try:
            with serial.Serial(usb, timeout=2) as s:
                s.write(b'V')
                v = s.read(1).decode('ascii')
                if v in [ 'S', 'D', 'P' ]:
                    return usb
        except Exception as e:
            print(e)
    print('VRO not found!')


if __name__ == "__main__":
    print("Ports...")
    import serial.tools.list_ports as port_list
    ports = list(port_list.comports())
    for p in ports:
        print (p)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("VRO")
    main = VROMainWindow()
    vro_tty = find_vro()
    if vro_tty is not None:
        reader = serial.threaded.ReaderThread(serial.Serial(vro_tty), VRO)
        reader.start()
        reader.protocol.set_model(main)
        #with serial.threaded.ReaderThread(serial.Serial(), VRO) as 
        
    else:
        msg = QMessageBox.warning(main, "PyVRO - VRO not found", "Unable to find the VRO.  Please plug it in and restart this application.")
        sys.exit(1)
        #reader = FakeVRO()
        #reader.set_model(main)
        #reader.start()
    main.show()
    sys.exit(app.exec_())
