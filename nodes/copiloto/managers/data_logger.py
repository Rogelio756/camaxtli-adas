# managers/data_logger.py

import csv
import os


class DataLogger:
    def __init__(self, csv_path):
        self.csv_path = csv_path

        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp_local",
                    "timestamp_mqtt",
                    "veh_label",
                    "veh_conf",
                    "veh_bbox",
                    "raw_path",
                    "roi_path",
                    "plate_text",
                    "plate_conf",
                    "status"
                ])

    def log(self, **kwargs):
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(kwargs.values())
