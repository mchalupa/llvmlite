"""Tests of the ValueRef/TypeRef API used to avoid parsing printed IR."""
from __future__ import print_function, absolute_import

from llvmlite import binding as llvm
from . import TestCase


def setUpModule():
    llvm.initialize()
    llvm.initialize_native_target()


def _insts(mod, fname):
    return [i for b in mod.get_function(fname).blocks for i in b.instructions]


class TestAlignment(TestCase):
    ir = r"""
    @g1 = global i32 0, align 16
    @g2 = global i32 0
    define void @f(ptr %p) {
      %a = alloca i64, align 8
      %b = alloca i8
      %l = load i32, ptr %p, align 2
      %m = load i32, ptr %p
      store i32 1, ptr %p, align 1
      store i64 1, ptr %a, align 4
      %c = add i32 %l, %m
      ret void
    }
    """

    def test_alignment(self):
        mod = llvm.parse_assembly(self.ir)
        mod.verify()
        self.assertEqual(mod.get_global_variable('g1').alignment, 16)
        self.assertIsNone(mod.get_global_variable('g2').alignment)
        i = _insts(mod, 'f')
        self.assertEqual([x.opcode for x in i[:4]],
                         ['alloca', 'alloca', 'load', 'load'])
        self.assertEqual(i[0].alignment, 8)
        self.assertEqual(i[1].alignment, 1)
        self.assertEqual(i[2].alignment, 2)
        self.assertEqual(i[3].alignment, 4)  # not given: ABI alignment of i32
        self.assertEqual(i[4].alignment, 1)
        self.assertEqual(i[5].alignment, 4)

    def test_no_alignment(self):
        mod = llvm.parse_assembly(self.ir)
        i = _insts(mod, 'f')
        self.assertEqual(i[6].opcode, 'add')
        with self.assertRaises(ValueError):
            i[6].alignment
        with self.assertRaises(ValueError):
            i[7].alignment


class TestPredicate(TestCase):
    ipreds = ['eq', 'ne', 'ugt', 'uge', 'ult', 'ule', 'sgt', 'sge', 'slt',
              'sle']
    fpreds = ['false', 'oeq', 'ogt', 'oge', 'olt', 'ole', 'one', 'ord',
              'uno', 'ueq', 'ugt', 'uge', 'ult', 'ule', 'une', 'true']

    def test_predicates(self):
        body = ''.join('  %%i%d = icmp %s i32 %%a, %%b\n' % (n, p)
                       for n, p in enumerate(self.ipreds))
        body += ''.join('  %%f%d = fcmp %s double %%x, %%y\n' % (n, p)
                        for n, p in enumerate(self.fpreds))
        body += '  %s = icmp samesign ult i32 %a, %b\n'.replace('%s', '%sm')
        mod = llvm.parse_assembly(
            'define void @f(i32 %a, i32 %b, double %x, double %y) {\n' +
            body + '  %c = add i32 %a, %b\n  ret void\n}\n')
        mod.verify()
        i = _insts(mod, 'f')
        n = len(self.ipreds)
        for x, p in zip(i[:n], self.ipreds):
            self.assertEqual(x.opcode, 'icmp')
            self.assertEqual(x.predicate, p)
            # the printed predicate is the same
            self.assertIn(' icmp %s ' % p, str(x))
        for x, p in zip(i[n:n + len(self.fpreds)], self.fpreds):
            self.assertEqual(x.opcode, 'fcmp')
            self.assertEqual(x.predicate, p)
            self.assertIn(' fcmp %s ' % p, str(x))
        # the samesign flag does not change the predicate
        sm = i[n + len(self.fpreds)]
        self.assertEqual(sm.predicate, 'ult')
        self.assertEqual(i[-2].opcode, 'add')
        with self.assertRaises(ValueError):
            i[-2].predicate
        with self.assertRaises(ValueError):
            i[-1].predicate


class TestWrapFlags(TestCase):
    def test_wrap_flags(self):
        mod = llvm.parse_assembly(r"""
        define void @f(i32 %a, i32 %b) {
          %v0 = add i32 %a, %b
          %v1 = add nsw i32 %a, %b
          %v2 = add nuw i32 %a, %b
          %v3 = add nuw nsw i32 %a, %b
          %v4 = mul nsw i32 %a, %b
          %v5 = sub nuw nsw i32 %a, %b
          %v6 = shl nsw i32 %a, %b
          %v7 = shl nuw i32 %a, %b
          %v8 = and i32 %a, %b
          ret void
        }
        """)
        mod.verify()
        i = _insts(mod, 'f')
        self.assertEqual(
            [(x.has_nsw, x.has_nuw) for x in i[:8]],
            [(False, False), (True, False), (False, True), (True, True),
             (True, False), (True, True), (True, False), (False, True)])
        for x in i[8:]:
            with self.assertRaises(ValueError):
                x.has_nsw
            with self.assertRaises(ValueError):
                x.has_nuw


