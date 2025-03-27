class ItiliteBaseException(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return str(self.message)


class PricelineException(ItiliteBaseException):
    def __init__(self, error_dict):
        super().__init__(
            message=error_dict["status"],
            # status_code=error_dict["status_code"]
        )
        self.time = error_dict["time"]
        self.status_message = error_dict.get("status_message")

    def __str__(self):
        return self.status_message or self.message


class EmptyVendorResponse(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class UnauthorizedException(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class InvalidHotelStayException(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class RestrictedAirlineException(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ResultAirportMismatchException(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class AirCreateReservationError(BaseException):
    def __init__(self, reason: str, message: str, data: dict):
        self.reason = reason
        self.message = f"Error while performing air create reservation: {reason} {message}"
        self.data = data

    def __str__(self):
        return self.message

    def get_price_change_info(self):
        return self.data
