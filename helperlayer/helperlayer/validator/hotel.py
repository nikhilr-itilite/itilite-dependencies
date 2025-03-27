import uuid
from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator
from helperlayer.tripmodels import CompanyDeal


def prepend(field: str, text: str) -> str:
    if not field or field.startswith(text):
        return field
    return text + field


def prepend_validator(field: str, text: str):
    return validator(field, allow_reuse=True)(lambda v: prepend(v, text))


class Geo(BaseModel):
    lat: float = Field(alias="latitude")
    lng: float = Field(alias="longitude")

    class Config:
        allow_population_by_field_name = True


class CustomerRating(BaseModel):
    pvr: str = Field(alias="provider")
    rat: float = Field(alias="ratings")
    rev: int = Field(alias="reviews")
    rrd: str = Field(alias="review_rating_desc")

    class Config:
        allow_population_by_field_name = True


class BreakDown(BaseModel):
    typ: str = Field(alias="type")
    nme: str = Field(alias="name")
    dsc: str = Field(alias="description")
    is_pre: bool = Field(alias="is_prepaid")
    tp: float = Field(alias="total_amount")
    tc: str = Field(alias="currency")

    class Config:
        allow_population_by_field_name = True


class FXPostPaid(BaseModel):
    tp: float = Field(alias="total_amount", default=0)
    pn: float = Field(alias="per_night", default=0)  # per night amount of mfd
    tc: str = Field(alias="currency", default="NA")
    bd: Optional[List[BreakDown]] = Field(alias="breakdown")

    class Config:
        allow_population_by_field_name = True


class PostPaid(BaseModel):
    tf: Optional[FXPostPaid] = Field(alias="traveller_fare")
    cf: Optional[FXPostPaid] = Field(alias="client_fare")
    vf: Optional[FXPostPaid] = Field(alias="vendor_fare")
    itf: Optional[FXPostPaid] = Field(alias="itilite_fare")

    class Config:
        allow_population_by_field_name = True


class MandatoryFeeDetails(BaseModel):
    pre: PostPaid = Field(alias="prepaid")
    pst: PostPaid = Field(alias="postpaid")

    class Config:
        allow_population_by_field_name = True


class NonDiscountedPrice(BaseModel):
    rpn: float = Field(alias="rate_per_night")
    na: float = Field(alias="net_amount")
    dis: float = Field(alias="discount_percent")
    avl: bool = Field(alias="discount_available", default=False)
    sdp: bool = Field(alias="show_discount_percent", default=False)

    class Config:
        allow_population_by_field_name = True


class FXPrice(BaseModel):
    rpn: float = Field(alias="rate_per_night")
    na: float = Field(alias="net_amount")
    cur: str = Field(alias="currency_type")
    tax: float = Field(alias="tax")
    bp: float = Field(alias="base_price")
    ppa: float = Field(alias="post_paid_amount")
    ndp: Optional[NonDiscountedPrice] = Field(alias="non_discounted_price")

    class Config:
        allow_population_by_field_name = True


class ItilitePrice(BaseModel):
    # TODO: traveller, vendor, itilite, client
    mp: float = Field(alias="markup_price")
    mt: Optional[str] = Field(alias="markup_type")
    mv: Optional[float] = Field(alias="markup_value")
    bp: float = Field(alias="base_price")
    dis: float = Field(alias="discount")
    tax: float = Field(alias="tax")
    tp: float = Field(alias="net_amount")  # total price , replace other places as well
    rpn: float = Field(alias="rate_per_night")
    tc: FXPrice = Field(alias="traveller_currency")
    ic: FXPrice = Field(alias="itilite_currency")
    vc: FXPrice = Field(alias="vendor_currency")  # baseline details
    cc: FXPrice = Field(alias="client_currency")  # baseline details
    mfd: Union[MandatoryFeeDetails, None] = Field(alias="mandatory_fee_details")

    class Config:
        allow_population_by_field_name = True


