#!/usr/bin/env python3
import asyncio
from intg_hyperion_apr16.driver import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass