from odmantic import Field, Model, EmbeddedModel
from typing import Optional, List
from datetime import datetime
from bson.objectid import ObjectId


class LocationDetail(EmbeddedModel):
    country: Optional[str]
    continent: Optional[str]
    region: Optional[str]
    sub_region: Optional[str]
    political_locality: Optional[str]
    city: Optional[str]
    name: Optional[str]
    lat: float
    lng: float
    country_short_name: Optional[str]


class FarePreferenceGroup(EmbeddedModel):
    fare: str
    priority: int
    x_type: int
    x_value: int


class ClientCurrency(EmbeddedModel):
    type: str
    rate: float


class StaffCurrency(EmbeddedModel):
    type: str
    rate: float


class ItiliteCurrency(EmbeddedModel):
    type: str
    rate: float


class VendorCurrency(EmbeddedModel):
    type: str
    rate: float


class IndexBasedLeg(EmbeddedModel):
    index: int
    mode: str
    leg_request_id: str


class Trip(Model):
    trip_unique_id: ObjectId = Field(primary_field=True)
    trip_id: str = Field(unique=True)
    version: int = Field(default=0)
    pre_fetch: int = Field(default=0)
    trip_request_id: Optional[str]
    trip_status: int = Field(default=0)
    is_travel: int = Field(default=0)
    is_accommodation: int = Field(default=0)
    trip_type: int = Field(default=0)
    trip_state: int = Field(default=0)
    staff_id: int
    client_id: int
    round_trip: int = Field(default=0)
    one_way: int = Field(default=0)
    multi_city: int = Field(default=0)
    multistop: int = Field(default=0)
    trip_requester: int
    overall_approval_trip_type: int = Field(default=0)
    overall_mis_trip_type: int = Field(default=0)
    personal_booking: int = Field(default=0)
    parent_client_id: int = Field(default=0)
    is_personal: int = Field(default=0, index=True)
    hotel_corporate_deal: int = Field(default=0, index=True)
    flight_corporate_fare: int = Field(default=0, index=True)
    overall_request_status: int = Field(default=0, index=True)
    overall_connector_status: int = Field(default=0, index=True)
    overall_transformation_status: int = Field(default=0, index=True)
    overall_consolidation_status: int = Field(default=0, index=True)
    overall_recommendation_status: int = Field(default=0, index=True)
    status: int = Field(default=1, index=True)
    created_on: datetime = Field(default=datetime.now(), index=True)
    updated_on: datetime = Field(default=datetime.now(), index=True)
    multioccupancy_rooms: int = Field(default=0)
    no_of_adults_count: int = Field(default=0)
    no_of_child_count: int = Field(default=0)
    no_of_infant_count: int = Field(default=0)
    no_of_rooms_count: int = Field(default=0)
    multicurrency: int = Field(default=0)
    app_version: str = Field(default="v3")
    overall_travel_type: str
    staff_currency: StaffCurrency
    client_currency: ClientCurrency
    cc_to_sc: float = Field(default=0.00)
    flight_leg_info: List[ObjectId] = []
    hotel_leg_info: List[ObjectId] = []
    flight_request_info: List[ObjectId] = []
    hotel_request_info: List[ObjectId] = []
    instant_hotel_book: int = Field(default=0)
    enable_membership_config: Optional[int] = Field(default=0)
    enable_unused_ticket: Optional[int] = Field(default=0)
    emp_level: Optional[str]
    enable_postpaid: int = Field(default=0)
    switch_postpaid_as_prepaid: int = Field(default=0)
    is_postpaid: int = Field(default=0)
    is_prepaid: int = Field(default=0)
    payment_method: int = Field(default=0)
    package_timer: str = Field(default="NA")
    rt_split: int = Field(default=0)
    traveller_rewards: int = Field(default=0)
    travellers_staff_id: Optional[List[int]]
    child_dob: Optional[List[str]]
    actual_trip_id: Optional[str]
    trip_creation_utc: Optional[str]
    allow_window_break_hours: int = Field(default=0)
    modify_request: Optional[List[dict]] = Field(default=[])
    leg_creation_status: str = Field(default="started")
    order_leg_request_info: List[IndexBasedLeg] = []
    enable_hotel_aaa_rate: bool = Field(default=True)
    user_search_type: Optional[str]


