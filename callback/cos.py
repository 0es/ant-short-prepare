# -*- coding=utf-8
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import os
import logging
from dotenv import load_dotenv

load_dotenv("../.env")

# Setup logger for cos operations
cos_logger = logging.getLogger("cos")
cos_logger.setLevel(logging.INFO)

# Configure cos logger to write to the same log directory as main.py
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)

# Create info log file handler for cos logger
from datetime import datetime

cos_info_log_file = os.path.join(
    log_dir, f'callback_{datetime.now().strftime("%Y%m%d")}.log'
)
cos_info_handler = logging.FileHandler(cos_info_log_file, encoding="utf-8")
cos_info_handler.setLevel(logging.INFO)

# Create error log file handler for cos logger
cos_error_log_file = os.path.join(
    log_dir, f'callback_error_{datetime.now().strftime("%Y%m%d")}.log'
)
cos_error_handler = logging.FileHandler(cos_error_log_file, encoding="utf-8")
cos_error_handler.setLevel(logging.ERROR)

# Create formatter for cos logger
cos_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
cos_info_handler.setFormatter(cos_formatter)
cos_error_handler.setFormatter(cos_formatter)

# Add handlers to cos logger
cos_logger.addHandler(cos_info_handler)
cos_logger.addHandler(cos_error_handler)

secret_id = os.getenv("TENCENTCLOUD_SECRET_ID")
secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY")
region = os.getenv("TENCENTCLOUD_REGION")
bucket = os.getenv("TENCENTCLOUD_BUCKET")
scheme = "https"

config = CosConfig(
    Region=region, SecretId=secret_id, SecretKey=secret_key, Scheme=scheme
)
client = CosS3Client(config)


def process_video_files(key):
    """
    Process video files according to the specified rules:
    - Copy and rename certain files
    - Delete specific files in batches

    Args:
        key (str): The base key without .mp4 extension (e.g., "/input/video_name/ep01")
    """
    cos_logger.info(f"Starting to process video files for key: {key}")

    # Define file operations
    copy_operations = [
        # (source_key, target_key)
        (f"{key}_smarterase_20100.mp4", f"{key}.mp4"),
        (f"{key}_smarterase_102.vtt", f"{key}_en.vtt"),
        (f"{key}_smarterase_20108_id.vtt", f"{key}_id.vtt"),
        (f"{key}_smarterase_20107_zh-TW.vtt", f"{key}_zh.vtt"),
    ]

    delete_keys = [
        f"{key}_smarterase_102.mp4",
        f"{key}_smarterase_20100.mp4",  # Delete after copy
        f"{key}_smarterase_102.vtt",  # Delete after copy
        f"{key}_smarterase_20108.vtt",
        f"{key}_smarterase_20108_id.vtt",  # Delete after copy
        f"{key}_smarterase_20107.vtt",
        f"{key}_smarterase_20107_zh-TW.vtt",  # Delete after copy
    ]

    # Perform copy operations
    for source_key, target_key in copy_operations:
        try:
            cos_logger.info(f"Copying {source_key} to {target_key}")
            response = client.copy(
                Bucket=bucket,
                Key=target_key,
                CopySource={
                    "Bucket": bucket,
                    "Key": source_key,
                    "Region": region,
                },
            )
            cos_logger.info(f"Successfully copied {source_key} to {target_key}")
        except Exception as e:
            cos_logger.error(f"Failed to copy {source_key} to {target_key}: {str(e)}")
            # Continue with other operations even if one fails

    # Perform batch delete operations
    if delete_keys:
        try:
            cos_logger.info(f"Batch deleting {len(delete_keys)} files")
            delete_objects = [{"Key": key} for key in delete_keys]
            response = client.delete_objects(
                Bucket=bucket,
                Delete={"Object": delete_objects},
            )

            # Log successful deletions
            if "Deleted" in response:
                for deleted in response["Deleted"]:
                    cos_logger.info(f"Successfully deleted: {deleted['Key']}")

            # Log failed deletions
            if "Error" in response:
                for error in response["Error"]:
                    cos_logger.error(
                        f"Failed to delete {error['Key']}: {error['Message']}"
                    )

        except Exception as e:
            cos_logger.error(f"Failed to perform batch delete: {str(e)}")

    cos_logger.info(f"Finished processing video files for key: {key}")
