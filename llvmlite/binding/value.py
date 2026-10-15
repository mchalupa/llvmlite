from ctypes import (POINTER, byref, c_char_p, c_int, c_longlong, c_size_t,
                    c_uint, c_ulonglong, c_bool, c_void_p, string_at)
import enum

from . import ffi
from .common import _decode_string, _encode_string


class Linkage(enum.IntEnum):
    # The LLVMLinkage enum from llvm-c/Core.h

    external = 0
    available_externally = 1
    linkonce_any = 2
    linkonce_odr = 3
    linkonce_odr_autohide = 4
    weak_any = 5
    weak_odr = 6
    appending = 7
    internal = 8
    private = 9
    dllimport = 10
    dllexport = 11
    external_weak = 12
    ghost = 13
    common = 14
    linker_private = 15
    linker_private_weak = 16


class Visibility(enum.IntEnum):
    # The LLVMVisibility enum from llvm-c/Core.h

    default = 0
    hidden = 1
    protected = 2


class StorageClass(enum.IntEnum):
    # The LLVMDLLStorageClass enum from llvm-c/Core.h

    default = 0
    dllimport = 1
    dllexport = 2


class TypeKind(enum.IntEnum):
    # The LLVMTypeKind enum from llvm-c/Core.h (15 was x86_mmx, removed)

    void = 0
    half = 1
    float = 2
    double = 3
    x86_fp80 = 4
    fp128 = 5
    ppc_fp128 = 6
    label = 7
    integer = 8
    function = 9
    struct = 10
    array = 11
    pointer = 12
    vector = 13
    metadata = 14
    token = 16
    scalable_vector = 17
    bfloat = 18
    x86_amx = 19
    target_ext = 20


class TypeRef(ffi.ObjectRef):
    """A weak reference to a LLVM type
    """
    @property
    def type_kind(self):
        """
        The kind of the type (TypeKind). Raises ValueError for a kind that
        is not known.
        """
        kind = ffi.lib.LLVMPY_GetTypeKind(self)
        try:
            return TypeKind(kind)
        except ValueError:
            raise ValueError('unknown kind of type: %s' % (kind,))

    @property
    def type_width(self):
        """
        The size in bits of a primitive type (the bit width of an integer
        type, 32 for float, 80 for x86_fp80, ...; the total size of a fixed
        vector of these), 0 for other types (pointers, aggregates, ...).
        These sizes do not depend on the target.
        """
        return ffi.lib.LLVMPY_GetTypeBitWidth(self)

    @property
    def element_count(self):
        """
        The number of elements of an array or a vector type (the minimal
        number for a scalable vector). Raises ValueError for other types.
        """
        n = ffi.lib.LLVMPY_GetTypeElementCount(self)
        if n < 0:
            raise ValueError('expected an array or a vector type, got %s'
                             % (self.type_kind.name,))
        return n

    @property
    def return_type(self):
        """
        The return type of a function type. Raises ValueError for other
        types.
        """
        ty = ffi.lib.LLVMPY_GetReturnType(self)
        if not ty:
            raise ValueError('expected a function type, got %s'
                             % (self.type_kind.name,))
        return TypeRef(ty)

    @property
    def is_sized(self):
        """
        Does the type have a size (opaque structs, functions, labels, void,
        ... do not)?
        """
        return ffi.lib.LLVMPY_TypeIsSized(self)

    @property
    def address_space(self):
        """
        The address space of a pointer type. Raises ValueError for other
        types.
        """
        n = ffi.lib.LLVMPY_GetPointerAddressSpace(self)
        if n < 0:
            raise ValueError('expected a pointer type, got %s'
                             % (self.type_kind.name,))
        return n

    @property
    def name(self):
        """
        Get type name
        """
        return ffi.ret_string(ffi.lib.LLVMPY_GetTypeName(self))

    @property
    def is_pointer(self):
        """
        Returns true is the type is a pointer type.
        """
        return ffi.lib.LLVMPY_TypeIsPointer(self)

    @property
    def is_vector(self):
        """
        Returns true is the type is a vector type.
        """
        return ffi.lib.LLVMPY_TypeIsVector(self)

    @property
    def is_array(self):
        """
        Returns true is the type is an array type.
        """
        return ffi.lib.LLVMPY_TypeIsArray(self)

    @property
    def is_struct(self):
        """
        Returns true is the type is an array type.
        """
        return ffi.lib.LLVMPY_TypeIsStruct(self)

    @property
    def element_type(self):
        """
        Returns the pointed-to type. When the type is not a pointer,
        raises exception.
        """
        if not (self.is_pointer or self.is_array or self.is_vector):
            raise ValueError(f"Type {self} has no elements")
        ty = ffi.lib.LLVMPY_GetElementType(self)
        if not ty:
            # opaque pointer
            raise ValueError(f"Type {self} has no element type")
        return TypeRef(ty)

    @property
    def struct_num_elements(self):
        """
        Returns the pointed-to type. When the type is not a pointer,
        raises exception.
        """
        if not self.is_struct:
            raise ValueError(f"Type {self} has no elements")
        return ffi.lib.LLVMPY_GetStructNumElements(self)

    def struct_element_type(self, n):
        """
        Returns the nth type in struct. When the type is not a pointer,
        raises exception.
        """
        if not self.is_struct:
            raise ValueError(f"Type {self} has no elements")
        assert n < self.struct_num_elements, f"Invalid type index: {n}"
        return TypeRef(ffi.lib.LLVMPY_GetStructElementType(self, n))


    def __str__(self):
        return ffi.ret_string(ffi.lib.LLVMPY_PrintType(self))