class HotelLegInfo(Model):
    leg_unique_id: ObjectId = Field(primary_field=True)
    trip_unique_id: ObjectId
    leg_request_id: ObjectId
    trip_id: str = Field(index=True)
    leg_no: int
    status: int = Field(default=1, index=True)
    location: str
    checkin: str
    checkout: str
    is_location: Optional[int]
    hotel_id: Optional[str]
    place_id: Optional[str]
    mode: str = Field(default="hotel")
    status: int = Field(default=1, index=True)
    location_details: LocationDetail
    trip_creation_utc: Optional[str]
    created_on: datetime = Field(default=datetime.now(), index=True)
    updated_on: datetime = Field(default=datetime.now(), index=True)


class LegDetail(EmbeddedModel):
    from_iata: str
    to_iata: str
    from_city: str
    to_city: str
    from_country: str
    to_country: str
    all_from_iata: bool
    all_to_iata: bool
    travel_city_from: Optional[str]
    travel_city_to: Optional[str]
    onward_date: Optional[str]
    onward_start_time: Optional[str]
    onward_end_time: Optional[str]
    status: int = Field(default=1, index=True)
    app_leg_id: Optional[int]
    app_leg_uuid: Optional[str]


class FlightLegInfo(Model):
    leg_unique_id: ObjectId = Field(primary_field=True)
    trip_unique_id: ObjectId
    leg_request_id: ObjectId
    trip_id: str = Field(index=True)
    leg_no: int
    status: int = Field(default=1, index=True)
    from_iata: str
    to_iata: str
    from_country: str
    to_country: str
    from_city: str = Field(default="")
    to_city: str = Field(default="")
    all_from_iata: bool = Field(default=False)
    all_to_iata: bool = Field(default=False)
    travel_city_from: Optional[str]
    travel_city_to: Optional[str]
    onward_date: Optional[str]
    onward_start_time: Optional[str]
    onward_end_time: Optional[str]
    return_date: Optional[str]
    return_start_time: Optional[str]
    return_end_time: Optional[str]
    mode: str = Field(default="flight")
    trip_creation_utc: Optional[str]
    multi_city: int = Field(default=0, index=True)
    leg_data: List[LegDetail] = []
    created_on: datetime = Field(default=datetime.now(), index=True)
    updated_on: datetime = Field(default=datetime.now(), index=True)
    previous_booking_details: Optional[dict]
    pax_list: Optional[List[int]]
    pax_count: Optional[dict]
    search_mode: Optional[str]


class HotelRequest(Model):
    leg_request_id: ObjectId = Field(primary_field=True)
    leg_unique_id: ObjectId
    trip_unique_id: ObjectId
    trip_id: str = Field(index=True)
    leg_no: int
    cwm_id: Optional[int]
    status: int = Field(default=1, index=True)
    location: str
    checkin: str
    checkout: str
    is_location: Optional[int]
    hotel_id: Optional[str]
    old_hotel_id: Optional[str]
    place_id: Optional[str]
    status: int = Field(default=1, index=True)
    location_details: LocationDetail
    mode: str = Field(default="hotel")
    app_leg_uuid: Optional[str] = Field(default="", index=True)
    app_leg_id: Optional[int] = Field(default=None, index=True)
    leg_request_status: int = Field(default=0, index=True)
    leg_connector_status: int = Field(default=0, index=True)
    leg_transformation_status: int = Field(default=0, index=True)
    leg_consolidation_status: int = Field(default=0, index=True)
    leg_recommendation_status: int = Field(default=0, index=True)
    trip_creation_utc: Optional[str]
    created_on: datetime = Field(default=datetime.now(), index=True)
    updated_on: datetime = Field(default=datetime.now(), index=True)


