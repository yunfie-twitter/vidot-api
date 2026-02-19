"""Main download logic using yt-dlp."""

import os
import subprocess
import logging
from typing import List

from app.config import settings
from app.worker.progress import update_progress
from app.worker.parser import parse_output_line

logger = logging.getLogger(__name__)


def build_ytdlp_command(url: str, format: str, output_template: str) -> List[str]:
    """
    Build yt-dlp command arguments.
    
    Args:
        url: Video URL to download
        format: Output format (mp4 or mp3)
        output_template: Output file path template
    
    Returns:
        List of command arguments
    """
    cmd: List[str] = [
        settings.ytdlp_path,
        '--no-playlist',
        '--progress',
        '--newline',
        '-o', output_template,
    ]
    
    if format == 'mp3':
        cmd.extend([
            '-x',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
        ])
    else:  # mp4
        cmd.extend([
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
        ])
    
    cmd.append(url)
    return cmd


def find_latest_file(directory: str, extensions: tuple = ('.mp4', '.mp3')) -> str:
    """
    Find the most recently modified file in directory.
    
    Args:
        directory: Directory to search
        extensions: File extensions to filter
    
    Returns:
        Full path to the most recent file
    
    Raises:
        RuntimeError: If no file found
    """
    files = [f for f in os.listdir(directory) if f.endswith(extensions)]
    if not files:
        raise RuntimeError("Could not find downloaded file")
    
    files.sort(
        key=lambda x: os.path.getmtime(os.path.join(directory, x)),
        reverse=True
    )
    return os.path.join(directory, files[0])


def download_video(url: str, format: str) -> str:
    """
    Download video using yt-dlp.
    
    Args:
        url: Video URL to download
        format: Output format (mp4 or mp3)
    
    Returns:
        Path to downloaded file
    
    Raises:
        RuntimeError: If download fails
    """
    logger.info(f"Starting download: {url} (format: {format})")
    update_progress(0.0)
    
    # Ensure download directory exists
    os.makedirs(settings.download_dir, exist_ok=True)
    
    # Build output template
    output_template = os.path.join(
        settings.download_dir,
        '%(title)s.%(ext)s'
    )
    
    # Build yt-dlp command
    cmd = build_ytdlp_command(url, format, output_template)
    logger.info(f"Executing command: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        output_file = None
        
        # Process output line by line
        for line in process.stdout:
            logger.debug(line.strip())
            
            progress, file_path = parse_output_line(line)
            
            if progress is not None:
                update_progress(progress)
                logger.info(f"Download progress: {progress}%")
            
            if file_path is not None:
                output_file = file_path
        
        # Wait for process to complete
        return_code = process.wait()
        if return_code != 0:
            raise RuntimeError(f"yt-dlp failed with return code {return_code}")
        
        # If we couldn't parse the output file, try to find it
        if not output_file:
            output_file = find_latest_file(settings.download_dir)
        
        # Verify file exists
        if not os.path.exists(output_file):
            raise RuntimeError(f"Downloaded file not found: {output_file}")
        
        update_progress(100.0)
        logger.info(f"Download completed: {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise RuntimeError(f"Download failed: {str(e)}")
