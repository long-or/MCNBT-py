"""
    root.py - 根标签相关
"""


from typing import Literal, Union
from io import StringIO, BytesIO, IOBase, RawIOBase, BufferedIOBase, TextIOBase
import zlib, gzip, os

from .error import *
from . import tags, snbt, codec as ce, TAG, TAGLIST

def buffer_is_texts_io(buffer):
    return True if isinstance(buffer, TextIOBase) else False

def buffer_is_bytes_io(buffer):
    return True if isinstance(buffer, (RawIOBase, BufferedIOBase)) else False

def path_is_file(path):
    if not os.path.exists(path): raise NbtFileError("路径('%s')未找到" % path)
    if not os.path.isfile(path): raise NbtFileError("路径('%s')非文件" % path)

def compress_file(data, zip_mode):
    if zip_mode == 'zlib':
        return zlib.compress(data)
    if zip_mode == 'gzip':
        return gzip.compress(data)
    if zip_mode == 'none':
        return data
    
def decompress_file(path, zip_mode):
    path_is_file(path)
    if zip_mode is None:
        with open(path, "rb") as f: head_byte = f.read(2)
        if   head_byte == b'\x78\x9C': zip_mode = "zlib"
        elif head_byte == b'\x1F\x8B': zip_mode = "gzip"
        else:                          zip_mode = "none"
    if zip_mode == 'zlib':
        f = open(path, 'rb')
        byte = f.read()
        if byte == b'': raise NbtFileError("文件(%s)是空文件" % f)
        try:
            data = zlib.decompress(byte)
        except Exception as e:
            raise NbtFileError("文件(%s)zlib解压失败: %s" % (f, e.args[0]))
        return BytesIO(data)
    if zip_mode == 'gzip':
        try:
            return gzip.open(path, 'rb')
        except Exception as e:
            raise NbtFileError("文件(%s)gzip解压失败: %s" % (f, e.args[0]))
    if zip_mode == 'none':
        return open(path, 'rb')


