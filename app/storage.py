"""
Simple case persistence layer using JSON files.
For production, replace with proper database (PostgreSQL, MongoDB, etc.).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class CaseStorage:
    """Simple JSON-based case storage for persistence."""

    def __init__(self, storage_dir: str = "data/cases"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"
        self._load_index()

    def _load_index(self):
        """Load case index from disk."""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {}

    def _save_index(self):
        """Save case index to disk."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def save_case(self, case_id: str, case_data: Dict[str, Any]) -> bool:
        """Save a case to disk."""
        try:
            case_file = self.storage_dir / f"{case_id}.json"

            # Add metadata
            case_data["_stored_at"] = datetime.now().isoformat()
            case_data["_storage_version"] = "1.0"

            # Save case file
            with open(case_file, 'w') as f:
                json.dump(case_data, f, indent=2, default=str)

            # Update index
            self.index[case_id] = {
                "file": str(case_file),
                "applicant_id": case_data.get("application_data", {}).get("applicant_id"),
                "classification": case_data.get("classification"),
                "timestamp": case_data.get("timestamp"),
                "stored_at": case_data["_stored_at"],
            }
            self._save_index()

            return True
        except Exception as e:
            print(f"Error saving case {case_id}: {e}")
            return False

    def load_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Load a case from disk."""
        try:
            if case_id not in self.index:
                return None

            case_file = Path(self.index[case_id]["file"])
            if not case_file.exists():
                return None

            with open(case_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading case {case_id}: {e}")
            return None

    def list_cases(self, limit: int = 100) -> list:
        """List all cases."""
        cases = []
        for case_id, info in sorted(self.index.items(), key=lambda x: x[1].get("timestamp", ""), reverse=True)[:limit]:
            cases.append({
                "case_id": case_id,
                **info,
            })
        return cases

    def case_exists(self, case_id: str) -> bool:
        """Check if a case exists."""
        return case_id in self.index

    def delete_case(self, case_id: str) -> bool:
        """Delete a case from disk."""
        try:
            if case_id in self.index:
                case_file = Path(self.index[case_id]["file"])
                if case_file.exists():
                    case_file.unlink()
                del self.index[case_id]
                self._save_index()
                return True
            return False
        except Exception as e:
            print(f"Error deleting case {case_id}: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_cases = len(self.index)
        classifications = {}
        for info in self.index.values():
            classification = info.get("classification", "UNKNOWN")
            classifications[classification] = classifications.get(classification, 0) + 1

        return {
            "total_cases": total_cases,
            "by_classification": classifications,
            "storage_dir": str(self.storage_dir),
            "index_file": str(self.index_file),
        }


# Global storage instance
_storage: Optional[CaseStorage] = None


def get_storage() -> CaseStorage:
    """Get or create the global storage instance."""
    global _storage
    if _storage is None:
        _storage = CaseStorage()
    return _storage


def init_storage(storage_dir: str = "data/cases"):
    """Initialize storage with custom directory."""
    global _storage
    _storage = CaseStorage(storage_dir)
    return _storage
