import os
import zipfile
def create_archive(folder_path):
    files = os.listdir(folder_path)
    files.sort(key=lambda x: int(x.split('_')[0]) if '_' in x else float('inf'))
    ranges = []
    singles = []
    current_range_start = None
    prev_id = None
    for file in files:
        if '_' in file:
            file_id = int(file.split('_')[0])
            if current_range_start is not None and file_id != prev_id + 1:
                ranges.append((current_range_start, prev_id))
                current_range_start = None
            prev_id = file_id
            if current_range_start is None:
                current_range_start = file_id
        else:
            singles.append(file)
    if current_range_start is not None:
        ranges.append((current_range_start, prev_id))
    archive_name = ", ".join([f"{start}-{end}" if start != end else str(start) for start, end in ranges])
    if singles:
        archive_name += ", " + ", ".join(singles)
    archive_name += ".zip"
    with zipfile.ZipFile(os.path.join(folder_path, archive_name), 'w') as zipf:
        for file in files:
            zipf.write(os.path.join(folder_path, file), arcname=file,compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    
    return archive_name