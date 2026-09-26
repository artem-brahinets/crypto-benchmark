import os


SERVICES = {
    "AES": os.getenv("AES_URL", "http://127.0.0.1:8002"),
    "STB": os.getenv("STB_URL", "http://127.0.0.1:8001"),
}

NUM_RUNS = 5
NUM_PHOTOS = 1000
PHOTO_SIZE = 100 * 1024
TIMEOUT = 60

RESULTS_DIR = "results"

COMPARISON_CSV = os.path.join(
    RESULTS_DIR,
    "crypto_comparison.csv",
)

STATISTICS_CSV = os.path.join(
    RESULTS_DIR,
    "crypto_statistics.csv",
)

OPERATIONS_CSV = os.path.join(
    RESULTS_DIR,
    "all_operations.csv",
)

INFO_CSV = os.path.join(
    RESULTS_DIR,
    "benchmark_info.csv",
)

CHART_FILE = os.path.join(
    RESULTS_DIR,
    "benchmark_chart.png",
)