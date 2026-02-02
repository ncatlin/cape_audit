from typing import List, Union, Dict, Any, Optional
import json
import re


class MissingResultVerifier:
    def evaluate(self, report: Dict[str, Any], report_string: str, test_storage_directory: str) -> bool:
        raise Exception("No verifier was attached to this objective")


class VerifyReportSectionHasContent:
    def __init__(
        self, 
        path: str
    ):
        self.path = path  # e.g., "behavior/processes/calls"
        
    def evaluate(self, report: Dict[str, Any], report_string: str, test_storage_directory: str) -> bool:
        innerVerifier = VerifyReportSectionHasMatching(self.path, None)
        return innerVerifier.has_content(report)


class VerifyReportSectionHasMatching:
    '''
    Checks report.json for a dict with matching prop:value pairs
    '''
    def __init__(
        self, 
        path: str, 
        match_criteria: Dict[str, Any] | None,
        values_are_regexes: bool = False
    ):
        self.path = path  # e.g., "behavior/processes/calls"
        self.match_criteria = match_criteria
        self.is_regexes = values_are_regexes

    def has_content(self, report) -> bool:
        targets = self._resolve_path(report, self.path)
        if targets:
            return True
        else:
            return False

    def evaluate(self, report: Dict[str, Any], report_string: str, test_storage_directory: str) -> bool:
        """
        Returns (bool, message) based on whether the criteria were met.
        """
        # 1. Resolve the path to get the list of items (processes or calls)
        targets = self._resolve_path(report, self.path)
        
        if not isinstance(targets, list):
            # If the result is a single dict, wrap it in a list so we can iterate
            targets = [targets] if targets else []

        if self.match_criteria is None:
            return True
        
        match_count_target = len(self.match_criteria) 
        for target in targets:
            match_count = 0
            for crit_path, expected_val in self.match_criteria.items():
                # For each criteria, resolve the path RELATIVE to the target
                found_vals = self._resolve_path(target, crit_path)
                
                # If resolve_path found the value (even inside a nested list)
                if self._verify_value(found_vals, expected_val):
                    match_count += 1
                    if match_count >= match_count_target:
                        return True
        return False

    def _resolve_path(self, data: Any, path: str) -> Any:
        """
        Recursively descends into data. 
        If it hits a list, it flattens the results from all items in that list.
        """
        keys = path.split('/')
        current = data

        for i, key in enumerate(keys):
            if isinstance(current, list):
                # List of dicts, so we have to check the path of every item
                remaining_path = "/".join(keys[i:])
                results = []
                for item in current:
                    res = self._resolve_path(item, remaining_path)
                    if isinstance(res, list):
                        results.extend(res)
                    elif res is not None:
                        results.append(res)
                return results
            
            if not isinstance(current, dict):
                return None
            current = current.get(key)

        return current

    def _verify_value(self, found: Any, expected: Any) -> bool:
        """Checks if expected value exists in found (handles single values or lists)"""

        found_list = found if isinstance(found, list) else [found]
        if self.is_regexes:
            pattern = re.compile(expected)
            return any(pattern.search(str(v)) for v in found_list)
        
        if isinstance(found, list):
            return any(str(v) == str(expected) for v in found)
        return str(found) == str(expected)
    

class VerifyReportHasExactString:
    def __init__(
        self, 
        pattern: str
    ):
        self.pattern = pattern
        
    def evaluate(self, report: Dict[str, Any], report_string: str, test_storage_directory: str) -> bool:
        return self.pattern in report_string

class VerifyReportHasPattern:
    def __init__(
        self, 
        pattern: re.Pattern
    ):
        self.pattern = pattern  # e.g., "behavior/processes/calls"
        
    def evaluate(self, report: Dict[str, Any], report_string: str, test_storage_directory: str) -> bool:
        if self.pattern.search(report_string) != None:
            return True
        return False