class FlightRequest(Model):
    leg_request_id: ObjectId = Field(primary_field=True)
    leg_unique_id: ObjectId
    trip_unique_id: ObjectId
    trip_id: str = Field(index=True)
    leg_no: int
    cwm_id: Optional[int]
    status: int = Field(default=1, index=True)
    from_iata: str
    to_iata: str
    from_country: str
    to_country: str
    from_city: str = Field(default="")
    to_city: str = Field(default="")
    all_from_iata: bool = Field(default=False)
    all_to_iata: bool = Field(default=False)
    travel_city_from: Optional[str]
    travel_city_to: Optional[str]
    onward_date: Optional[str]
    onward_start_time: Optional[str]
    onward_end_time: Optional[str]
    return_date: Optional[str]
    return_start_time: Optional[str]
    return_end_time: Optional[str]
    mode: str = Field(default="flight")
    app_leg_uuid: Optional[str] = Field(default="", index=True)
    app_leg_id: Optional[int] = Field(default=None, index=True)
    app_leg_uuid_return: Optional[str] = Field(default="", index=True)
    app_leg_id_return: Optional[int] = Field(default=None, index=True)
    leg_request_status: int = Field(default=0, index=True)
    leg_connector_status: int = Field(default=0, index=True)
    leg_transformation_status: int = Field(default=0, index=True)
    leg_consolidation_status: int = Field(default=0, index=True)
    leg_recommendation_status: int = Field(default=0, index=True)
    trip_creation_utc: Optional[str]
    multi_city: int = Field(default=0, index=True)
    leg_data: List[LegDetail] = []
    status: int = Field(default=1, index=True)
    created_on: datetime = Field(default=datetime.now(), index=True)
    updated_on: datetime = Field(default=datetime.now(), index=True)
    previous_booking_details: Optional[dict]
    pax_list: Optional[List[int]]
    pax_count: Optional[dict]
    search_mode: Optional[str]


class VendorRequest(Model):
    vendor_request_id: ObjectId = Field(primary_field=True)
    leg_request_id: ObjectId
    leg_unique_id: ObjectId
    trip_id: str = Field(index=True)
    cwm_id: int
    status: int = Field(default=1, index=True)
    created_on: datetime = Field(default=datetime.now(), index=True)
    updated_on: datetime = Field(default=datetime.now(), index=True)
    flight_vendor_req: List[ObjectId] = []
    hotel_vendor_req: List[ObjectId] = []


class HotelDynamicMarkupPolicy(Model):
    min_vendor_discount: int
    max_vendor_discount: int
    dynamic_markup_percent: float


class CompanyDeal(Model):
    deal_code: Optional[str]
    deal_group_id: Optional[str]
    chain: Optional[str]
    hotel_id: Optional[str]


class HotelVendorRequest(Model):
    vendor_request_id: ObjectId = Field(primary_field=True)
    leg_request_id: ObjectId
    leg_unique_id: ObjectId
    trip_id: str = Field(index=True)
    cvwdm_id: int
    request_status: int = Field(default=0, index=True)
    connector_status: int = Field(default=0, index=True)
    transformation_status: int = Field(default=0, index=True)
    status: int = Field(default=1, index=True)
    created_on: datetime = Field(default=datetime.now(), index=True)
    updated_on: datetime = Field(default=datetime.now(), index=True)
    vendor_id: int
    name: Optional[str]
    response_type: str
    cwm_id: int
    wrapper: Optional[str]
    trip_orign_country: str
    detail_id: int = Field(default=0, index=True)
    markup_id: int = Field(default=0, index=True)
    commision_id: int = Field(default=0, index=True)
    currency: Optional[str]
    property_id: Optional[str]
    uname: str
    password: str
    end_point: str
    end_point_1: Optional[str]
    display_name: str
    token_member_id: Optional[str]
    markup_type: Optional[str]
    markup_value: Optional[float]
    price_diff: Optional[str]
    client_currency: ClientCurrency = None
    staff_currency: StaffCurrency = None
    itilite_currency: ItiliteCurrency = None
    vendor_currency: VendorCurrency = None
    app_leg_uuid: Optional[str] = Field(default="", index=True)
    # batch_transformation: List[ObjectId] = []
    connector_start_time: datetime = Field(default=datetime.now())
    connector_end_time: datetime = Field(default=datetime.now())
    deal_codes: Optional[List[str]]
    dynamic_markup_policy: Optional[List[HotelDynamicMarkupPolicy]]
    batch_count: int = Field(default=0)


