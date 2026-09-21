import os
import shutil
import subprocess
import json
import sys


def resolve_ffprobe_path():
    """Resolve the bundled ffprobe executable for development or packaging."""

    executable_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"

    if getattr(sys, "frozen", False):
        search_roots = [
            os.path.dirname(sys.executable),
            getattr(sys, "_MEIPASS", "")
        ]
    else:
        search_roots = [
            os.path.dirname(os.path.abspath(__file__))
        ]

    for root in search_roots:
        if not root:
            continue

        bundled_path = os.path.join(
            root,
            "ffmpeg",
            executable_name
        )

        if os.path.isfile(bundled_path):
            return bundled_path

    return shutil.which(executable_name) or os.environ.get(
        "FFPROBE_PATH"
    )

FFPROBE_PATH = resolve_ffprobe_path()

if not FFPROBE_PATH:
    raise RuntimeError(
        "ffprobe was not found. Place ffprobe.exe in the app's ffmpeg "
        "folder, install ffmpeg, or set FFPROBE_PATH to its location."
    )

from collections import Counter
from datetime import datetime

from PIL import Image, ExifTags
from pillow_heif import register_heif_opener


# Enable HEIC support
register_heif_opener()


# ------------------------------------
# FILE TYPES
# ------------------------------------

PHOTO_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".heic",
    ".png"
}

VIDEO_EXTENSIONS = {
    ".mov",
    ".mp4",
    ".m4v"
}


# ------------------------------------
# FILE MODIFIED DATE
# ------------------------------------

def get_modified_year(path):

    timestamp = os.path.getmtime(path)

    return datetime.fromtimestamp(
        timestamp
    ).year


# ------------------------------------
# PARSE EXIF DATE
# ------------------------------------

def parse_exif_date(value):

    if not value:
        return None

    try:

        return datetime.strptime(
            str(value),
            "%Y:%m:%d %H:%M:%S"
        )

    except Exception:

        return None


# ------------------------------------
# PHOTO METADATA
# ------------------------------------

def get_photo_date(path):

    try:

        image = Image.open(path)

        exif = image.getexif()

        if not exif:
            return None

        # --------------------------------
        # Identify camera/software
        # --------------------------------

        make = str(
            exif.get(271, "")
        ).strip().lower()

        model = str(
            exif.get(272, "")
        ).strip().lower()

        software = str(
            exif.get(305, "")
        ).strip().lower()

        # --------------------------------
        # DateTimeOriginal
        # --------------------------------
        #
        # This is our highest-confidence
        # capture date.
        #

        original_date = parse_exif_date(
            exif.get(36867)
        )

        if original_date:

            return {
                "year": original_date.year,
                "date_source":
                    "EXIF DateTimeOriginal"
            }

        # --------------------------------
        # Apple / iPhone DateTime
        # --------------------------------
        #
        # Some iPhone HEIC files don't have
        # DateTimeOriginal but do contain
        # DateTime.
        #
        # We trust this when the metadata
        # identifies the file as Apple/iPhone
        # generated.
        #

        is_apple_device = (
            "apple" in make
            or "iphone" in model
            or "ipad" in model
            or "ipod" in model
        )

        if is_apple_device:

            apple_date = parse_exif_date(
                exif.get(306)
            )

            if apple_date:

                return {
                    "year": apple_date.year,
                    "date_source":
                        "Apple EXIF DateTime"
                }

        # --------------------------------
        # Ignore editing software dates
        # --------------------------------
        #
        # Photoshop and similar programs can
        # rewrite DateTime when an image is
        # edited or exported.
        #

        editing_software = {
            "adobe photoshop",
            "photoshop",
            "adobe photoshop cs",
            "adobe photoshop cs3",
            "adobe photoshop cs4",
            "adobe photoshop cs5",
            "adobe photoshop cs6"
        }

        is_editing_software = any(
            software_name in software
            for software_name
            in editing_software
        )

        if is_editing_software:

            return None

        # --------------------------------
        # Generic DateTime
        # --------------------------------
        #
        # We intentionally do NOT trust a
        # generic DateTime value for unknown
        # software/cameras.
        #

    except Exception:

        return None

    return None


# ------------------------------------
# INSPECT PHOTO METADATA
# ------------------------------------

