import json
import typing
import uuid
from datetime import datetime
from typing import List, Optional, Union

import jmespath
from pydantic import BaseModel, Field, root_validator

DATE_FORMAT = "%Y-%m-%d"
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"


class TaxBreakUpDetailsInfo(BaseModel):
    #
    key: str
    #
    category: str
    #
    value: float


class TaxBreakUpDetailsInfoInsidePassengers(BaseModel):
    id: str
    key: str
    value: float


class RescheduleBreakUp(BaseModel):
    # fare difference from the original booked flight
    fd: float = Field(alias="fare_difference")
    # change fee, can be None if not available.
    chf: Union[float, None] = Field(alias="change_fee")

    class Config:
        allow_population_by_field_name = True


class FXPrice(BaseModel):
    tp: float = Field(alias="total_price")
    # Vendor Base Price
    bp: float = Field(alias="base_price")
    # Vendor Currency
    cur: str = Field(alias="currency")
    # Vendor Tax
    tax: Union[float, None] = Field(alias="tax")

    total_baggage_charges: Optional[float] = Field(alias="total_baggage_charges", default=0.0)
    total_meal_charges: Optional[float] = Field(alias="total_meal_charges", default=0.0)
    other_charges: Optional[float] = Field(alias="other_charges", default=0.0)
    tax_breakup: Optional[Union[List[TaxBreakUpDetailsInfo], List[TaxBreakUpDetailsInfoInsidePassengers]]] = Field(default=list())
    # change fee
    chf: Optional[Union[float, None]] = Field(alias="change_fee")
    # Reschedule fare break up
    brk: Optional[RescheduleBreakUp] = Field(alias="reschedule_fare_breakup")
    total_seat_charges: Optional[float] = Field(alias="total_seat_charges", default=0.0)

    class Config:
        allow_population_by_field_name = True

    # _round = validator('rpn', 'na', allow_reuse=True)(float_round)


class SSRPrice(BaseModel):
    # Total Price
    tp: float = Field(alias="total_price")
    # Vendor Currency
    cur: str = Field(alias="currency")

    class Config:
        allow_population_by_field_name = True


class CancellationPolicy(BaseModel):
    # Type
    typ: str = Field(alias="cancellation_amount_type")
    # Chargable Currency
    cgc: Optional[str] = Field(alias="chargable_currency")
    # Charge
    cg: float = Field(alias="charge")
    # Applies on
    ao: Union[str, None] = Field(alias="applies_on")

    class Config:
        allow_population_by_field_name = True


class ReschedulePolicy(BaseModel):
    # Type
    typ: str = Field(alias="reschedule_amount_type")
    # Chargable Currency
    cgc: Optional[str] = Field(alias="chargable_currency")
    # Charge
    cg: float = Field(alias="charge")
    # Applies on
    ao: Union[str, None] = Field(alias="applies_on")

    class Config:
        allow_population_by_field_name = True


class Meals(BaseModel):
    # Pax Type
    Key: str = Field(alias="key_reference")
    # Vendor meal price
    vmp: float = Field(alias="vendor_meal_price")
    # Vendor Currency
    vc: str = Field(alias="vendor_currency")
    tf: Optional[SSRPrice] = Field(alias="meals_traveller_fare")
    itf: Optional[SSRPrice] = Field(alias="meals_itilite_fare")
    vf: Optional[SSRPrice] = Field(alias="meals_vendor_fare")
    cf: Optional[SSRPrice] = Field(alias="meals_client_fare")
    # segment Key
    sgk: str = Field(alias="segment_key")
    # description Key
    desc: str = Field(alias="description_code")
    # travel reference Key
    trk: str = Field(alias="travel_reference_key")
    # airline description code
    adesc: str = Field(alias="airline_description_code")
    # ssr meal code
    sc: str = Field(alias="ssr_code")
    # Pax Key
    pax_key: Optional[str] = Field(alias="pax_key")

    class Config:
        allow_population_by_field_name = True