class VendorDetails(Model):
    client_id: str
    client_secret: str
    access_group: str


class FlightVendorRequest(Model):
    vendor_request_id: ObjectId = Field(primary_field=True)
    leg_request_id: ObjectId
    leg_unique_id: ObjectId
    trip_id: str = Field(index=True)
    cvwdm_id: int
    cabin_class: Optional[str]
    request_status: int = Field(default=0, index=True)
    connector_status: int = Field(default=0, index=True)
    transformation_status: int = Field(default=0, index=True)
    status: int = Field(default=1, index=True)
    created_on: datetime = Field(default=datetime.now(), index=True)
    updated_on: datetime = Field(default=datetime.now(), index=True)
    vendor_id: int
    name: Optional[str]
    response_type: str
    cwm_id: int
    wrapper: Optional[str]
    trip_orign_country: str
    detail_id: int = Field(default=0, index=True)
    deal_code: Optional[List[dict]]
    deal_codes: Optional[str]
    connection_priority: int = Field(default=0, index=True)
    fare_preference_group_id: int = Field(default=0, index=True)
    fare_preference_group: List[FarePreferenceGroup] = []
    currency: Optional[str]
    travel_type: Optional[str]
    v2_wrapper: Optional[str]
    terminal_or_client_id: Optional[str]
    uname: str
    password: str
    end_point: str
    end_point_1: Optional[str]
    token_agency_id: Optional[str]
    token_member_id: Optional[str]
    other_details: Optional[str]
    primary: int = Field(default=0, index=True)
    secondary: int = Field(default=0, index=True)
    property_id: Optional[str]
    price_diff: Optional[str]
    window_break_hours: int = Field(default=0)
    expanded_window_break_hours: int = Field(default=0)
    remove_flight_in_duration_hours: int = Field(default=0)
    default_preference_group_id: int = Field(default=0)
    fixed_window_break_hours: int = Field(default=0)
    refundable: int = Field(default=0)
    client_currency: ClientCurrency = None
    staff_currency: StaffCurrency = None
    itilite_currency: ItiliteCurrency = None
    vendor_currency: VendorCurrency = None
    app_leg_uuid: Optional[str] = Field(default="", index=True)
    # batch_transformation: List[ObjectId] = []
    connector_start_time: datetime = Field(default=datetime.now())
    connector_end_time: datetime = Field(default=datetime.now())
    restrict_airlines: Optional[str] = Field(default=None)
    search_refundable: Optional[int] = Field(default=0)
    markup_id: Optional[int] = Field(default=0)
    markup_type: Optional[str] = Field(default=None)
    markup_value: Optional[float] = Field(default=0)
    vendor_details: Optional[VendorDetails]
    booked_pnr: Optional[str]
    booked_ulc: Optional[str]
    permitted_carriers: Optional[str]


class BatchTransformation(Model):
    batch_id: ObjectId = Field(primary_field=True)
    batch_no: int
    status: int
    vendor_request_id: ObjectId


class LegTimestampLog(Model):
    leg_request_id: ObjectId = Field(primary_field=True)
    connector_start_time: datetime = Field(default=None)
    connector_end_time: datetime = Field(default=None)
    transformation_start_time: datetime = Field(default=None)
    transformation_end_time: datetime = Field(default=None)
    consolidation_start_time: datetime = Field(default=None)
    consolidation_end_time: datetime = Field(default=None)
    recommendation_start_time: datetime = Field(default=None)
    recommendation_end_time: datetime = Field(default=None)


class SkipLegAudit(Model):
    trip_id: str = Field(index=True)
    leg_request_id: ObjectId
    leg_no: int
    mode: str = Field(index=True)
    updated_by: str = Field(index=True)
    updated_on: datetime = Field(default=datetime.now(), index=True)
