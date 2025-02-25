from batch_based.batch_processor import initializer
from logger import configure_logger

def main():
    configure_logger()
    initializer()

if __name__ == "__main__":
    main()