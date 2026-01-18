#conftest.py
import sys
from pathlib import Path


# Dodaje katalog główny projektu do sys.path
# dzięki temu testy w folderze "tests" mogą importować moduły
# z serwisów (service_a, service_b, worker, detector_yolo)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)