class TestValueKind(TestCase):
    ir = r"""
    %S = type { i32, i8 }
    @gu = global i32 undef
    @gp = global i32 poison
    @gz = global [4 x i32] zeroinitializer
    @gi = global i32 5
    @gf = global double 1.5
    @gn = global ptr null
    @ga = global [3 x i32] [i32 1, i32 2, i32 3]
    @gs = global [4 x i8] c"abc\00"
    @gst = global %S { i32 1, i8 2 }
    @gv = global <2 x i32> <i32 1, i32 2>
    @gca = global [2 x ptr] [ptr @gi, ptr null]
    @gce = global i64 ptrtoint (ptr @gi to i64)
    @gal = alias i32, ptr @gi
    declare void @ext()
    define void @f(i32 %a, ptr %p) {
    entry:
      %x = add i32 %a, 1
      store i32 undef, ptr %p
      store i32 poison, ptr %p
      store i32 7, ptr %p
      store double 2.5, ptr %p
      store ptr null, ptr %p
      store ptr @ext, ptr %p
      call void asm sideeffect "nop", ""()
      call void @ext()
      ret void
    }
    """

    def test_kinds(self):
        mod = llvm.parse_assembly(self.ir)
        mod.verify()
        init = lambda n: mod.get_global_variable(n).initializer  # noqa
        self.assertEqual(init('gu').value_kind, 'undef')
        self.assertEqual(init('gp').value_kind, 'poison')
        self.assertEqual(init('gz').value_kind, 'constant_aggregate_zero')
        self.assertEqual(init('gi').value_kind, 'constant_int')
        self.assertEqual(init('gf').value_kind, 'constant_fp')
        self.assertEqual(init('gn').value_kind, 'constant_pointer_null')
        self.assertEqual(init('ga').value_kind, 'constant_data_array')
        self.assertEqual(init('gs').value_kind, 'constant_data_array')
        self.assertEqual(init('gst').value_kind, 'constant_struct')
        self.assertEqual(init('gv').value_kind, 'constant_data_vector')
        self.assertEqual(init('gca').value_kind, 'constant_array')
        self.assertEqual(init('gce').value_kind, 'constant_expr')
        self.assertEqual(mod.get_global_variable('gi').value_kind,
                         'global_variable')
        f = mod.get_function('f')
        self.assertEqual(f.value_kind, 'function')
        self.assertEqual(mod.get_function('ext').value_kind, 'function')
        args = list(f.arguments)
        self.assertEqual([a.value_kind for a in args],
                         ['argument', 'argument'])
        insts = [i for b in f.blocks for i in b.instructions]
        self.assertEqual(insts[0].value_kind, 'instruction')
        stores = [i for i in insts if i.opcode == 'store']
        self.assertEqual([list(s.operands)[0].value_kind for s in stores],
                         ['undef', 'poison', 'constant_int', 'constant_fp',
                          'constant_pointer_null', 'function'])
        call = [i for i in insts if i.opcode == 'call']
        self.assertEqual(list(call[0].operands)[-1].value_kind, 'inline_asm')
        self.assertEqual(list(call[1].operands)[-1].value_kind, 'function')
        self.assertEqual(list(insts[-1].operands), [])


