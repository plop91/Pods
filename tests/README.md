# Pods Unit Tests

This directory contains unit tests for the Pods application.

## Test Coverage

### test_pod.py
Tests for the `Pod` class (src/pod.py):
- Pod creation with default and custom parameters
- Unique ID generation
- Child pod management (add, remove)
- Coordinate and bounds calculations
- Point containment checks
- Movement operations
- Serialization/deserialization (to_dict, from_dict)
- Visual properties
- Description properties

**Total: 28 test cases**

### test_relationship.py
Tests for the `Relationship` class (src/relationship.py):
- Relationship creation with default and custom parameters
- Unique ID generation
- Endpoint calculations
- External relationship detection
- Serialization/deserialization (to_dict, from_dict)
- Visual properties
- Description properties

**Total: 16 test cases**

### test_app.py
Tests for the `PodsApp` class (src/app.py):
- Point-to-line distance calculations (for relationship selection)
- Pod lookup dictionary building
- Pod hierarchy operations
- Relationship serialization with complex graphs

**Total: 9 test cases**

## Running Tests

### Run all tests:
```bash
python -m unittest discover tests -v
```

### Run a specific test file:
```bash
python -m unittest tests.test_pod -v
```

### Run a specific test class:
```bash
python -m unittest tests.test_pod.TestPod -v
```

### Run a specific test method:
```bash
python -m unittest tests.test_pod.TestPod.test_pod_creation -v
```

## Test Statistics

- **Total Test Cases:** 44
- **Test Files:** 3
- **Test Classes:** 8
- **All Tests Passing:** ✓

## Notes

- Tests use Python's built-in `unittest` framework (no external dependencies required)
- GUI-related tests are minimal since the app is heavily GUI-based
- Focus is on testing data models (Pod, Relationship) and non-GUI helper methods
- All tests should run quickly (< 1 second total execution time)
