import base64

from pyroaring import BitMap


def serialize_bitmap(bitmap: BitMap) -> str:
    return base64.b64encode(bitmap.serialize()).decode("ascii")


def bitmap_count(bitmap: BitMap) -> int:
    return len(bitmap)
