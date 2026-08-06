import traceback
from dataclasses import dataclass


@dataclass
class ExceptionInfo:
    exception_type: str
    file_path: str
    line_number: int
    stack_trace: str


def extract_exception_info(exc: BaseException) -> ExceptionInfo:
    frames = traceback.extract_tb(exc.__traceback__)
    origin_frame = frames[-1]
    stack_trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    return ExceptionInfo(
        exception_type=type(exc).__name__,
        file_path=origin_frame.filename,
        line_number=origin_frame.lineno,
        stack_trace=stack_trace,
    )
