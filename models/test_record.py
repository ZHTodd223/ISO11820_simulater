"""试验记录模型。"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestRecord:
    """一次试验的基础信息与结果信息。"""

    productid: str
    testid: str
    productname: str
    specific: str
    diameter: float
    height: float
    operator: str
    preweight: float
    ambtemp: float = 25.0
    ambhumi: float = 50.0
    testdate: str = ""
    postweight: float = 0.0
    memo: str = ""

    def __post_init__(self) -> None:
        if not self.testdate:
            self.testdate = datetime.now().strftime("%Y-%m-%d")
