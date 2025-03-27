# Flight Helper Layer Module

This module provides reusable functions that can be shared across multiple handlers.

## Changes Made
- **FlightTransformation for Priceline** has been shifted (remove this section in future versions).

## Guidelines
- Follow the base structure when adding new functions or features to this module.
- Do **not** expose functions directly. Instead, create a class to manage function access.

## Usage Example

```python
from service.flight_factory import FlightFactory

# Initialize flight factory
flight_factory = FlightFactory()

# Get the JSON type factory
json_factory = flight_factory.get_type("json")

# Get Priceline vendor from the JSON factory
priceline = json_factory.get_vendor("priceline")
