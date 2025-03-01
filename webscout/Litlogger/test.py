from core.logger import Logger
from core.level import LogLevel
from styles.formats import LogFormat

def main():
    # Create logger instance (no need to specify handler - it uses default)
    logger = Logger(
        name="TestApp",
        level=LogLevel.DEBUG,
        format=LogFormat.MODERN_EMOJI,
        enable_colors=True
    )

    print("Starting logger tests...\n")

    # Test all log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Test context
    logger.set_context(user="test_user", env="development")
    logger.info("Action with context", action="test")

    # Test exception handling
    try:
        e = Exception("Test error")  # Simulate an exception
        raise ValueError("Test error") from e
    except Exception as e:
        logger.error(f"Caught an error: {str(e)}", exc_info=True)

    print("\nLogger tests completed!")

if __name__ == "__main__":
    main()
