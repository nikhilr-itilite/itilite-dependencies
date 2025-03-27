from flight_helper_layer.mapping.lfs.priceline import mapping as pricelineflightmapping
from flight_helper_layer.service.json.enums import JsonVendor


LFS_INITIAL_TRANSFORM_MAPPING = {
    JsonVendor.PRICELINE: pricelineflightmapping,
    # Add more mappings as needed.
}
