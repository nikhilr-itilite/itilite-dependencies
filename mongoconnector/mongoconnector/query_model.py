from pydantic import BaseModel
from typing import Optional, Dict, List


class GroupDocResponseFields(BaseModel):
    field_path: str
    return_obj_name: str
    complete_obj: bool


class NestedExactMatch(BaseModel):
    match_field_path: str = None
    condition: str = None


class SubQuery(BaseModel):
    subquery: Dict[str, Dict[str, list]]
    compound_query: Optional[dict] = None
    nested_exact_match: Optional[NestedExactMatch] = None


class Group(BaseModel):
    group_by: str
    doc_response_fields: List[GroupDocResponseFields]


class Query(BaseModel):
    query: SubQuery
    sort_by: Optional[dict] = None
    group: Optional[Group] = None
    page_no: Optional[int] = (int(1),)
    page_size: Optional[int] = int(25)
