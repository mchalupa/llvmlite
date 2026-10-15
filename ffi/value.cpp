#include <string>
#include "llvm-c/Core.h"
#include "core.h"

#include <iostream>

// the following is needed for WriteGraph()
#include "llvm/Analysis/CFGPrinter.h"
#include "llvm/Support/GraphWriter.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Operator.h"

/* An iterator around a attribute list, including the stop condition */
struct AttributeListIterator {
    typedef llvm::AttributeList::iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    AttributeListIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueAttributeListIterator;
typedef OpaqueAttributeListIterator* LLVMAttributeListIteratorRef;

/* An iterator around a attribute set, including the stop condition */
struct AttributeSetIterator {
    typedef llvm::AttributeSet::iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    AttributeSetIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueAttributeSetIterator;
typedef OpaqueAttributeSetIterator* LLVMAttributeSetIteratorRef;

/* An iterator around a function's blocks, including the stop condition */
struct BlocksIterator {
    typedef llvm::Function::const_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    BlocksIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueBlocksIterator;
typedef OpaqueBlocksIterator* LLVMBlocksIteratorRef;

/* An iterator around a function's arguments, including the stop condition */
struct ArgumentsIterator {
    typedef llvm::Function::const_arg_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    ArgumentsIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueArgumentsIterator;
typedef OpaqueArgumentsIterator* LLVMArgumentsIteratorRef;


/* An iterator around a basic block's instructions, including the stop condition */
struct InstructionsIterator {
    typedef llvm::BasicBlock::const_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    InstructionsIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueInstructionsIterator;
typedef OpaqueInstructionsIterator* LLVMInstructionsIteratorRef;

/* An iterator around a instruction's operands, including the stop condition */
struct OperandsIterator {
    typedef llvm::Instruction::const_op_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    OperandsIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueOperandsIterator;
typedef OpaqueOperandsIterator* LLVMOperandsIteratorRef;

namespace llvm {

static LLVMAttributeListIteratorRef
wrap(AttributeListIterator* GI){
    return reinterpret_cast<LLVMAttributeListIteratorRef>(GI);
}

static AttributeListIterator*
unwrap(LLVMAttributeListIteratorRef GI){
    return reinterpret_cast<AttributeListIterator *>(GI);
}

static LLVMAttributeSetIteratorRef
wrap(AttributeSetIterator* GI){
    return reinterpret_cast<LLVMAttributeSetIteratorRef>(GI);
}

static AttributeSetIterator*
unwrap(LLVMAttributeSetIteratorRef GI){
    return reinterpret_cast<AttributeSetIterator *>(GI);
}

static LLVMBlocksIteratorRef
wrap(BlocksIterator* GI){
    return reinterpret_cast<LLVMBlocksIteratorRef>(GI);
}

static BlocksIterator*
unwrap(LLVMBlocksIteratorRef GI){
    return reinterpret_cast<BlocksIterator *>(GI);
}

static LLVMArgumentsIteratorRef
wrap(ArgumentsIterator* GI){
    return reinterpret_cast<LLVMArgumentsIteratorRef>(GI);
}

static ArgumentsIterator*
unwrap(LLVMArgumentsIteratorRef GI){
    return reinterpret_cast<ArgumentsIterator *>(GI);
}

static LLVMInstructionsIteratorRef
wrap(InstructionsIterator* GI){
    return reinterpret_cast<LLVMInstructionsIteratorRef>(GI);
}

static InstructionsIterator*
unwrap(LLVMInstructionsIteratorRef GI){
    return reinterpret_cast<InstructionsIterator *>(GI);
}

static LLVMOperandsIteratorRef
wrap(OperandsIterator* GI){
    return reinterpret_cast<LLVMOperandsIteratorRef>(GI);
}

static OperandsIterator*
unwrap(LLVMOperandsIteratorRef GI){
    return reinterpret_cast<OperandsIterator *>(GI);
}


}

extern "C" {

API_EXPORT(LLVMAttributeListIteratorRef)
LLVMPY_FunctionAttributesIter(LLVMValueRef F)
{
    using namespace llvm;
    Function* func = unwrap<Function>(F);
    AttributeList attrs = func->getAttributes();
    return wrap(new AttributeListIterator(attrs.begin(),
                                          attrs.end()));
}

API_EXPORT(LLVMAttributeSetIteratorRef)
LLVMPY_ArgumentAttributesIter(LLVMValueRef A)
{
    using namespace llvm;
    Argument* arg = unwrap<Argument>(A);
    unsigned argno = arg->getArgNo();
    AttributeSet attrs = arg->getParent()
#if LLVM_VERSION_MAJOR >= 14
      ->getAttributes().getParamAttrs(argno);
#else
      ->getAttributes().getParamAttributes(argno);
#endif
    return wrap(new AttributeSetIterator(attrs.begin(),
                                         attrs.end()));
}

API_EXPORT(LLVMAttributeListIteratorRef)
LLVMPY_CallInstAttributesIter(LLVMValueRef C)
{
    using namespace llvm;
    CallInst* inst = unwrap<CallInst>(C);
    AttributeList attrs = inst->getAttributes();
    return wrap(new AttributeListIterator(attrs.begin(),
                                          attrs.end()));
}

API_EXPORT(LLVMAttributeListIteratorRef)
LLVMPY_InvokeInstAttributesIter(LLVMValueRef C)
{
    using namespace llvm;
    InvokeInst* inst = unwrap<InvokeInst>(C);
    AttributeList attrs = inst->getAttributes();
    return wrap(new AttributeListIterator(attrs.begin(),
                                          attrs.end()));
}

API_EXPORT(LLVMAttributeSetIteratorRef)
LLVMPY_GlobalAttributesIter(LLVMValueRef G)
{
    using namespace llvm;
    GlobalVariable* g = unwrap<GlobalVariable>(G);
    AttributeSet attrs = g->getAttributes();
    return wrap(new AttributeSetIterator(attrs.begin(),
                                         attrs.end()));
}

API_EXPORT(LLVMBlocksIteratorRef)
LLVMPY_FunctionBlocksIter(LLVMValueRef F)
{
    using namespace llvm;
    Function* func = unwrap<Function>(F);
    return wrap(new BlocksIterator(func->begin(),
                                   func->end()));
}

API_EXPORT(LLVMArgumentsIteratorRef)
LLVMPY_FunctionArgumentsIter(LLVMValueRef F)
{
    using namespace llvm;
    Function* func = unwrap<Function>(F);
    return wrap(new ArgumentsIterator(func->arg_begin(),
                                      func->arg_end()));
}

API_EXPORT(LLVMInstructionsIteratorRef)
LLVMPY_BlockInstructionsIter(LLVMValueRef B)
{
    using namespace llvm;
    BasicBlock* block = unwrap<BasicBlock>(B);
    return wrap(new InstructionsIterator(block->begin(),
                                         block->end()));
}

API_EXPORT(LLVMOperandsIteratorRef)
LLVMPY_InstructionOperandsIter(LLVMValueRef I)
{
    using namespace llvm;
    // works for instructions as well as for constants (e.g. aggregates)
    User* user = cast<User>(unwrap<Value>(I));
    return wrap(new OperandsIterator(user->op_begin(),
                                user->op_end()));
}

API_EXPORT(const char *)
LLVMPY_AttributeListIterNext(LLVMAttributeListIteratorRef GI)
{
    using namespace llvm;
    AttributeListIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return LLVMPY_CreateString((&*iter->cur++)->getAsString().c_str());
    } else {
      return NULL;
    }
}

API_EXPORT(const char *)
LLVMPY_AttributeSetIterNext(LLVMAttributeSetIteratorRef GI)
{
    using namespace llvm;
    AttributeSetIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return LLVMPY_CreateString((&*iter->cur++)->getAsString().c_str());
    } else {
      return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_BlocksIterNext(LLVMBlocksIteratorRef GI)
{
    using namespace llvm;
    BlocksIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
      return wrap(static_cast<const Value*>(&*iter->cur++));
    } else {
      return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_ArgumentsIterNext(LLVMArgumentsIteratorRef GI)
{
    using namespace llvm;
    ArgumentsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
      return wrap(&*iter->cur++);
    } else {
      return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_InstructionsIterNext(LLVMInstructionsIteratorRef GI)
{
    using namespace llvm;
    InstructionsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
      return wrap(&*iter->cur++);
    } else {
      return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_OperandsIterNext(LLVMOperandsIteratorRef GI)
{
    using namespace llvm;
    OperandsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
      return wrap((&*iter->cur++)->get());
    } else {
      return NULL;
    }
}

API_EXPORT(void)
LLVMPY_DisposeAttributeListIter(LLVMAttributeListIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeAttributeSetIter(LLVMAttributeSetIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeBlocksIter(LLVMBlocksIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeArgumentsIter(LLVMArgumentsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeInstructionsIter(LLVMInstructionsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeOperandsIter(LLVMOperandsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_PrintValueToString(LLVMValueRef Val,
                          const char** outstr)
{
    *outstr = LLVMPrintValueToString(Val);
}

API_EXPORT(const char *)
LLVMPY_GetValueName(LLVMValueRef Val)
{
    return LLVMGetValueName(Val);
}

API_EXPORT(const char *)
LLVMPY_GetDbgFile(LLVMValueRef Val)
{
    using namespace llvm;
    auto *val = unwrap<Value>(Val);
    if (auto *I = dyn_cast<Instruction>(val)) {
        if (auto &D = I->getDebugLoc()) {
            return LLVMPY_CreateString(D.get()->getFilename().str().c_str());
        }
    }

    return LLVMPY_CreateString("");
}

API_EXPORT(unsigned)
LLVMPY_GetDbgLine(LLVMValueRef Val)
{
    using namespace llvm;
    auto *val = unwrap<Value>(Val);
    if (auto *I = dyn_cast<Instruction>(val)) {
        if (auto &D = I->getDebugLoc()) {
            return D.getLine();
        }
    }

    return 0;
}


API_EXPORT(unsigned)
LLVMPY_GetDbgCol(LLVMValueRef Val)
{
    using namespace llvm;
    auto *val = unwrap<Value>(Val);
    if (auto *I = dyn_cast<Instruction>(val)) {
        if (auto &D = I->getDebugLoc()) {
            return D.getCol();
        }
    }

    return 0;
}


API_EXPORT(void)
LLVMPY_SetValueName(LLVMValueRef Val, const char *Name)
{
    LLVMSetValueName(Val, Name);
}

API_EXPORT(LLVMModuleRef)
LLVMPY_GetGlobalParent(LLVMValueRef Val)
{
    return LLVMGetGlobalParent(Val);
}

API_EXPORT(LLVMTypeRef)
LLVMPY_TypeOf(LLVMValueRef Val)
{
    return LLVMTypeOf(Val);
}

API_EXPORT(const char *)
LLVMPY_PrintType(LLVMTypeRef type)
{
    char *str = LLVMPrintTypeToString(type);
    const char *out = LLVMPY_CreateString(str);
    LLVMDisposeMessage(str);
    return out;
}

API_EXPORT(const char *)
LLVMPY_GetTypeName(LLVMTypeRef type)
{
    // try to convert to a struct type, works for other derived
    // types too
    llvm::Type* unwrapped = llvm::unwrap(type);
    llvm::StructType* ty = llvm::dyn_cast<llvm::StructType>(unwrapped);
    if (ty && !ty->isLiteral()) {
        return LLVMPY_CreateString(ty->getStructName().str().c_str());
    }
    return LLVMPY_CreateString("");
}

API_EXPORT(bool)
LLVMPY_TypeIsPointer(LLVMTypeRef type)
{
    return llvm::unwrap(type)->isPointerTy();
}

API_EXPORT(bool)
LLVMPY_TypeIsArray(LLVMTypeRef type)
{
    return llvm::unwrap(type)->isArrayTy();
}

API_EXPORT(bool)
LLVMPY_TypeIsStruct(LLVMTypeRef type)
{
    return llvm::unwrap(type)->isStructTy();
}

API_EXPORT(bool)
LLVMPY_TypeIsVector(LLVMTypeRef type)
{
    return llvm::unwrap(type)->isVectorTy();
}

API_EXPORT(LLVMTypeRef)
LLVMPY_GetElementType(LLVMTypeRef type)
{
    llvm::Type* unwrapped = llvm::unwrap(type);
    if (auto* ty = llvm::dyn_cast<llvm::PointerType>(unwrapped)) {
        // opaque pointers (the only pointers since LLVM 17) have no element
        // type, use LLVMPY_GetAllocatedType, LLVMPY_GetGEPSourceElementType
        // or LLVMPY_GlobalGetValueType instead
#if LLVM_VERSION_MAJOR < 15
        return llvm::wrap(ty->getElementType());
#elif LLVM_VERSION_MAJOR < 17
        if (!ty->isOpaque())
            return llvm::wrap(ty->getNonOpaquePointerElementType());
        return nullptr;
#else
        return nullptr;
#endif
    }

    if (auto* ty = llvm::dyn_cast<llvm::ArrayType>(unwrapped)) {
        return llvm::wrap(ty->getElementType());
    }

    if (auto* ty = llvm::dyn_cast<llvm::VectorType>(unwrapped)) {
        return llvm::wrap(ty->getElementType());
    }

    return nullptr;
}

API_EXPORT(unsigned)
LLVMPY_GetStructNumElements(LLVMTypeRef type)
{
    llvm::Type* unwrapped = llvm::unwrap(type);
    if (auto* ty = llvm::dyn_cast<llvm::StructType>(unwrapped)) {
        return ty->getNumElements();
    }
    return 0;
}

API_EXPORT(LLVMTypeRef)
LLVMPY_GetAllocatedType(LLVMValueRef Val)
{
    if (llvm::isa<llvm::AllocaInst>(llvm::unwrap(Val)))
        return LLVMGetAllocatedType(Val);
    return nullptr;
}

API_EXPORT(LLVMTypeRef)
LLVMPY_GetGEPSourceElementType(LLVMValueRef Val)
{
    // works for both GEP instructions and GEP constant expressions
    if (llvm::isa<llvm::GEPOperator>(llvm::unwrap(Val)))
        return LLVMGetGEPSourceElementType(Val);
    return nullptr;
}

API_EXPORT(LLVMTypeRef)
LLVMPY_GlobalGetValueType(LLVMValueRef Val)
{
    if (llvm::isa<llvm::GlobalValue>(llvm::unwrap(Val)))
        return LLVMGlobalGetValueType(Val);
    return nullptr;
}

API_EXPORT(LLVMTypeRef)
LLVMPY_GetStructElementType(LLVMTypeRef type, unsigned n)
{
    llvm::Type* unwrapped = llvm::unwrap(type);
    if (auto* ty = llvm::dyn_cast<llvm::StructType>(unwrapped)) {
        assert (n < ty->getNumElements() && "Invalid element number");
        return llvm::wrap(ty->getElementType(n));
    }
    return nullptr;
}


API_EXPORT(void)
LLVMPY_SetLinkage(LLVMValueRef Val, int Linkage)
{
    LLVMSetLinkage(Val, (LLVMLinkage)Linkage);
}

API_EXPORT(int)
LLVMPY_GetLinkage(LLVMValueRef Val)
{
    return (int)LLVMGetLinkage(Val);
}

API_EXPORT(void)
LLVMPY_SetVisibility(LLVMValueRef Val, int Visibility)
{
    LLVMSetVisibility(Val, (LLVMVisibility)Visibility);
}

API_EXPORT(int)
LLVMPY_GetVisibility(LLVMValueRef Val)
{
    return (int)LLVMGetVisibility(Val);
}

API_EXPORT(void)
LLVMPY_SetDLLStorageClass(LLVMValueRef Val, int DLLStorageClass)
{
    LLVMSetDLLStorageClass(Val, (LLVMDLLStorageClass)DLLStorageClass);
}

API_EXPORT(int)
LLVMPY_GetDLLStorageClass(LLVMValueRef Val)
{
    return (int)LLVMGetDLLStorageClass(Val);
}

API_EXPORT(unsigned)
LLVMPY_GetEnumAttributeKindForName(const char *name, size_t len)
{
    /* zero is returned if no match */
    return LLVMGetEnumAttributeKindForName(name, len);
}

API_EXPORT(void)
LLVMPY_AddFunctionAttr(LLVMValueRef Fn, unsigned AttrKind)
{
    LLVMContextRef ctx = LLVMGetModuleContext(LLVMGetGlobalParent(Fn));
    LLVMAttributeRef attr_ref = LLVMCreateEnumAttribute(ctx, AttrKind, 0);
    LLVMAddAttributeAtIndex(Fn, LLVMAttributeReturnIndex, attr_ref);
}

API_EXPORT(int)
LLVMPY_IsDeclaration(LLVMValueRef GV)
{
    return LLVMIsDeclaration(GV);
}

API_EXPORT(int)
LLVMPY_IsConstant(LLVMValueRef V)
{
    using namespace llvm;
    return isa<Constant>(unwrap<Value>(V));
}


/* Alignment (in bytes) of a load, store, alloca or global object.
 * Returns 0 for a global object without explicit alignment and -1 for values
 * that have no alignment. */
API_EXPORT(int)
LLVMPY_GetAlignment(LLVMValueRef V)
{
    using namespace llvm;
    Value *Val = unwrap<Value>(V);
    if (auto *LI = dyn_cast<LoadInst>(Val))
        return LI->getAlign().value();
    if (auto *SI = dyn_cast<StoreInst>(Val))
        return SI->getAlign().value();
    if (auto *AI = dyn_cast<AllocaInst>(Val))
        return AI->getAlign().value();
    if (auto *GV = dyn_cast<GlobalVariable>(Val))
        return GV->getAlign() ? GV->getAlign()->value() : 0;
    if (auto *F = dyn_cast<Function>(Val))
        return F->getAlign() ? F->getAlign()->value() : 0;
    return -1;
}

/* The predicate of an icmp/fcmp instruction (llvm::CmpInst::Predicate), -1
 * if the value is not a compare instruction. */
API_EXPORT(int)
LLVMPY_GetCmpPredicate(LLVMValueRef V)
{
    using namespace llvm;
    if (auto *CI = dyn_cast<CmpInst>(unwrap<Value>(V)))
        return static_cast<int>(CI->getPredicate());
    return -1;
}

/* The wrap flags of add, sub, mul, shl, neg: bit 0 is nsw, bit 1 is nuw.
 * -1 if the value is not such an operation. */
API_EXPORT(int)
LLVMPY_GetWrapFlags(LLVMValueRef V)
{
    using namespace llvm;
    if (auto *OBO = dyn_cast<OverflowingBinaryOperator>(unwrap<Value>(V)))
        return (OBO->hasNoSignedWrap() ? 1 : 0) |
               (OBO->hasNoUnsignedWrap() ? 2 : 0);
    return -1;
}

/* The kind of a value (LLVMValueKind), translated to a numbering that does not
 * depend on the version of LLVM (see _VALUE_KINDS in value.py).
 * -1 for a kind that we do not know. */
API_EXPORT(int)
LLVMPY_GetValueKind(LLVMValueRef V)
{
    switch (LLVMGetValueKind(V)) {
    case LLVMArgumentValueKind: return 0;
    case LLVMBasicBlockValueKind: return 1;
    case LLVMFunctionValueKind: return 2;
    case LLVMGlobalAliasValueKind: return 3;
    case LLVMGlobalIFuncValueKind: return 4;
    case LLVMGlobalVariableValueKind: return 5;
    case LLVMBlockAddressValueKind: return 6;
    case LLVMConstantExprValueKind: return 7;
    case LLVMConstantArrayValueKind: return 8;
    case LLVMConstantStructValueKind: return 9;
    case LLVMConstantVectorValueKind: return 10;
    case LLVMUndefValueValueKind: return 11;
    case LLVMConstantAggregateZeroValueKind: return 12;
    case LLVMConstantDataArrayValueKind: return 13;
    case LLVMConstantDataVectorValueKind: return 14;
    case LLVMConstantIntValueKind: return 15;
    case LLVMConstantFPValueKind: return 16;
    case LLVMConstantPointerNullValueKind: return 17;
    case LLVMConstantTokenNoneValueKind: return 18;
    case LLVMMetadataAsValueValueKind: return 19;
    case LLVMInlineAsmValueKind: return 20;
    case LLVMInstructionValueKind: return 21;
    case LLVMPoisonValueValueKind: return 22;
    case LLVMConstantTargetNoneValueKind: return 23;
    default: return -1;
    }
}

API_EXPORT(int)
LLVMPY_IsConstantExpr(LLVMValueRef V)
{
    using namespace llvm;
    return isa<ConstantExpr>(unwrap<Value>(V));
}

API_EXPORT(int)
LLVMPY_IsGlobalVariableConstant(LLVMValueRef V)
{
    using namespace llvm;
    auto *GV = dyn_cast<GlobalVariable>(unwrap<Value>(V));
    return GV && GV->isConstant();
}



API_EXPORT(LLVMValueRef)
LLVMPY_GlobalGetInitializer(LLVMValueRef G)
{
    return LLVMGetInitializer(G);
}

API_EXPORT(LLVMValueRef)
LLVMPY_ConstantExprAsInst(LLVMValueRef CE)
{
    using namespace llvm;
    return wrap(cast<ConstantExpr>(unwrap<Value>(CE))->getAsInstruction());
}


API_EXPORT(unsigned)
LLVMPY_PhiCountIncoming(LLVMValueRef P)
{
    return LLVMCountIncoming(P);
}

API_EXPORT(LLVMValueRef)
LLVMPY_PhiGetIncomingValue(LLVMValueRef P, unsigned Idx)
{
    return LLVMGetIncomingValue(P, Idx);
}

API_EXPORT(LLVMBasicBlockRef)
LLVMPY_PhiGetIncomingBlock(LLVMValueRef P, unsigned Idx)
{
    return LLVMGetIncomingBlock(P, Idx);
}

API_EXPORT(void)
LLVMPY_WriteCFG(LLVMValueRef Fval, const char **OutStr, int ShowInst) {
    using namespace llvm;
    Function *F  = unwrap<Function>(Fval);
    std::string buffer;
    raw_string_ostream stream(buffer);
    // Note: The (const Function*)F is necessary to trigger the right behavior.
    //       A non constant Function* will result in the instruction not
    //       printed regardless of the value in the 3rd argument.
    WriteGraph(stream, (const Function*)F, !ShowInst);
    *OutStr = LLVMPY_CreateString(stream.str().c_str());
}

API_EXPORT(const char *)
LLVMPY_GetOpcodeName(LLVMValueRef Val)
{
    // try to convert to an instruction value, works for other derived
    // types too
    llvm::Value* unwrapped = llvm::unwrap(Val);
    llvm::Instruction* inst = llvm::dyn_cast<llvm::Instruction>(unwrapped);
    if (inst) {
        return LLVMPY_CreateString(inst->getOpcodeName());
    }
    return LLVMPY_CreateString("");
}


} // end extern "C"