class Lounge(BaseModel):
    # Pax Type
    Key: str = Field(alias="key_reference")
    # Vendor lounge price
    vmp: float = Field(alias="vendor_lounge_price")
    # Vendor Currency
    vc: str = Field(alias="vendor_currency")
    # segment Key
    sgk: str = Field(alias="segment_key")
    # description Key
    desc: str = Field(alias="description_code")
    # travel reference Key
    trk: str = Field(alias="travel_reference_key")
    # airline description code
    adesc: str = Field(alias="airline_description_code")
    # ssr meal code
    sc: str = Field(alias="ssr_code")
    # Pax Key
    pax_key: Optional[str] = Field(alias="pax_key")

    class Config:
        allow_population_by_field_name = True


class OptionBaggage(BaseModel):
    # Pax Type
    Key: str = Field(alias="key_reference")
    # Vendor baggage price
    vmp: float = Field(alias="vendor_baggage_price")
    # Vendor Currency
    vc: str = Field(alias="vendor_currency")
    tf: Optional[SSRPrice] = Field(alias="baggage_traveller_fare")
    itf: Optional[SSRPrice] = Field(alias="baggage_itilite_fare")
    vf: Optional[SSRPrice] = Field(alias="baggage_vendor_fare")
    cf: Optional[SSRPrice] = Field(alias="baggage_client_fare")
    # segment Key
    sgk: str = Field(alias="segment_key")
    # description Key
    desc: str = Field(alias="description_code")
    # travel reference Key
    trk: str = Field(alias="travel_reference_key")
    # airline description code
    adesc: str = Field(alias="airline_description_code")
    # ssr meal code
    sc: str = Field(alias="ssr_code")

    class Config:
        allow_population_by_field_name = True


class Seats(BaseModel):
    # rows
    row: Optional[str] = Field(alias="rows")
    # paid
    pd: Optional[str] = Field(alias="paid")
    # seat
    st: str = Field(alias="seat")
    # Type
    type: Union[str, None] = Field(alias="type")
    # Vendor meal price
    vmp: Optional[float] = Field(alias="Vendor_seat_price")
    # Vendor Currency
    vc: Optional[str] = Field(alias="vendor_currency")
    # segment Key
    sgk: Optional[str] = Field(alias="segment_key")
    # exit row
    erw: str = Field(alias="exit_row")
    # Branded Info
    brdinfo: Optional[str] = Field(alias="brand_info")
    # Seat number
    sn: Union[str, None] = Field(alias="seat_number")
    # Availability
    avail: Union[str, None] = Field(alias="availability")
    # Extra_details
    extdet: str = Field(alias="extra_details")
    # is child seat
    ischildseat: Optional[str] = Field(alias="ischild_seat")
    # description Key
    desc: Optional[str] = Field(alias="description_code")
    # travel reference Key
    trk: Optional[str] = Field(alias="travel_reference_key")
    # airline description code
    adesc: Optional[str] = Field(alias="airline_description_code")
    # ssr meal code
    sc: Optional[str] = Field(alias="ssr_code")

    class Config:
        allow_population_by_field_name = True


class Segment(BaseModel):
    ogn: str
    dty: str
    ddt: str
    cid: str
    ci: Optional[str] = Field(default=None)
    ogn_city: Optional[str]
    dty_city: Optional[str]


class Meal(BaseModel):
    data: Optional[List[Meals]]
    segment: Optional[Segment]


class Bags(BaseModel):
    data: Optional[List[OptionBaggage]]
    segment: Optional[Segment]


class SeatRow(BaseModel):
    adesc: Optional[str] = Field(alias="airline_description_code")
    sn: Union[str, None] = Field(alias="seat_number")
    type: Union[str, None] = Field(alias="type")
    avail: Union[str, None] = Field(alias="availability")
    ischildseat: Optional[str] = Field(alias="ischild_seat")
    pd: Optional[str] = Field(alias="paid")
    vsp: Optional[float] = Field(alias="vendor_seat_price")
    vc: Optional[str] = Field(alias="vendor_currency")
    tf: Optional[SSRPrice] = Field(alias="seat_traveller_fare")
    itf: Optional[SSRPrice] = Field(alias="seat_itilite_fare")
    vf: Optional[SSRPrice] = Field(alias="seat_vendor_fare")
    cf: Optional[SSRPrice] = Field(alias="seat_client_fare")
    erw: Optional[str] = Field(alias="exit_row")
    brdinfo: Optional[str] = Field(alias="brand_info")
    extdet: Optional[str] = Field(alias="extra_details")
    st: Optional[str] = Field(alias="seat")
    sgk: Optional[str] = Field(alias="segment_key")
    key: Optional[List]
    pdt: Optional[str] = Field(alias="provider_defined_type")

    class Config:
        allow_population_by_field_name = True


