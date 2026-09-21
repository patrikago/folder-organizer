import os
import shutil


def get_unique_destination(destination):
    """
    Prevent files from being overwritten.

    Example:
        IMG_1234.JPG
        IMG_1234 (1).JPG
        IMG_1234 (2).JPG
    """

    if not os.path.exists(destination):
        return destination

    folder = os.path.dirname(destination)
    filename = os.path.basename(destination)
    name, extension = os.path.splitext(filename)

    counter = 1

    while True:
        new_filename = f"{name} ({counter}){extension}"
        new_destination = os.path.join(
            folder,
            new_filename
        )

        if not os.path.exists(new_destination):
            return new_destination

        counter += 1


def organize_files(
    results,
    source_folder,
    destination_folder,
    mode="move"
):
    """
    Organize photos and videos by year.

    mode="move"
        Moves files from the source folder.

    mode="copy"
        Copies files while leaving the originals untouched.
    """

    moved = 0
    copied = 0
    skipped = 0
    errors = []

    files_to_organize = []

    # ------------------------------------
    # PHOTOS
    # ------------------------------------

    for photo in results["photos"]:

        if photo["size"] == 0:
            skipped += 1
            continue

        files_to_organize.append(
            (
                "Photos",
                photo["file"],
                photo["path"],
                photo["year"]
            )
        )

    # ------------------------------------
    # VIDEOS
    # ------------------------------------

    for video in results["videos"]:

        if video["size"] == 0:
            skipped += 1
            continue

        files_to_organize.append(
            (
                "Videos",
                video["file"],
                video["path"],
                video["year"]
            )
        )

    # ------------------------------------
    # ORGANIZE FILES
    # ------------------------------------

    for file_type, file, source_path, year in files_to_organize:

        destination_year_folder = os.path.join(
            destination_folder,
            file_type,
            str(year)
        )

        os.makedirs(
            destination_year_folder,
            exist_ok=True
        )

        destination_path = os.path.join(
            destination_year_folder,
            file
        )

        destination_path = get_unique_destination(
            destination_path
        )

        try:

            if mode == "move":

                shutil.move(
                    source_path,
                    destination_path
                )

                moved += 1

            elif mode == "copy":

                shutil.copy2(
                    source_path,
                    destination_path
                )

                copied += 1

            else:

                skipped += 1

                errors.append(
                    f"{file}: Unknown organization mode."
                )

        except Exception as error:

            skipped += 1

            errors.append(
                f"{file}: {error}"
            )

    return {
        "moved": moved,
        "copied": copied,
        "skipped": skipped,
        "errors": errors
    }