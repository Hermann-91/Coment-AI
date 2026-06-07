import logging

def setup_logger(name: str = "RoboMarketing", log_file: str = "robot_marketing.log") -> logging.Logger:
    """
    Configura e retorna um logger que grava as ações no console e em um arquivo de texto local.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Evita duplicação de saídas se o logger já tiver sido configurado anteriormente
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Log no Console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Log no Arquivo Local
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
