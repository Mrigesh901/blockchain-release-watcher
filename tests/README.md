# Tests Directory

This directory contains test and demonstration files for the blockchain release monitor.

## Test Files

- **test_ai_manual.py** - Manual testing of Gemini AI analysis
- **test_config.py** - Configuration validation tests
- **test_gitlab.py** - GitLab API integration tests
- **test_notifications.py** - Email and Slack notification tests
- **test_optimism_monitoring.py** - Optimism repository monitoring tests
- **test_tag_filters.py** - Tag filtering functionality tests
- **test_unified_service.py** - Unified repository service tests

## Demo Files

- **demo_tag_filtering.py** - Interactive demonstration of tag filtering
- **verify_filter_behavior.py** - Verification script for filter behavior

## Running Tests

From the project root directory:

```bash
# Run a specific test
python3 tests/test_config.py

# Run all tests
for test in tests/test_*.py; do python3 "$test"; done
```

Make sure your virtual environment is activated and all dependencies are installed before running tests.