# llvm::CmpInst::Predicate (the numbering is part of the stable LLVM API)
_CMP_PREDICATES = {
    0: 'false', 1: 'oeq', 2: 'ogt', 3: 'oge', 4: 'olt', 5: 'ole', 6: 'one',
    7: 'ord', 8: 'uno', 9: 'ueq', 10: 'ugt', 11: 'uge', 12: 'ult', 13: 'ule',
    14: 'une', 15: 'true',
    32: 'eq', 33: 'ne', 34: 'ugt', 35: 'uge', 36: 'ult', 37: 'ule',
    38: 'sgt', 39: 'sge', 40: 'slt', 41: 'sle',
}


# the numbering of LLVMPY_GetValueKind
_VALUE_KINDS = {
    0: 'argument', 1: 'basic_block', 2: 'function', 3: 'global_alias',
    4: 'global_ifunc', 5: 'global_variable', 6: 'block_address',
    7: 'constant_expr', 8: 'constant_array', 9: 'constant_struct',
    10: 'constant_vector', 11: 'undef', 12: 'constant_aggregate_zero',
    13: 'constant_data_array', 14: 'constant_data_vector', 15: 'constant_int',
    16: 'constant_fp', 17: 'constant_pointer_null', 18: 'constant_token_none',
    19: 'metadata_as_value', 20: 'inline_asm', 21: 'instruction', 22: 'poison',
    23: 'constant_target_none',
}

# the numbering of LLVMPY_GetConstantFP
_FP_KINDS = {0: 'half', 1: 'bfloat', 2: 'float', 3: 'double', 4: 'x86_fp80',
             5: 'fp128', 6: 'ppc_fp128'}
_FP_BITS = {0: 16, 1: 16, 2: 32, 3: 64, 4: 80, 5: 128, 6: 128}


