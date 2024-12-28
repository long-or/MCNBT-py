"""
    tags.py - nbt的所有标签
"""


from abc import ABC
from io import BytesIO, StringIO, IOBase
from copy import deepcopy
from array import array
from math import ceil
from collections import deque

from . import TAGLIST, TAG, codec as ce
from .error import *
from .snbt import SnbtIO, get_line

ARRAY_TYPECODE = {
    TAG.BYTE:   "b",
    TAG.SHORT:  "h",
    TAG.INT:    "i",
    TAG.LONG:   "q",
    TAG.FLOAT:  "f",
    TAG.DOUBLE: "d",
}

def buffer_is_readable(buffer):
    if not isinstance(buffer, IOBase): return False
    if not buffer.readable(): raise TypeError("io(%s)不能读" % buffer)
    buffer_is_seekable(buffer)
    return True

def buffer_is_writable(buffer):
    if not isinstance(buffer, IOBase): return False
    if not buffer.writable(): raise TypeError("io(%s)不能写" % buffer)
    buffer_is_seekable(buffer)
    return True

def buffer_is_seekable(buffer):
    if not buffer.seekable(): raise TypeError("io(%s)不能随机访问" % buffer)

def try_to_number(v):
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, TAG_Number):
        return v.get_value()
    raise ValueError("数值自动转换失败：" + repr(v))


class BaseTag:
    type: TAG = None
    __slots__ = ()

    @classmethod
    def from_bytes(cls, buffer, mode=False):
        if buffer_is_readable(buffer):
            return cls._from_bytesIO(buffer, mode)
        elif isinstance(buffer, bytes):
            return cls._from_bytes(buffer, mode)
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % ((BytesIO, bytes), buffer.__class__))

    @classmethod
    def from_snbt(cls, buffer):
        if isinstance(buffer, SnbtIO):
            return cls._from_snbtIO(buffer)
        elif isinstance(buffer, str):
            return cls._from_snbt(buffer)

    def get_value(self): assert False

    def set_value(self, value): assert False

    def to_string(self): assert False

    def to_snbt(self, format=False): assert False

    def to_bytes(self): assert False

    def print_info(self):
        print(self.get_info())

    def get_info(self):
        return repr(self)

    @property
    def value(self):
        self.get_value()

    @value.setter
    def value(self, value):
        self.set_value(value)

    @property
    def id(self):
        return self.type.value

    @id.setter
    def id(self, value):
        raise ValueError("id属性是只读的")


class TAG_End(BaseTag):
    type = TAG.END


class Meta(type):
    def __init__(self, *arg) :
        super().__init__(*arg)
        self._memory = {}
    
    def __call__(self, v) :
        v = try_to_number(v)
        if v not in self._memory:
            self._memory[v] = super().__call__(v)
        return self._memory[v]


