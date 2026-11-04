import logging
import sys


def setup_logging():
    """
    Cấu hình hệ thống logging chuẩn cho toàn bộ service.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(__name__)
    logger.info('Logging đã được cấu hình thành công.')
