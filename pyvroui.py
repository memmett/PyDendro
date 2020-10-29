#
# Simple GUI to record measurements from VRO
#

import serial
import serial.threaded
import sys
import time

import pandas as pd

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize, Qt, QPersistentModelIndex
from PyQt5.QtGui import QStandardItemModel, QIcon

from pathlib import Path as path

top = path(__file__).resolve().parent

class HelloWindow(QMainWindow):

    CORE, YEAR, WIDTH, MEASUREMENT = range(4)
    model = None

    def __init__(self):
        QMainWindow.__init__(self)

        self.setWindowTitle("VRO")
        self.setWindowIcon(QIcon(str(top / "leaf-fill.svg")))
        self.setCentralWidget(QWidget())

        self.fileName = QLabel()
        self.coreName = QLineEdit()
        self.year = QLineEdit()
        self.measurements = QTableView()
        self.measurements.setAlternatingRowColors(True)

        self.load_button = QPushButton('Load')
        self.load_button.clicked.connect(self.load_file)

        self.new_button = QPushButton('New')
        self.new_button.clicked.connect(self.new_file)

        self.delete_button = QPushButton('Delete rows')
        self.delete_button.clicked.connect(self.delete_rows)

        fbox = QHBoxLayout()
        fbox.addWidget(self.load_button)
        fbox.addWidget(self.new_button)
        fbox.addWidget(QLabel("File:"))
        fbox.addWidget(self.fileName)

        cbox = QHBoxLayout()
        cbox.addWidget(QLabel("Core:"))
        cbox.addWidget(self.coreName)
        cbox.addWidget(QLabel("Year:"))
        cbox.addWidget(self.year)

        bbox = QHBoxLayout()
        bbox.addWidget(self.delete_button)

        dbox = QVBoxLayout()
        dbox.addLayout(cbox)
        dbox.addWidget(self.measurements)
        dbox.addLayout(bbox)

        gbox = QGroupBox("Measurements")
        gbox.setLayout(dbox)

        self.model = self.createMeasurementsModel()
        self.measurements.setModel(self.model)

        vbox = QVBoxLayout()
        vbox.addLayout(fbox)
        vbox.addWidget(gbox)

        self.centralWidget().setLayout(vbox)


    def createMeasurementsModel(self):
        model = QStandardItemModel(0, 4, self)
        model.setHeaderData(self.CORE, Qt.Horizontal, "Core")
        model.setHeaderData(self.YEAR, Qt.Horizontal, "Year")
        model.setHeaderData(self.WIDTH, Qt.Horizontal, "Width")
        model.setHeaderData(self.MEASUREMENT, Qt.Horizontal, "Measurement")
        model.itemChanged.connect(self.on_item_changed)
        return model

    def add_measurement(self, value, units):
        if self.model is None:
            return

        if self.model.rowCount() <= 0:
            current = "0.0"
        else:
            last_core = self.model.item(0, self.CORE).text()
            current_core = self.coreName.text()
            if last_core != current_core:
                current = "0.0"
            else:
                current = self.model.item(0, self.MEASUREMENT).text()
        digits  = len(value.split('.')[-1])
        fmt     = "{:.0" + str(digits) + "f}"
        width   = fmt.format(float(value) - float(current))
        self.model.insertRow(0)
        self.model.setData(self.model.index(0, self.CORE), self.coreName.text())
        self.model.setData(self.model.index(0, self.YEAR), self.year.text())
        self.model.setData(self.model.index(0, self.WIDTH), width)
        self.model.setData(self.model.index(0, self.MEASUREMENT), value)
        self.year.setText(str(int(self.year.text()) - 1))
        self.write()

    def on_item_changed(self, *args):
        self.write()

    def write(self):
        if self.model is None:
            return

        if len(self.fileName.text()) == 0:
            return

        data = []
        for r in range(self.model.rowCount()):
            data.append({ 'core': self.model.item(r, self.CORE).text(),
                          'year': self.model.item(r, self.YEAR).text(),
                          'width': self.model.item(r, self.WIDTH).text(),
                          'measurement': self.model.item(r, self.MEASUREMENT).text() })

        if data:
            df = pd.DataFrame(data)
            df.to_csv(self.fileName.text(), index=False)

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Load CSV file')
        if not fname:
            return

        self.fileName.setText(fname)
        self.model.itemChanged.disconnect()
        self.model.removeRows(0, self.model.rowCount())
        df = pd.read_csv(self.fileName.text(), dtype=str)
        for r, row in enumerate(df.itertuples()):
            self.model.insertRow(r)
            self.model.setData(self.model.index(r, self.CORE), row.core)
            self.model.setData(self.model.index(r, self.YEAR), row.year)
            self.model.setData(self.model.index(r, self.WIDTH), row.width)
            self.model.setData(self.model.index(r, self.MEASUREMENT), row.measurement)
        self.model.itemChanged.connect(self.on_item_changed)

    def new_file(self):
        fname, _ = QFileDialog.getSaveFileName(self, 'Create CSV file')
        if not fname:
            return

        self.fileName.setText(fname)
        self.model.itemChanged.disconnect()
        self.model.removeRows(0, self.model.rowCount())
        self.model.itemChanged.connect(self.on_item_changed)

    def delete_rows(self):
        self.model.itemChanged.disconnect()
        plist = [ QPersistentModelIndex(i) for i in
                  self.measurements.selectionModel().selectedRows() ]
        for i in plist:
            self.model.removeRow(i.row())
        self.write()
        self.model.itemChanged.connect(self.on_item_changed)



class VRO(serial.threaded.LineReader):
    model = None
    def set_model(self, model):
        self.model = model
    def handle_line(self, data):
        _, value, units = data.strip().split()
        if self.model is not None:
            self.model.add_measurement(value, units)


def find_vro():
    usbs = [ f'/dev/ttyUSB{i}' for i in range(10) ]
    for usb in usbs:
        try:
            with serial.Serial(usb, timeout=2) as s:
                s.write(b'V')
                v = s.read(1).decode('ascii')
                if v in [ 'S', 'D', 'P' ]:
                    return usb
        except Exception as e:
            pass
    print('VRO not found!')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("VRO")
    mainWin = HelloWindow()
    vro_tty = find_vro()
    if vro_tty is not None:
        reader = serial.threaded.ReaderThread(serial.Serial(), VRO)
        reader.start()
        reader.protocol.set_model(mainWin)
    mainWin.show()
    sys.exit(app.exec_())
