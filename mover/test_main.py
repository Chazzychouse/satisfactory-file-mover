import unittest
import shutil
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from mover.main import (
    file_is_factory_save,
    file_is_factory_blueprint,
    is_file_ready,
    FileProcessor
)


class TestFileDetection(unittest.TestCase):
    """Tests for file type detection functions."""
    
    def test_file_is_factory_save_valid_cases(self):
        """Test valid save file names."""
        self.assertTrue(file_is_factory_save('testCALCULATOR.sav'))
        self.assertTrue(file_is_factory_save('MySaveCALCULATOR.sav'))
        self.assertTrue(file_is_factory_save('123CALCULATOR.sav'))
        self.assertTrue(file_is_factory_save('CALCULATOR.sav'))
        self.assertTrue(file_is_factory_save('path/to/fileCALCULATOR.sav'))
    
    def test_file_is_factory_save_invalid_cases(self):
        """Test invalid save file names."""
        self.assertFalse(file_is_factory_save('test.sav'))
        self.assertFalse(file_is_factory_save('testCALCULATOR.txt'))
        self.assertFalse(file_is_factory_save('testcalculator.sav'))  # case sensitive
        self.assertFalse(file_is_factory_save('testCALCULATOR'))
        self.assertFalse(file_is_factory_save('.sav'))
        self.assertFalse(file_is_factory_save('CALCULATOR.sav.bak'))
        self.assertFalse(file_is_factory_save('testCALCULATOR.sav.backup'))
    
    def test_file_is_factory_save_edge_cases(self):
        """Test edge cases for save file detection."""
        self.assertFalse(file_is_factory_save(''))
        self.assertFalse(file_is_factory_save('CALCULATOR'))
        self.assertFalse(file_is_factory_save('testCALCULATOR.sav.old'))
        self.assertFalse(file_is_factory_save('testCALCULATOR.SAV'))  # uppercase extension
        self.assertFalse(file_is_factory_save('testCALCULATOR.sav '))  # trailing space in extension
        self.assertTrue(file_is_factory_save(' testCALCULATOR.sav'))  # leading space in name
    
    def test_file_is_factory_blueprint_valid_cases(self):
        """Test valid blueprint file names."""
        self.assertTrue(file_is_factory_blueprint('blueprint.sbp'))
        self.assertTrue(file_is_factory_blueprint('blueprint.sbpcfg'))
        self.assertTrue(file_is_factory_blueprint('MyBlueprint.sbp'))
        self.assertTrue(file_is_factory_blueprint('test123.sbpcfg'))
        self.assertTrue(file_is_factory_blueprint('path/to/file.sbp'))
        self.assertTrue(file_is_factory_blueprint('file with spaces.sbp'))
    
    def test_file_is_factory_blueprint_invalid_cases(self):
        """Test invalid blueprint file names."""
        self.assertFalse(file_is_factory_blueprint('blueprint.sav'))
        self.assertFalse(file_is_factory_blueprint('blueprint.txt'))
        self.assertFalse(file_is_factory_blueprint('blueprint.sbp.backup'))
        self.assertFalse(file_is_factory_blueprint('blueprint.sbpcfg.old'))
        self.assertFalse(file_is_factory_blueprint('blueprint'))
        self.assertFalse(file_is_factory_blueprint('.sbp'))
    
    def test_file_is_factory_blueprint_edge_cases(self):
        """Test edge cases for blueprint file detection."""
        self.assertFalse(file_is_factory_blueprint(''))
        self.assertFalse(file_is_factory_blueprint('blueprint.SBP'))  # uppercase extension
        self.assertFalse(file_is_factory_blueprint('blueprint.SBPCFG'))  # uppercase extension
        self.assertFalse(file_is_factory_blueprint('blueprint.sbp '))  # trailing space in extension
        self.assertTrue(file_is_factory_blueprint(' blueprint.sbp'))  # leading space in name