class RootNBT:
    def __init__(self, tag=None, root_name=""):
        self.__tag = tags.TAG_Compound() if tag is None else tag
        self.__root_name = root_name

    # === nbt ===
    @classmethod
    def from_nbt(cls,
        data     : Union[str, bytes, IOBase],
        zip_mode : Literal['none', 'gzip', 'zlib'] = None,
        byteorder: Literal['little', 'big'] = 'little'):
        if isinstance(data, str):
            data = decompress_file(data, zip_mode)
        if isinstance(data, bytes):
            data = BytesIO(data)
        if not buffer_is_bytes_io(data):
            raise NbtBufferError("不符合要求(二进制流)的数据(%s)" % data)
        if not data.readable():
            raise NbtBufferError("不符合要求(读取流)的数据(%s)" % data)
        if not data.seekable():
            raise NbtBufferError("不符合要求(随机读写流)的数据(%s)" % data)
        data = NBT_Data.parse(data, byteorder == 'big')
        return cls(data._tag, data._root_name)
    
    def to_nbt(self,
        target   : Union[str, IOBase] = None,
        zip_mode : Literal['none', 'gzip', 'zlib'] = 'none',
        byteorder: Literal['little', 'big'] = 'little'):
        res = True if target is None else False
        if target is None:
            target = BytesIO()
        if isinstance(target, str):
            target = open(target, 'wb')
        if not buffer_is_bytes_io(target):
            raise NbtBufferError("不符合要求(二进制流)的数据(%s)" % target)
        if not target.writable():
            raise NbtBufferError("不符合要求(写入流)的数据(%s)" % target)
        if not target.seekable():
            raise NbtBufferError("不符合要求(随机读写流)的数据(%s)" % target)
        data = NBT_Data(self.__tag, self.__root_name)
        data = data.render(byteorder == 'big')
        data = compress_file(data, zip_mode)
        if res:
            return data
        else:
            target.write(data)

    # === snbt ===
    @classmethod
    def from_snbt(cls, data: Union[str, IOBase]):
        if isinstance(data, str):
            if os.path.exists(data) and not os.path.isfile(data): raise NbtFileError("路径('%s')非文件" % data)
            if os.path.exists(data) and os.path.isfile(data): data = open(data, 'r')
            elif not os.path.exists(data): data = StringIO(data)
        if not buffer_is_texts_io(data):
            raise NbtBufferError("不符合要求(字符串流)的数据(%s)" % data)
        if not data.seekable():
            raise NbtBufferError("不符合要求(随机读写流)的数据(%s)" % data)
        data = SNBT_Data.parse(data)
        return cls(data._tag, data._root_name)

    def to_snbt(self, target: Union[str, IOBase] = None, format=False, size=4):
        res = True if target is None else False
        if target is None:
            target = StringIO()
        if isinstance(target, str):
            target = open(target, 'w')
        if not buffer_is_texts_io(target):
            raise NbtBufferError("不符合要求(二进制流)的数据(%s)" % target)
        if not target.writable():
            raise NbtBufferError("不符合要求(写入流)的数据(%s)" % target)
        if not target.seekable():
            raise NbtBufferError("不符合要求(随机读写流)的数据(%s)" % target)
        data = SNBT_Data(self.__tag, self.__root_name)
        data = data.render(target, format, size)
        if res:
            return data.read()

    # === dat ===
    @classmethod
    def from_dat(cls,
        data     : Union[str, bytes, IOBase],
        zip_mode : Literal['none', 'gzip', 'zlib'] = 'none',
        byteorder: Literal['little', 'big'] = 'little'):
        if isinstance(data, str):
            data = decompress_file(data, zip_mode)
        if isinstance(data, bytes):
            data = BytesIO(data)
        if not buffer_is_bytes_io(data):
            raise NbtBufferError("不符合要求(二进制流)的数据(%s)" % data)
        if not data.seekable():
            raise NbtBufferError("不符合要求(随机读写流)的数据(%s)" % data)
        byte = buffer_read(data, 4, "工具版本号")
        try:
            tool_version = ce.unpack_data(byte, TAG.INT, byteorder == 'big')
        except Exception as e:
            throw_nbt_error(e, data, 4)
        byte = buffer_read(data, 4, "除头文件后的长度")
        try:
            length = ce.unpack_data(byte, TAG.INT, byteorder == 'big')
        except Exception as e:
            throw_nbt_error(e, data, 4)
        data = NBT_Data.parse(data, byteorder == 'big')
        return cls(data._tag, data._root_name)

    def to_dat(self,
        target   : Union[str, IOBase] = None,
        zip_mode : Literal['none', 'gzip', 'zlib'] = 'none',
        byteorder: Literal['little', 'big'] = 'little'):
        res = True if target is None else False
        if target is None:
            target = BytesIO()
        if isinstance(target, str):
            target = open(target, 'wb')
        if not buffer_is_bytes_io(target):
            raise NbtBufferError("不符合要求(二进制流)的数据(%s)" % target)
        if not target.writable():
            raise NbtBufferError("不符合要求(写入流)的数据(%s)" % target)
        if not target.seekable():
            raise NbtBufferError("不符合要求(随机读写流)的数据(%s)" % target)
        data = NBT_Data(self.__tag, self.__root_name)
        data = data.render(byteorder == 'big')
        data = b'\x0A\x00\x00\00' + ce.pack_data(len(data), TAG.INT, byteorder == 'big') + data
        data = compress_file(data, zip_mode)
        if res:
            return data
        else:
            target.write(data)

    def get_tag(self):
        return self.__tag

    def path(self, path):
        pass
    
    def __repr__(self):
        return f"{repr(self.__class__)[:-1]} object\n    {repr(self.__root_name)}: {repr(self.__tag)}\nat 0x{id(self)}>"


class DataBase:
    def __init__(self, tag, root_name=''):
        self._tag = tag
        self._root_name = root_name

    @classmethod
    def parse(cls, buffer):
        if not isinstance(buffer, IOBase): NbtBufferError("源数据(%s)非IO 应该为 %s" % (buffer, IOBase))


class SNBT_Data(DataBase):
    @classmethod
    def parse(cls, buffer):
        super().parse(buffer)
        if not buffer_is_texts_io(buffer): NbtBufferError("源数据(%s)非文本IO 应该为 %s" % (buffer, TextIOBase))
        res = cls(1)
        buffer = snbt.SnbtIO(buffer.read())
        token = buffer._read_one()
        type = token[0]
        if type in {"Int", "Float", "Key"}:
            res._root_name = token[1]
            if buffer._read_one()[1] != ":": buffer.throw_error(token, ":")
            token = buffer._read_one()
        elif type in {"SString", "DString"}:
            res._root_name = ce.string_to_str(token[1])
            if buffer._read_one()[1] != ":": buffer.throw_error(token, ":")
            token = buffer._read_one()
        else:
            res._root_name = ''
        if token[1] == "{":
            res._tag = tags.TAG_Compound._from_snbtIO(buffer)
            buffer.close()
        elif token[1] == "[":
            res._tag = tags.TAG_List._from_snbtIO(buffer)
            buffer.close()
        else:
            buffer.throw_error(token, "{ [")
        buffer.close()
        return res
    
    def render(self, target, format, size):
        if not isinstance(size, int): raise TypeError("缩进期望类型为 %s，但传入了 %s" % (int, size.__class__))
        if not 1 <= size <= 16: raise ValueError("超出范围(1 ~ 16)的数字 %s" % size)
        if not format:
            target.write(f'{ce.str_to_snbt_key(self._root_name)}:{self._tag._to_snbt()}')
        else:
            target.write(f'{ce.str_to_snbt_key(self._root_name)}:{self._tag._to_snbt_format(target, 1, size)}')
        return target


