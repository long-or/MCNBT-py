"""
    error.py - 错误信息
"""


class SnbtParseError(Exception): pass
class SnbtTokenError(Exception): pass

class NbtParseError(Exception): pass
class NbtFileError(Exception): pass

class NbtBufferError(Exception): pass
class NbtContextError(Exception): pass
class NbtDataError(Exception): pass

def throw_nbt_error(e, buffer, length):
    buffer.seek(buffer.tell() - length)
    value = buffer.read(length)
    if len(value) >= 10:
        value = value[0:4] + b'...' + value[-3:]
    raise NbtParseError("%s (%s) 位于 %s 到 %s字节" % (e.args[0], value, buffer.tell() - length, buffer.tell()))

def buffer_read(buffer, length, msg):
    byte = buffer.read(length)
    if len(byte) != length: raise NbtParseError("数据可能被截断了 数据长度应该为 %s 实际为 %s 数据类型为 %s" % (length, len(byte), msg))
    return byte
