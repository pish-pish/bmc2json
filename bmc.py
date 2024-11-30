import binary
import json
import argparse
from dataclasses import dataclass, field
from io import BufferedIOBase
from pathlib import Path
from itertools import chain


@dataclass
class JDataHeader:
    signature: str = ""
    size: int = 0
    _section_start: int = field(init=False, repr=False)
    _size_offset: int = field(init=False, repr=False)

    @classmethod
    def from_file(cls, signature: str, f: BufferedIOBase):
        kind = f.read(len(signature)).decode()
        assert kind == signature

        size = binary.read_u32(f)

        return cls(kind, size)

    def write(self, f: BufferedIOBase):
        self._section_start = f.tell()
        f.write(self.signature.encode())
        self._size_offset = f.tell()
        binary.write_u32(f, self.size)

    def write_size(self, f: BufferedIOBase):
        self.size = f.tell()
        f.seek(self._size_offset)
        binary.write_u32(f, self.size - self._section_start)
        f.seek(self.size)


@dataclass
class Color:
    red: int
    green: int
    blue: int
    alpha: int

    def write(self, f: BufferedIOBase):
        binary.write_u8(f, self.red)
        binary.write_u8(f, self.green)
        binary.write_u8(f, self.blue)
        binary.write_u8(f, self.alpha)

    @classmethod
    def from_file(cls, f: BufferedIOBase):
        red = binary.read_u8(f)
        green = binary.read_u8(f)
        blue = binary.read_u8(f)
        alpha = binary.read_u8(f)
        return cls(red, green, blue, alpha)

    @classmethod
    def from_string(cls, string: str):
        components = [string[i : i + 2] for i in range(0, len(string), 2)]
        return cls(
            int(components[0], 16),
            int(components[1], 16),
            int(components[2], 16),
            int(components[3], 16),
        )

    def __repr__(self) -> str:
        color = (self.red << 24) + (self.green << 16) + (self.blue << 8) + (self.alpha)
        return hex(color).strip("0x").rjust(8, "0").upper()


@dataclass
class ColorTable(JDataHeader):
    MAGIC = "CLT1"

    entry_count: int = 0
    color_array: list[Color] = field(default_factory=list)

    def __post_init__(self):
        self.signature = self.MAGIC

    def write(self, f: BufferedIOBase):
        super().write(f)
        binary.write_u16(f, self.entry_count)
        binary.write_u16(f, 0)  # padding

        for color in self.color_array:
            color.write(f)

    def dump_json(self, color_group_size=1) -> dict[str, list]:
        dict = {"Colors": list()}

        if color_group_size <= 1 or self.entry_count % color_group_size != 0:
            dict["Colors"] = [str(color) for color in self.color_array]
            return dict

        for i in range(0, self.entry_count, color_group_size):
            dict["Colors"].append(
                [str(self.color_array[i + j]) for j in range(color_group_size)]
            )
        return dict

    @classmethod
    def from_file(cls, f: BufferedIOBase):  # type: ignore
        table = super().from_file(cls.MAGIC, f)
        table.entry_count = binary.read_u16(f)
        binary.read_u16(f)  # skip padding

        for _ in range(table.entry_count):
            table.color_array.append(Color.from_file(f))

        return table

    @classmethod
    def from_array(cls, array: list):
        flat_array = []
        for item in array:
            if isinstance(item, list):
                flat_array.extend(item)
                continue

            flat_array.append(item)

        table = cls()
        table.color_array = [Color.from_string(color) for color in flat_array]
        table.entry_count = len(table.color_array)

        return table


@dataclass
class BinaryMessageColor:
    MAGIC = "MGCLbmc1"
    SECTIONS = 1

    header: JDataHeader = field(default_factory=JDataHeader)
    color_table: ColorTable = field(default_factory=ColorTable)

    def __post_init__(self):
        self.header = JDataHeader(self.MAGIC)
        self.color_table = ColorTable()

    def write(self, filepath: str):
        path = Path(filepath)
        with open(path, "wb") as f:
            self.header.write(f)

            binary.write_u32(f, self.SECTIONS)
            binary.write_zero_padding(f, 16)

            self.color_table.write(f)
            binary.write_zero_padding(f, 16)
            self.color_table.write_size(f)

            self.header.write_size(f)

    def dump_json(self, filepath: str, group_size: int):
        path = Path(filepath)
        with open(path, "w") as f:
            json.dump(self.color_table.dump_json(group_size), f, indent=4)

    @classmethod
    def from_file(cls, filepath: str):
        path = Path(filepath)

        with open(path, "rb") as f:
            header = JDataHeader.from_file(cls.MAGIC, f)

            section_count = binary.read_u32(f)
            assert section_count == cls.SECTIONS
            binary.skip_padding(f, 16)

            color_table = ColorTable.from_file(f)

            # bitch
            bmc = cls()
            bmc.header = header
            bmc.color_table = color_table

        return bmc

    @classmethod
    def from_json(cls, filepath: str):
        path = Path(filepath)
        with open(path, "r") as f:
            color_array = json.load(f)["Colors"]

            bmc = cls()
            bmc.color_table = ColorTable.from_array(color_array)

        return bmc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, required=True)
    parser.add_argument("-o", "--output", type=str, required=True)
    parser.add_argument("--tojson", type=int)
    parser.add_argument("--tobinary", action="store_true")

    args = parser.parse_args()

    if args.tobinary:
        bmc = BinaryMessageColor.from_json(args.input)
        bmc.write(args.output)
    elif args.tojson:
        bmc = BinaryMessageColor.from_file(args.input)
        bmc.dump_json(args.output, args.tojson)