def inspect_photo_metadata(path):

    try:

        image = Image.open(path)

        exif = image.getexif()

        print("\n--- PHOTO METADATA ---")

        print(
            "File:",
            os.path.basename(path)
        )

        if not exif:

            print(
                "No EXIF metadata found."
            )

        else:

            for tag_id, value in exif.items():

                tag_name = ExifTags.TAGS.get(
                    tag_id,
                    tag_id
                )

                print(
                    f"{tag_name}: {value}"
                )

        print(
            "----------------------\n"
        )

    except Exception as error:

        print(
            "Could not read metadata:",
            error
        )


# ------------------------------------
# VIDEO DATE PARSING
# ------------------------------------

def parse_video_date(value):

    if not value:
        return None

    value = str(value).strip()

    try:

        # ISO format
        #
        # Example:
        # 2017-07-03T16:07:48Z

        date_string = value.replace(
            "Z",
            "+00:00"
        )

        return datetime.fromisoformat(
            date_string
        )

    except Exception:

        try:

            # Some files may contain
            # only the first part of the date.

            return datetime.strptime(
                value[:19],
                "%Y-%m-%dT%H:%M:%S"
            )

        except Exception:

            return None


# ------------------------------------
# VIDEO METADATA
# ------------------------------------

def get_video_date(path):
    try:
        command = [
            FFPROBE_PATH,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_entries",
            "format_tags:stream_tags",
            path
        ]

        creationflags = (
            subprocess.CREATE_NO_WINDOW
            if sys.platform == "win32"
            else 0
        )

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            creationflags=creationflags
        )

        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)

        possible_dates = []

        # Check format-level metadata
        format_tags = (
            data
            .get("format", {})
            .get("tags", {})
        )

        for key, value in format_tags.items():
            key_lower = str(key).lower()

            if key_lower in {
                "creation_time",
                "com.apple.quicktime.creationdate"
            }:
                possible_dates.append(value)

        # Check stream-level metadata
        for stream in data.get("streams", []):
            stream_tags = stream.get("tags", {})

            for key, value in stream_tags.items():
                key_lower = str(key).lower()

                if key_lower in {
                    "creation_time",
                    "com.apple.quicktime.creationdate"
                }:
                    possible_dates.append(value)

        # Try each discovered date
        for value in possible_dates:
            date = parse_video_date(value)

            if not date:
                continue

            year = date.year

            if 1900 <= year <= datetime.now().year + 1:
                return {
                    "year": year,
                    "date_source": "Video metadata"
                }

    except Exception:
        return None

    return None


# ------------------------------------
# GET FILE DATE
# ------------------------------------

def get_file_date(path, extension):

    # --------------------------------
    # PHOTOS
    # --------------------------------

    if extension in PHOTO_EXTENSIONS:

        metadata_date = get_photo_date(
            path
        )

        if metadata_date:

            return metadata_date

    # --------------------------------
    # VIDEOS
    # --------------------------------

    elif extension in VIDEO_EXTENSIONS:

        metadata_date = get_video_date(
            path
        )

        if metadata_date:

            return metadata_date

    # --------------------------------
    # FALLBACK
    # --------------------------------

    return {
        "year": get_modified_year(path),
        "date_source":
            "File modified date"
    }


# ------------------------------------
# SCAN FOLDER
# ------------------------------------