class SeatGlobalInfo(BaseModel):
    maspr: int = Field(alias="max_asile_seats_per_row")
    mspr: int = Field(alias="max_seats_per_row")
    fsa: Optional[int] = Field(alias="is_free_seat_available", default=0)
    bi: list = Field(alias="brand_info", default=[])
    extd: list = Field(alias="extra_details", default=[])
    ex: Optional[list] = Field(alias="exit_row", default=[])
    slr: Optional[List[SeatRow]] = Field(alias="seat_layout")

    class Config:
        allow_population_by_field_name = True


class SeatInfo(BaseModel):
    row: str = Field(alias="row")
    st: List[SeatRow] = Field(alias="seats")

    class Config:
        allow_population_by_field_name = True


class SeatInfomation(BaseModel):
    sgi: SeatGlobalInfo = Field(alias="seat_global_info")
    si: List[SeatInfo] = Field(alias="seat_info")

    class Config:
        allow_population_by_field_name = True


class SSRDetails(BaseModel):
    # Pax Type
    pax: str = Field(alias="pax_type")
    # Meals, Lounge, Seats, Baggage with respect to PAX
    mls: Union[List[Meal], List[List[Meals]]] = Field(alias="mls", default=list())

    lnge: List[List[Lounge]] = Field(alias="lnge", default=list())

    bkg: Union[List[Bags], List[List[OptionBaggage]]] = Field(alias="bkg", default=list())

    sts: Union[List[List[Seats]], List[SeatInfomation]] = Field(alias="sts", default=list())

    class Config:
        allow_population_by_field_name = True


class SSR(BaseModel):
    ssr: List[SSRDetails] = Field(alias="ssrDetails")
    segment: Optional[Segment]

    class Config:
        allow_population_by_field_name = True


class ViaDetails(BaseModel):
    airport: Optional[str]
    duration: Optional[int]


class ViaBase(BaseModel):
    stops: int = 0
    detail: Optional[List[ViaDetails]]

    class Config:
        allow_population_by_field_name = True


class Flight(BaseModel):
    # carrier_iata
    ci: str = Field(alias="carrier_iata")
    # carrier_id
    cid: str = Field(alias="carrier_id")
    # carrier_name
    cn: str = Field(alias="carrier_name", default="")
    # operating/platting carrer iata
    pci: str = Field(alias="platting_carrier_iata")

    # operating/platting carrier_name
    pcn: Union[str, None] = Field(alias="platting_carrier_name")
    # Duration in minutes
    dn: int = Field(alias="duration")
    # Origin
    ogn: str = Field(alias="origin")
    # Origin City
    ogn_city: Optional[str] = Field(alias="origin_city")
    # Destination
    dty: str = Field(alias="destination")
    # Destination City
    dty_city: Optional[str] = Field(alias="destination_city")
    # Arrival Date Time
    adt: str = Field(alias="arrival_date_time")
    # Departure Date Time
    ddt: str = Field(alias="departure_date_time")
    # Origin Terminal
    ot: Union[str, None] = Field(alias="origin_terminal")
    # Destination Terminal
    dt: Union[str, None] = Field(alias="destination_terminal")
    # LayOver Time,
    lo: Union[int, None] = Field(alias="layover_time")
    # OverNight,
    on: Union[int, None] = Field(alias="over_night")
    # via
    via: Optional[ViaBase]

    class Config:
        allow_population_by_field_name = True


class Baggage(BaseModel):
    # Check in Baggaege
    cb: Union[str, None] = Field(alias="checkin_baggage")
    # Check in Baggage Unit
    cbu: Union[str, None] = Field(alias="checkin_baggage_unit")
    # Hand Baggage
    hb: Union[str, None] = Field(alias="hand_baggage", default=None)
    # Hand Baggage Unit
    hbu: Union[str, None] = Field(alias="hand_baggage_unit", default=None)

    class Config:
        allow_population_by_field_name = True