class TAG_Number(BaseTag):
    type = None
    unit = None
    
    def __init__(self, value):
        if isinstance(value, (int, float)):
            self.__value = value
            self.to_bytes()
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % ((int, float), value.__class__))

    @classmethod
    def _from_bytes(cls, buffer, mode=False):
        return cls(ce.unpack_data(buffer, cls.type, mode)[0])

    @classmethod
    def _from_bytesIO(cls, buffer, mode=False):
        length = ce.number_bytes_len[cls.type]
        byte = buffer_read(buffer, length, "数字")
        try:
            return cls._from_bytes(byte, mode)
        except Exception as e:
            throw_nbt_error(e, buffer, length)

    @classmethod
    def _from_snbt(cls, buffer):
        buffer = SnbtIO(buffer)
        res = cls._from_snbtIO(buffer)
        buffer.close()

    @classmethod
    def _from_snbtIO(cls, buffer):
        token = buffer._read_one()
        value = buffer.parse_value(token)
        if value.type == cls.type:
            return value
        else:
            buffer.throw_error(token, "数字")

    def get_value(self):
        return self.__value

    def set_value(self, value):
        raise Exception("不能调用的方法")
    
    def to_string(self):
        return f"{self.get_value()}"
    
    def to_snbt(self, format=False, indent=4):
        return self._to_snbt()
    
    def _to_snbt(self):
        try:
            return self.__snbt_cache
        except:
            self.__snbt_cache = f"{self.get_value()}{self.unit}"
            return self.__snbt_cache
    
    def _to_snbt_format(self, buffer, indent, size):
        buffer.write(self._to_snbt())
    
    def to_bytes(self, mode=False):
        try:
            return self.__byte_cache
        except:
            self.__byte_cache = ce.pack_data(self.__value, self.type, mode)
            return self.__byte_cache

    def get_info(self):
        return f'{self.__class__.__name__}({self.get_value()})'

    def __repr__(self):
        return f"<{self.type} value={self.to_string()} bytes={self.to_bytes()} at 0x{id(self)}>"
    
    def __str__(self):
        return self.to_string()
    
    def __bytes__(self):
        return self.to_bytes()
    
    def __hash__(self):
        return hash(self.get_value())
    
    def __bool__(self):
        return bool(self.get_value())
    
    def __format__(self, fs):
        return format(self.get_value(), fs)
    
    def __lt__(self, other):
        return self.get_value() < try_to_number(other)
    
    def __le__(self, other):
        return self.get_value() <= try_to_number(other)
    
    def __eq__(self, other):
        return self.get_value() == try_to_number(other)
    
    def __ne__(self, other):
        return self.get_value() != try_to_number(other)
    
    def __gt__(self, other):
        return self.get_value() > try_to_number(other)
    
    def __ge__(self, other):
        return self.get_value() >= try_to_number(other)
    
    def __add__(self, other):
        return self.__class__(self.get_value() + try_to_number(other))
    
    def __sub__(self, other):
        return self.__class__(self.get_value() - try_to_number(other))
    
    def __mul__(self, other):
        return self.__class__(self.get_value() * try_to_number(other))
    
    def __truediv__(self, other):
        return self.__class__(self.get_value() / try_to_number(other))
    
    def __floordiv__(self, other):
        return self.__class__(self.get_value() // try_to_number(other))
    
    def __mod__(self, other):
        return self.__class__(self.get_value() + try_to_number(other))
    
    def __divmod__(self, other):
        q = self.__class__(self.get_value() // try_to_number(other))
        r = self.__class__(self.get_value() % try_to_number(other))
        return (q, r)
    
    def __pow__(self, other, modulo=None):
        res = self.get_value() ** try_to_number(other)
        if modulo is not None:
            res = res % modulo
        return self.__class__(res)
    
    def __lshift__(self, other):
        return self.__class__(self.get_value() << try_to_number(other))
    
    def __rshift__(self, other):
        return self.__class__(self.get_value() >> try_to_number(other))
    
    def __and__(self, other):
        return self.__class__(self.get_value() & try_to_number(other))
    
    def __xor__(self, other):
        return self.__class__(self.get_value() ^ try_to_number(other))
    
    def __or__(self, other):
        return self.__class__(self.get_value() | try_to_number(other))
    
    def __radd__(self, other):
        return self.__class__(self.get_value() + try_to_number(other))
    
    def __rsub__(self, other):
        return self.__class__(self.get_value() - try_to_number(other))
    
    def __rmul__(self, other):
        return self.__class__(self.get_value() * try_to_number(other))
    
    def __rtruediv__(self, other):
        return self.__class__(self.get_value() / try_to_number(other))
    
    def __rfloordiv__(self, other):
        return self.__class__(self.get_value() // try_to_number(other))
    
    def __rmod__(self, other):
        return self.__class__(self.get_value() + try_to_number(other))
    
    def __rdivmod__(self, other):
        q = self.__class__(self.get_value() // try_to_number(other))
        r = self.__class__(self.get_value() % try_to_number(other))
        return (q, r)
    
    def __rpow__(self, other, modulo=None):
        res = self.get_value() ** try_to_number(other)
        if modulo is not None:
            res = res % modulo
        return self.__class__(res)
    
    def __rlshift__(self, other):
        return self.__class__(self.get_value() << try_to_number(other))
    
    def __rrshift__(self, other):
        return self.__class__(self.get_value() >> try_to_number(other))
    
    def __rand__(self, other):
        return self.__class__(self.get_value() & try_to_number(other))
    
    def __rxor__(self, other):
        return self.__class__(self.get_value() ^ try_to_number(other))
    
    def __ror__(self, other):
        return self.__class__(self.get_value() | try_to_number(other))
    
    def __pos__(self):
        return self.__class__(+self.get_value())
    
    def __neg__(self):
        return self.__class__(-self.get_value())
    
    def __abs__(self):
        return self.__class__(abs(self.get_value()))
    
    def __invert__(self):
        return self.__class__(~self.get_value())
    
    def __float__(self):
        return TAG_Double(self.get_value())
    
    def __round__(self, n=None):
        return self.__class__(round(self.get_value(), n) if n else round(self.get_value()))
    
    def __index__(self):
        return int(self.get_value())


class TAG_Byte(TAG_Number, metaclass=Meta):
    type = TAG.BYTE
    unit = "b"


class TAG_Short(TAG_Number, metaclass=Meta):
    type = TAG.SHORT
    unit = "s"


class TAG_Int(TAG_Number, metaclass=Meta):
    type = TAG.INT
    unit = ""


class TAG_Long(TAG_Number, metaclass=Meta):
    type = TAG.LONG
    unit = "l"


class TAG_Float(TAG_Number, metaclass=Meta):
    type = TAG.FLOAT
    unit = "f"


class TAG_Double(TAG_Number, metaclass=Meta):
    type = TAG.DOUBLE
    unit = "d"


class TAG_String(BaseTag):
    type = TAG.STRING
    
    def __init__(self, value):
        self.__value = None
        self.__cache = None
        if isinstance(value, str):
            self.__value = ce.pack_data(value, self.type)
            self.__cache = value
        elif isinstance(value, bytes):
            self.__value = value
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % ((str, bytes), value.__class__))

    @classmethod
    def _from_bytes(cls, buffer, mode=False):
        return cls(buffer[2:])

    @classmethod
    def _from_bytesIO(cls, buffer, mode=False):
        byte = buffer_read(buffer, 2, "字符串长度")
        try:
            length = ce.bytes_to_length(byte, mode)
        except Exception as e:
            throw_nbt_error(e, buffer, 2)
        byte = buffer_read(buffer, length, "字符串")
        try:
            return cls(byte)
        except Exception as e:
            throw_nbt_error(e, buffer, length)

    @classmethod
    def _from_snbt(cls, buffer):
        buffer = SnbtIO(buffer)
        res = cls._from_snbtIO(buffer)
        buffer.close()

    @classmethod
    def _from_snbtIO(cls, buffer):
        token = buffer._read_one()
        value = buffer.parse_value(token)
        if value.type == cls.type:
            return value
        else:
            buffer.throw_error(token, "字符串")

    def to_string(self):
        return f'{self.get_value()}'

    def to_snbt(self, format=False, size=4):
        return self._to_snbt()
    
    def _to_snbt(self):
        try:
            return self.__snbt_cache
        except:
            self.__snbt_cache = ce.str_to_string(self.get_value())
            return self.__snbt_cache

    def _to_snbt_format(self, buffer, indent, size):
        buffer.write(self._to_snbt())

    def to_bytes(self, mode=False):
        return ce.length_to_bytes(len(self.__value), mode) + self.__value

    def get_value(self):
        if self.__cache is None:
            self.__cache = ce.unpack_data(self.__value, self.type)
        return self.__cache

    def set_value(self, value):
        if isinstance(value, str):
            self.__value = ce.pack_data(value, self.type)
            self.__cache = value
        elif isinstance(value, bytes):
            self.__value = value
            self.__cache = None
        elif isinstance(value, TAG_String):
            self.__value = value.to_bytes()
            self.__cache = None
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % ((str, bytes, TAG_String), value.__class__))

    def get_info(self):
        return f'{self.__class__.__name__}({self.to_snbt()})'

    def __len__(self):
        return len(self.get_value())

    def __repr__(self):
        s = self.to_string()
        b = self.to_bytes()
        s = s if len(s) <= 10 else s[:7] +  '...'
        b = b if len(b) <= 10 else b[:7] + b'...'
        return f"<{self.type} value={s} bytes={b} at 0x{id(self)}>"
    
    def __str__(self):
        return self.to_string()
    
    def __bytes__(self):
        return self.to_bytes()
    
    def __hash__(self):
        return hash(self.get_value())
    
    def __bool__(self):
        return bool(self.get_value())
    
    def __format__(self, fs):
        return format(self.get_value(), fs)
    
    def __add__(self, other):
        if isinstance(other, str):
            return TAG_String(self.get_value() + other)
        elif isinstance(other, TAG_String):
            return TAG_String(self.get_value() + other.to_string())
        else:
            raise TypeError("")
    
    def __radd__(self, other):
        if isinstance(other, str):
            return TAG_String(self.get_value() + other)
        elif isinstance(other, TAG_String):
            return TAG_String(self.get_value() + other.to_string())
        else:
            raise TypeError("")
    
    def __mul__(self, other):
        self.__value *= other
    
    def __mod__(self, other):
        return TAG_String(self.get_value() % other)


class TAG_List(BaseTag):
    type = TAG.LIST
    
    def __init__(self, value=None, type=TAG.END):
        self.__type = None
        self.__value = []
        self.set_type(type)
        if value is None: return
        self.set_value(value)

    @classmethod
    def _from_bytes(cls, buffer, mode=False):
        return cls._from_bytesIO(BytesIO(buffer), mode)

    @classmethod
    def _from_bytesIO(cls, buffer, mode=False):
        byte = buffer_read(buffer, 1, "列表元素类型标签")
        try:
            type = ce.bytes_to_tag_type(byte)
        except Exception as e:
            throw_nbt_error(e, buffer, 1)
        tag = TAGLIST[type]
        byte = buffer_read(buffer, 4, "列表元素数量")
        try:
            count = ce.unpack_data(byte, TAG.INT, mode)[0]
        except Exception as e:
            throw_nbt_error(e, buffer, 4)
        List = cls()
        List.set_type(type)
        if type in list(ARRAY_TYPECODE.keys()):
            res = array(ARRAY_TYPECODE[type])
            length = ce.number_bytes_len[type]
            byte = buffer_read(buffer, count * length, "列表元素内容")
            try:
                res.frombytes(byte)
            except Exception as e:
                throw_nbt_error(e, buffer, length)
            if mode: res.byteswap()
            List.__value = res
        else:
            res = [None] * count
            for i in range(count):
                res[i] = tag._from_bytesIO(buffer, mode)
            List.__value = res
        List.test_type()
        return List

    @classmethod
    def _from_snbt(cls, buffer):
        buffer = SnbtIO(buffer)
        token = buffer._read_one()
        if token[1] == "[":
            res = cls._from_snbtIO(buffer)
            buffer.close()
            return res
        else:
            buffer.throw_error(token, "[")

    @classmethod
    def _from_snbtIO(cls, buffer):
        res, List, Type, is_number = deque(), cls(), None, False
        token = buffer._read_one()
        if token[1] == "]":
            return cls()
        elif token[1] == "B" and buffer._read_one()[1] == ";":
            return TAG_ByteArray._from_snbtIO(buffer)
        elif token[1] == "I" and buffer._read_one()[1] == ";":
            return TAG_IntArray._from_snbtIO(buffer)
        elif token[1] == "L" and buffer._read_one()[1] == ";":
            return TAG_LongArray._from_snbtIO(buffer)
        value = buffer.parse_value(token)
        res.append(value)
        Type = value.type
        if token[0] == "Int" or token[0] == "Float":
            is_number = True
        while True:
            token = buffer._read_one()
            if token[1] == "]":
                List.set_type(Type)
                if is_number:
                    List.__value = array(ARRAY_TYPECODE[Type])
                    List.__value.fromlist(list(res))
                else:
                    List.__value = list(res)
                return List
            elif not token[1] == ",":
                buffer.throw_error(token, ", ]")
            token = buffer._read_one()
            if is_number:
                value = buffer.parse_py_number(token[0], token[1])
                if value is None: raise SnbtParseError("无法解析的数字 '%s' 位于第%s行 第%s个字符到第%s个字符" % (token[1], *get_line(buffer.code, token[2])))
                res.append(value)
                continue
            value = buffer.parse_value(token)
            if value.type == Type:
                res.append(value)
            else:
                buffer.throw_error(token, f"类型:{Type}")

    def to_string(self):
        if self.__is_number_list:
            return "[" + ', '.join([str(i) for i in self.__value]) + "]"
        else:
            return "[" + ', '.join([i.to_string() for i in self.__value]) + "]"

    def to_snbt(self, format=False, size=4):
        if not isinstance(size, int): raise TypeError("缩进期望类型为 %s，但传入了 %s" % (int, size.__class__))
        if not 1 <= size <= 16: raise ValueError("超出范围(1 ~ 16)的数字 %s" % size)
        if format:
            buffer = StringIO()
            self._to_snbt_format(buffer, 1, size)
            buffer.seek(0)
            return buffer.read()
        else:
            return self._to_snbt()

    def _to_snbt(self):
        if self.__is_number_list:
            return "[" + ','.join([i._to_snbt() for i in self]) + "]"
        else:
            return "[" + ','.join([i._to_snbt() for i in self.__value]) + "]"

    def _to_snbt_format(self, buffer, indent, size):
        count, tab = len(self.__value), " " * size
        if count == 0:
            buffer.write("[]")
            return
        type1 = [TAG.BYTE, TAG.SHORT]
        type2 = [TAG.INT, TAG.LONG, TAG.FLOAT, TAG.DOUBLE]
        type3 = type1 + type2
        if count <= 5:
            if self.__type in type1:
                buffer.write("[" + ', '.join([i._to_snbt() for i in self]) + "]")
                return
            elif self.__type in type3 and count <= 3:
                buffer.write("[" + ', '.join([i._to_snbt() for i in self]) + "]")
                return
            elif self.__type == TAG.STRING and count <= 1:
                buffer.write("[" + ', '.join([i._to_snbt() for i in self]) + "]")
                return
        elif count >= 16 and self.__type in type3:
            width  = count ** 0.5
            height = int(width) if int(width) == width else int(width) + 1
            width = ceil(width)
            count2, height2 = count - 1, height - 2
            buffer.write("[\n")
            unit = TAGLIST[self.__type].unit
            for i in range(height):
                buffer.write(tab * indent)
                for k in range(width):
                    index = i * width + k
                    if i >= height2 and index == count2:
                        buffer.write(f"{self.__value[index]}{unit}")
                        break
                    else:
                        buffer.write(f"{self.__value[index]}{unit}, ")
                else:
                    buffer.write("\n")
                    continue
                break
            buffer.write("\n" + tab * (indent - 1) + "]")
            return
        nbt = self if self.__is_number_list else self.__value
        buffer.write("[\n")
        for v, i in zip(nbt, range(1, count + 1)):
            buffer.write(tab * indent)
            v._to_snbt_format(buffer, indent + 1, size)
            if i < count: buffer.write(",\n")
        buffer.write("\n" + tab * (indent - 1) + "]")

    def to_bytes(self, mode=False):
        byte = None
        if self.__is_number_list:
            if mode: self.__value.byteswap()
            byte = self.__value.tobytes()
            if mode: self.__value.byteswap()
        else:
            byte = b''.join([i.to_bytes(mode) for i in self.__value])
        return ce.tag_type_to_bytes(self.__type)\
             + ce.pack_data(len(self.__value), TAG.INT, mode)\
             + byte
    
    def get_value(self):
        if self.__is_number_list:
            return [TAGLIST[self.__type](i) for i in self.__value]
        else:
            return deepcopy(self.__value)
    
    def set_value(self, value):
        if isinstance(value, list):
            type = None
            for v in value:
                if not isinstance(v, BaseTag):
                    raise TypeError("TAG_List容器类型期望类型为 %s，但传入了 %s" % (tuple(TAGLIST.values()), v.__class__))
                if type is None:
                    type = v.type
                elif not type == v.type:
                    raise TypeError("TAG_List容器元素期望类型为 %s，但传入了 %s" % (type, v.type))
            self.__type = type
            self.test_type()
            self.__value = value.copy()
        elif isinstance(value, TAG_List):
            self.__type = value.get_type()
            self.test_type()
            self.__value = value.get_value().copy()
        elif isinstance(value, (TAG_ByteArray, TAG_IntArray, TAG_LongArray)):
            raise Exception()
        elif isinstance(value, TAG_Compound):
            raise Exception()
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % (
                (list, TAG_List, TAG_ByteArray, TAG_IntArray, TAG_LongArray, TAG_Compound), value.__class__))
    
    def get_type(self):
        return self.__type
    
    def set_type(self, type):
        if isinstance(type, int):
            self.__type = TAG(type)
            self.test_type()
        elif isinstance(type, TAG):
            self.__type = type
            self.test_type()
        elif isinstance(type, BaseTag):
            self.__type = type.type
            self.test_type()
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % ((tuple([TAG] + list(TAGLIST.values()) + [int])), type.__class__))
    
    def test_type(self):
        self.__is_number_list = self.__type in list(ARRAY_TYPECODE.keys())
    
    def test_value(self, value):
        if isinstance(value, tuple(TAGLIST.values())):
            if len(self.__value) == 0:
                self.__type = value.type
                self.test_type()
                if self.__is_number_list:
                    self.__value = array(ARRAY_TYPECODE[self.__type])
            if value.type == self.__type:
                if self.__is_number_list:
                    return value.get_value()
                else:
                    return value
            else:
                raise TypeError("期望类型为 %s，但传入了 %s" % (
                list(TAGLIST.values())[self.__type.value].type, value.type))
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % (
                tuple(TAGLIST.values()), value.__class__))

    def get_info(self):
        if len(self.__value) <= 10:
            return f'{self.__class__.__name__}(' + ''.join([f'\n    {v.get_info()}' for v in self]) + '\n)'
        else:
            res = []
            for i in range(5): res.append(f'\n    {self[i].get_info()}')
            res.append(f'\n    ...more {len(self) - 10}')
            for i in range(len(self) - 5, len(self)): res.append(f'\n    {self[i].get_info()}')
            return f'{self.__class__.__name__}(' + ''.join(res) + '\n)'

    def __repr__(self):
        return f"<{self.type} type={self.__type} count={len(self.__value)} at 0x{id(self)}>"

    def __str__(self):
        return self.to_string()
    
    def __bytes__(self):
        return self.to_bytes()
    
    def __bool__(self):
        return bool(self.__value)
    
    def __add__(self, other):
        if isinstance(other, TAG_List):
            if other.get_type() != self.get_type():
                raise TypeError("TAG_List容器类型期望类型为 %s，但传入了 %s" % (self.get_type(), other.get_type()))
            if not bool(other): return TAG_List(self)
            return TAG_List(self.__value + other.__value)
        elif isinstance(other, list):
            return TAG_List(other) + self
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % ((TAG_List, list), other.__class__))
    
    def __len__(self):
        return len(self.__value)

    def __iter__(self):
        if self.__is_number_list:
            return iter([TAGLIST[self.__type](i) for i in self.__value])
        else:
            return iter(self.__value)

    def __contains__(self, item):
        return item in self.__value

    def __getitem__(self, key):
        if self.__is_number_list:
            return TAGLIST[self.__type](self.__value[key])
        else:
            return self.__value[key]

    def __setitem__(self, key, value):
        value = self.test_value(value)
        self.__value[key] = value

    def __delitem__(self, key):
        del (self.__value[key])

    def __reversed__(self):
        self.__value = reversed(self.__value)

    def insert(self, key, value):
        value = self.test_value(value)
        self.__value.insert(key, value)

    def append(self, value):
        value = self.test_value(value)
        self.__value.append(value)

    def add(self, value):
        self.append(value)

    def clear(self):
        if self.__is_number_list:
            self.__value = array(ARRAY_TYPECODE[self.__type])
        else:
            self.__value.clear()

    def copy(self):
        return TAG_List(self)

    def pop(self, key):
        if self.__is_number_list:
            return TAGLIST[self.__type](self.__value.pop(key))
        else:
            return self.__value.pop(key)

    def remove(self, value):
        value = self.test_value(value)
        self.__value.remove(value)