class NBT_Data(DataBase):
    @classmethod
    def parse(cls, buffer, mode):
        super().parse(buffer)
        if not buffer_is_bytes_io(buffer): NbtBufferError("源数据(%s)非二进制IO 应该为 %s" % (buffer, (RawIOBase, BufferedIOBase)))
        res = cls(1)
        byte = buffer_read(buffer, 1, "根标签类型")
        try:
            if (type := ce.bytes_to_tag_type(byte)) not in [TAG.COMPOUND, TAG.LIST]:
                raise NbtDataError("数据的根标签必须是TAG_Compound或TAG_List，但实际是 %s" % type)
        except Exception as e:
            throw_nbt_error(e, buffer, 1)
        byte = buffer_read(buffer, 2, "根标签键名长度")
        try:
            length = ce.bytes_to_length(byte, mode)
        except Exception as e:
            throw_nbt_error(e, buffer, 2)
        byte = buffer_read(buffer, length, "根标签键名")
        try:
            res._root_name = ce.unpack_data(byte, TAG.STRING)
        except Exception as e:
            throw_nbt_error(e, buffer, length)
        res._tag = TAGLIST[type]._from_bytesIO(buffer, mode)
        buffer.close()
        return res

    def render(self, mode):
        res = bytearray()
        name = ce.pack_data(self._root_name, TAG.STRING)
        res.extend(ce.tag_type_to_bytes(self._tag.type))
        res.extend(ce.length_to_bytes(len(name), mode))
        res.extend(name)
        res.extend(self._tag.to_bytes(mode))
        return bytes(res)


def read_from_nbt_file(
    data     : Union[str, bytes, IOBase],
    zip_mode : Literal['none', 'gzip', 'zlib'] = 'none',
    byteorder: Literal['little', 'big'] = 'little') -> RootNBT:
    return RootNBT.from_nbt(data, zip_mode, byteorder)

def write_to_nbt_file(
    file     : Union[str, IOBase],
    tag      : Union[tags.TAG_List, tags.TAG_Compound, RootNBT],
    zip_mode : Literal['none', 'gzip', 'zlib'] = 'none',
    byteorder: Literal['little','big'] = 'little',
    root_name: str = ''):
    if isinstance(tag, (tags.TAG_List, tags.TAG_Compound)):
        tag = RootNBT(tag, root_name)
    tag.to_nbt(file, zip_mode, byteorder)

def read_from_dat_file(
    data     : Union[str, bytes, IOBase],
    zip_mode : Literal['none', 'gzip', 'zlib'] = 'none',
    byteorder: Literal['little', 'big'] = 'little') -> RootNBT:
    return RootNBT.from_dat(data, zip_mode, byteorder)

def write_to_dat_file(
    file     : Union[str, IOBase],
    tag      : Union[tags.TAG_List, tags.TAG_Compound, RootNBT],
    zip_mode : Literal['none', 'gzip', 'zlib'] = 'none',
    byteorder: Literal['little','big'] = 'little',
    root_name: str = ''):
    if isinstance(tag, (tags.TAG_List, tags.TAG_Compound)):
        tag = RootNBT(tag, root_name)
    tag.to_dat(file, zip_mode, byteorder)

def read_from_snbt_file(data: Union[str, bytes, IOBase]) -> RootNBT:
    return RootNBT.from_snbt(data)

def write_to_snbt_file(
    file     : Union[str, IOBase],
    tag      : Union[tags.TAG_List, tags.TAG_Compound, RootNBT],
    root_name: str = '',
    format   : Literal[True, False] = False,
    size     : str = 4):
    if isinstance(tag, (tags.TAG_List, tags.TAG_Compound)):
        tag = RootNBT(tag, root_name)
    tag.to_snbt(file, format, size)