class ValueRef(ffi.ObjectRef):
    """A weak reference to a LLVM value.
    """

    def __init__(self, ptr, kind, parents):
        self._kind = kind
        self._parents = parents
        ffi.ObjectRef.__init__(self, ptr)

    def __str__(self):
        with ffi.OutputString() as outstr:
            ffi.lib.LLVMPY_PrintValueToString(self, outstr)
            return str(outstr)

    @property
    def module(self):
        """
        The module this function or global variable value was obtained from.
        """
        return self._parents.get('module')

    @property
    def function(self):
        """
        The function this argument or basic block value was obtained from.
        """
        return self._parents.get('function')

    @property
    def block(self):
        """
        The block this instruction value was obtained from.
        """
        return self._parents.get('block')

    @property
    def instruction(self):
        """
        The instruction this operand value was obtained from.
        """
        return self._parents.get('instruction')

    @property
    def is_global(self):
        return self._kind == 'global'

    @property
    def is_function(self):
        return self._kind == 'function'

    @property
    def is_block(self):
        return self._kind == 'block'

    @property
    def is_argument(self):
        return self._kind == 'argument'

    @property
    def is_instruction(self):
        return self._kind == 'instruction'

    @property
    def is_operand(self):
        return self._kind == 'operand'

    @property
    def is_constant(self):
        """
        Whether this operand is a contant expr
        """
        return ffi.lib.LLVMPY_IsConstant(self) != 0

    def is_global_constant(self):
        """
        Whether this value is global variable and the memory it references
        is constant.
        """
        return ffi.lib.LLVMPY_IsGlobalVariableConstant(self) != 0

    @property
    def is_constantexpr(self):
        """
        Whether this operand is a contant expr
        """
        return ffi.lib.LLVMPY_IsConstantExpr(self) != 0

    @property
    def name(self):
        return _decode_string(ffi.lib.LLVMPY_GetValueName(self))

    @property
    def dbg_loc(self):
        """
        The debug location of an instruction as the triple (file, line,
        column); ('', 0, 0) if there is none (or this is not an
        instruction).
        """
        line = c_uint(0)
        col = c_uint(0)
        n = c_size_t(0)
        ptr = ffi.lib.LLVMPY_GetDbgLoc(self, byref(line), byref(col),
                                       byref(n))
        if not ptr:
            return ('', 0, 0)
        return (_decode_string(string_at(ptr, n.value)), line.value,
                col.value)

    @name.setter
    def name(self, val):
        ffi.lib.LLVMPY_SetValueName(self, _encode_string(val))

    @property
    def linkage(self):
        return Linkage(ffi.lib.LLVMPY_GetLinkage(self))

    @linkage.setter
    def linkage(self, value):
        if not isinstance(value, Linkage):
            value = Linkage[value]
        ffi.lib.LLVMPY_SetLinkage(self, value)

    @property
    def visibility(self):
        return Visibility(ffi.lib.LLVMPY_GetVisibility(self))

    @visibility.setter
    def visibility(self, value):
        if not isinstance(value, Visibility):
            value = Visibility[value]
        ffi.lib.LLVMPY_SetVisibility(self, value)

    @property
    def storage_class(self):
        return StorageClass(ffi.lib.LLVMPY_GetDLLStorageClass(self))

    @storage_class.setter
    def storage_class(self, value):
        if not isinstance(value, StorageClass):
            value = StorageClass[value]
        ffi.lib.LLVMPY_SetDLLStorageClass(self, value)

    def add_function_attribute(self, attr):
        """Only works on function value

        Parameters
        -----------
        attr : str
            attribute name
        """
        if not self.is_function:
            raise ValueError('expected function value, got %s' % (self._kind,))
        attrname = str(attr)
        attrval = ffi.lib.LLVMPY_GetEnumAttributeKindForName(
            _encode_string(attrname), len(attrname))
        if attrval == 0:
            raise ValueError('no such attribute {!r}'.format(attrname))
        ffi.lib.LLVMPY_AddFunctionAttr(self, attrval)

    @property
    def type(self):
        """
        This value's LLVM type.
        """
        # XXX what does this return?
        return TypeRef(ffi.lib.LLVMPY_TypeOf(self))

    @property
    def is_declaration(self):
        """
        Whether this value (presumably global) is defined in the current
        module.
        """
        if not (self.is_global or self.is_function):
            raise ValueError('expected global or function value, got %s'
                             % (self._kind,))
        return ffi.lib.LLVMPY_IsDeclaration(self)

    @property
    def attributes(self):
        """
        Return an iterator over this value's attributes.
        The iterator will yield a string for each attribute.
        """
        itr = iter(())
        if self.is_function:
            it = ffi.lib.LLVMPY_FunctionAttributesIter(self)
            itr = _AttributeListIterator(it)
        elif self.is_instruction:
            if self.opcode == 'call':
                it = ffi.lib.LLVMPY_CallInstAttributesIter(self)
                itr = _AttributeListIterator(it)
            elif self.opcode == 'invoke':
                it = ffi.lib.LLVMPY_InvokeInstAttributesIter(self)
                itr = _AttributeListIterator(it)
        elif self.is_global:
            it = ffi.lib.LLVMPY_GlobalAttributesIter(self)
            itr = _AttributeSetIterator(it)
        elif self.is_argument:
            it = ffi.lib.LLVMPY_ArgumentAttributesIter(self)
            itr = _AttributeSetIterator(it)
        return itr

    @property
    def blocks(self):
        """
        Return an iterator over this function's blocks.
        The iterator will yield a ValueRef for each block.
        """
        if not self.is_function:
            raise ValueError('expected function value, got %s' % (self._kind,))
        it = ffi.lib.LLVMPY_FunctionBlocksIter(self)
        parents = self._parents.copy()
        parents.update(function=self)
        return _BlocksIterator(it, parents)

    @property
    def arguments(self):
        """
        Return an iterator over this function's arguments.
        The iterator will yield a ValueRef for each argument.
        """
        if not self.is_function:
            raise ValueError('expected function value, got %s' % (self._kind,))
        it = ffi.lib.LLVMPY_FunctionArgumentsIter(self)
        parents = self._parents.copy()
        parents.update(function=self)
        return _ArgumentsIterator(it, parents)

    @property
    def instructions(self):
        """
        Return an iterator over this block's instructions.
        The iterator will yield a ValueRef for each instruction.
        """
        if not self.is_block:
            raise ValueError('expected block value, got %s' % (self._kind,))
        it = ffi.lib.LLVMPY_BlockInstructionsIter(self)
        parents = self._parents.copy()
        parents.update(block=self)
        return _InstructionsIterator(it, parents)

    @property
    def operands(self):
        """
        Return an iterator over this instruction's operands.
        The iterator will yield a ValueRef for each operand.
        """
        if not self.is_instruction:
            raise ValueError('expected instruction value, got %s'
                             % (self._kind,))
        it = ffi.lib.LLVMPY_InstructionOperandsIter(self)
        parents = self._parents.copy()
        parents.update(instruction=self)
        return _OperandsIterator(it, parents)

    @property
    def constant_operands(self):
        """
        Return an iterator over the operands of a constant that is a user
        (e.g. the elements of a constant struct/array initializer).
        """
        if self.is_instruction or self.is_function or self.is_block \
                or self.is_argument:
            raise ValueError('expected a constant value, got %s'
                             % (self._kind,))
        it = ffi.lib.LLVMPY_InstructionOperandsIter(self)
        parents = self._parents.copy()
        return _OperandsIterator(it, parents)

    @property
    def alignment(self):
        """
        The alignment (in bytes) of this load, store or alloca instruction or
        global object. None for a global object without explicit alignment.
        Raises ValueError for any other value.
        """
        al = ffi.lib.LLVMPY_GetAlignment(self)
        if al < 0:
            raise ValueError('value has no alignment (expected load, store, '
                             'alloca or global object), got %s' % (self._kind,))
        return al if al > 0 else None

    @property
    def predicate(self):
        """
        The predicate of this icmp or fcmp instruction as a string: 'eq',
        'ne', 'ugt', 'uge', 'ult', 'ule', 'sgt', 'sge', 'slt', 'sle' for
        icmp and 'false', 'oeq', 'ogt', 'oge', 'olt', 'ole', 'one', 'ord',
        'uno', 'ueq', 'ugt', 'uge', 'ult', 'ule', 'une', 'true' for fcmp
        (use `opcode` to tell the two apart).
        Raises ValueError for any other value.
        """
        pred = ffi.lib.LLVMPY_GetCmpPredicate(self)
        if pred < 0:
            raise ValueError('expected icmp or fcmp instruction, got %s'
                             % (self._kind,))
        try:
            return _CMP_PREDICATES[pred]
        except KeyError:
            raise ValueError('unknown compare predicate %d' % pred)

    def _wrap_flags(self):
        flags = ffi.lib.LLVMPY_GetWrapFlags(self)
        if flags < 0:
            raise ValueError('expected add, sub, mul or shl, got %s'
                             % (self._kind,))
        return flags

    @property
    def has_nsw(self):
        """
        Does this add, sub, mul or shl have the 'nsw' (no signed wrap) flag?
        Raises ValueError for other values.
        """
        return bool(self._wrap_flags() & 1)

    @property
    def has_nuw(self):
        """
        Does this add, sub, mul or shl have the 'nuw' (no unsigned wrap) flag?
        Raises ValueError for other values.
        """
        return bool(self._wrap_flags() & 2)

    @property
    def value_kind(self):
        """
        The kind of this value (the LLVM ValueID) as a string, one of
        _VALUE_KINDS. Raises ValueError for a kind that is not known.
        """
        kind = ffi.lib.LLVMPY_GetValueKind(self)
        try:
            return _VALUE_KINDS[kind]
        except KeyError:
            raise ValueError('unknown kind of value: %s' % (kind,))

    @property
    def constant_int(self):
        """
        For a constant integer, the pair (bit width, value), where the value
        is the signed value (the unsigned value would be ambiguous for
        i1: 'true' is -1). Raises ValueError for any other value.
        """
        small = c_longlong(0)
        width = ffi.lib.LLVMPY_GetConstantInt(self, byref(small))
        if width == 0:
            raise ValueError('expected a constant integer, got %s'
                             % (self._kind,))
        if width <= 64:
            return width, small.value
        return width, int(ffi.ret_string(
            ffi.lib.LLVMPY_GetConstantIntString(self)))

    @property
    def constant_fp(self):
        """
        For a floating-point constant, the pair (type, bits), where the type
        is one of 'half', 'bfloat', 'float', 'double', 'x86_fp80', 'fp128',
        'ppc_fp128' and bits is the raw (IEEE, for x86_fp80 the 80-bit
        extended format) bit pattern of the value as an unsigned integer.
        Raises ValueError for any other value (or a type that is not
        supported).
        """
        bits = (c_ulonglong * 2)()
        nbits = c_uint(0)
        kind = ffi.lib.LLVMPY_GetConstantFP(self, bits, byref(nbits))
        if kind < 0:
            raise ValueError('expected a floating-point constant, got %s'
                             % (self._kind,))
        assert nbits.value == _FP_BITS[kind], (kind, nbits.value)
        return _FP_KINDS[kind], bits[0] | (bits[1] << 64)

    @property
    def constant_data_raw(self):
        """
        The raw bytes of the elements of a constant data array or vector
        (value kinds 'constant_data_array' and 'constant_data_vector', whose
        elements are i8, i16, i32, i64, half, bfloat, float or double), in
        the byte order of the host. Raises ValueError for other values.
        """
        n = c_size_t(0)
        ptr = ffi.lib.LLVMPY_GetConstantDataRaw(self, byref(n))
        if not ptr:
            raise ValueError('expected a constant data array or vector, '
                             'got %s' % (self._kind,))
        return string_at(ptr, n.value)

    @property
    def is_constant_string(self):
        """
        Is this a constant data array or vector of i8 elements (a string)?
        """
        return ffi.lib.LLVMPY_IsConstantString(self)

    @property
    def aggregate_indices(self):
        """
        The constant indices of an extractvalue or insertvalue instruction
        as a list of ints. Raises ValueError for other values.
        """
        n = ffi.lib.LLVMPY_GetNumAggregateIndices(self)
        if n < 0:
            raise ValueError('expected extractvalue or insertvalue, got %s'
                             % (self._kind,))
        idxs = ffi.lib.LLVMPY_GetAggregateIndices(self)
        assert idxs, self._kind
        return [idxs[i] for i in range(n)]

    @property
    def switch_default(self):
        """
        The default destination block of a switch instruction. Raises
        ValueError for other values.
        """
        if ffi.lib.LLVMPY_SwitchNumCases(self) < 0:
            raise ValueError('expected a switch instruction, got %s'
                             % (self._kind,))
        return ValueRef(ffi.lib.LLVMPY_SwitchDefaultDest(self), 'block',
                        self._parents)

    @property
    def switch_cases(self):
        """
        The cases of a switch instruction (without the default one) as
        a list of pairs (value, destination block), where the value is
        a constant integer. Raises ValueError for other values.
        """
        n = ffi.lib.LLVMPY_SwitchNumCases(self)
        if n < 0:
            raise ValueError('expected a switch instruction, got %s'
                             % (self._kind,))
        parents = self._parents.copy()
        parents.update(instruction=self)
        return [(ValueRef(ffi.lib.LLVMPY_SwitchCaseValue(self, i), 'operand',
                          parents),
                 ValueRef(ffi.lib.LLVMPY_SwitchCaseDest(self, i), 'block',
                          self._parents))
                for i in range(n)]

    def strip_pointer_casts(self):
        """
        The value with the pointer casts (bitcasts, address space casts,
        GEPs with zero indices; instructions and constant expressions)
        stripped, the value itself if there are none.
        """
        ret = ValueRef(ffi.lib.LLVMPY_StripPointerCasts(self), 'operand',
                       self._parents)
        return self if ret == self else ret

    @property
    def atomicrmw_operation(self):
        """
        The operation of an atomicrmw instruction ('xchg', 'add', 'sub',
        'and', 'nand', 'or', 'xor', 'max', 'min', 'umax', 'umin', 'fadd',
        ...). Raises ValueError for other values.
        """
        ptr = ffi.lib.LLVMPY_GetAtomicRMWOperation(self)
        if not ptr:
            raise ValueError('expected an atomicrmw instruction, got %s'
                             % (self._kind,))
        return ffi.ret_string(ptr)

    @property
    def is_weak(self):
        """
        Is this cmpxchg instruction weak? Raises ValueError for other values.
        """
        r = ffi.lib.LLVMPY_IsWeakCmpXchg(self)
        if r < 0:
            raise ValueError('expected a cmpxchg instruction, got %s'
                             % (self._kind,))
        return bool(r)

    @property
    def byval_type(self):
        """
        The type of a 'byval' argument, None for other arguments. Raises
        ValueError for values that are not arguments.
        """
        if not self.is_argument:
            raise ValueError('expected an argument, got %s' % (self._kind,))
        ty = ffi.lib.LLVMPY_GetArgByValType(self)
        return TypeRef(ty) if ty else None

    def has_attribute(self, name):
        """
        Does this argument have the (enum or type) attribute 'name' (e.g.
        'byval', 'inalloca', 'noundef')? Raises ValueError for values that
        are not arguments and names that are not of enum or type attributes.
        """
        r = ffi.lib.LLVMPY_ArgHasAttribute(self, _encode_string(name))
        if r == -1:
            raise ValueError('expected an argument, got %s' % (self._kind,))
        if r == -2:
            raise ValueError('unknown attribute: %s' % (name,))
        return bool(r)

    @property
    def opcode(self):
        if not self.is_instruction:
            raise ValueError('expected instruction value, got %s'
                             % (self._kind,))
        return ffi.ret_string(ffi.lib.LLVMPY_GetOpcodeName(self))

    @property
    def initializer(self):
        """
        This value's initializer
        """
        if not self.is_global:
            raise ValueError('expected global value, got %s'
                             % (self._kind,))
        return ValueRef(ffi.lib.LLVMPY_GlobalGetInitializer(self),
                        self._kind, self._parents)

    @property
    def allocated_type(self):
        """
        The type allocated by this alloca instruction.
        """
        ty = ffi.lib.LLVMPY_GetAllocatedType(self)
        if not ty:
            raise ValueError('expected alloca instruction, got %s' % (self,))
        return TypeRef(ty)

    @property
    def gep_source_element_type(self):
        """
        The source element type of this GEP instruction or constant expr.
        """
        ty = ffi.lib.LLVMPY_GetGEPSourceElementType(self)
        if not ty:
            raise ValueError('expected getelementptr, got %s' % (self,))
        return TypeRef(ty)

    @property
    def global_value_type(self):
        """
        The type of the value of this global (the function type for
        functions). Unlike the type of the global itself (which is
        a pointer), this works also with opaque pointers.
        """
        ty = ffi.lib.LLVMPY_GlobalGetValueType(self)
        if not ty:
            raise ValueError('expected global value, got %s' % (self,))
        return TypeRef(ty)

    @property
    def ce_as_inst(self):
        """
        ConstantExpr as Instruction
        """
        if not self.is_constantexpr:
            raise ValueError('expected constant expr, got %s' % (self._kind,))
        return ValueRef(ffi.lib.LLVMPY_ConstantExprAsInst(self),
                        'instruction', self._parents)


    @property
    def phi_incoming_count(self):
        """
        Get incoming value and block of a PHI node
        """
        if not self.opcode == 'phi':
            raise ValueError('expected phi instruction, got %s'
                             % (self.opcode()))
        return ffi.lib.LLVMPY_PhiCountIncoming(self)

    def phi_incoming(self, idx):
        """
        Get incoming value and block of a PHI node
        """
        if not self.opcode == 'phi':
            raise ValueError('expected phi instruction, got %s'
                             % (self.opcode()))
        if idx >= self.phi_incoming_count:
            raise ValueError('index of phi instruction out of bounds')

        # FIXME: we screw up the parents here
        return (ValueRef(ffi.lib.LLVMPY_PhiGetIncomingValue(self, idx),
                         'operand', self._parents),
                ValueRef(ffi.lib.LLVMPY_PhiGetIncomingBlock(self, idx),
                         'block', self._parents))