class Commission(BaseModel):
    # ct: str = Field(alias='commission_type')    # TODO: check me
    amt: float = Field(alias="amount")
    nc: float = Field(alias="net_commission")
    per: float = Field(alias="percent")
    tc: float = Field(alias="tax_on_commission")
    tcd: str = Field(alias="tax_on_commission_desc")

    class Config:
        allow_population_by_field_name = True


class VendorPrice(BaseModel):
    bp: float = Field(alias="base_price")
    cms: Commission = Field(alias="commission_details")
    dis: float = Field(alias="discount")
    tp: float = Field(alias="net_amount")  # total price
    rpn: float = Field(alias="rate_per_night")
    tax: float = Field(alias="tax")
    cur: Optional[str] = Field(alias="base_currency")
    vta: Optional[str] = Field(alias="vendor_total_amount")
    vcr: Optional[str] = Field(alias="vendor_conv_rate")
    # mfd: Union[MandatoryFeeDetails, None] = Field(alias='mandatory_fee_details')

    class Config:
        allow_population_by_field_name = True


class Restrictions(BaseModel):
    pass


class Distance(BaseModel):
    dt: str = Field(alias="distance_type", default="direct")
    ut: str = Field(alias="unit")
    val: float = Field(alias="value")
    vkm: float = Field(alias="value_in_km")
    vmi: float = Field(alias="value_in_mi")

    class Config:
        allow_population_by_field_name = True


class Package(BaseModel):
    pass


class Tag(BaseModel):
    id: int = Field(alias="id")
    nme: str = Field(alias="tag_name")
    dsc: str = Field(alias="tag_description")

    class Config:
        allow_population_by_field_name = True


class BeddingData(BaseModel):
    cnt: Optional[int] = Field(alias="bed_count")
    typ: Optional[str] = Field(alias="bed_type")
    desc: Optional[str] = Field(alias="description")

    class Config:
        allow_population_by_field_name = True


class Thumbnails(BaseModel):
    # Add more for a new vendor if applicable
    hundred_fifty_square: Optional[str]
    three_hundred_square: Optional[str]

    _prepend_150 = prepend_validator("hundred_fifty_square", "https:")
    _prepend_300 = prepend_validator("three_hundred_square", "https:")

    class Config:
        allow_population_by_field_name = True


# This might need to be adjusted when a new vendor is created.
class CancellationDetails(BaseModel):
    dsc: str = Field(alias="description")
    da: Optional[str] = Field(alias="date_after")
    db: Optional[str] = Field(alias="date_before")
    # pn: int = Field(alias='penalty_nights')
    # sc: str = Field(alias='source_currency')
    # samt: int = Field(alias='source_amount')
    # st: int = Field(alias='source_tax')
    # spf: int = Field(alias='source_processing_fee')
    # scf: int = Field(alias='source_cancellation_fee')
    # sr: int = Field(alias='source_refund')
    # stc: int = Field(alias='source_total_charges')
    dc: Optional[str] = Field(alias="display_currency")
    # damt: int = Field(alias='display_amount')
    # dt: int = Field(alias='display_tax')
    # dpf: int = Field(alias='display_processing_fee')
    # dcf: int = Field(alias='display_cancellation_fee')
    # dr: int = Field(alias='display_refund')
    dtc: Optional[float] = Field(alias="display_total_charges")
    sdd: Optional[int] = Field(alias="show_description_directly")

    class Config:
        allow_population_by_field_name = True


class MembershipDetails(BaseModel):
    avl: bool = Field(default=False, alias="available")
    chn: str = Field(default="", alias="chain")

    class Config:
        allow_population_by_field_name = True


class HotelDynamicMarkupPolicy(BaseModel):
    min_vendor_discount: int
    max_vendor_discount: int
    dynamic_markup_percent: float


class Address(BaseModel):
    address_line_one: Optional[str]
    city_name: Optional[str]
    state_code: Optional[str]
    state_name: Optional[str]
    country_code: Optional[str]
    country_name: Optional[str]
    zip_code: Optional[str]