def scan_folder(folder):

    photos = []
    videos = []
    other = []

    zero_byte_files = []
    unreadable_files = []
    missing_metadata = []

    all_filenames = []

    # --------------------------------
    # WALK THROUGH FOLDER
    # --------------------------------

    for root, dirs, files in os.walk(folder):

        # Ignore folders created by
        # the organizer itself.
        dirs[:] = [
            directory
            for directory in dirs
            if directory not in {
                "Photos",
                "Videos"
            }
        ]

        for file in files:

            path = os.path.join(
                root,
                file
            )

            all_filenames.append(
                file
            )

            extension = (
                os.path.splitext(file)[1]
                .lower()
            )

            # --------------------------------
            # GET FILE SIZE
            # --------------------------------

            try:

                size = os.path.getsize(
                    path
                )

            except Exception as error:

                unreadable_files.append({
                    "file": file,
                    "path": path,
                    "error": str(error)
                })

                continue

            # --------------------------------
            # ZERO BYTE FILES
            # --------------------------------

            if size == 0:

                zero_byte_files.append({
                    "file": file,
                    "path": path
                })

                continue

            # --------------------------------
            # PHOTOS
            # --------------------------------

            if extension in PHOTO_EXTENSIONS:

                try:

                    date_info = get_file_date(
                        path,
                        extension
                    )

                except Exception as error:

                    unreadable_files.append({
                        "file": file,
                        "path": path,
                        "error": str(error)
                    })

                    continue

                # --------------------------------
                # Missing capture metadata
                # --------------------------------

                if (
                    date_info["date_source"]
                    == "File modified date"
                ):

                    missing_metadata.append({
                        "file": file,
                        "path": path,
                        "type": "Photos",
                        "year":
                            date_info["year"]
                    })

                photos.append({

                    "file": file,

                    "size": size,

                    "path": path,

                    "year":
                        date_info["year"],

                    "date_source":
                        date_info["date_source"]

                })

            # --------------------------------
            # VIDEOS
            # --------------------------------

            elif extension in VIDEO_EXTENSIONS:

                try:

                    date_info = get_file_date(
                        path,
                        extension
                    )

                except Exception as error:

                    unreadable_files.append({
                        "file": file,
                        "path": path,
                        "error": str(error)
                    })

                    continue

                # --------------------------------
                # Missing capture metadata
                # --------------------------------

                if (
                    date_info["date_source"]
                    == "File modified date"
                ):

                    missing_metadata.append({
                        "file": file,
                        "path": path,
                        "type": "Videos",
                        "year":
                            date_info["year"]
                    })

                videos.append({

                    "file": file,

                    "size": size,

                    "path": path,

                    "year":
                        date_info["year"],

                    "date_source":
                        date_info["date_source"]

                })

            # --------------------------------
            # OTHER FILES
            # --------------------------------

            else:

                other.append({

                    "file": file,

                    "size": size,

                    "path": path

                })

    # ------------------------------------
    # DUPLICATE FILENAMES
    # ------------------------------------

    filename_counts = Counter(
        all_filenames
    )

    duplicates = {

        name: count

        for name, count
        in filename_counts.items()

        if count > 1
    }

    # ------------------------------------
    # RETURN RESULTS
    # ------------------------------------

    return {

        "total_files":
            len(all_filenames),

        "photos":
            photos,

        "videos":
            videos,

        "other":
            other,

        "zero_byte_files":
            zero_byte_files,

        "unreadable_files":
            unreadable_files,

        "missing_metadata":
            missing_metadata,

        "duplicates":
            duplicates
    }


# ------------------------------------
# DUPLICATE RENAME PREVIEW
# ------------------------------------

def build_duplicate_details(results, duplicates):
    """
    Predict what each duplicate filename will be renamed to.

    Mirrors the "(n)" renaming pattern used by
    organizer.get_unique_destination, simulated per
    destination folder (file type + year).
    """

    occurrence_counts = {}
    details_by_name = {}

    def register(file_type, year, filename, size):

        if filename not in duplicates:
            return

        if size == 0:

            # Zero-byte files are skipped during organizing,
            # so they are never actually renamed.
            renamed_to = filename

        else:

            key = (file_type, year, filename)
            count = occurrence_counts.get(key, 0)
            occurrence_counts[key] = count + 1

            if count == 0:
                renamed_to = filename
            else:
                name_part, extension = os.path.splitext(
                    filename
                )
                renamed_to = f"{name_part} ({count}){extension}"

        details_by_name.setdefault(filename, []).append({
            "type": file_type,
            "year": year,
            "renamed_to": renamed_to
        })

    for photo in results["photos"]:
        register(
            "Photos",
            photo["year"],
            photo["file"],
            photo["size"]
        )

    for video in results["videos"]:
        register(
            "Videos",
            video["year"],
            video["file"],
            video["size"]
        )

    for item in results["other"]:

        # "Other" files are never organized/renamed,
        # they simply stay in place.
        details_by_name.setdefault(item["file"], [])

        if item["file"] in duplicates:
            details_by_name[item["file"]].append({
                "type": "Other (not organized)",
                "year": None,
                "renamed_to": item["file"]
            })

    for item in results["zero_byte_files"]:

        details_by_name.setdefault(item["file"], [])

        if item["file"] in duplicates:
            details_by_name[item["file"]].append({
                "type": "0-byte file (skipped)",
                "year": None,
                "renamed_to": item["file"]
            })

    for item in results["unreadable_files"]:

        details_by_name.setdefault(item["file"], [])

        if item["file"] in duplicates:
            details_by_name[item["file"]].append({
                "type": "Unreadable file (skipped)",
                "year": None,
                "renamed_to": item["file"]
            })

    return [
        {"file": name, "occurrences": occurrences}
        for name, occurrences in sorted(details_by_name.items())
        if occurrences
    ]