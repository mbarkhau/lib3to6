import sys


def hello(who: str) -> None:
    print(f"Hello {who} from {sys.version.split()[0]}!")


print(__file__)
hello("世界")