class Room(BaseModel):
    # Unique Id
    ruid: uuid.UUID = Field(default_factory=uuid.uuid4)
    vid: int = Field(alias="vendor_id")
    sid: str = Field(alias="vendor_request_id")
    rid: Union[str, None] = Field(alias="room_id")
    hid: str = Field(alias="hotel_id")
    cvwdm_id: int = Field(alias="cvwdm_id")
    markup_value: Optional[Union[float, None]] = Field(alias="markup_value", default=0.0)
    api: str = Field(alias="source")
    chn: Optional[str] = Field(alias="chain")
    rt: str = Field(alias="room_type")
    bf: bool = Field(alias="breakfast")
    lch: bool = Field(alias="lunch")
    dnr: bool = Field(alias="dinner")
    rft: int = Field(alias="refund_tag")
    cp: Optional[List[CancellationDetails]] = Field(alias="cancellation_details")  # TODO: change me to proper format
    ib: bool = Field(alias="instant_book")
    rpc: str = Field(alias="rate_plan_code")
    rtc: str = Field(alias="room_type_code")
    vp: VendorPrice = Field(alias="vendor_price")
    ip: ItilitePrice = Field(alias="itilite_price")
    lft: int = Field(alias="rooms_left")
    inc: Union[List, None] = Field(alias="room_inclusions")  # just show room inclusions
    mo: int = Field(alias="max_occupancy")
    tns: int = Field(alias="number_of_nights")  # Total night stay
    bd: Optional[List[BeddingData]] = Field([], alias="bedding_data")
    avl: bool = Field(default=False, alias="available")
    tgs: Optional[List[Tag]] = Field(alias="room_tag_list")  # TODO: finalize the need at the end
    gtg: int = Field(0, alias="gst_tag")
    pkg: Optional[Package] = Field(None, alias="package")
    corp: Optional[bool] = Field(False, alias="corporate_booking")
    dcd: Optional[str] = Field("", alias="deal_code")
    pcd: Optional[str] = Field("", alias="plan_code")
    rimg: Union[List, None] = Field(alias="room_photos")
    pah: bool = Field(alias="pay_at_hotel")
    btc: Optional[bool] = Field(alias="bill_to_company")
    pnw: Optional[bool] = Field(alias="pay_now")
    vcp: Optional[bool] = Field(alias="virtual_card_payment")
    elp: bool = Field(False, alias="earn_loyalty_points")
    huuid: uuid.UUID
    pc: int = Field(0, alias="client_preferred")  # preferred by client
    ich: bool = Field(False, alias="itilite_contracted")  # Itilite contracted
    qt: bool = Field(alias="quality")
    gt: Optional[str] = Field(alias="guarantee_type")
    cdt: Optional[str] = Field(alias="cancellation_date")
    mem: Optional[MembershipDetails] = Field(alias="membership_details")
    rtyp: Optional[str] = Field(alias="rate_type")
    rl: Optional[str] = Field(alias="room_label")
    ri: Optional[str] = Field(alias="room_identifier")

    class Config:
        allow_population_by_field_name = True


