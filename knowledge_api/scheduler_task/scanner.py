"""timed task scanner

Automatically scan and import all Python modules in the timed task directory to ensure that the decorator can register all tasks"""
import importlib
import importlib.util
import inspect
import logging
import os
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import List, Set, Optional

logger = logging.getLogger(__name__)

# Imported module collection
imported_modules: Set[str] = set()


def import_module_from_file(module_path: str, module_name: Optional[str] = None) -> Optional[ModuleType]:
    """Import modules from file path

@Param module_path: module file path
@Param module_name: module name, generated from path if None
@Return: Imported module or None"""
    try:
        if module_name is None:
            module_name = os.path.splitext(os.path.basename(module_path))[0]
        
        # Check if it has been imported
        if module_name in imported_modules:
            return importlib.import_module(module_name)
        
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            logger.error(f"无法为文件创建模块规范: {module_path}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        imported_modules.add(module_name)
        return module
    except Exception as e:
        logger.error(f"导入模块失败 {module_path}: {e}")
        return None


def import_submodules(package_name: str) -> List[ModuleType]:
    """Import all submodules in the package

@Param package_name: package name
@Return: List of imported modules"""
    modules = []
    try:
        package = importlib.import_module(package_name)
        for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
            if is_pkg:
                # Recursive import of subpackages
                modules.extend(import_submodules(name))
            else:
                # import module
                try:
                    module = importlib.import_module(name)
                    modules.append(module)
                    imported_modules.add(name)
                except Exception as e:
                    logger.error(f"导入模块失败 {name}: {e}")
    except Exception as e:
        logger.error(f"导入包失败 {package_name}: {e}")
    
    return modules


def scan_directory(directory: str) -> List[ModuleType]:
    """Scan the directory and import all Python modules

@Param directory: directory path to scan
@Return: List of imported modules"""
    modules = []
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        logger.warning(f"目录不存在或不是一个目录: {directory}")
        return modules
    
    # Process all Python files
    for file_path in dir_path.glob("*.py"):
        if file_path.name.startswith("_"):
            continue
            
        module = import_module_from_file(str(file_path))
        if module:
            modules.append(module)
    
    # Process all subdirectories
    for subdir in dir_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("_"):
            # Check if there is a __init__ .py file
            init_file = subdir / "__init__.py"
            if init_file.exists():
                # Try importing as a package
                package_name = f"{dir_path.name}.{subdir.name}"
                modules.extend(import_submodules(package_name))
            else:
                # Recursive scan as a normal directory
                modules.extend(scan_directory(str(subdir)))
    
    return modules


def scan_tasks() -> None:
    """Scan and import all timed task modules"""
    # Get scheduler_task directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Import example_tasks.py
    scan_directory(current_dir)
    
    logger.info(f"定时任务扫描完成，共导入了 {len(imported_modules)} 个模块") 