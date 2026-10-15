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