class _ValueIterator(ffi.ObjectRef):

    kind = None  # derived classes must specify the Value kind value
                 # as class attribute

    def __init__(self, ptr, parents):
        ffi.ObjectRef.__init__(self, ptr)
        # Keep parent objects (module, function, etc) alive
        self._parents = parents
        if self.kind is None:
            raise NotImplementedError('%s must specify kind attribute'
                                      % (type(self).__name__,))

    def __next__(self):
        vp = self._next()
        if vp:
            return ValueRef(vp, self.kind, self._parents)
        else:
            raise StopIteration

    next = __next__

    def __iter__(self):
        return self


class _AttributeIterator(ffi.ObjectRef):

    def __next__(self):
        vp = self._next()
        if vp:
            return vp
        else:
            raise StopIteration

    next = __next__

    def __iter__(self):
        return self


class _AttributeListIterator(_AttributeIterator):

    def _dispose(self):
        self._capi.LLVMPY_DisposeAttributeListIter(self)

    def _next(self):
        return ffi.ret_bytes(ffi.lib.LLVMPY_AttributeListIterNext(self))


class _AttributeSetIterator(_AttributeIterator):

    def _dispose(self):
        self._capi.LLVMPY_DisposeAttributeSetIter(self)

    def _next(self):
        return ffi.ret_bytes(ffi.lib.LLVMPY_AttributeSetIterNext(self))


