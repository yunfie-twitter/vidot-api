import os
import subprocess
import logging
from typing import List
import re
from rq import get_current_job

from app.config import settings

logger = logging.getLogger(__name__)


def update_progress(progress: float) -> None:
    """Update job progress in Redis."""
    try:
        job = get_current_job()
        if job:
            job.meta['progress'] = progress
            job.save_meta()
    except Exception as e:
        logger.warning(f"Failed to update progress: {str(e)}")


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
    cmd: List[str] = [
        settings.ytdlp_path,
        '--no-playlist',
        '--no-warnings',
        '--progress',
        '--newline',
        '-o', output_template
    ]
    
    if format == 'mp3':
        cmd.extend([
            '-x',
            '--audio-format', 'mp3',
            '--audio-quality', '0'
        ])
    else:  # mp4
        cmd.extend([
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4'
        ])
    
    cmd.append(url)
    
    logger.info(f"Executing command: {' '.join(cmd)}")
    
    try:
        # Execute yt-dlp with subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        output_file = None
        
        # Parse output for progress and filename
        for line in process.stdout:
            logger.debug(line.strip())
            
            # Parse progress: [download]  45.2% of 10.5MiB at 1.2MiB/s ETA 00:05
            progress_match = re.search(r'\[download\]\s+(\d+\.?\d*)%', line)
            if progress_match:
                progress = float(progress_match.group(1))
                update_progress(progress)
                logger.info(f"Download progress: {progress}%")
            
            # Parse destination: [download] Destination: /path/to/file.mp4
            if '[download] Destination:' in line:
                dest_match = re.search(r'\[download\] Destination: (.+)$', line)
                if dest_match:
                    output_file = dest_match.group(1).strip()
            
            # Parse merger output: [Merger] Merging formats into "/path/to/file.mp4"
            if '[Merger]' in line or '[ExtractAudio]' in line:
                merger_match = re.search(r'["\']([^"\'
]+\.(mp4|mp3))["\']', line)
                if merger_match:
                    output_file = merger_match.group(1)
        
        # Wait for process to complete
        return_code = process.wait()
        
        if return_code != 0:
            raise RuntimeError(f"yt-dlp exited with code {return_code}")
        
        # If we couldn't parse the output file, try to find it
        if not output_file:
            # List files in download directory
            files = [f for f in os.listdir(settings.download_dir) 
                    if f.endswith(('.mp4', '.mp3'))]
            if files:
                # Get the most recently modified file
                files.sort(key=lambda x: os.path.getmtime(
                    os.path.join(settings.download_dir, x)
                ), reverse=True)
                output_file = os.path.join(settings.download_dir, files[0])
            else:
                raise RuntimeError("Could not find downloaded file")
        
        # Verify file exists
        if not os.path.exists(output_file):
            raise RuntimeError(f"Downloaded file not found: {output_file}")
        
        update_progress(100.0)
        logger.info(f"Download completed: {output_file}")
        
        return output_file
    
    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess error: {str(e)}")
        raise RuntimeError(f"Download failed: {str(e)}")
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise RuntimeError(f"Download failed: {str(e)}")
