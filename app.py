import json
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

import webview

from scanner import scan_folder, build_duplicate_details
from organizer import organize_files
from version import __version__

UPDATE_CHECK_URL = (
    "https://api.github.com/repos/patrikago/folder-organizer/releases/latest"
)
UPDATE_CHECK_TIMEOUT_SECONDS = 5


def _parse_version(version_string):
    parts = []

    for part in version_string.strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        parts.append(int(digits) if digits else 0)

    return tuple(parts)


class Api:

    def __init__(self):
        self.results = None
        self.source_folder = None

    def check_for_update(self):
        try:
            request = urllib.request.Request(
                UPDATE_CHECK_URL,
                headers={"Accept": "application/vnd.github+json"}
            )

            with urllib.request.urlopen(
                request,
                timeout=UPDATE_CHECK_TIMEOUT_SECONDS
            ) as response:
                data = json.load(response)

            tag_name = data.get("tag_name", "")
            html_url = data.get("html_url", "")

            if not tag_name or not html_url:
                return None

            if _parse_version(tag_name) <= _parse_version(__version__):
                return None

            return {
                "latest_version": tag_name,
                "url": html_url
            }
        except Exception:
            # Network failures, timeouts, or malformed responses should
            # never interrupt the app - fail silently.
            return None

    def open_release_page(self, url):
        if not isinstance(url, str) or not url.startswith(
            "https://github.com/"
        ):
            return False

        webbrowser.open(url)

        return True

    def select_folder(self):
        result = window.create_file_dialog(
            webview.FOLDER_DIALOG
        )

        if result:
            return result[0]

        return None

    def scan_folder(self, folder):
        if not folder:
            return None

        self.source_folder = folder

        self.results = scan_folder(folder)

        return {
            "total_files": self.results["total_files"],
            "photos": len(self.results["photos"]),
            "videos": len(self.results["videos"]),
            "other": len(self.results["other"]),
            "zero_byte_files": len(
                self.results["zero_byte_files"]
            ),
            "duplicates": len(
                self.results["duplicates"]
            ),
            "unreadable_files": len(
                self.results["unreadable_files"]
            ),
            "missing_metadata": len(
                self.results["missing_metadata"]
            )
        }

    def get_preview(self):
        if not self.results:
            return None

        photo_years = {}
        video_years = {}

        photo_sources = {}
        video_sources = {}

        photo_fallback_years = set()
        video_fallback_years = set()

        for photo in self.results["photos"]:
            year = photo["year"]

            if year not in photo_years:
                photo_years[year] = 0

            photo_years[year] += 1

            source = photo["date_source"]

            if source not in photo_sources:
                photo_sources[source] = 0

            photo_sources[source] += 1

            if source == "File modified date":
                photo_fallback_years.add(year)

        for video in self.results["videos"]:
            year = video["year"]

            if year not in video_years:
                video_years[year] = 0

            video_years[year] += 1

            source = video["date_source"]

            if source not in video_sources:
                video_sources[source] = 0

            video_sources[source] += 1

            if source == "File modified date":
                video_fallback_years.add(year)

        duplicate_details = build_duplicate_details(
            self.results,
            self.results["duplicates"]
        )

        missing_metadata_details = [
            {
                "file": item["file"],
                "type": item["type"],
                "year": item["year"]
            }
            for item in self.results["missing_metadata"]
        ]

        return {
            "photos": dict(
                sorted(photo_years.items())
            ),

            "videos": dict(
                sorted(video_years.items())
            ),

            "photo_sources": photo_sources,

            "video_sources": video_sources,

            "photo_fallback_years":
                sorted(photo_fallback_years),

            "video_fallback_years":
                sorted(video_fallback_years),

            "missing_metadata":
                len(self.results["missing_metadata"]),

            "missing_metadata_details":
                missing_metadata_details,

            "zero_byte_files":
                len(self.results["zero_byte_files"]),

            "unreadable_files":
                len(self.results["unreadable_files"]),

            "duplicates":
                len(self.results["duplicates"]),

            "duplicate_details":
                duplicate_details,

            "other":
                len(self.results["other"])
    }

    def organize_files(
        self,
        mode,
        destination_folder=None
    ):

        if not self.results:
            return {
                "success": False,
                "message": "Please scan a folder first."
            }

        if mode == "copy":

            if not destination_folder:
                return {
                    "success": False,
                    "message":
                        "Please select a destination folder."
                }

            destination = destination_folder

        else:

            destination = self.source_folder


        result = organize_files(
            self.results,
            self.source_folder,
            destination,
            mode=mode
        )


        return {
            "success": True,
            "moved": result["moved"],
            "copied": result["copied"],
            "skipped": result["skipped"],
            "errors": result["errors"]
        }


def resource_path(relative_path):
    # PyInstaller extracts bundled data next to the exe under _internal.
    base_path = getattr(sys, "_MEIPASS", Path(__file__).parent)

    return str(Path(base_path) / relative_path)


api = Api()


window = webview.create_window(
    "PicPur",
    "ui/index.html",
    js_api=api,
    width=1000,
    height=800,
    min_size=(750, 600)
)


# Devtools stay off in the packaged (frozen) build.
webview.start(
    debug=not getattr(sys, "frozen", False),
    icon=resource_path("assets/icon.ico")
)