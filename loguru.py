import logging


class _SimpleLogger:
    def __init__(self):
        self._logger = logging.getLogger("mecam")
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def _emit(self, level, message, *args, **kwargs):
        try:
            if args:
                message = message.format(*args)
        except Exception:
            pass
        self._logger.log(level, str(message))

    def debug(self, message, *args, **kwargs):
        self._emit(logging.DEBUG, message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self._emit(logging.INFO, message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self._emit(logging.WARNING, message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self._emit(logging.ERROR, message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self._emit(logging.CRITICAL, message, *args, **kwargs)

    def success(self, message, *args, **kwargs):
        self._emit(logging.INFO, message, *args, **kwargs)

    def trace(self, message, *args, **kwargs):
        self._emit(logging.DEBUG, message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        self._logger.exception(str(message))

    def add(self, *args, **kwargs):
        return 0

    def remove(self, *args, **kwargs):
        return None

    def bind(self, **kwargs):
        return self

    def opt(self, *args, **kwargs):
        return self


logger = _SimpleLogger()