class DetailBaggage(BaseModel):
    # Check in Baggaege
    cb: Union[str, None] = Field(alias="checkin_baggage")
    # Check in Baggage Unit
    cbu: Union[str, None] = Field(alias="checkin_baggage_unit")
    # Hand Baggage
    hb: Union[str, None] = Field(alias="hand_baggage", default=None)
    # Hand Baggage Unit
    hbu: Union[str, None] = Field(alias="hand_baggage_unit", default=None)
    # Origin
    ogn: str = Field(alias="origin")
    # Destination
    dty: str = Field(alias="destination")

    class Config:
        allow_population_by_field_name = True


class FareBreakup(BaseModel):
    # Booking Class Code
    bc: str = Field(alias="booking_class_code")
    # Cabin Class
    cc: str = Field(alias="cabin_class")
    # Fare Basis Code
    fbc: str = Field(alias="fare_basis_code")
    # Pax Type
    pax: str = Field(alias="pax_type")
    # Origin
    ogn: str = Field(alias="origin")
    # Destination
    dty: str = Field(alias="destination")
    # Vendor Base Price
    vbp: float = Field(alias="vendor_base_price")
    # Vendor Currency
    vc: str = Field(alias="vendor_currency")
    # Baggage
    bg: Baggage = Field(alias="baggage")
    # Brand Id
    bid: Union[str, None] = Field(alias="brand_id")
    # Brand Tier
    bt: Union[str, None] = Field(alias="brand_tier")
    # Brand Name
    bnm: Union[str, None] = Field(alias="brand_name")
    # 1 Checked Baggage
    obn: Union[str, None] = Field(alias="original_brand_name")
    cbg: Union[str, None] = Field(alias="checked_baggage")
    # 2 Carry On
    crn: Union[str, None] = Field(alias="carry_on_baggage")
    # 3 Rebooking
    rbk: Union[str, None] = Field(alias="rebookable")
    # 4 Refund
    rfn: Union[str, None] = Field(alias="refundable")
    # 5 Seat
    st: Union[str, None] = Field(alias="seat")
    # 6 Meal
    mls: Union[str, None] = Field(alias="meal")
    # 7 Wifi
    y5: Union[str, None] = Field(alias="wifi")
    # Beverage
    bv: Union[str, None] = Field(alias="beverage")

    class Config:
        allow_population_by_field_name = True
        allow_extra = True


class PaxFareBreakup(BaseModel):
    # Pax Type
    pax: str = Field(alias="pax_type")
    # Fare Breakup with respect to PAX
    fb: List[List[FareBreakup]] = Field(alias="fare_breakup")
    # Vendor Total Price
    vtp: float = Field(alias="vendor_total_price")
    # Vendor Base Price
    vbp: float = Field(alias="vendor_base_price")
    # Vendor Currency
    vc: str = Field(alias="vendor_currency")
    # Vendor Tax
    vt: Union[float, None] = Field(alias="vendor_tax")
    # Reschedule Policy
    rp: List[ReschedulePolicy] = Field(alias="reschedule_policy", default=list())
    # Cancellation Policy
    cp: List[CancellationPolicy] = Field(alias="cancellation_policy", default=list())
    tf: Optional[FXPrice] = Field(alias="traveller_fare")
    itf: Optional[FXPrice] = Field(alias="itilite_fare")
    vf: Optional[FXPrice] = Field(alias="vendor_fare")  # baseline details
    cf: Optional[FXPrice] = Field(alias="client_fare")

    class Config:
        allow_population_by_field_name = True


class CompareFare(BaseModel):
    cf: float = Field(alias="compare_fare")
    cfp: float = Field(alias="compare_fare_priority")

    class Config:
        allow_population_by_field_name = True


class BrandDesc(BaseModel):
    # type_of_inclusion
    typ: str = Field(alias="type_of_inclusion")
    desc: Union[str, None, List] = Field(alias="description")
    inc: Union[int, None] = Field(alias="inclusion_value")
    val: Union[str, None] = Field(alias="value", default=None)
    add_ons: Union[List, None] = Field(alias="add_ons", default=[])

    class Config:
        allow_population_by_field_name = True


class MoreDetail(BaseModel):
    type: Optional[str]
    path: Union[str, None]

    class Config:
        allow_population_by_field_name = True


