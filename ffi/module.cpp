#include <string>
#include <clocale>
#include "llvm-c/Core.h"
#include "llvm-c/Analysis.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/TypeFinder.h"
#include "llvm/IR/IntrinsicInst.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "core.h"


/* An iterator around a module's globals, including the stop condition */
struct GlobalsIterator {
    typedef llvm::Module::global_iterator iterator;
    iterator cur;
    iterator end;

    GlobalsIterator(iterator cur, iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueGlobalsIterator;
typedef OpaqueGlobalsIterator* LLVMGlobalsIteratorRef;


/* An iterator around a module's functions, including the stop condition */
struct FunctionsIterator {
    typedef llvm::Module::const_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    FunctionsIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueFunctionsIterator;
typedef OpaqueFunctionsIterator* LLVMFunctionsIteratorRef;

/* module types iterator */
class TypesIterator {
private:
    llvm::TypeFinder finder;
    using const_iterator = llvm::TypeFinder::const_iterator;
    const_iterator cur;
public:
    TypesIterator(llvm::Module& m, bool namedOnly) : finder(llvm::TypeFinder()) {
        finder.run(m, namedOnly);
        cur = finder.begin();
     }
    const llvm::Type* next() {
        if (cur != finder.end()) {
            return *cur++;
        }
        return nullptr;
    }
};

typedef TypesIterator* LLVMTypesIteratorRef;

//
// Local helper functions
//

namespace llvm {

static LLVMGlobalsIteratorRef
wrap(GlobalsIterator* GI){
    return reinterpret_cast<LLVMGlobalsIteratorRef>(GI);
}

static GlobalsIterator*
unwrap(LLVMGlobalsIteratorRef GI){
    return reinterpret_cast<GlobalsIterator*>(GI);
}

static LLVMFunctionsIteratorRef
wrap(FunctionsIterator* GI){
    return reinterpret_cast<LLVMFunctionsIteratorRef>(GI);
}

static FunctionsIterator*
unwrap(LLVMFunctionsIteratorRef GI){
    return reinterpret_cast<FunctionsIterator *>(GI);
}

static LLVMTypesIteratorRef
wrap(TypesIterator* TyI) {
    return reinterpret_cast<LLVMTypesIteratorRef>(TyI);
}

static TypesIterator*
unwrap(LLVMTypesIteratorRef TyI) {
    return reinterpret_cast<TypesIterator*>(TyI);
}

}  // end namespace llvm


//
// Exported API
//

extern "C" {

API_EXPORT(void)
LLVMPY_DisposeModule(LLVMModuleRef m) {
    return LLVMDisposeModule(m);
}

API_EXPORT(void)
LLVMPY_PrintModuleToString(LLVMModuleRef M,
                           const char **outstr)
{
    // Change the locale to en_US before calling LLVM to print the module
    // due to a LLVM bug https://llvm.org/bugs/show_bug.cgi?id=12906
    char *old_locale = strdup(setlocale(LC_ALL, NULL));
    setlocale(LC_ALL, "C");

    *outstr = LLVMPrintModuleToString(M);

    // Revert locale
    setlocale(LC_ALL, old_locale);
    free(old_locale);
}

API_EXPORT(const char *)
LLVMPY_GetModuleName(LLVMModuleRef M)
{
    return llvm::unwrap(M)->getModuleIdentifier().c_str();
}

API_EXPORT(void)
LLVMPY_SetModuleName(LLVMModuleRef M, const char *Name)
{
    llvm::unwrap(M)->setModuleIdentifier(Name);
}

API_EXPORT(LLVMValueRef)
LLVMPY_ParseDbgDeclareAddr(LLVMValueRef I)
{
    using namespace llvm;
    if (auto *DD = dyn_cast<DbgDeclareInst>(llvm::unwrap<Value>(I))) {
        return wrap(DD->getAddress());
    }
    if (auto *DD = dyn_cast<DbgValueInst>(llvm::unwrap<Value>(I))) {
        return wrap(DD->getValue());
    }
    return nullptr;
}


API_EXPORT(const char *)
LLVMPY_ParseDbgDeclareVar(LLVMValueRef I)
{
    using namespace llvm;
    if (auto *DD = dyn_cast<DbgDeclareInst>(llvm::unwrap<Value>(I))) {
        return DD->getVariable()->getName().str().c_str();
    }
    if (auto *DD = dyn_cast<DbgValueInst>(llvm::unwrap<Value>(I))) {
        return DD->getVariable()->getName().str().c_str();
    }
    return "";
}

API_EXPORT(const char *)
LLVMPY_ParseDbgDeclareType(LLVMValueRef I)
{
    using namespace llvm;
    if (auto *DD = dyn_cast<DbgDeclareInst>(llvm::unwrap<Value>(I))) {
        return DD->getVariable()->getType()->getName().str().c_str();
    }
    if (auto *DD = dyn_cast<DbgValueInst>(llvm::unwrap<Value>(I))) {
        return DD->getVariable()->getType()->getName().str().c_str();
    }
    return "";
}

/*
 * Debug records are not instructions: they are attached to the
 * instruction that follows them. These functions give access to the
 * llvm.dbg.declare/llvm.dbg.value records attached to an instruction.
 */
static const llvm::DbgVariableRecord *
getDbgVariableRecord(LLVMValueRef I, size_t idx)
{
    using namespace llvm;
    auto *Inst = dyn_cast<Instruction>(unwrap<Value>(I));
    if (!Inst)
        return nullptr;
    size_t n = 0;
    for (DbgRecord &R : Inst->getDbgRecordRange()) {
        auto *DVR = dyn_cast<DbgVariableRecord>(&R);
        if (!DVR || !(DVR->isDbgDeclare() || DVR->isDbgValue()))
            continue;
        if (n++ == idx)
            return DVR;
    }
    return nullptr;
}

API_EXPORT(size_t)
LLVMPY_InstDbgRecordCount(LLVMValueRef I)
{
    using namespace llvm;
    auto *Inst = dyn_cast<Instruction>(unwrap<Value>(I));
    size_t n = 0;
    if (Inst)
        for (DbgRecord &R : Inst->getDbgRecordRange())
            if (auto *DVR = dyn_cast<DbgVariableRecord>(&R))
                if (DVR->isDbgDeclare() || DVR->isDbgValue())
                    ++n;
    return n;
}

/* the value (the address for declare) that the record describes, null if unknown */
API_EXPORT(LLVMValueRef)
LLVMPY_InstDbgRecordAddr(LLVMValueRef I, size_t idx)
{
    if (auto *DVR = getDbgVariableRecord(I, idx))
        if (DVR->getNumVariableLocationOps() == 1)
            return llvm::wrap(DVR->getVariableLocationOp(0));
    return nullptr;
}

API_EXPORT(const char *)
LLVMPY_InstDbgRecordVar(LLVMValueRef I, size_t idx)
{
    static thread_local std::string buf;
    buf.clear();
    if (auto *DVR = getDbgVariableRecord(I, idx))
        if (auto *Var = DVR->getVariable())
            buf = Var->getName().str();
    return buf.c_str();
}

API_EXPORT(const char *)
LLVMPY_InstDbgRecordType(LLVMValueRef I, size_t idx)
{
    static thread_local std::string buf;
    buf.clear();
    if (auto *DVR = getDbgVariableRecord(I, idx))
        if (auto *Var = DVR->getVariable())
            if (auto *Ty = Var->getType())
                buf = Ty->getName().str();
    return buf.c_str();
}

API_EXPORT(LLVMValueRef)
LLVMPY_GetNamedFunction(LLVMModuleRef M,
                        const char *Name)
{
    return LLVMGetNamedFunction(M, Name);
}

API_EXPORT(LLVMValueRef)
LLVMPY_GetNamedGlobalVariable(LLVMModuleRef M,
                              const char *Name)
{
    using namespace llvm;
    return wrap(unwrap(M)->getGlobalVariable(Name));
}

API_EXPORT(size_t)
LLVMPY_TypeSize(LLVMModuleRef mod, LLVMTypeRef type)
{
    llvm::Module *m = llvm::unwrap(mod);
    return m->getDataLayout().getTypeSizeInBits(llvm::unwrap(type));
}

API_EXPORT(size_t)
LLVMPY_TypeStoreSize(LLVMModuleRef mod, LLVMTypeRef type)
{
    llvm::Module *m = llvm::unwrap(mod);
    return m->getDataLayout().getTypeStoreSizeInBits(llvm::unwrap(type));
}


API_EXPORT(LLVMTypeRef)
LLVMPY_GetNamedStructType(LLVMModuleRef M,
                        const char *Name)
{
    return LLVMGetTypeByName(M, Name);
}

API_EXPORT(int)
LLVMPY_VerifyModule(LLVMModuleRef M, char **OutMsg)
{
    return LLVMVerifyModule(M, LLVMReturnStatusAction, OutMsg);
}

API_EXPORT(void)
LLVMPY_GetDataLayout(LLVMModuleRef M,
                     const char **DL)
{
    *DL = LLVMGetDataLayoutStr(M);
}


API_EXPORT(void)
LLVMPY_SetDataLayout(LLVMModuleRef M,
                     const char *DL)
{
    LLVMSetDataLayout(M, DL);
}


API_EXPORT(void)
LLVMPY_GetTarget(LLVMModuleRef M,
                 const char **Triple)
{
    *Triple = LLVMGetTarget(M);
}


API_EXPORT(void)
LLVMPY_SetTarget(LLVMModuleRef M,
                 const char *Triple)
{
    LLVMSetTarget(M, Triple);
}

// Iteration APIs

API_EXPORT(LLVMGlobalsIteratorRef)
LLVMPY_ModuleGlobalsIter(LLVMModuleRef M)
{
    using namespace llvm;
    Module* mod = unwrap(M);
    return wrap(new GlobalsIterator(mod->global_begin(),
                                    mod->global_end()));
}

API_EXPORT(LLVMFunctionsIteratorRef)
LLVMPY_ModuleFunctionsIter(LLVMModuleRef M)
{
    using namespace llvm;
    Module* mod = unwrap(M);
    return wrap(new FunctionsIterator(mod->begin(),
                                      mod->end()));
}

API_EXPORT(LLVMTypesIteratorRef)
LLVMPY_ModuleTypesIter(LLVMModuleRef M)
{
    llvm::Module* mod = llvm::unwrap(M);
    auto* iter = new TypesIterator(*mod, false);
    return llvm::wrap(iter);
}


/*
  These functions return NULL if we are at the end
*/
API_EXPORT(LLVMValueRef)
LLVMPY_GlobalsIterNext(LLVMGlobalsIteratorRef GI)
{
    using namespace llvm;
    GlobalsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return wrap(&*iter->cur++);
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_FunctionsIterNext(LLVMFunctionsIteratorRef GI)
{
    using namespace llvm;
    FunctionsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return wrap(&*iter->cur++);
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMTypeRef)
LLVMPY_TypesIterNext(LLVMTypesIteratorRef TyI)
{
    return llvm::wrap(llvm::unwrap(TyI)->next());
}

API_EXPORT(void)
LLVMPY_DisposeGlobalsIter(LLVMGlobalsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeFunctionsIter(LLVMFunctionsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeTypesIter(LLVMTypesIteratorRef TyI)
{
    delete llvm::unwrap(TyI);
}



API_EXPORT(LLVMModuleRef)
LLVMPY_CloneModule(LLVMModuleRef M)
{
    return LLVMCloneModule(M);
}

} // end extern "C"
