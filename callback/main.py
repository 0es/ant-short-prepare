from flask import Flask, request, jsonify
import json
import logging
import os
from datetime import datetime
from .cos import process_video_files

app = Flask(__name__)

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)

# Setup logger
logger = logging.getLogger("callback")
logger.setLevel(logging.INFO)

# Create info log file handler
info_log_file = os.path.join(
    log_dir, f'callback_{datetime.now().strftime("%Y%m%d")}.log'
)
info_handler = logging.FileHandler(info_log_file, encoding="utf-8")
info_handler.setLevel(logging.INFO)

# Create error log file handler
error_log_file = os.path.join(
    log_dir, f'callback_error_{datetime.now().strftime("%Y%m%d")}.log'
)
error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
error_handler.setLevel(logging.ERROR)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
info_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(info_handler)
logger.addHandler(error_handler)


@app.route("/callback", methods=["POST"])
def callback():
    """
    HTTP callback endpoint for processing video tasks
    """
    try:
        # Get JSON data
        json_data = request.get_json()
        if not json_data:
            logger.error("No JSON data received in callback")
            return jsonify({"status": "error", "message": "No JSON data"}), 400

        # Log the callback received
        logger.info(f"Callback received: {json.dumps(json_data, ensure_ascii=False)}")

        # Process ScheduleTaskEvent
        if json_data.get("EventType") == "ScheduleTask":
            schedule_event = json_data.get("ScheduleTaskEvent")
            if schedule_event:
                task_id = schedule_event.get("TaskId", "Unknown")
                status = schedule_event.get("Status", "Unknown")
                message = schedule_event.get("Message", "")

                # Check if task failed
                if message != "SUCCESS":
                    logger.error(
                        f"Task failed - TaskId: {task_id}, Status: {status}, Message: {message}"
                    )
                else:
                    logger.info(f"Task completed successfully - TaskId: {task_id}")

                    # Extract original key from input info
                    input_info = schedule_event.get("InputInfo", {})
                    cos_input_info = input_info.get("CosInputInfo", {})
                    original_object = cos_input_info.get("Object", "")

                    if original_object:
                        # Remove .mp4 extension to get the key
                        original_key = (
                            original_object.replace(".mp4", "")
                            if original_object.endswith(".mp4")
                            else original_object
                        )
                        logger.info(f"Processing files for key: {original_key}")

                        try:
                            # Process video files using cos.py
                            process_video_files(original_key)
                            logger.info(
                                f"Successfully processed video files for key: {original_key}"
                            )
                        except Exception as cos_error:
                            logger.error(
                                f"Failed to process video files for key {original_key}: {str(cos_error)}"
                            )

                    # Process activity results for logging
                    activity_results = schedule_event.get("ActivityResultSet", [])
                    for activity in activity_results:
                        activity_type = activity.get("ActivityType", "Unknown")
                        smart_erase_task = activity.get("ActivityResItem", {}).get(
                            "SmartEraseTask"
                        )
                        if smart_erase_task:
                            erase_status = smart_erase_task.get("Status", "Unknown")
                            output_path = smart_erase_task.get("Output", {}).get(
                                "Path", ""
                            )
                            origin_subtitle = smart_erase_task.get("Output", {}).get(
                                "OriginSubtitlePath", ""
                            )
                            translate_subtitle = smart_erase_task.get("Output", {}).get(
                                "TranslateSubtitlePath", ""
                            )

                            logger.info(
                                f"Activity {activity_type} - Status: {erase_status}"
                            )
                            if output_path:
                                logger.info(f"  Output video: {output_path}")
                            if origin_subtitle:
                                logger.info(f"  Origin subtitle: {origin_subtitle}")
                            if translate_subtitle:
                                logger.info(
                                    f"  Translated subtitle: {translate_subtitle}"
                                )

        return jsonify({"status": "success", "message": "Callback processed"}), 200

    except Exception as e:
        logger.error(f"Error processing callback: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint
    """
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    print("Starting HTTP Callback Service...")
    print("Callback endpoint: POST /callback")
    print("Health check: GET /health")
    print(f"Info logs will be saved to: {info_log_file}")
    print(f"Error logs will be saved to: {error_log_file}")
    print("Server running on http://0.0.0.0:8080")

    app.run(host="0.0.0.0", port=8080, debug=False)