class MoreDetailData(BaseModel):
    path: Union[str, None]
    desc: Union[str, None, List] = Field(alias="description")

    class Config:
        allow_population_by_field_name = True


class FareRule(BaseModel):
    rule: List[str] = Field(alias="rule")

    class Config:
        allow_population_by_field_name = True


class StaticFareRule(BaseModel):
    type: Optional[str]
    path: Union[str, None]

    class Config:
        allow_population_by_field_name = True


class Fare(BaseModel):
    # Vendor Total Price
    vtp: float = Field(alias="vendor_total_price")
    # In case of multi_city this is required as vtp will consist all subsequent legs price
    mvtp: float = Field(alias="actual_vendor_total_price", default=0.0)
    # Vendor Base Price
    vbp: float = Field(alias="vendor_base_price")
    # Vendor Currency
    vc: str = Field(alias="vendor_currency")
    # Vendor Tax
    vt: Union[float, None] = Field(alias="vendor_tax")
    # Vendor change fee
    vchf: Union[float, None] = Field(alias="vendor_change_fee")
    # Platting Carrier
    pc: Union[str, None] = Field(alias="platting_carrier")
    # Platting Carrier Name
    pcn: Union[str, None] = Field(alias="platting_carrier_name")
    # api
    api: str = Field(alias="api")
    # Pax Fare Breakup
    pfb: List[PaxFareBreakup] = Field(alias="pax_fare_breakup")
    # Reschedule Policy
    rp: List[ReschedulePolicy] = Field(alias="reschedule_policy", default=list())
    # Cancellation Policy
    cp: List[CancellationPolicy] = Field(alias="cancellation_policy", default=list())

    # Fare Selection
    fs: str = Field(alias="fare_selection")

    ac: Union[str, None] = Field(alias="account_code")

    # cf: CompareFare = Field(alias='compare_fare')
    cfv: float = Field(alias="compare_fare")
    cfp: float = Field(alias="compare_fare_priority")
    cvwdm_id: str = Field(alias="cvwdm_id")
    cnp: str = Field(alias="connection_priority")

    # Brand Name
    bn: Union[str, None] = Field(alias="brand_name")
    # Self Check In Basic Economy
    scc: int = Field(alias="scc", default=0)
    # Brand Id
    bid: Union[str, None] = Field(alias="brand_id")
    # Cabin Class
    cc: Union[str, None] = Field(alias="cabin_class")
    # Brand Description
    bd: List[BrandDesc] = Field(alias="brand_desc")
    # More Details
    md: MoreDetail = Field(alias="more_detail")
    # Multi city fare
    mc: int = Field(alias="multi_city_fare", default=0)
    # Search Id
    sid: str = Field(alias="search_id")
    # Result Index
    rs: Union[List, None] = Field(alias="result_index")
    # detail_baggage
    bg: List[DetailBaggage] = Field(alias="detail_baggage")
    # Fare Id
    fid: uuid.UUID = Field(default_factory=uuid.uuid4)
    mc_lid: Optional[str] = Field(default="")
    # mc_fid is not needed for travelportus fares as mc_lid will be unique
    mc_fid: Optional[uuid.UUID] = Field(default=None)
    mc_mvh: Optional[str] = Field(default="")
    status: Optional[str] = Field(default="")
    # ppn bundle for priceline
    ppn_bid: Optional[str] = Field(alias="ppn_bundle")

    # ppn return bundle for priceline used in return search endpoint
    ppn_return_bid: Optional[str] = Field(alias="ppn_return_bundle")

    ppn_seat_bid: Optional[str] = Field(alias="ppn_seat_bundle")

    # journey key for akasa and air asia
    jk: Optional[str] = Field(alias="journey_key")

    # fare availability key for akasa and air asia
    fk: Optional[str] = Field(alias="fare_availability_key")

    # discounted tag
    df: Optional[int] = Field(alias="discounted_return")

    tf: FXPrice = Field(alias="traveller_fare")
    itf: FXPrice = Field(alias="itilite_fare")
    vf: FXPrice = Field(alias="vendor_fare")  # baseline details
    cf: FXPrice = Field(alias="client_fare")

    ssr: Optional[Union[List[SSR], List[SSRDetails]]] = Field(alias="ssrDetails")
    frl: Optional[FareRule] = Field(alias="frl")
    # brand_name_hash
    bnh: Optional[str] = Field(alias="brand_name_hash")
    # One adult fare in client currency for rewards
    afcr: float = Field(alias="adult_fare_client_rate", default=0.0)
    # original_brand_name
    obn: Union[str, None] = Field(alias="original_brand_name")

    sfr: Optional[StaticFareRule] = Field(alias="static_fare_rule")

    # catalog_identifier for gds  json rescehdule
    cat_idt: Optional[str] = Field(alias="catalog_identifier")
    # indentifier_value for gds  json rescehdule
    idn_val: Optional[str] = Field(alias="indentifier_value")
    # workbench_indentifier for gds json rescehdule
    wrk_idn: Optional[str] = Field(alias="workbench_indentifier")

    l3_trigger: Optional[bool] = Field(alias="is_l3_card_trigger", default=False)
    parent_fares: Optional[str] = Field(alias="parent_fares", default="")
    previous_leg_lh: Optional[str] = Field(default="")
    mfc_done: Optional[bool] = Field(default=False)
    pmf: Optional[int] = Field(default=0)
    fsa: Optional[int] = Field(alias="is_free_seat_available", default=0)

    vbd: Optional[List] = Field(alias="vendor_brand_data", default=[])

    hcd: Optional[bool] = Field(alias="is_hardcoded_data", default=False)

    gc: Optional[bool] = Field(alias="gordian_call", default=True)

    class Config:
        allow_population_by_field_name = True