class _BlocksIterator(_ValueIterator):

    kind = 'block'

    def _dispose(self):
        self._capi.LLVMPY_DisposeBlocksIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_BlocksIterNext(self)


class _ArgumentsIterator(_ValueIterator):

    kind = 'argument'

    def _dispose(self):
        self._capi.LLVMPY_DisposeArgumentsIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_ArgumentsIterNext(self)


class _InstructionsIterator(_ValueIterator):

    kind = 'instruction'

    def _dispose(self):
        self._capi.LLVMPY_DisposeInstructionsIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_InstructionsIterNext(self)


class _OperandsIterator(_ValueIterator):

    kind = 'operand'

    def _dispose(self):
        self._capi.LLVMPY_DisposeOperandsIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_OperandsIterNext(self)


# FFI

ffi.lib.LLVMPY_PrintValueToString.argtypes = [
    ffi.LLVMValueRef,
    POINTER(c_char_p)
]

ffi.lib.LLVMPY_GetGlobalParent.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetGlobalParent.restype = ffi.LLVMModuleRef

ffi.lib.LLVMPY_GetValueName.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetValueName.restype = c_char_p

ffi.lib.LLVMPY_GetDbgFile.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetDbgFile.restype = c_char_p

ffi.lib.LLVMPY_SetValueName.argtypes = [ffi.LLVMValueRef, c_char_p]

