mapping = {
    "field_set": [
        {
            "from": "branding_data",
            "to": "branding_data",
            "add_to_cache": True,
            "action": {
                "action_type": "list_to_dict",
                "key": "name",
            },
        },
        {"from": "sid", "to": "search_id"},
        {
            "for_each": {
                "from": "itinerary_data",
                "to": "leg",
                "field_set": [
                    {
                        "from": "price_details.display_total_fare",
                        "to": "total_price",
                    },
                    {
                        "from": "price_details.display_total_fare_per_ticket",
                        "to": "total_price_per_ticket",
                    },
                    {
                        "from": "price_details.display_base_fare",
                        "to": "base_fare_per_ticket",
                    },
                    {
                        "from": "price_details.display_base_fare",
                        "to": "base_price",
                    },
                    {"from": "price_details.display_taxes", "to": "vendor_tax"},
                    {
                        "from": "price_details.display_currency",
                        "to": "display_currency",
                    },
                    {"from": "ppn_contract_bundle", "to": "ppn_contract_bundle"},
                    {"from": "ppn_return_bundle", "to": "ppn_return_bundle"},
                    {
                        "for_each": {
                            "from": "slice_data",
                            "to": "flight_details",
                            "field_set": [
                                {
                                    "from": "info.connection_count",
                                    "to": "connection_count",
                                },
                                {"from": "info.stop_count", "to": "stop_count"},
                                {
                                    "for_each": {
                                        "from": "flight_data",
                                        "to": "flight_data",
                                        "field_set": [
                                            {
                                                "from": "info.cabin_class",
                                                "to": "cabin_class",
                                            },
                                            {
                                                "from": "info.bkg_class",
                                                "to": "class_of_service",
                                            },
                                            {
                                                "from": "info.cabin_name",
                                                "to": "cabin_name",
                                            },
                                            {
                                                "from": "info.marketing_airline",
                                                "to": "carrier_name",
                                            },
                                            {
                                                "from": "info.marketing_airline_code",
                                                "to": "carrier_iata",
                                            },
                                            {
                                                "from": "info.operating_airline_code",
                                                "to": "operating_carrier_iata",
                                            },
                                            {
                                                "from": "info.operating_airline",
                                                "to": "operating_carrier_name",
                                            },
                                            {
                                                "from": "info.flight_number",  # TODO: carrier data ?
                                                "to": "carrier_id",
                                            },
                                            {
                                                "from": "arrival.datetime.date_time",
                                                "to": "arrival_time",  # TODO: datetime conversion ?
                                            },
                                            {
                                                "from": "departure.datetime.date_time",
                                                "to": "departure_time",  # TODO: datetime conversion ?
                                            },
                                            {"from": "info.duration", "to": "duration"},
                                            {
                                                "from": "departure.airport.code",
                                                "to": "departure_airport_code",
                                            },
                                            {
                                                "from": "arrival.airport.code",
                                                "to": "arrival_airport_code",
                                            },
                                            {
                                                "from": "arrival.airport.name",
                                                "to": "origin_terminal",
                                            },
                                            {
                                                "from": "departure.airport.name",
                                                "to": "destination_terminal",
                                            },
                                            {
                                                "from": "baggage_allowances",
                                                "to": "baggage_allowances",
                                            },
                                        ],
                                    }
                                },
                            ],
                        },
                    },
                ],
            }
        },
    ]
}
