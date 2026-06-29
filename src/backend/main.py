"""
RITUAL - Hermetic LLM Context Management Portal
Main entry point for the application

Supports both full (with frontend) and headless (API-only) modes.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from app.server import create_app


def setup_logging(debug: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """Main entry point for RITUAL."""
    parser = argparse.ArgumentParser(
        description="RITUAL - Hermetic LLM Context Management Portal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with full UI
  ritual --port 8000
  
  # Run headless (API only)
  ritual --headless --port 8080
  
  # Run with custom host
  ritual --host 127.0.0.1 --port 3000
  
  # Development with auto-reload
  ritual --reload --debug
        """
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (API only, no frontend)",
    )

    args = parser.parse_args()

    setup_logging(args.debug)

    logger = logging.getLogger(__name__)
    logger.info("⊙ RITUAL - Starting server...")
    logger.info(f"Host: {args.host}, Port: {args.port}, Debug: {args.debug}, Headless: {args.headless}")

    app = create_app(headless=args.headless)

    import uvicorn
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