ffi.lib.LLVMPY_TypeOf.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_TypeOf.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_PrintType.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_PrintType.restype = c_void_p

ffi.lib.LLVMPY_TypeIsPointer.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_TypeIsPointer.restype = c_bool

ffi.lib.LLVMPY_TypeIsArray.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_TypeIsArray.restype = c_bool

ffi.lib.LLVMPY_TypeIsStruct.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_TypeIsStruct.restype = c_bool

ffi.lib.LLVMPY_TypeIsVector.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_TypeIsVector.restype = c_bool

ffi.lib.LLVMPY_GetElementType.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetElementType.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_GetAllocatedType.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetAllocatedType.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_GetGEPSourceElementType.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetGEPSourceElementType.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_GlobalGetValueType.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GlobalGetValueType.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_GetStructNumElements.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetStructNumElements.restype = c_uint

ffi.lib.LLVMPY_GetStructElementType.argtypes = [ffi.LLVMTypeRef, c_uint]
ffi.lib.LLVMPY_GetStructElementType.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_GetTypeName.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetTypeName.restype = c_void_p

ffi.lib.LLVMPY_GetTypeKind.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetTypeKind.restype = c_int

ffi.lib.LLVMPY_GetTypeBitWidth.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetTypeBitWidth.restype = c_ulonglong

