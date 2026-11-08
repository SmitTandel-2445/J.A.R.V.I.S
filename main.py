from core.app import JarvisApp
from utils.logger import logger


def main():
    app = JarvisApp()
    app.initialize()

    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Application stopped by user (Ctrl+C).")
        app.shutdown()


if __name__ == "__main__":
    main()
