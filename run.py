#!/usr/bin/env python3
import asyncio
import logging
from intg_hyperion_apr16.driver import APR16Driver

_LOGGER = logging.getLogger(__name__)

async def main():
    """Bootstrap and run the AudioControl Hyperion APR-16 integration driver."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    _LOGGER.info("Starting AudioControl Hyperion APR-16 integration driver...")
    
    # Initialize the driver wrapper (ucapi-framework handles server binding on init)
    driver_wrapper = APR16Driver()
    
    # Keep the async loop alive for framework server tasks and mDNS broadcasting
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("Driver stopped by user")