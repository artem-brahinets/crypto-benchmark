import base64
import csv
import statistics

import matplotlib.pyplot as plt
import requests

from config import *


def upload(service, url, photo, run, index):
    response = requests.post(
        f"{url}/upload",
        json={"photo_base64": photo},
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    return {
        "run": run,
        "service": service,
        "photo": index,
        "photo_id": data["photo_id"],
        "operation": "encrypt",
        "time_ms": data["crypto_time_ms"],
    }


def download(service, url, photo_id, run, index):
    response = requests.get(
        f"{url}/download/{photo_id}",
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    return {
        "run": run,
        "service": service,
        "photo": index,
        "photo_id": photo_id,
        "operation": "decrypt",
        "time_ms": data["decrypt_time_ms"],
    }


def run_service(service, url, photos, run):
    results = []

    print()
    print(f"{service} | Run {run}/{NUM_RUNS}")
    print("-" * 50)

    for index, photo in enumerate(photos, 1):
        try:
            result = upload(
                service,
                url,
                photo,
                run,
                index,
            )

            results.append(result)

            if index % 100 == 0:
                print(
                    f"Encrypt: "
                    f"{index}/{len(photos)}"
                )

        except Exception as e:
            print(
                f"Encrypt {index} failed: {e}"
            )

    encrypted = [
        r for r in results
        if r["operation"] == "encrypt"
    ]

    for index, item in enumerate(encrypted, 1):
        try:
            result = download(
                service,
                url,
                item["photo_id"],
                run,
                item["photo"],
            )

            results.append(result)

            if index % 100 == 0:
                print(
                    f"Decrypt: "
                    f"{index}/{len(encrypted)}"
                )

        except Exception as e:
            print(
                f"Decrypt {index} failed: {e}"
            )

    return results


def get_values(results, service, operation):
    return [
        row["time_ms"]
        for row in results
        if row["service"] == service
        and row["operation"] == operation
    ]


def calculate_stats(values):
    if not values:
        return {
            "count": 0,
            "total": 0,
            "average": 0,
            "median": 0,
            "min": 0,
            "max": 0,
            "std": 0,
        }

    return {
        "count": len(values),
        "total": sum(values),
        "average": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "std": (
            statistics.stdev(values)
            if len(values) > 1
            else 0
        ),
    }


def save_operations(results):
    with open(
        OPERATIONS_CSV,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        fields = [
            "run",
            "service",
            "photo",
            "photo_id",
            "operation",
            "time_ms",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )

        writer.writeheader()

        for row in results:
            writer.writerow({
                "run": row["run"],
                "service": row["service"],
                "photo": row["photo"],
                "photo_id": row["photo_id"],
                "operation": row["operation"],
                "time_ms": round(
                    row["time_ms"],
                    6,
                ),
            })


def save_statistics(results):
    with open(
        STATISTICS_CSV,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        fields = [
            "service",
            "operation",
            "count",
            "total_ms",
            "average_ms",
            "median_ms",
            "min_ms",
            "max_ms",
            "std_ms",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )

        writer.writeheader()

        for service in SERVICES:
            for operation in [
                "encrypt",
                "decrypt",
            ]:
                values = get_values(
                    results,
                    service,
                    operation,
                )

                s = calculate_stats(values)

                writer.writerow({
                    "service": service,
                    "operation": operation,
                    "count": s["count"],
                    "total_ms": round(
                        s["total"],
                        6,
                    ),
                    "average_ms": round(
                        s["average"],
                        6,
                    ),
                    "median_ms": round(
                        s["median"],
                        6,
                    ),
                    "min_ms": round(
                        s["min"],
                        6,
                    ),
                    "max_ms": round(
                        s["max"],
                        6,
                    ),
                    "std_ms": round(
                        s["std"],
                        6,
                    ),
                })


def save_comparison(results):
    rows = []

    for operation, name in [
        ("encrypt", "Encryption"),
        ("decrypt", "Decryption"),
    ]:
        aes = calculate_stats(
            get_values(
                results,
                "AES",
                operation,
            )
        )

        stb = calculate_stats(
            get_values(
                results,
                "STB",
                operation,
            )
        )

        aes_avg = aes["average"]
        stb_avg = stb["average"]

        faster = (
            "AES"
            if aes_avg < stb_avg
            else "STB"
        )

        faster_time = min(
            aes_avg,
            stb_avg,
        )

        slower_time = max(
            aes_avg,
            stb_avg,
        )

        difference = (
            (slower_time - faster_time)
            / slower_time
            * 100
            if slower_time
            else 0
        )

        times_faster = (
            slower_time / faster_time
            if faster_time
            else 0
        )

        rows.append({
            "Operation": name,
            "AES avg ms": aes_avg,
            "STB avg ms": stb_avg,
            "Faster": faster,
            "Times faster": times_faster,
            "Difference %": difference,
        })

    aes_encrypt = calculate_stats(
        get_values(
            results,
            "AES",
            "encrypt",
        )
    )

    aes_decrypt = calculate_stats(
        get_values(
            results,
            "AES",
            "decrypt",
        )
    )

    stb_encrypt = calculate_stats(
        get_values(
            results,
            "STB",
            "encrypt",
        )
    )

    stb_decrypt = calculate_stats(
        get_values(
            results,
            "STB",
            "decrypt",
        )
    )

    aes_total = (
        aes_encrypt["average"]
        + aes_decrypt["average"]
    )

    stb_total = (
        stb_encrypt["average"]
        + stb_decrypt["average"]
    )

    faster = (
        "AES"
        if aes_total < stb_total
        else "STB"
    )

    faster_time = min(
        aes_total,
        stb_total,
    )

    slower_time = max(
        aes_total,
        stb_total,
    )

    difference = (
        (slower_time - faster_time)
        / slower_time
        * 100
        if slower_time
        else 0
    )

    times_faster = (
        slower_time / faster_time
        if faster_time
        else 0
    )

    rows.append({
        "Operation": "Crypto total",
        "AES avg ms": aes_total,
        "STB avg ms": stb_total,
        "Faster": faster,
        "Times faster": times_faster,
        "Difference %": difference,
    })

    with open(
        COMPARISON_CSV,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        fields = [
            "Operation",
            "AES avg ms",
            "STB avg ms",
            "Faster",
            "Times faster",
            "Difference %",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow({
                key: (
                    round(value, 4)
                    if isinstance(value, float)
                    else value
                )
                for key, value in row.items()
            })


def save_info():
    with open(
        INFO_CSV,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            "Parameter",
            "Value",
        ])

        writer.writerow([
            "Algorithm 1",
            "AES",
        ])

        writer.writerow([
            "Algorithm 2",
            "STB",
        ])

        writer.writerow([
            "Runs",
            NUM_RUNS,
        ])

        writer.writerow([
            "Photos per run",
            NUM_PHOTOS,
        ])

        writer.writerow([
            "Photo size",
            f"{PHOTO_SIZE / 1024:.0f} KB",
        ])

        writer.writerow([
            "Total operations per algorithm",
            NUM_RUNS * NUM_PHOTOS,
        ])

        writer.writerow([
            "Encryption operations per algorithm",
            NUM_RUNS * NUM_PHOTOS,
        ])

        writer.writerow([
            "Decryption operations per algorithm",
            NUM_RUNS * NUM_PHOTOS,
        ])

        writer.writerow([
            "Measured metric",
            "Pure encryption/decryption time",
        ])

        writer.writerow([
            "Time unit",
            "milliseconds",
        ])

        writer.writerow([
            "Input data",
            "Identical random data",
        ])


def create_chart(results):
    operations = [
        "Encryption",
        "Decryption",
    ]

    aes_values = [
        calculate_stats(
            get_values(
                results,
                "AES",
                "encrypt",
            )
        )["average"],
        calculate_stats(
            get_values(
                results,
                "AES",
                "decrypt",
            )
        )["average"],
    ]

    stb_values = [
        calculate_stats(
            get_values(
                results,
                "STB",
                "encrypt",
            )
        )["average"],
        calculate_stats(
            get_values(
                results,
                "STB",
                "decrypt",
            )
        )["average"],
    ]

    x = range(len(operations))
    width = 0.35

    plt.figure(figsize=(9, 6))

    plt.bar(
        [i - width / 2 for i in x],
        aes_values,
        width,
        label="AES",
    )

    plt.bar(
        [i + width / 2 for i in x],
        stb_values,
        width,
        label="STB",
    )

    plt.xticks(
        list(x),
        operations,
    )

    plt.ylabel("Average time (ms)")
    plt.title("AES vs STB — Cryptographic Performance")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        CHART_FILE,
        dpi=200,
    )

    plt.close()


def print_summary(results):
    print()
    print("=" * 70)
    print("AES vs STB")
    print("=" * 70)

    for operation, name in [
        ("encrypt", "Encryption"),
        ("decrypt", "Decryption"),
    ]:
        aes = calculate_stats(
            get_values(
                results,
                "AES",
                operation,
            )
        )

        stb = calculate_stats(
            get_values(
                results,
                "STB",
                operation,
            )
        )

        faster = (
            "AES"
            if aes["average"] < stb["average"]
            else "STB"
        )

        faster_time = min(
            aes["average"],
            stb["average"],
        )

        slower_time = max(
            aes["average"],
            stb["average"],
        )

        times_faster = (
            slower_time / faster_time
            if faster_time
            else 0
        )

        difference = (
            (slower_time - faster_time)
            / slower_time
            * 100
            if slower_time
            else 0
        )

        print()
        print(name)
        print(
            f"  AES: "
            f"{aes['average']:.4f} ms"
        )
        print(
            f"  STB: "
            f"{stb['average']:.4f} ms"
        )
        print(
            f"  Faster: "
            f"{faster}"
        )
        print(
            f"  Times faster: "
            f"{times_faster:.2f}x"
        )
        print(
            f"  Difference: "
            f"{difference:.2f}%"
        )

    print()
    print("=" * 70)


def main():
    print(
        f"Benchmark: "
        f"{NUM_RUNS} runs × "
        f"{NUM_PHOTOS} photos × "
        f"{PHOTO_SIZE / 1024:.0f} KB"
    )

    os.makedirs(
        RESULTS_DIR,
        exist_ok=True,
    )

    for path in [
        COMPARISON_CSV,
        STATISTICS_CSV,
        OPERATIONS_CSV,
        INFO_CSV,
        CHART_FILE,
    ]:
        if os.path.exists(path):
            os.remove(path)

    results = []

    for run in range(1, NUM_RUNS + 1):
        photos = [
            base64.b64encode(
                os.urandom(PHOTO_SIZE)
            ).decode()
            for _ in range(NUM_PHOTOS)
        ]

        for service, url in SERVICES.items():
            service_results = run_service(
                service,
                url,
                photos,
                run,
            )

            results.extend(
                service_results
            )

    save_comparison(results)
    save_statistics(results)
    save_operations(results)
    save_info()
    create_chart(results)

    print_summary(results)

    print()
    print("Results:")
    print(f"  {COMPARISON_CSV}")
    print(f"  {STATISTICS_CSV}")
    print(f"  {OPERATIONS_CSV}")
    print(f"  {INFO_CSV}")
    print(f"  {CHART_FILE}")


if __name__ == "__main__":
    main()