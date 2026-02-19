"""Parser utilities for yt-dlp output."""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def parse_progress(line: str) -> Optional[float]:
    """
    Parse download progress from yt-dlp output line.
    
    Args:
        line: Output line from yt-dlp
    
    Returns:
        Progress percentage (0-100) or None if not found
    
    Example:
        >>> parse_progress("[download]  45.2% of 10.5MiB at 1.2MiB/s ETA 00:05")
        45.2
    """
    progress_match = re.search(r'\[download\]\s+(\d+\.?\d*)%', line)
    if progress_match:
        return float(progress_match.group(1))
    return None


def parse_destination(line: str) -> Optional[str]:
    """
    Parse destination file path from yt-dlp output line.
    
    Args:
        line: Output line from yt-dlp
    
    Returns:
        File path or None if not found
    
    Example:
        >>> parse_destination("[download] Destination: /path/to/file.mp4")
        '/path/to/file.mp4'
    """
    if '[download] Destination:' in line:
        dest_match = re.search(r'\[download\] Destination: (.+)$', line)
        if dest_match:
            return dest_match.group(1).strip()
    return None


def parse_merger_output(line: str) -> Optional[str]:
    """
    Parse merged/extracted file path from yt-dlp output line.
    
    Args:
        line: Output line from yt-dlp
    
    Returns:
        File path or None if not found
    
    Example:
        >>> parse_merger_output('[Merger] Merging formats into "/path/to/file.mp4"')
        '/path/to/file.mp4'
    """
    if '[Merger]' in line or '[ExtractAudio]' in line:
        merger_match = re.search(r'["\']([^"\'
]+\.(mp4|mp3))["\']', line)
        if merger_match:
            return merger_match.group(1)
    return None


def parse_output_line(line: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Parse a single yt-dlp output line for progress and file path.
    
    Args:
        line: Output line from yt-dlp
    
    Returns:
        Tuple of (progress, file_path), either can be None
    """
    progress = parse_progress(line)
    file_path = parse_destination(line) or parse_merger_output(line)
    return progress, file_path
