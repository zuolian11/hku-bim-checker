"""
Tests for the compliance checker rules.
"""
import pytest
import sys
sys.path.insert(0, ".")
from checker import check_door_width, check_fire_rating, RuleResult
from ai_rule_gen import parse_regulation


class TestDoorWidth:
    def test_parse_basic(self):
        rules = parse_regulation("doors at least 900mm wide")
        assert len(rules) == 1
        assert rules[0]["target"] == "IfcDoor"
        assert rules[0]["property"] == "OverallWidth"
        assert rules[0]["value"] == 900

    def test_parse_egress(self):
        rules = parse_regulation("egress doors at least 1000mm")
        assert rules[0]["value"] == 1000
        assert rules[0]["scope"] == "egress"

    def test_parse_fire_rating(self):
        rules = parse_regulation("walls must have FireRating")
        assert rules[0]["property"] == "FireRating"
        assert rules[0]["condition"] == "exists"

    def test_parse_unknown(self):
        rules = parse_regulation("xyz abc def")
        assert rules == [] or rules[0]["condition"] == "parse_failed"


class TestRuleResult:
    def test_empty_rule(self):
        r = RuleResult("test", "desc")
        assert r.passed == 0
        assert r.failed == 0
        assert r.warnings == 0
        assert r.items == []

    def test_rule_with_items(self):
        r = RuleResult("test", "desc")
        r.items.append({"status": "fail", "message": "bad"})
        r.failed += 1
        assert r.failed == 1


class TestEdgeCases:
    def test_empty_regulation(self):
        rules = parse_regulation("")
        assert rules == []

    def test_missing_number(self):
        rules = parse_regulation("doors must be wide")
        assert rules == [] or ("parse_failed" in str(rules))

    def test_chinese(self):
        rules = parse_regulation("疏散门宽度不小于1000毫米")
        assert len(rules) >= 1
