import os
import shutil
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

save_path = os.environ.get('SAVE_PATH')
blueprint_path = os.environ.get('BLUEPRINT_PATH')
source_path = os.environ.get('SOURCE_PATH')

POLL_INTERVAL = float(os.environ.get('POLL_INTERVAL', '2.0'))
FILE_STABILITY_DELAY = float(os.environ.get('FILE_STABILITY_DELAY', '1.0'))

def file_is_factory_save(filename: str) -> bool:
    """Check if a file is a Satisfactory save file."""
    name, ext = os.path.splitext(filename)
    if ext == ".sav" and name.endswith("CALCULATOR"):
        return True
    return False

def file_is_factory_blueprint(filename: str) -> bool:
    """Check if a file is a Satisfactory blueprint file."""
    name, ext = os.path.splitext(filename)
    if ext == ".sbp" or ext == ".sbpcfg":
        return True
    return False

def is_file_ready(file_path: str) -> bool:
    """Check if a file is ready to be moved (not being written to)."""
    try:
        if not os.path.exists(file_path):
            return False
        
        current_time = time.time()
        mtime = os.path.getmtime(file_path)
        time_since_modification = current_time - mtime
        
        if time_since_modification < FILE_STABILITY_DELAY:
            return False
        
        try:
            with open(file_path, 'rb'):
                pass
            return True
        except (IOError, OSError, PermissionError) as e:
            logger.debug(f"File {os.path.basename(file_path)} is locked: {e}")
            return False
    except (OSError, PermissionError) as e:
        logger.debug(f"Error checking file {os.path.basename(file_path)}: {e}")
        return False

class FileProcessor:
    """Handles processing and moving files with caching."""
    
    def __init__(self):
        self.processed_cache = {}
        logger.info("FileProcessor initialized")
    
    def get_file_signature(self, file_path: str) -> tuple:
        """Get a unique signature for a file (mtime, size) to detect changes."""
        try:
            stat = os.stat(file_path)
            return (stat.st_mtime, stat.st_size)
        except (OSError, PermissionError) as e:
            logger.debug(f"Error getting file signature for {file_path}: {e}")
            return None
    
    def is_file_processed(self, file_path: str) -> bool:
        """Check if a file has already been processed (and hasn't changed)."""
        if file_path not in self.processed_cache:
            return False
        
        signature = self.get_file_signature(file_path)
        if signature is None:
            return False
        
        cached_signature = self.processed_cache[file_path]
        return signature == cached_signature
    
    def mark_file_processed(self, file_path: str):
        """Mark a file as processed in the cache."""
        signature = self.get_file_signature(file_path)
        if signature:
            self.processed_cache[file_path] = signature
            logger.debug(f"Marked file as processed: {os.path.basename(file_path)}")
    
    def process_file(self, file_path: str) -> bool:
        """Process a single file if it matches criteria and is ready.
        Returns True if file was processed, False otherwise.
        """
        filename = os.path.basename(file_path)
        
        if self.is_file_processed(file_path):
            logger.debug(f"Skipping already processed file: {filename}")
            return False
        
        is_save = file_is_factory_save(filename)
        is_blueprint = file_is_factory_blueprint(filename)
        
        if not (is_save or is_blueprint):
            return False
        
        logger.info(f"Found matching file: {filename} (type: {'save' if is_save else 'blueprint'})")
        
        if not is_file_ready(file_path):
            logger.debug(f"File not ready yet, will retry: {filename}")
            return False
        
        try:
            if is_save:
                dest = os.path.join(save_path, filename)
                file_type = "save"
            else:
                dest = os.path.join(blueprint_path, filename)
                file_type = "blueprint"
            
            logger.info(f"Moving {file_type} file: {filename} -> {dest}")
            try:
                shutil.move(file_path, dest)
            except OSError as e:
                if e.errno == 18:
                    logger.debug(f"Cross-device move detected, using copy+remove: {filename}")
                    shutil.copy2(file_path, dest)
                    os.remove(file_path)
                else:
                    raise
            logger.info(f"Successfully moved {file_type} file: {filename}")
            
            self.mark_file_processed(file_path)
            return True
            
        except Exception as e:
            logger.error(f"Error moving file {filename}: {e}", exc_info=True)
            return False
    
    def process_all_files(self):
        """Process all files in the source directory."""
        try:
            if not os.path.exists(source_path):
                logger.warning(f"Source path does not exist: {source_path}")
                return
            
            logger.debug(f"Scanning directory: {source_path}")
            entries = os.listdir(source_path)
            files_processed = 0
            files_skipped = 0
            files_not_ready = 0
            
            for entry in entries:
                file_path = os.path.join(source_path, entry)
                
                if not os.path.isfile(file_path):
                    continue
                
                if self.process_file(file_path):
                    files_processed += 1
                elif self.is_file_processed(file_path):
                    files_skipped += 1
                else:
                    filename = os.path.basename(file_path)
                    if file_is_factory_save(filename) or file_is_factory_blueprint(filename):
                        files_not_ready += 1
            
            if files_processed > 0 or files_not_ready > 0:
                logger.info(f"Scan complete: {files_processed} processed, {files_not_ready} waiting, {files_skipped} skipped")
            else:
                logger.debug(f"Scan complete: {files_processed} processed, {files_not_ready} waiting, {files_skipped} skipped")
                
        except Exception as e:
            logger.error(f"Error processing files: {e}", exc_info=True)

def main():
    logger.info("=" * 60)
    logger.info("Satisfactory File Mover - Starting")
    logger.info("=" * 60)
    logger.info(f"Source directory: {source_path}")
    logger.info(f"Save destination: {save_path}")
    logger.info(f"Blueprint destination: {blueprint_path}")
    logger.info(f"Poll interval: {POLL_INTERVAL} seconds")
    logger.info("=" * 60)
    
    processor = FileProcessor()
    
    logger.info("Processing existing files in source directory...")
    processor.process_all_files()
    
    logger.info(f"Starting polling loop (checking every {POLL_INTERVAL} seconds)...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            processor.process_all_files()
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
    finally:
        logger.info("Application stopped")

if __name__ == "__main__":
    main()