class TestScalarConstants(TestCase):
    ir = r"""
    @i1t = global i1 true
    @i1f = global i1 false
    @i8 = global i8 -1
    @i32 = global i32 -2147483648
    @i64 = global i64 -9223372036854775808
    @i65 = global i65 36893488147419103231
    @i128 = global i128 -170141183460469231731687303715884105728
    @i128p = global i128 170141183460469231731687303715884105727
    @h = global half 1.0
    @bf = global bfloat 1.0
    @f = global float 0x3FB99999A0000000
    @fn = global float 0x7FF8000000000000
    @fi = global float 0xFFF0000000000000
    @d = global double 0.1
    @dz = global double -0.0
    @x = global x86_fp80 0xK3FFF8000000000000000
    @q = global fp128 0xL00000000000000003FFF000000000000
    @pp = global ppc_fp128 0xM3FF00000000000000000000000000000
    """

    def init(self, mod, name):
        return mod.get_global_variable(name).initializer

    def test_ints(self):
        mod = llvm.parse_assembly(self.ir)
        ci = lambda n: self.init(mod, n).constant_int  # noqa
        self.assertEqual(ci('i1t'), (1, -1))
        self.assertEqual(ci('i1f'), (1, 0))
        self.assertEqual(ci('i8'), (8, -1))
        self.assertEqual(ci('i32'), (32, -2 ** 31))
        self.assertEqual(ci('i64'), (64, -2 ** 63))
        self.assertEqual(ci('i65'), (65, -1))
        self.assertEqual(ci('i128'), (128, -2 ** 127))
        self.assertEqual(ci('i128p'), (128, 2 ** 127 - 1))
        with self.assertRaises(ValueError):
            self.init(mod, 'f').constant_int

    def test_fps(self):
        import struct
        mod = llvm.parse_assembly(self.ir)
        cf = lambda n: self.init(mod, n).constant_fp  # noqa
        self.assertEqual(cf('h'), ('half', 0x3C00))
        self.assertEqual(cf('bf'), ('bfloat', 0x3F80))
        self.assertEqual(cf('f'), ('float',
                                   struct.unpack('<I',
                                                 struct.pack('<f', 0.1))[0]))
        self.assertEqual(cf('fn'), ('float', 0x7FC00000))
        self.assertEqual(cf('fi'), ('float', 0xFF800000))
        self.assertEqual(cf('d'), ('double',
                                   struct.unpack('<Q',
                                                 struct.pack('<d', 0.1))[0]))
        self.assertEqual(cf('dz'), ('double', 1 << 63))
        self.assertEqual(cf('x'), ('x86_fp80', 0x3FFF8000000000000000))
        self.assertEqual(cf('q'), ('fp128', 0x3FFF << 112))
        self.assertEqual(cf('pp')[0], 'ppc_fp128')
        with self.assertRaises(ValueError):
            self.init(mod, 'i8').constant_fp


class TestTypes(TestCase):
    ir = r"""
    %struct.opaque_named = type { i32, ptr }
    %struct.Opq = type opaque
    @i = global i37 0
    @h = global half 0.0
    @f = global float 0.0
    @d = global double 0.0
    @x = global x86_fp80 0xK00000000000000000000
    @q = global fp128 0xL00000000000000000000000000000000
    @p = global ptr null
    @p1 = global ptr addrspace(1) null
    @a = global [5 x [3 x i16]] zeroinitializer
    @v = global <4 x i32> zeroinitializer
    @s = global %struct.opaque_named zeroinitializer
    @o = external global %struct.Opq
    @l = global { i8, double } zeroinitializer
    declare { i32, i1 } @agg(i32, ...)
    declare void @vd()
    """

    def vt(self, mod, name):
        return mod.get_global_variable(name).global_value_type

    def test_kinds(self):
        mod = llvm.parse_assembly(self.ir)
        K = llvm.TypeKind
        kinds = {'i': K.integer, 'h': K.half, 'f': K.float, 'd': K.double,
                 'x': K.x86_fp80, 'q': K.fp128, 'p': K.pointer,
                 'p1': K.pointer, 'a': K.array, 'v': K.vector, 's': K.struct,
                 'o': K.struct, 'l': K.struct}
        for n, k in kinds.items():
            self.assertEqual(self.vt(mod, n).type_kind, k, n)
        fty = mod.get_function('agg').global_value_type
        self.assertEqual(fty.type_kind, K.function)
        self.assertEqual(mod.get_function('vd').global_value_type
                         .return_type.type_kind, K.void)

    def test_widths(self):
        mod = llvm.parse_assembly(self.ir)
        widths = {'i': 37, 'h': 16, 'f': 32, 'd': 64, 'x': 80, 'q': 128,
                  'v': 128, 'p': 0, 'a': 0, 's': 0, 'o': 0}
        for n, w in widths.items():
            self.assertEqual(self.vt(mod, n).type_width, w, n)

    def test_element_count(self):
        mod = llvm.parse_assembly(self.ir)
        a = self.vt(mod, 'a')
        self.assertEqual(a.element_count, 5)
        self.assertEqual(a.element_type.element_count, 3)
        self.assertEqual(a.element_type.element_type.type_width, 16)
        self.assertEqual(self.vt(mod, 'v').element_count, 4)
        for n in ('i', 'p', 's'):
            with self.assertRaises(ValueError):
                self.vt(mod, n).element_count

    def test_return_type(self):
        mod = llvm.parse_assembly(self.ir)
        rt = mod.get_function('agg').global_value_type.return_type
        self.assertTrue(rt.is_struct)
        self.assertEqual(rt.struct_num_elements, 2)
        self.assertEqual(rt.struct_element_type(1).type_width, 1)
        with self.assertRaises(ValueError):
            self.vt(mod, 'i').return_type

    def test_sized(self):
        mod = llvm.parse_assembly(self.ir)
        for n in ('i', 'h', 'x', 'p', 'a', 'v', 's', 'l'):
            self.assertTrue(self.vt(mod, n).is_sized, n)
        # (the name of a sized struct may contain 'opaque')
        self.assertIn('opaque', str(self.vt(mod, 's')))
        self.assertFalse(self.vt(mod, 'o').is_sized)
        self.assertFalse(mod.get_function('vd').global_value_type.is_sized)
        self.assertFalse(mod.get_function('vd').global_value_type
                         .return_type.is_sized)

    def test_address_space(self):
        mod = llvm.parse_assembly(self.ir)
        self.assertEqual(self.vt(mod, 'p').address_space, 0)
        self.assertEqual(self.vt(mod, 'p1').address_space, 1)
        with self.assertRaises(ValueError):
            self.vt(mod, 'i').address_space