class TAG_Compound(BaseTag):
    type = TAG.COMPOUND
    
    def __init__(self, value=None):
        self.__value = {}
        if value is None: return
        self.set_value(value)
    
    @classmethod
    def _from_bytes(cls, buffer, mode=False):
        return cls._from_bytesIO(BytesIO(buffer), mode)

    @classmethod
    def _from_bytesIO(cls, buffer, mode=False):
        res = {}
        while True:
            byte = buffer_read(buffer, 1, "标签")
            try:
                if (type := ce.bytes_to_tag_type(byte)) == TAG.END: break
            except Exception as e:
                throw_nbt_error(e, buffer, 1)
            byte = buffer_read(buffer, 2, "复合键名长度")
            try:
                length = ce.bytes_to_length(byte, mode)
            except Exception as e:
                throw_nbt_error(e, buffer, 2)
            byte = buffer_read(buffer, length, "复合键名")
            try:
                key = ce.unpack_data(byte, TAG.STRING)
            except Exception as e:
                throw_nbt_error(e, buffer, length)
            res[key] = TAGLIST[type]._from_bytesIO(buffer, mode)
        compound = cls()
        compound.__value = res
        return compound

    @classmethod
    def _from_snbt(cls, buffer):
        buffer = SnbtIO(buffer)
        token = buffer._read_one()
        if token[1] == "{":
            res = cls._from_snbtIO(buffer)
            buffer.close()
            return res
        else:
            buffer.throw_error(token, "{")

    @classmethod
    def _from_snbtIO(cls, buffer):
        res, compound = {}, cls()
        token = buffer._read_one()
        if token[1] == "}":
            return cls()
        key = buffer.parse_key(token)
        if buffer._read_one()[1] == ":":
            res[key] = buffer.parse_value(buffer._read_one())
        else:
            buffer.throw_error(token, ":")
        while True:
            token = buffer._read_one()
            if token[1] == "}":
                compound.__value = res
                return compound
            elif not token[1] == ",":
                buffer.throw_error(token, ", }")
            key = buffer.parse_key(buffer._read_one())
            if buffer._read_one()[1] == ":":
                res[key] = buffer.parse_value(buffer._read_one())
            else:
                buffer.throw_error(token, ":")
    
    def to_string(self):
        return '{' + ', '.join([f"'{k}': {v}" for k, v in self.__value.items()]) + '}'
    
    def to_snbt(self, format=False, size=4):
        if not isinstance(size, int): raise TypeError("缩进期望类型为 %s，但传入了 %s" % (int, size.__class__))
        if not 1 <= size <= 16: raise ValueError("超出范围(1 ~ 16)的数字 %s" % size)
        if format:
            buffer = StringIO()
            self._to_snbt_format(buffer, 1, size)
            buffer.seek(0)
            return buffer.read()
        else:
            return self._to_snbt()
    
    def _to_snbt(self):
        return '{' + ','.join([f'{ce.str_to_snbt_key(k)}:{v._to_snbt()}' for k, v in self.__value.items()]) + '}'
    
    def _to_snbt_format(self, buffer, indent, size):
        count, tab = len(self.__value), " " * size
        if count == 0:
            buffer.write("{}")
            return
        if count == 1 and next(iter(self.__value.values())).type in [TAG.BYTE, TAG.SHORT, TAG.INT, TAG.FLOAT, TAG.DOUBLE]:
            buffer.write("{" + f"{ce.str_to_snbt_key(next(iter(self.__value.keys())))}: {next(iter(self.__value.values()))._to_snbt()}" + "}")
            return
        buffer.write("{\n")
        for (k, v), i in zip(self.__value.items(), range(1, count + 1)):
            buffer.write(indent * tab)
            buffer.write(ce.str_to_snbt_key(k))
            buffer.write(": ")
            v._to_snbt_format(buffer, indent + 1, size)
            if i < count: buffer.write(",\n")
        buffer.write("\n" + tab * (indent - 1) + "}")
    
    def to_bytes(self, mode=False):
        res = bytearray()
        for k, v in self.__value.items():
            name = ce.pack_data(k, TAG.STRING)
            res.extend(ce.tag_type_to_bytes(v.type))
            res.extend(ce.length_to_bytes(len(name), mode))
            res.extend(name)
            res.extend(v.to_bytes(mode))
        res.extend(ce.tag_type_to_bytes(TAG.END))
        return bytes(res)
    
    def get_value(self):
        return deepcopy(self.__value)
    
    def set_value(self, value):
        if isinstance(value, TAG_Compound):
            self.__value = value.get_value()
        elif isinstance(value, dict):
            if not all(isinstance(k, str) and isinstance(v, BaseTag) for k, v in value.items()):
                raise TypeError("dict内含非期望类型：%s" % repr(value))
            self.__value = value
        elif isinstance(value, list):
            pass
        elif isinstance(value, TAG_List):
            pass
        elif isinstance(value, (TAG_ByteArray, TAG_IntArray, TAG_LongArray)):
            pass
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % ((TAG_Compound, dict, list, TAG_List, TAG_ByteArray, TAG_IntArray, TAG_LongArray), value.__class__))
    
    def dump_info(self):
        pass
    
    def _test_key(self, key):
        if isinstance(key, str):
            return key
        elif isinstance(key, BaseTag) and key.type == TAG.STRING:
            return key.to_string()
        else:
            raise TypeError("Compound键的期望类型为 %s，但传入了 %s" % ((str, TAG_String), key.__class__))
    
    def _test_value(self, value):
        if isinstance(value, BaseTag):
            return value
        else:
            raise TypeError("Compound值的期望类型为 %s，但传入了 %s" % (tuple(TAGLIST.values()), value.__class__))

    def get_info(self):
        if len(self.__value) <= 10:
            return f'{self.__class__.__name__}(' + ''.join([f'\n    {k}: {v.get_info()}' for k, v in self.items()]) + '\n)'
        else:
            res = []
            for i, (k, v) in zip(range(5), self.items()): res.append(f'\n    {k}: {v.get_info()}')
            res.append(f'\n    ...more {len(self) - 10}')
            res2 = []
            for i, (k, v) in zip(range(5), reversed(self.items())): res2.append(f'\n    {k}: {v.get_info()}')
            res.extend(reversed(res2))
            return f'{self.__class__.__name__}(' + ''.join(res) + '\n)'

    def __repr__(self):
        return f"<{self.type} count={len(self.__value)} at 0x{id(self)}>"

    def __str__(self):
        return self.to_string()

    def __bytes__(self):
        return self.to_bytes()

    def __hash__(self):
        return hash(self.__value)

    def __bool__(self):
        return bool(self.__value)

    # def __eq__(self, other): pass

    # def __ne__(self, other): pass

    def __len__(self):
        return len(self.__value)

    def __getitem__(self, key):
        key = self._test_key(key)
        return self.__value[key]

    def __setitem__(self, key, value):
        key = self._test_key(key)
        value = self._test_value(value)
        self.__value[key] = value

    def __delitem__(self, key):
        key = self._test_key(key)
        del self.__value[key]

    def __iter__(self):
        return iter(self.__value)

    def __contains__(self, item):
        return item in self.__value

    def clear(self):
        self.__value.clear()

    def copy(self):
        return TAG_Compound(self)

    def get(self, key, default=None):
        key = self._test_key(key)
        default = self._test_value(default)
        return self.__value.get(key, default)

    def items(self):
        return list(self.__value.items())

    def keys(self):
        return list(self.__value.keys())

    def pop(self, key, default=None):
        key = self._test_key(key)
        return self.__value.pop(key, default)

    def popitem(self):
        return self.__value.popitem()

    def setdefault(self, key, default=None):
        key = self._test_key(key)
        default = self._test_value(default)
        return self.__value.setdefault(key, default)

    def values(self):
        return list(self.__value.values())


