import logging
from datetime import datetime


# ==========================================
# BLOQUE 1: LOGGING Y EXCEPCIONES PERSONALIZADAS
# ==========================================

def configurar_logger(nombre_archivo: str = "software_fj.log") -> logging.Logger:
    """Configura el registrador de eventos y errores en archivo y consola."""
    logger = logging.getLogger("SoftwareFJ")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formato = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        archivo_handler = logging.FileHandler(nombre_archivo, encoding="utf-8")
        archivo_handler.setFormatter(formato)

        consola_handler = logging.StreamHandler()
        consola_handler.setFormatter(formato)

        logger.addHandler(archivo_handler)
        logger.addHandler(consola_handler)

    return logger


class ErrorSoftwareFJ(Exception):
    """Excepción base del sistema Software FJ."""

    def __init__(self, mensaje: str, codigo: str = "ERR_GENERAL"):
        super().__init__(mensaje)
        self.codigo = codigo
        self.timestamp = datetime.now().isoformat()


class ErrorValidacionDato(ErrorSoftwareFJ):
    """Excepción lanzada cuando un dato es inválido o falta un parámetro."""

    def __init__(self, mensaje: str, campo: str | None = None):
        super().__init__(mensaje, codigo="ERR_VALIDACION")
        self.campo = campo


class ErrorDisponibilidadServicio(ErrorSoftwareFJ):
    """Excepción lanzada cuando un servicio no está disponible o la reserva falla."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR_RESERVA")


class ErrorCalculoFinanciero(ErrorSoftwareFJ):
    """Excepción lanzada ante cálculos inconsistentes o erróneos."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje, codigo="ERR_CALCULO")


# --- Prueba rápida del Bloque 1 ---
if __name__ == "__main__":
    logger = configurar_logger()
    logger.info("Bloque 1 iniciado correctamente.")

    try:
        raise ErrorValidacionDato("Ejemplo de dato inválido", campo="correo")
    except ErrorSoftwareFJ as err:
        logger.error(f"[{err.codigo}] {err}")