class FlightSegmentOnly(BaseModel):
    fgt: List[Flight]


class FlightSegment(BaseModel):
    # Flights
    fgt: List[Flight] = Field(alias="flight")
    # Total Duration
    td: int = Field(alias="total_duration")
    # Total Stop
    ts: typing.Optional[int] = Field(alias="total_stop")
    # No of day
    nd: typing.Optional[int] = Field(alias="no_of_day")
    # Leg hash to identify packaged other return or onward flight
    lh: typing.Optional[str] = Field(alias="leg_hash")
    # morefare key to check the staus for Multifare
    mf: typing.Optional[int] = Field(alias="morefare_status")
    # via
    via: Optional[ViaBase]
    # multi_city sector fare hash
    lmvh: typing.Optional[str] = Field(alias="leg_with_fare_hash")
    # multi_city sector fare code share hash
    lcsh: typing.Optional[str] = Field(alias="leg_with_fare_cs")
    # multi_city sector fare same details hash
    lsd: typing.Optional[str] = Field(alias="leg_with_fare_sd")

    colleague_count: Optional[int]

    colleague_info: Optional[str]
    # Journey Sell Key for SG
    jsk: str = Field(alias="journey_sell_key", default="")

    class Config:
        allow_population_by_field_name = True

    @root_validator
    def compute(cls, values) -> typing.Dict:
        # convert string to date object
        flight_starting_at = datetime.strptime(values["fgt"][0].ddt, DATE_TIME_FORMAT)
        flight_ending_at = datetime.strptime(values["fgt"][-1].adt, DATE_TIME_FORMAT)
        flight_ending_date = flight_ending_at.date()
        flight_starting_date = flight_starting_at.date()
        delta = flight_ending_date - flight_starting_date
        flight_list_only = FlightSegmentOnly(fgt=values["fgt"]).dict()
        via = values.get("via")
        leg_detail = json.dumps(jmespath.search("@.fgt[*].{ci:ci,cid:cid,adt:adt,ddt:ddt}", flight_list_only))
        values["lh"] = str(uuid.uuid3(uuid.NAMESPACE_X500, leg_detail))
        values["nd"] = delta.days
        values["ts"] = len(values["fgt"]) - 1
        if values["lmvh"]:
            values["lmvh"] = str(uuid.uuid3(uuid.NAMESPACE_X500, values["lmvh"]))
        if values["lcsh"]:
            values["lcsh"] = str(uuid.uuid3(uuid.NAMESPACE_X500, values["lcsh"]))
        if values["lsd"]:
            values["lsd"] = str(uuid.uuid3(uuid.NAMESPACE_X500, values["lsd"]))
        if via and via.stops:
            values["ts"] += via.stops
        return values


