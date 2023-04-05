import asyncio
import threading

import app.main_app
import tracemalloc

if __name__ == "__main__":
    tracemalloc.start()
    app.main_app.main()
