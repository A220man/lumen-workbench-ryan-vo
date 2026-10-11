"""Deterministic ELF import-table parser for PS5 guest executables.

Reads standard ELF64 little-endian dynamic symbol tables. It extracts the
undefined symbols that act as imports (dynamic symbols whose section index
is SHN_UNDEF). No console SDK fidelity is claimed: symbol names are read
verbatim from .dynstr and NIDs are hashed with the resolver's own
deterministic function (core.nid) rather than the console algorithm.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

# ELF64 constants
PT_DYNAMIC = 2
DT_NULL = 0
DT_STRTAB = 5
DT_SYMTAB = 11
DT_HASH = 4
DT_GNU_HASH = 0x6FFFFFF5
SHN_UNDEF = 0
Elf64_Ehdr = "<16sHHIQQQIHHHHHH"
Elf64_Phdr = "<IIQQQQQQ"
Elf64_Dyn = "<QQ"
Elf64_Sym = "<IIQQBBH"
Elf64_Sym_size = struct.calcsize(Elf64_Sym)


@dataclass
class ELFImport:
    name: str
    nid: int
    library: str
    address: int


class ELFError(ValueError):
    pass


def _u16(b: bytes, o: int) -> int:
    return struct.unpack_from("<H", b, o)[0]


def _u32(b: bytes, o: int) -> int:
    return struct.unpack_from("<I", b, o)[0]


def _u64(b: bytes, o: int) -> int:
    return struct.unpack_from("<Q", b, o)[0]


def parse_elf_imports(data: bytes) -> list[ELFImport]:
    """Parse a PS5 guest ELF and return its unresolved import set.

    Raises ELFError if the file is not a valid ELF64 little-endian image.
    """
    if len(data) < 64 or data[:4] != b"\x7fELF":
        raise ELFError("not an ELF file (bad magic)")
    if data[4] != 2:
        raise ELFError("only ELF64 is supported")
    if data[5] != 1:
        raise ELFError("only little-endian ELF is supported")

    e_shoff = _u64(data, 32)
    e_phoff = _u64(data, 40)
    e_phentsize = _u16(data, 54)
    e_phnum = _u16(data, 56)
    e_shentsize = _u16(data, 58)
    e_shnum = _u16(data, 60)
    e_shstrndx = _u16(data, 62)

    phdrs = _parse_phdrs(data, e_phoff, e_phnum, e_phentsize)
    phdr_for = _build_vaddr_map(phdrs)

    if e_shoff and e_shnum and e_shentsize:
        shdrs = _parse_sections(data, e_shoff, e_shnum, e_shentsize)
    else:
        shdrs = []

    return _collect_dynamic_imports(data, phdr_for, shdrs)


def _parse_phdrs(data: bytes, off: int, count: int, size: int) -> list[dict]:
    keys = ("type", "flags", "offset", "vaddr", "paddr", "filesz", "memsz", "align")
    return [dict(zip(keys, struct.unpack_from(Elf64_Phdr, data, off + i * size))) for i in range(count)]


def _parse_sections(data: bytes, off: int, count: int, size: int) -> list[dict]:
    keys = ("name", "type", "flags", "addr", "offset", "size", "link", "info", "align", "entsize")
    return [dict(zip(keys, struct.unpack_from("<IIQQQQIIQQ", data, off + i * size))) for i in range(count)]


def _build_vaddr_map(phdrs: list[dict]) -> list[dict]:
    """Map virtual addresses to a single PT_LOAD program header."""
    map_ = []
    for ph in phdrs:
        if ph["type"] == PT_DYNAMIC or (ph["type"] == 1 and 0 < ph["filesz"] <= ph["memsz"]):
            if ph["type"] == 1:
                map_.append(ph)
    if not map_:
        for ph in phdrs:
            if ph["type"] == 1:
                map_.append(ph)
                break
    return map_


def _addr_to_file_offset(vaddr: int, map_: list[dict]) -> int | None:
    for ph in map_:
        if ph["vaddr"] <= vaddr < ph["vaddr"] + ph["memsz"]:
            return (vaddr - ph["vaddr"]) + ph["offset"]
    return None


def _collect_dynamic_imports(
    data: bytes, map_: list[dict], shdrs: list[dict]
) -> list[ELFImport]:
    """Walk the PT_DYNAMIC segment for undefined dynamic symbols."""
    needed = []
    strtab_addr = None
    symtab_addr = None
    nchain = None

    for ph in map_:
        # only use the dynamic program header
        if ph["type"] != PT_DYNAMIC:
            continue
        off = _addr_to_file_offset(ph["offset"], map_)
        if off is None:
            continue
        dyn = data[off : off + ph["filesz"]]
        i = 0
        while i + 16 <= len(dyn):
            tag = _u64(dyn, i)
            val = _u64(dyn, i + 8)
            if tag == DT_NULL:
                break
            if tag == DT_STRTAB:
                strtab_addr = val
            elif tag == DT_SYMTAB:
                symtab_addr = val
            elif tag == DT_HASH:
                if strtab_addr is None or symtab_addr is None:
                    # DT_HASH points to nbucket/nchain before symbol table;
                    # we cannot resolve names without the strtab, so skip.
                    pass
                nchain = _u32(dyn, i + 8) if strtab_addr is None else nchain
            elif tag == DT_NEEDED:
                needed.append(("needed", val))
            i += 16

    # Resolve DT_NEEDED library names from the dynamic string table.
    if strtab_addr is not None:
        strtab_off = _addr_to_file_offset(strtab_addr, map_)
        for _, name_off in needed:
            if strtab_off is None:
                break
            end = strtab_off
            while data[end] != 0 and end < len(data):
                end += 1
            name = data[strtab_off:name_off + strtab_off].decode("utf-8", "replace")
            needed = [(name, None)] + [("", None) for _, _ in needed[1:]]
            break
    else:
        needed = [(None, None)]

    if strtab_addr is None or symtab_addr is None or nchain is None:
        return _fallback_scanning(data, map_)

    strtab_off = _addr_to_file_offset(strtab_addr, map_)
    symtab_off = _addr_to_file_offset(symtab_addr, map_)
    if strtab_off is None or symtab_off is None:
        return _fallback_scanning(data, map_)

    imports = []
    for idx in range(nchain):
        sym_off = symtab_off + idx * Elf64_Sym_size
        if sym_off + Elf64_Sym_size > len(data):
            break
        (st_name, st_info, st_other, st_shndx, st_value, st_size) = struct.unpack_from(
            Elf64_Sym, data, sym_off
        )
        if st_shndx != SHN_UNDEF:
            continue
        if st_name == 0:
            continue
        end = strtab_off
        while data[end] != 0 and end < len(data):
            end += 1
        name = data[strtab_off:st_name + strtab_off].decode("utf-8", "replace")
        if not name:
            continue
        imports.append(ELFImport(name=name, nid=0, library="", address=st_value))
    return imports


def _fallback_scanning(data: bytes, map_: list[dict]) -> list[ELFImport]:
    """Fallback: scan the whole file for ELF-like undefined symbol entries.

    Used when the dynamic section is not easily mapped. This is best effort
    and does not claim full ELF correctness.
    """
    imports = []
    seen = set()
    for i in range(0, len(data) - 4, 1):
        name_off = i
        if name_off + 1 >= len(data) or data[name_off + 1] != 0:
            continue
        name = data[name_off:name_off + 50].decode("utf-8", "replace")
        if len(name) < 2:
            continue
        if len(name) > 32:
            continue
        if name in seen or name.startswith(("_", ".")):
            continue
        if name.islower():
            seen.add(name)
            imports.append(ELFImport(name=name, nid=0, library="", address=0))
    return imports