class LegListOnly(BaseModel):
    leg: List[FlightSegment]


class FareListOnly(BaseModel):
    fl: List[Fare]


class LegDetails(BaseModel):
    # Flight Leg
    leg: List[FlightSegment]
    # Fare List
    fl: List[Fare] = None
    # Hash values
    mvh: typing.Optional[str] = Field(alias="mv_hash")
    csh: typing.Optional[str] = Field(alias="cs_hash")
    sh: typing.Optional[str] = Field(alias="s_hash")
    alh: typing.Optional[str] = Field(alias="al_hash")
    # Unique Id
    lid: uuid.UUID = Field(default_factory=uuid.uuid4)

    class Config:
        allow_population_by_field_name = True

    @root_validator
    def compute(cls, values) -> typing.Dict:
        leg_list_only = LegListOnly(leg=values["leg"]).dict()
        multi_vendor_detail = json.dumps(jmespath.search("leg[*].fgt[*].{ci:ci,cid:cid,ddt:ddt}", leg_list_only))
        fl_list_only = FareListOnly(fl=values["fl"]).dict()
        cc_data = json.dumps(jmespath.search("fl[*].{cc:cc}", fl_list_only))
        multi_vendor_detail += cc_data
        code_share_detail = json.dumps(jmespath.search("leg[*].fgt[*].{adt:adt,ddt:ddt}", leg_list_only))
        code_share_detail += cc_data
        same_detail = json.dumps(jmespath.search("leg[*].fgt[*].{ci:ci,cid:cid,adt:adt,ddt:ddt}", leg_list_only))
        same_detail += cc_data
        same_leg_detail = json.dumps(jmespath.search("leg[*].fgt[*].{ci:ci,cid:cid,adt:adt,ddt:ddt}", leg_list_only))
        # If you change logic here change in gds transformer as well as priceline transformer
        values["mvh"] = str(uuid.uuid3(uuid.NAMESPACE_X500, multi_vendor_detail))
        values["csh"] = str(uuid.uuid3(uuid.NAMESPACE_X500, code_share_detail))
        values["sh"] = str(uuid.uuid3(uuid.NAMESPACE_X500, same_detail))
        values["alh"] = str(uuid.uuid3(uuid.NAMESPACE_X500, same_leg_detail))
        return values


class FlightResult(BaseModel):
    result: List[LegDetails]
    status: int = 1

    class Config:
        allow_population_by_field_name = True


class FarePreferenceGroup(BaseModel):
    fare: str
    priority: int
    x_type: int
    x_value: int

    class Config:
        allow_population_by_field_name = True


class currencyConversion(BaseModel):
    type: str = Field(alias="type")
    rate: float = Field(alias="rate")

    class Config:
        allow_population_by_field_name = True


class VendorDetails(BaseModel):
    client_id: str
    client_secret: str
    access_group: str


class FlightFREConfig(BaseModel):
    cvwdm_id: int
    name: str
    wrapper: str
    detail_id: int
    vendor_id: int
    deal_codes: Optional[str]
    deal_code: Optional[List[dict]]
    connection_priority: int
    travel_type: str
    trip_orign_country: str
    cwm_id: int
    terminal_or_client_id: str
    uname: str
    password: str
    end_point: str
    end_point_1: Optional[str]
    token_agency_id: str
    token_member_id: str
    other_details: str
    primary: int
    secondary: int
    fare_preference_group: List[FarePreferenceGroup]
    currency: str
    vendor_request_id: str
    cabin_class: str
    client_currency: currencyConversion
    staff_currency: currencyConversion
    itilite_currency: currencyConversion
    vendor_currency: currencyConversion
    response_type: str
    vendor_call_date: Optional[str]
    restrict_airlines: Optional[str]
    search_refundable: Optional[int]
    is_farequote_trigger: Optional[bool]
    leg_request_id: Optional[str]
    v2_wrapper: Optional[str]
    detailed_error: Optional[str]
    vendor_details: Optional[VendorDetails]
    booked_pnr: Optional[str]
    workbench_indentifier: Optional[str]
    booked_ulc: Optional[str]
    permitted_carriers: Optional[str]

    class Config:
        allow_population_by_field_name = True
