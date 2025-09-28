# -*- coding: utf-8 -*-

import os
import json
import types
import base64
import glob
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.vod.v20180717 import vod_client, models
from dotenv import load_dotenv

load_dotenv("../.env")


def get_language_from_filename(filename):
    """
    Extract language code from filename
    Rules:
    - Files without language suffix are English (en)
    - Files ending with _zh-TW are Traditional Chinese
    - Files ending with _id are Indonesian
    """
    base_name = os.path.splitext(filename)[0]  # Remove .vtt extension

    if base_name.endswith("_zh-TW"):
        return "zh"
    elif base_name.endswith("_id"):
        return "id"
    else:
        return "en"  # Default to English for files without language suffix


def load_subtitle_files(assets_dir="assets"):
    """
    Dynamically load subtitle files from assets directory
    Returns list of subtitle dictionaries for AddSubtitles
    """
    subtitles = []

    # Get all .vtt files in assets directory
    vtt_files = glob.glob(os.path.join(assets_dir, "*.vtt"))

    for file_path in vtt_files:
        filename = os.path.basename(file_path)
        language = get_language_from_filename(filename)

        # Read file content and encode in base64
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Encode content to base64
                content_base64 = base64.b64encode(content.encode("utf-8")).decode(
                    "utf-8"
                )

                subtitle_info = {
                    "Name": filename,
                    "Language": language,
                    "Format": "vtt",
                    "Content": content_base64,
                }
                subtitles.append(subtitle_info)
                print(f"Loaded subtitle: {filename} (Language: {language})")

        except Exception as e:
            print(f"Error loading subtitle file {filename}: {e}")

    return subtitles


try:
    cred = credential.Credential(
        os.getenv("TENCENTCLOUD_SECRET_ID"), os.getenv("TENCENTCLOUD_SECRET_KEY")
    )

    httpProfile = HttpProfile()
    httpProfile.endpoint = "vod.intl.tencentcloudapi.com"
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile

    client = vod_client.VodClient(cred, "", clientProfile)

    # Load subtitle files dynamically
    subtitles = load_subtitle_files("assets")

    if not subtitles:
        print("No subtitle files found in assets directory")
        exit(1)

    req = models.ModifyMediaInfoRequest()
    params = {
        "Action": "ModifyMediaInfo",
        "Version": "2018-07-17",
        "FileId": "5145403700325128644",
        "AddSubtitles": subtitles,
    }

    req.from_json_string(json.dumps(params))

    resp = client.ModifyMediaInfo(req)
    print(resp.to_json_string())

except TencentCloudSDKException as err:
    print(err)