ffi.lib.LLVMPY_GetTypeElementCount.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetTypeElementCount.restype = c_longlong

ffi.lib.LLVMPY_GetReturnType.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetReturnType.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_TypeIsSized.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_TypeIsSized.restype = c_bool

ffi.lib.LLVMPY_GetPointerAddressSpace.argtypes = [ffi.LLVMTypeRef]
ffi.lib.LLVMPY_GetPointerAddressSpace.restype = c_int

ffi.lib.LLVMPY_GetDbgLine.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetDbgLine.restype = c_uint

ffi.lib.LLVMPY_GetDbgCol.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetDbgCol.restype = c_uint

ffi.lib.LLVMPY_GetLinkage.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetLinkage.restype = c_int

ffi.lib.LLVMPY_SetLinkage.argtypes = [ffi.LLVMValueRef, c_int]

ffi.lib.LLVMPY_GetVisibility.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetVisibility.restype = c_int

ffi.lib.LLVMPY_SetVisibility.argtypes = [ffi.LLVMValueRef, c_int]

ffi.lib.LLVMPY_GetDLLStorageClass.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetDLLStorageClass.restype = c_int

ffi.lib.LLVMPY_SetDLLStorageClass.argtypes = [ffi.LLVMValueRef, c_int]

ffi.lib.LLVMPY_GetEnumAttributeKindForName.argtypes = [c_char_p, c_size_t]
ffi.lib.LLVMPY_GetEnumAttributeKindForName.restype = c_uint

ffi.lib.LLVMPY_AddFunctionAttr.argtypes = [ffi.LLVMValueRef, c_uint]

ffi.lib.LLVMPY_IsDeclaration.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_IsDeclaration.restype = c_int

ffi.lib.LLVMPY_IsConstant.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_IsConstant.restype = c_int

ffi.lib.LLVMPY_IsConstantExpr.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_IsConstantExpr.restype = c_int

ffi.lib.LLVMPY_IsGlobalVariableConstant.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_IsGlobalVariableConstant.restype = c_int

ffi.lib.LLVMPY_FunctionAttributesIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_FunctionAttributesIter.restype = ffi.LLVMAttributeListIterator

ffi.lib.LLVMPY_CallInstAttributesIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_CallInstAttributesIter.restype = ffi.LLVMAttributeListIterator

ffi.lib.LLVMPY_InvokeInstAttributesIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_InvokeInstAttributesIter.restype = ffi.LLVMAttributeListIterator

ffi.lib.LLVMPY_GlobalAttributesIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GlobalAttributesIter.restype = ffi.LLVMAttributeSetIterator

ffi.lib.LLVMPY_ArgumentAttributesIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_ArgumentAttributesIter.restype = ffi.LLVMAttributeSetIterator

ffi.lib.LLVMPY_FunctionBlocksIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_FunctionBlocksIter.restype = ffi.LLVMBlocksIterator

ffi.lib.LLVMPY_FunctionArgumentsIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_FunctionArgumentsIter.restype = ffi.LLVMArgumentsIterator

ffi.lib.LLVMPY_BlockInstructionsIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_BlockInstructionsIter.restype = ffi.LLVMInstructionsIterator

ffi.lib.LLVMPY_InstructionOperandsIter.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_InstructionOperandsIter.restype = ffi.LLVMOperandsIterator

ffi.lib.LLVMPY_DisposeAttributeListIter.argtypes = [ffi.LLVMAttributeListIterator]

ffi.lib.LLVMPY_DisposeAttributeSetIter.argtypes = [ffi.LLVMAttributeSetIterator]

ffi.lib.LLVMPY_DisposeBlocksIter.argtypes = [ffi.LLVMBlocksIterator]

ffi.lib.LLVMPY_DisposeInstructionsIter.argtypes = [ffi.LLVMInstructionsIterator]