class TestIsFileReady(unittest.TestCase):
    """Tests for is_file_ready function."""
    
    @patch('src.main.os.path.exists')
    @patch('src.main.os.path.getmtime')
    @patch('src.main.time.time')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.main.FILE_STABILITY_DELAY', 1.0)
    def test_is_file_ready_file_not_exists(self, mock_file, mock_time, mock_mtime, mock_exists):
        """Test when file doesn't exist."""
        mock_exists.return_value = False
        self.assertFalse(is_file_ready('/path/to/file.sav'))
    
    @patch('src.main.os.path.exists')
    @patch('src.main.os.path.getmtime')
    @patch('src.main.time.time')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.main.FILE_STABILITY_DELAY', 1.0)
    def test_is_file_ready_file_too_recent(self, mock_file, mock_time, mock_mtime, mock_exists):
        """Test when file was modified too recently."""
        mock_exists.return_value = True
        mock_time.return_value = 100.0
        mock_mtime.return_value = 99.5
        self.assertFalse(is_file_ready('/path/to/file.sav'))
    
    @patch('src.main.os.path.exists')
    @patch('src.main.os.path.getmtime')
    @patch('src.main.time.time')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.main.FILE_STABILITY_DELAY', 1.0)
    def test_is_file_ready_file_stable(self, mock_file, mock_time, mock_mtime, mock_exists):
        """Test when file is stable and ready."""
        mock_exists.return_value = True
        mock_time.return_value = 100.0
        mock_mtime.return_value = 98.0
        self.assertTrue(is_file_ready('/path/to/file.sav'))
        mock_file.assert_called_once_with('/path/to/file.sav', 'rb')
    
    @patch('src.main.os.path.exists')
    @patch('src.main.os.path.getmtime')
    @patch('src.main.time.time')
    @patch('builtins.open', side_effect=PermissionError("File is locked"))
    @patch('src.main.FILE_STABILITY_DELAY', 1.0)
    def test_is_file_ready_file_locked(self, mock_file, mock_time, mock_mtime, mock_exists):
        """Test when file is locked."""
        mock_exists.return_value = True
        mock_time.return_value = 100.0
        mock_mtime.return_value = 98.0
        self.assertFalse(is_file_ready('/path/to/file.sav'))
    
    @patch('src.main.os.path.exists')
    @patch('src.main.os.path.getmtime', side_effect=OSError("Permission denied"))
    @patch('src.main.FILE_STABILITY_DELAY', 1.0)
    def test_is_file_ready_permission_error(self, mock_mtime, mock_exists):
        """Test when there's a permission error."""
        mock_exists.return_value = True
        self.assertFalse(is_file_ready('/path/to/file.sav'))