class TAG_Array(ABC, BaseTag):
    _type = None
    type = None
    unit = None
    
    def __init__(self, value=None):
        self.__value = array(self.unit[2])
        if value is None: return
        self.set_value(value)

    @classmethod
    def _from_bytes(cls, buffer, mode=False):
        return cls._from_bytesIO(BytesIO(buffer), mode)

    @classmethod
    def _from_bytesIO(cls, buffer, mode=False):
        byte = buffer_read(buffer, 4, "数组元素个数")
        try:
            count = ce.unpack_data(byte, TAG.INT, mode)[0]
        except Exception as e:
            throw_nbt_error(e, buffer, 4)
        length = ce.number_bytes_len[cls._type]
        size = count * length
        byte = buffer_read(buffer, size, "数组元素")
        array = cls()
        try:
            array.__value.frombytes(byte)
        except Exception as e:
            throw_nbt_error(e, buffer, size)
        if mode: array.__value.byteswap()
        return array

    @classmethod
    def _from_snbt(cls, buffer):
        buffer = SnbtIO(buffer)
        token = buffer._read_one()
        if token[1] == "[":
            if buffer._read_one()[1] == cls.unit[0]:
                if buffer._read_one()[1] == ";":
                    res = cls._from_snbtIO(buffer)
                    buffer.close()
                    return res
                else:
                    buffer.throw_error(token, ";")
            else:
                buffer.throw_error(token, cls.unit[0])
        else:
            buffer.throw_error(token, "{")

    @classmethod
    def _from_snbtIO(cls, buffer):
        token = buffer._read_one()
        if token[1] == "]":
            return cls()
        res = deque()
        if token[0] == "Int":
            if cls.unit[1] in token[1]:
                res.append(int(token[1].rstrip("bl")))
            else:
                buffer.throw_error(token, "%s的单位" % cls.__name__)
        else:
            buffer.throw_error(token, "整数")
        while True:
            token = buffer._read_one()
            if token[1] == "]":
                Array = cls()
                Array.__value.fromlist(list(res))
                return Array
            elif token[1] == ",":
                token = buffer._read_one()
                if token[0] == "Int":
                    if cls.unit[1] in token[1]:
                        res.append(int(token[1].rstrip("bl")))
                    else:
                        buffer.throw_error(token, "%s的单位" % cls.__name__)
                else:
                    buffer.throw_error(token, "整数")
            else:
                buffer.throw_error(token, "] ,")
        value = buffer.parse_value(token)
        if value.type == cls.type:
            return value
        else:
            buffer.throw_error(token, "字符串")

    def to_string(self):
        return "[" + ', '.join([str(i) for i in self.__value]) + "]"

    def to_snbt(self, format=False, size=4):
        if not isinstance(size, int): raise TypeError("缩进期望类型为 %s，但传入了 %s" % (int, size.__class__))
        if not 1 <= size <= 16: raise ValueError("超出范围(1 ~ 16)的数字 %s" % size)
        if format:
            buffer = StringIO()
            self._to_snbt_format(buffer, 1, size)
            buffer.seek(0)
            return buffer.read()
        else:
            return self._to_snbt()

    def _to_snbt(self):
        return f"[{self.unit[0]};" + ','.join([f"{str(i)}{self.unit[1]}" for i in self.__value]) + "]"

    def _to_snbt_format(self, buffer, indent, size):
        count, tab = len(self.__value), " " * size
        if count == 0:
            buffer.write(f"[{self.unit[0]};]")
            return
        if 1 <= count <= 3:
            buffer.write(f"[{self.unit[0]}; " + ', '.join([f"{str(i)}{self.unit[1]}" for i in self.__value]) + "]")
            return
        buffer.write("[\n")
        buffer.write(f"{tab * indent}{self.unit[0]};\n")
        for v, i in zip(self.__value, range(1, count + 1)):
            buffer.write(f"{tab * indent}{str(v)}{self.unit[1]}")
            if i < count: buffer.write(",\n")
        buffer.write("\n" + tab * (indent - 1) + "]")

    def to_bytes(self, mode=False):
        if mode:
            self.__value.byteswap()
            res = ce.pack_data(len(self.__value), TAG.INT, mode) + self.__value.tobytes()
            self.__value.byteswap()
            return res
        else:
            return ce.pack_data(len(self.__value), TAG.INT, mode) + self.__value.tobytes()
    
    def get_value(self):
        return deepcopy(self.__value)
    
    def set_value(self, value):
        if isinstance(value, list):
            res = array(self.unit[2])
            try:
                res.fromlist(value)
            except:
                raise ValueError("尝试自动转换数值失败")
            else:
                self.__value = res
        elif isinstance(value, TAG_List):
            raise Exception()
            """未实现"""
        elif isinstance(value, (TAG_ByteArray, TAG_IntArray, TAG_LongArray)):
            if self.__class__ == value.__class__:
                self.__value = value.get_value()
            else:
                res = array(self.unit[2])
                try:
                    res.fromlist(value.get_value().tolist())
                except:
                    raise ValueError("尝试自动转换数值失败")
                else:
                    self.__value = res
        elif isinstance(value, TAG_Compound):
            raise Exception()
            """未实现"""
        elif isinstance(value, array) and value.typecode == self.unit[2]:
            self.__value = value
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % ((list, array, TAG_List, TAG_Compound, TAG_ByteArray, TAG_IntArray, TAG_LongArray), value.__class__))
    
    def test_value(self, value):
        if isinstance(value, int):
            if self.range[0] <= value <= self.range[1]: return value
            raise ValueError("超出范围(%s)的数字 %s" % (self.range, value))
        elif isinstance(value, (TAG_Byte, TAG_Short, TAG_Int, TAG_Long)):
            if self.range[0] <= value.get_value() <= self.range[1]: return value.get_value()
            raise ValueError("超出范围(%s)的数字 %s" % (self.range, value.get_value()))
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % (
                (int, TAG_Byte, TAG_Short, TAG_Int, TAG_Long), value.__class__))

    def get_info(self):
        if len(self.__value) <= 10:
            return f'{self.__class__.__name__}(' + ''.join([f'\n    {v}' for v in self]) + '\n)'
        else:
            res = []
            for i in range(5): res.append(f'\n    {self[i]}')
            res.append(f'\n    ...more {len(self) - 10}')
            for i in range(len(self) - 5, len(self)): res.append(f'\n    {self[i]}')
            return f'{self.__class__.__name__}(' + ''.join(res) + '\n)'

    def __repr__(self):
        return f"<{self.type} count={len(self.__value)} at 0x{id(self)}>"

    def __str__(self):
        return self.to_string()
    
    def __bytes__(self):
        return self.to_bytes()
    
    def __bool__(self):
        return bool(self.__value)
    
    def __add__(self, other):
        if isinstance(other, TAG_Array):
            if other.__class__ != self.__class__: raise TypeError("期望类型为 %s，但传入了 %s" % (self.__class__, other.__class__))
            if not bool(other): return self.__class__(self)
            return self.__class__(self.__value + other.__value)
        elif isinstance(other, list):
            return self.__class__(other) + self
        elif isinstance(other, array) and other.typecode == self.unit[2]:
            return self.__class__(self.__value + other)
        else:
            raise TypeError("期望类型为 %s，但传入了 %s" % ((self.__class__, list, array), other.__class__))
    
    def __len__(self):
        return len(self.__value)

    def __iter__(self):
        return iter(self.__value)

    def __contains__(self, item):
        return item in self.__value

    def __getitem__(self, key):
        return self.__value[key]

    def __setitem__(self, key, value):
        value = self.test_value(value)
        self.__value[key] = value

    def __delitem__(self, key):
        del (self.__value[key])

    def __reversed__(self):
        self.__value = reversed(self.__value)

    def insert(self, key, value):
        value = self.test_value(value)
        self.__value.insert(key, value)

    def append(self, value):
        value = self.test_value(value)
        self.__value.append(value)

    def add(self, value):
        self.append(value)

    def clear(self):
        self.__value = array(self.unit[2])

    def copy(self):
        return self.__class__(self)

    def pop(self, key):
        return self.__value.pop(key)

    def remove(self, value):
        self.__value.remove(value)


class TAG_ByteArray(TAG_Array):
    _type = TAG.BYTE
    type = TAG.BYTE_ARRAY
    unit = ("B", "b", "b")
    range = (-128, 127)


class TAG_IntArray(TAG_Array):
    _type = TAG.INT
    type = TAG.INT_ARRAY
    unit = ("I", "", "l")
    range = (-2147483648, 2147483647)


class TAG_LongArray(TAG_Array):
    _type = TAG.LONG
    type = TAG.LONG_ARRAY
    unit = ("L", "l", "q")
    range = (-9223372036854775808, 9223372036854775807)