ffi.lib.LLVMPY_DisposeOperandsIter.argtypes = [ffi.LLVMOperandsIterator]

ffi.lib.LLVMPY_AttributeListIterNext.argtypes = [ffi.LLVMAttributeListIterator]
ffi.lib.LLVMPY_AttributeListIterNext.restype = c_void_p

ffi.lib.LLVMPY_AttributeSetIterNext.argtypes = [ffi.LLVMAttributeSetIterator]
ffi.lib.LLVMPY_AttributeSetIterNext.restype = c_void_p

ffi.lib.LLVMPY_BlocksIterNext.argtypes = [ffi.LLVMBlocksIterator]
ffi.lib.LLVMPY_BlocksIterNext.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_ArgumentsIterNext.argtypes = [ffi.LLVMArgumentsIterator]
ffi.lib.LLVMPY_ArgumentsIterNext.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_InstructionsIterNext.argtypes = [ffi.LLVMInstructionsIterator]
ffi.lib.LLVMPY_InstructionsIterNext.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_OperandsIterNext.argtypes = [ffi.LLVMOperandsIterator]
ffi.lib.LLVMPY_OperandsIterNext.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetAlignment.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetAlignment.restype = c_int

ffi.lib.LLVMPY_GetCmpPredicate.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetCmpPredicate.restype = c_int

ffi.lib.LLVMPY_GetWrapFlags.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetWrapFlags.restype = c_int

ffi.lib.LLVMPY_GetValueKind.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetValueKind.restype = c_int

ffi.lib.LLVMPY_GetConstantInt.argtypes = [ffi.LLVMValueRef,
                                          POINTER(c_longlong)]
ffi.lib.LLVMPY_GetConstantInt.restype = c_uint

ffi.lib.LLVMPY_GetConstantIntString.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetConstantIntString.restype = c_void_p

ffi.lib.LLVMPY_GetConstantFP.argtypes = [ffi.LLVMValueRef,
                                         POINTER(c_ulonglong),
                                         POINTER(c_uint)]
ffi.lib.LLVMPY_GetConstantFP.restype = c_int

ffi.lib.LLVMPY_GetConstantDataRaw.argtypes = [ffi.LLVMValueRef,
                                             POINTER(c_size_t)]
ffi.lib.LLVMPY_GetConstantDataRaw.restype = c_void_p

ffi.lib.LLVMPY_IsConstantString.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_IsConstantString.restype = c_bool

ffi.lib.LLVMPY_GetNumAggregateIndices.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetNumAggregateIndices.restype = c_int

ffi.lib.LLVMPY_GetAggregateIndices.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetAggregateIndices.restype = POINTER(c_uint)

ffi.lib.LLVMPY_SwitchNumCases.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_SwitchNumCases.restype = c_int

ffi.lib.LLVMPY_SwitchCaseValue.argtypes = [ffi.LLVMValueRef, c_uint]
ffi.lib.LLVMPY_SwitchCaseValue.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_SwitchCaseDest.argtypes = [ffi.LLVMValueRef, c_uint]
ffi.lib.LLVMPY_SwitchCaseDest.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_SwitchDefaultDest.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_SwitchDefaultDest.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_StripPointerCasts.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_StripPointerCasts.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_GetDbgLoc.argtypes = [ffi.LLVMValueRef, POINTER(c_uint),
                                    POINTER(c_uint), POINTER(c_size_t)]
ffi.lib.LLVMPY_GetDbgLoc.restype = c_void_p

ffi.lib.LLVMPY_GetAtomicRMWOperation.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetAtomicRMWOperation.restype = c_void_p

ffi.lib.LLVMPY_IsWeakCmpXchg.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_IsWeakCmpXchg.restype = c_int

ffi.lib.LLVMPY_GetArgByValType.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetArgByValType.restype = ffi.LLVMTypeRef

ffi.lib.LLVMPY_ArgHasAttribute.argtypes = [ffi.LLVMValueRef, c_char_p]
ffi.lib.LLVMPY_ArgHasAttribute.restype = c_int

ffi.lib.LLVMPY_GetOpcodeName.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GetOpcodeName.restype = c_void_p

ffi.lib.LLVMPY_GlobalGetInitializer.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_GlobalGetInitializer.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_ConstantExprAsInst.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_ConstantExprAsInst.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_PhiCountIncoming.argtypes = [ffi.LLVMValueRef]
ffi.lib.LLVMPY_PhiCountIncoming.restype = c_uint

ffi.lib.LLVMPY_PhiGetIncomingValue.argtypes = [ffi.LLVMValueRef, c_uint]
ffi.lib.LLVMPY_PhiGetIncomingValue.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_PhiGetIncomingBlock.argtypes = [ffi.LLVMValueRef, c_uint]
ffi.lib.LLVMPY_PhiGetIncomingBlock.restype = ffi.LLVMValueRef

