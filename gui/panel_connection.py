"""
Panel połączeń urządzeń — adresy, status, reconnect.
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from core.config import DeviceAddresses


class StatusIndicator(QWidget):
    """Kółko statusu: szare=brak, zielone=OK, czerwone=błąd."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self._color = QColor('#888888')

    def set_ok(self):
        self._color = QColor('#27ae60')
        self.update()

    def set_error(self):
        self._color = QColor('#e74c3c')
        self.update()

    def set_idle(self):
        self._color = QColor('#888888')
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QBrush
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(self._color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(1, 1, 12, 12)
        p.end()


class ConnectionPanel(QGroupBox):
    """Panel z adresami urządzeń i przyciskami połączenia."""

    connect_requested = Signal()
    disconnect_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Połączenia", parent)

        layout = QGridLayout()
        layout.setSpacing(6)

        self._fields = {}
        self._indicators = {}

        devices = [
            ('moku_ip', 'Moku:Pro IP'),
            ('rigol_visa', 'Rigol DP831'),
            ('siglent_visa', 'Siglent SDM'),
            ('arduino_port', 'Arduino'),
        ]

        for row, (key, label) in enumerate(devices):
            lbl = QLabel(label)
            lbl.setFixedWidth(100)

            edit = QLineEdit()
            edit.setMinimumWidth(250)
            self._fields[key] = edit

            ind = StatusIndicator()
            self._indicators[key] = ind

            layout.addWidget(lbl, row, 0)
            layout.addWidget(edit, row, 1)
            layout.addWidget(ind, row, 2)

        btn_row = QHBoxLayout()
        self.btn_connect = QPushButton("Połącz wszystko")
        self.btn_connect.clicked.connect(self.connect_requested.emit)
        self.btn_disconnect = QPushButton("Rozłącz")
        self.btn_disconnect.clicked.connect(self.disconnect_requested.emit)
        self.btn_disconnect.setEnabled(False)

        btn_row.addWidget(self.btn_connect)
        btn_row.addWidget(self.btn_disconnect)
        btn_row.addStretch()

        main = QVBoxLayout()
        main.addLayout(layout)
        main.addLayout(btn_row)
        self.setLayout(main)

    def get_addresses(self) -> DeviceAddresses:
        return DeviceAddresses(
            moku_ip=self._fields['moku_ip'].text(),
            rigol_visa=self._fields['rigol_visa'].text(),
            siglent_visa=self._fields['siglent_visa'].text(),
            arduino_port=self._fields['arduino_port'].text(),
        )

    def set_addresses(self, addr: DeviceAddresses):
        self._fields['moku_ip'].setText(addr.moku_ip)
        self._fields['rigol_visa'].setText(addr.rigol_visa)
        self._fields['siglent_visa'].setText(addr.siglent_visa)
        self._fields['arduino_port'].setText(addr.arduino_port)

    def set_device_status(self, key: str, ok: bool):
        ind = self._indicators.get(key)
        if ind:
            ind.set_ok() if ok else ind.set_error()

    def set_all_idle(self):
        for ind in self._indicators.values():
            ind.set_idle()

    def set_connected_state(self, connected: bool):
        self.btn_connect.setEnabled(not connected)
        self.btn_disconnect.setEnabled(connected)
        for edit in self._fields.values():
            edit.setReadOnly(connected)