class TestConstantData(TestCase):
    ir = r"""
    @s = global [4 x i8] c"a\00\FF\5C"
    @a16 = global [3 x i16] [i16 1, i16 -2, i16 300]
    @a64 = global [2 x i64] [i64 -1, i64 9223372036854775807]
    @f = global [2 x float] [float 1.0, float -0.5]
    @d = global [2 x double] [double 0.1, double 2.0]
    @v = global <2 x i32> <i32 7, i32 -7>
    @z = global [2 x i32] zeroinitializer
    @st = global { i32, i32 } { i32 1, i32 2 }
    define i32 @f1({ i32, { i8, [2 x i16] } } %a) {
      %x = extractvalue { i32, { i8, [2 x i16] } } %a, 1, 1, 0
      %y = insertvalue { i32, { i8, [2 x i16] } } %a, i8 1, 1, 0
      %z = add i32 1, 2
      ret i32 %z
    }
    """

    def init(self, mod, name):
        return mod.get_global_variable(name).initializer

    def test_raw(self):
        import struct
        import sys
        mod = llvm.parse_assembly(self.ir)
        bo = '<' if sys.byteorder == 'little' else '>'
        raw = lambda n: self.init(mod, n).constant_data_raw  # noqa
        self.assertEqual(raw('s'), b'a\x00\xff\\')
        self.assertEqual(struct.unpack(bo + '3h', raw('a16')), (1, -2, 300))
        self.assertEqual(struct.unpack(bo + '2q', raw('a64')),
                         (-1, 2 ** 63 - 1))
        self.assertEqual(struct.unpack(bo + '2f', raw('f')), (1.0, -0.5))
        self.assertEqual(struct.unpack(bo + '2d', raw('d')), (0.1, 2.0))
        self.assertEqual(struct.unpack(bo + '2i', raw('v')), (7, -7))
        for n in ('z', 'st'):
            with self.assertRaises(ValueError):
                raw(n)

    def test_is_string(self):
        mod = llvm.parse_assembly(self.ir)
        self.assertTrue(self.init(mod, 's').is_constant_string)
        for n in ('a16', 'f', 'z', 'st'):
            self.assertFalse(self.init(mod, n).is_constant_string, n)

    def test_aggregate_indices(self):
        mod = llvm.parse_assembly(self.ir)
        i = _insts(mod, 'f1')
        self.assertEqual(i[0].opcode, 'extractvalue')
        self.assertEqual(i[0].aggregate_indices, [1, 1, 0])
        self.assertEqual(i[1].opcode, 'insertvalue')
        self.assertEqual(i[1].aggregate_indices, [1, 0])
        with self.assertRaises(ValueError):
            i[2].aggregate_indices