class Hotel(BaseModel):
    # huuid: uuid.UUID = Field(default_factory=uuid.uuid4)     # unique id
    huuid: uuid.UUID  # unique id
    uid: str = Field(alias="itilite_unique_id")
    hid: str = Field(alias="hotel_id")
    did: int = Field(0, alias="deal_group_id")
    nme: str = Field(alias="name")
    adr: str = Field(alias="address")
    cty: str = Field(alias="country_code", default="")
    # abt: str = Field(alias='hotel_description')  # about
    pc: int = Field(False, alias="client_preferred")  # preferred by client
    ich: bool = Field(False, alias="itilite_contracted")  # Itilite contracted
    pt: bool = Field(False, alias="traveller_preferred")  # preferred by client
    gd: Distance = Field(alias="geo_distance")
    dd: Distance = Field(
        {"unit": "kms", "value": 99999, "value_in_km": 99999, "value_in_mi": 99999},
        alias="driving_distance",
    )
    po: Optional[int] = Field(alias="preference_order")  # cph preference order
    star: int = Field(alias="star_rating")
    img: Optional[str] = Field(alias="image")
    himg: Union[List, None] = Field(alias="hotel_photos")
    vis: bool = Field(True, alias="visibility")
    pr: int = Field(0, alias="priority")
    sig: int = Field(1, alias="significance")
    rst: Union[List[Restrictions], None] = Field([], alias="restrictions")  # empty for priceline
    gtg: int = Field(0, alias="gst_tag")
    loc: Geo = Field(alias="location")
    ctr: CustomerRating = Field(alias="customer_rating")
    qt: bool = Field(alias="quality")
    pkg: Package = Field(None, alias="package")
    rms: List[Room] = Field(alias="rooms")
    inc: Union[List, None] = Field(alias="hotel_inclusions")
    cid: str = Field(alias="checkin_date")
    cod: str = Field(alias="checkout_date")
    cit: str = Field("", alias="checkin_time")
    cot: str = Field("", alias="checkout_time")
    # cih: str = Field('', alias='checkin_hour')
    # coh: str = Field('', alias='checkout_hour')
    tag: Optional[dict] = Field({}, alias="hotel_tag")  # change me later
    imgs: Optional[Thumbnails] = Field(alias="thumbnails")
    ptn: str = Field(default="", alias="property_type_name")
    feedback_no: Optional[int]
    feedback_info: Optional[str]
    mem: Optional[MembershipDetails] = Field(alias="hotel_membership_details")  # Hotel level mem avl tag
    cadr: Optional[Address] = Field(alias="complete_address")
    rtyps: Optional[List[str]] = Field(alias="rate_types")  # Available rate types
    ucid: Optional[int] = Field(0, alias="unica_chain_id")
    ars: Optional[int] = Field(0, alias="api_response_status")
    ucid: Optional[int] = Field(0, alias="unica_chain_id")

    class Config:
        allow_population_by_field_name = True


class HotelList(BaseModel):
    hotels: List[Hotel]

    class Config:
        allow_population_by_field_name = True


class CurrencyConversion(BaseModel):
    type: str = Field(alias="type")
    rate: float = Field(alias="rate")

    class Config:
        allow_population_by_field_name = True


class HotelFREConfig(BaseModel):
    vendor_id: int
    name: str
    cvwdm_id: int
    wrapper: str
    detail_id: int
    markup_id: int
    commision_id: int
    currency: str
    property_id: str
    uname: str
    password: str
    end_point: str
    end_point_1: Optional[str]
    display_name: str
    token_member_id: str
    vendor_request_id: Optional[str]
    markup_type: Optional[str]
    markup_value: Optional[float]
    response_type: str
    client_currency: CurrencyConversion
    staff_currency: CurrencyConversion
    itilite_currency: CurrencyConversion
    vendor_currency: CurrencyConversion
    vendor_call_date: Optional[str]
    deal_codes: Optional[List[str]]
    dynamic_markup_policy: Optional[List[HotelDynamicMarkupPolicy]]
    company_deal_codes: Optional[List[CompanyDeal]]

    class Config:
        allow_population_by_field_name = True


class Location(BaseModel):
    # address: str
    longitude: float = Field(alias="lng")
    latitude: float = Field(alias="lat")
    country: Optional[str]
    continent: Optional[str]
    region: Optional[str]
    sub_region: Optional[str]
    political_locality: Optional[str]
    country_short_name: Optional[str]
    # add more fields as per requirement

    class Config:
        allow_population_by_field_name = True


def apply_alias_recursively(model, data: dict) -> dict:
    alias_values = {}
    for key, value in data.items():
        # Check if the key exists in the model's fields
        if hasattr(model, "__fields__") and key in model.__fields__:
            alias = model.__fields__[key].alias
            if isinstance(value, dict):
                alias_values[alias] = {k: v for k, v in value.items()}
            else:
                alias_values[alias] = value
        else:
            alias_values[key] = value  # Keep the original key if no alias is found
    return alias_values
