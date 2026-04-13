"""
Worker thread — uruchamia silnik pomiarowy w osobnym wątku.
Komunikacja z GUI przez Qt signals (thread-safe).
"""

from PySide6.QtCore import QThread, Signal, QObject

from core.config import StationConfig
from core.callbacks import MeasurementPoint, MeasurementCallback
from core.engine import GMIMeasurementEngine


class WorkerSignals(QObject):
    """Sygnały emitowane z wątku pomiarowego do GUI."""
    point = Signal(object)            # MeasurementPoint
    status = Signal(str)
    progress = Signal(int, int)       # current, total
    error = Signal(str)
    finished = Signal(str)            # output_file path
    prompt = Signal(str, object)      # message, callback Event


class QtCallback(MeasurementCallback):
    """Implementacja callbacków — emituje Qt signals."""

    def __init__(self, signals: WorkerSignals):
        self._signals = signals
        self._prompt_event = None

    def on_point(self, point: MeasurementPoint):
        self._signals.point.emit(point)

    def on_status(self, message: str):
        self._signals.status.emit(message)

    def on_progress(self, current: int, total: int):
        self._signals.progress.emit(current, total)

    def on_error(self, message: str):
        self._signals.error.emit(message)

    def on_finished(self, output_file: str):
        self._signals.finished.emit(output_file)

    def prompt_user(self, message: str):
        """Blokuje wątek pomiarowy dopóki GUI nie potwierdzi."""
        import threading
        event = threading.Event()
        self._signals.prompt.emit(message, event)
        event.wait()


class MeasurementWorker(QThread):
    """Wątek pomiarowy — uruchamia engine.run_measurement()."""

    signals = WorkerSignals()

    def __init__(self, engine: GMIMeasurementEngine, output_path: str):
        super().__init__()
        self.engine = engine
        self.output_path = output_path
        self.callback = QtCallback(self.signals)
        self.engine.set_callback(self.callback)

    def run(self):
        self.engine.run_measurement(self.output_path)

    def stop(self):
        self.engine.stop()


class CalibrationWorker(QThread):
    """Wątek kalibracji OSL."""

    signals = WorkerSignals()

    def __init__(self, engine: GMIMeasurementEngine):
        super().__init__()
        self.engine = engine
        self.callback = QtCallback(self.signals)
        self.engine.set_callback(self.callback)

    def run(self):
        try:
            self.engine.run_calibration()
            self.signals.status.emit("Kalibracja OSL zakończona")
        except Exception as e:
            self.signals.error.emit(str(e))