class TestSwitchAndCallee(TestCase):
    ir = r"""
    @g = global i32 0
    @ga = alias i32, ptr @g
    declare void @ext()
    define i32 @f(i64 %x, ptr %fp) {
    entry:
      switch i64 %x, label %d [ i64 -1, label %a
                                i64 7, label %b
                                i64 9223372036854775807, label %a ]
    a:
      call void @ext()
      call void %fp()
      call addrspace(1) void addrspacecast (ptr @ext to ptr addrspace(1))()
      ret i32 1
    b:
      ret i32 2
    d:
      switch i128 0, label %b [ i128 170141183460469231731687303715884105727, label %a ]
    }
    """

    def test_switch(self):
        mod = llvm.parse_assembly(self.ir)
        mod.verify()
        f = mod.get_function('f')
        blocks = list(f.blocks)
        sw = list(blocks[0].instructions)[0]
        self.assertEqual(sw.opcode, 'switch')
        self.assertEqual(sw.switch_default, blocks[3])
        cases = sw.switch_cases
        self.assertEqual([v.constant_int for v, _ in cases],
                         [(64, -1), (64, 7), (64, 2 ** 63 - 1)])
        self.assertEqual([b for _, b in cases],
                         [blocks[1], blocks[2], blocks[1]])
        self.assertTrue(all(b.is_block for _, b in cases))
        sw2 = list(blocks[3].instructions)[0]
        self.assertEqual(sw2.switch_default, blocks[2])
        self.assertEqual([(v.constant_int, b) for v, b in sw2.switch_cases],
                         [((128, 2 ** 127 - 1), blocks[1])])
        with self.assertRaises(ValueError):
            list(blocks[1].instructions)[0].switch_cases
        with self.assertRaises(ValueError):
            list(blocks[1].instructions)[0].switch_default

    def test_strip_pointer_casts(self):
        mod = llvm.parse_assembly(self.ir)
        calls = list(list(mod.get_function('f').blocks)[1].instructions)[:3]
        callees = [list(c.operands)[-1] for c in calls]
        self.assertEqual(callees[0].strip_pointer_casts().value_kind,
                         'function')
        self.assertIs(callees[0].strip_pointer_casts(), callees[0])
        self.assertEqual(callees[1].strip_pointer_casts().value_kind,
                         'argument')
        self.assertEqual(callees[2].value_kind, 'constant_expr')
        s = callees[2].strip_pointer_casts()
        self.assertEqual(s.value_kind, 'function')
        self.assertEqual(s.name, 'ext')
        ga = list(mod.global_variables)
        self.assertEqual(ga[0].strip_pointer_casts(), ga[0])


class TestDbgAtomicsArgs(TestCase):
    ir = r"""
    %struct.S = type { i32, i64 }
    define void @f(ptr byval(%struct.S) %s, ptr byval([4 x i8]) %a, ptr %p,
                   ptr inalloca(i32) %ia) {
      %1 = atomicrmw add ptr %p, i32 1 seq_cst, !dbg !10
      %2 = atomicrmw volatile umax ptr %p, i32 1 monotonic
      %3 = atomicrmw xchg ptr %p, ptr null acquire
      %4 = cmpxchg weak ptr %p, i32 0, i32 1 seq_cst seq_cst
      %5 = cmpxchg volatile ptr %p, i32 0, i32 1 seq_cst seq_cst
      ret void
    }
    !llvm.dbg.cu = !{!0}
    !llvm.module.flags = !{!3}
    !0 = distinct !DICompileUnit(language: DW_LANG_C99, file: !1,
                                 emissionKind: FullDebug)
    !1 = !DIFile(filename: "dir/a\C3\A9.c", directory: "/tmp")
    !3 = !{i32 2, !"Debug Info Version", i32 3}
    !5 = distinct !DISubprogram(name: "f", scope: !1, file: !1, line: 1,
                                type: !6, unit: !0)
    !6 = !DISubroutineType(types: !{})
    !10 = !DILocation(line: 7, column: 3, scope: !5)
    """

    def test_dbg_loc(self):
        mod = llvm.parse_assembly(self.ir)
        i = _insts(mod, 'f')
        self.assertEqual(i[0].dbg_loc, ('dir/a\xc3\xa9.c', 7, 3))
        self.assertEqual(i[1].dbg_loc, ('', 0, 0))
        self.assertEqual(mod.get_function('f').dbg_loc, ('', 0, 0))

    def test_atomics(self):
        mod = llvm.parse_assembly(self.ir)
        i = _insts(mod, 'f')
        self.assertEqual([x.atomicrmw_operation for x in i[:3]],
                         ['add', 'umax', 'xchg'])
        self.assertEqual([x.is_weak for x in i[3:5]], [True, False])
        with self.assertRaises(ValueError):
            i[3].atomicrmw_operation
        with self.assertRaises(ValueError):
            i[0].is_weak

    def test_args(self):
        mod = llvm.parse_assembly(self.ir)
        args = list(mod.get_function('f').arguments)
        self.assertEqual(args[0].byval_type, mod.get_struct_type('struct.S'))
        self.assertEqual(args[1].byval_type.element_count, 4)
        self.assertIsNone(args[2].byval_type)
        self.assertIsNone(args[3].byval_type)
        self.assertEqual([a.has_attribute('byval') for a in args],
                         [True, True, False, False])
        self.assertEqual([a.has_attribute('inalloca') for a in args],
                         [False, False, False, True])
        with self.assertRaises(ValueError):
            args[0].has_attribute('no-such-attribute')
        with self.assertRaises(ValueError):
            _insts(mod, 'f')[0].byval_type