class TestFileProcessor(unittest.TestCase):
    """Tests for FileProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = FileProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.main.os.stat')
    def test_get_file_signature_success(self, mock_stat):
        """Test getting file signature successfully."""
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = 1234567890.0
        mock_stat_result.st_size = 1024
        mock_stat.return_value = mock_stat_result
        
        signature = self.processor.get_file_signature('/path/to/file.sav')
        self.assertEqual(signature, (1234567890.0, 1024))
    
    @patch('src.main.os.stat', side_effect=OSError("File not found"))
    def test_get_file_signature_error(self, mock_stat):
        """Test getting file signature when file doesn't exist."""
        signature = self.processor.get_file_signature('/path/to/nonexistent.sav')
        self.assertIsNone(signature)
    
    @patch('src.main.os.stat')
    def test_is_file_processed_not_in_cache(self, mock_stat):
        """Test checking if file is processed when not in cache."""
        file_path = '/path/to/file.sav'
        self.assertFalse(self.processor.is_file_processed(file_path))
    
    @patch('src.main.os.stat')
    def test_is_file_processed_in_cache_matching(self, mock_stat):
        """Test checking if file is processed when signature matches."""
        file_path = '/path/to/file.sav'
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = 1234567890.0
        mock_stat_result.st_size = 1024
        mock_stat.return_value = mock_stat_result
        
        self.processor.mark_file_processed(file_path)
        
        self.assertTrue(self.processor.is_file_processed(file_path))
    
    @patch('src.main.os.stat')
    def test_is_file_processed_in_cache_changed(self, mock_stat):
        """Test checking if file is processed when file has changed."""
        file_path = '/path/to/file.sav'
        
        mock_stat_result1 = MagicMock()
        mock_stat_result1.st_mtime = 1234567890.0
        mock_stat_result1.st_size = 1024
        mock_stat.return_value = mock_stat_result1
        self.processor.mark_file_processed(file_path)
        
        mock_stat_result2 = MagicMock()
        mock_stat_result2.st_mtime = 1234567890.0
        mock_stat_result2.st_size = 2048
        mock_stat.return_value = mock_stat_result2
        
        self.assertFalse(self.processor.is_file_processed(file_path))
    
    @patch('src.main.os.stat', side_effect=OSError("File not found"))
    def test_is_file_processed_signature_error(self, mock_stat):
        """Test checking if file is processed when signature can't be retrieved."""
        file_path = '/path/to/file.sav'
        self.processor.processed_cache[file_path] = (1234567890.0, 1024)
        
        self.assertFalse(self.processor.is_file_processed(file_path))
    
    @patch('src.main.os.stat')
    def test_mark_file_processed(self, mock_stat):
        """Test marking a file as processed."""
        file_path = '/path/to/file.sav'
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = 1234567890.0
        mock_stat_result.st_size = 1024
        mock_stat.return_value = mock_stat_result
        
        self.processor.mark_file_processed(file_path)
        self.assertIn(file_path, self.processor.processed_cache)
        self.assertEqual(self.processor.processed_cache[file_path], (1234567890.0, 1024))
    
    @patch('src.main.os.stat', side_effect=OSError("File not found"))
    def test_mark_file_processed_error(self, mock_stat):
        """Test marking file as processed when file doesn't exist."""
        file_path = '/path/to/nonexistent.sav'
        self.processor.mark_file_processed(file_path)
        self.assertNotIn(file_path, self.processor.processed_cache)
    
    @patch('src.main.is_file_ready', return_value=True)
    @patch('src.main.shutil.move')
    @patch('src.main.os.path.join')
    @patch('src.main.os.path.basename')
    @patch('src.main.os.stat')
    @patch('src.main.save_path', '/dest/saves')
    def test_process_file_save_success(self, mock_stat, mock_basename, mock_join, mock_move, mock_ready):
        """Test successfully processing a save file."""
        file_path = '/source/testCALCULATOR.sav'
        mock_basename.return_value = 'testCALCULATOR.sav'
        mock_join.return_value = '/dest/saves/testCALCULATOR.sav'
        
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = 1234567890.0
        mock_stat_result.st_size = 1024
        mock_stat.return_value = mock_stat_result
        
        result = self.processor.process_file(file_path)
        self.assertTrue(result)
        mock_move.assert_called_once()
        self.assertTrue(self.processor.is_file_processed(file_path))
    
    @patch('src.main.is_file_ready', return_value=True)
    @patch('src.main.shutil.move')
    @patch('src.main.os.path.join')
    @patch('src.main.os.path.basename')
    @patch('src.main.blueprint_path', '/dest/blueprints')
    def test_process_file_blueprint_success(self, mock_basename, mock_join, mock_move, mock_ready):
        """Test successfully processing a blueprint file."""
        file_path = '/source/blueprint.sbp'
        mock_basename.return_value = 'blueprint.sbp'
        mock_join.return_value = '/dest/blueprints/blueprint.sbp'
        
        result = self.processor.process_file(file_path)
        self.assertTrue(result)
        mock_move.assert_called_once()
    
    @patch('src.main.os.path.basename')
    def test_process_file_not_matching(self, mock_basename):
        """Test processing a file that doesn't match criteria."""
        file_path = '/source/random.txt'
        mock_basename.return_value = 'random.txt'
        
        result = self.processor.process_file(file_path)
        self.assertFalse(result)
    
    @patch('src.main.is_file_ready', return_value=False)
    @patch('src.main.os.path.basename')
    def test_process_file_not_ready(self, mock_basename, mock_ready):
        """Test processing a file that's not ready yet."""
        file_path = '/source/testCALCULATOR.sav'
        mock_basename.return_value = 'testCALCULATOR.sav'
        
        result = self.processor.process_file(file_path)
        self.assertFalse(result)
    
    @patch('src.main.is_file_ready', return_value=True)
    @patch('src.main.shutil.move')
    @patch('src.main.os.path.join')
    @patch('src.main.os.path.basename')
    @patch('src.main.os.stat')
    @patch('src.main.save_path', '/dest/saves')
    def test_process_file_already_processed(self, mock_stat, mock_basename, mock_join, mock_move, mock_ready):
        """Test processing a file that's already been processed."""
        file_path = '/source/testCALCULATOR.sav'
        mock_basename.return_value = 'testCALCULATOR.sav'
        mock_join.return_value = '/dest/saves/testCALCULATOR.sav'
        
        # Mock file signature (same for both calls)
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = 1234567890.0
        mock_stat_result.st_size = 1024
        mock_stat.return_value = mock_stat_result
        
        self.processor.process_file(file_path)
        
        result = self.processor.process_file(file_path)
        self.assertFalse(result)
        self.assertEqual(mock_move.call_count, 1)
    
    @patch('src.main.is_file_ready', return_value=True)
    @patch('src.main.shutil.move', side_effect=OSError(18, "Cross-device link"))
    @patch('src.main.shutil.copy2')
    @patch('src.main.os.remove')
    @patch('src.main.os.path.join')
    @patch('src.main.os.path.basename')
    @patch('src.main.save_path', '/dest/saves')
    def test_process_file_cross_device_move(self, mock_basename, mock_join, mock_remove, 
                                            mock_copy2, mock_move, mock_ready):
        """Test processing a file that requires cross-device move."""
        file_path = '/source/testCALCULATOR.sav'
        mock_basename.return_value = 'testCALCULATOR.sav'
        mock_join.return_value = '/dest/saves/testCALCULATOR.sav'
        
        result = self.processor.process_file(file_path)
        self.assertTrue(result)
        mock_move.assert_called_once()
        mock_copy2.assert_called_once()
        mock_remove.assert_called_once_with(file_path)
    
    @patch('src.main.is_file_ready', return_value=True)
    @patch('src.main.shutil.move', side_effect=OSError(13, "Permission denied"))
    @patch('src.main.os.path.join')
    @patch('src.main.os.path.basename')
    @patch('src.main.save_path', '/dest/saves')
    def test_process_file_move_error(self, mock_basename, mock_join, mock_move, mock_ready):
        """Test processing a file when move fails."""
        file_path = '/source/testCALCULATOR.sav'
        mock_basename.return_value = 'testCALCULATOR.sav'
        mock_join.return_value = '/dest/saves/testCALCULATOR.sav'
        
        result = self.processor.process_file(file_path)
        self.assertFalse(result)
    
    @patch('src.main.os.path.exists', return_value=False)
    @patch('src.main.source_path', '/nonexistent/path')
    def test_process_all_files_source_not_exists(self, mock_exists):
        """Test processing when source path doesn't exist."""
        self.processor.process_all_files()
    
    @patch('src.main.os.listdir')
    @patch('src.main.os.path.exists', return_value=True)
    @patch('src.main.os.path.isfile')
    @patch('src.main.os.path.join')
    @patch('src.main.source_path', '/source')
    def test_process_all_files_with_files(self, mock_join, mock_isfile, mock_exists, mock_listdir):
        """Test processing all files in directory."""
        mock_listdir.return_value = ['file1.sav', 'file2.sbp', 'file3.txt']
        mock_isfile.side_effect = lambda x: x.endswith(('.sav', '.sbp', '.txt'))
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        with patch.object(self.processor, 'process_file', return_value=False) as mock_process:
            self.processor.process_all_files()
            self.assertEqual(mock_process.call_count, 3)


if __name__ == '__main__':
    unittest.main()
