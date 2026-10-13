#include "core.h"
#include "llvm-c/Target.h"

#if LLVM_VERSION_MAJOR >= 17

// PassManagerBuilder (and the legacy optimization pipeline) was removed
// in LLVM 17. Keep the API so that the Python bindings load: the builder
// only stores the settings and populating a pass manager adds no passes.

struct LLVMOpaquePassManagerBuilder {
    unsigned OptLevel = 2;
    unsigned SizeLevel = 0;
    bool DisableUnrollLoops = false;
    bool LoopVectorize = false;
    bool SLPVectorize = false;
};

typedef struct LLVMOpaquePassManagerBuilder *LLVMPassManagerBuilderRef;

extern "C" {

API_EXPORT(LLVMPassManagerBuilderRef)
LLVMPY_PassManagerBuilderCreate()
{
    return new LLVMOpaquePassManagerBuilder();
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderDispose(LLVMPassManagerBuilderRef PMB)
{
    delete PMB;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderPopulateModulePassManager(
                            LLVMPassManagerBuilderRef PMB,
                            LLVMPassManagerRef PM)
{
}

API_EXPORT(unsigned)
LLVMPY_PassManagerBuilderGetOptLevel(LLVMPassManagerBuilderRef PMB)
{
    return PMB->OptLevel;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetOptLevel(LLVMPassManagerBuilderRef PMB,
                                  unsigned OptLevel)
{
    PMB->OptLevel = OptLevel;
}

API_EXPORT(unsigned)
LLVMPY_PassManagerBuilderGetSizeLevel(LLVMPassManagerBuilderRef PMB)
{
    return PMB->SizeLevel;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetSizeLevel(LLVMPassManagerBuilderRef PMB,
                                   unsigned SizeLevel)
{
    PMB->SizeLevel = SizeLevel;
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB)
{
    return PMB->DisableUnrollLoops;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB,
                                            LLVMBool Value)
{
    PMB->DisableUnrollLoops = Value;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderUseInlinerWithThreshold(LLVMPassManagerBuilderRef PMB,
                                                 unsigned Threshold)
{
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderPopulateFunctionPassManager(
                                        LLVMPassManagerBuilderRef PMB,
                                        LLVMPassManagerRef PM)
{
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetLoopVectorize(LLVMPassManagerBuilderRef PMB,
                                          int Value)
{
    PMB->LoopVectorize = Value;
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetLoopVectorize(LLVMPassManagerBuilderRef PMB)
{
    return PMB->LoopVectorize;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetSLPVectorize(LLVMPassManagerBuilderRef PMB,
                                          int Value)
{
    PMB->SLPVectorize = Value;
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetSLPVectorize(LLVMPassManagerBuilderRef PMB)
{
    return PMB->SLPVectorize;
}

} // end extern "C"

#else // LLVM_VERSION_MAJOR < 17

#include "llvm-c/Transforms/PassManagerBuilder.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"

extern "C" {

#if LLVM_VERSION_MAJOR < 11
namespace llvm {
    inline PassManagerBuilder *unwrap(LLVMPassManagerBuilderRef P) {
        return reinterpret_cast<PassManagerBuilder*>(P);
    }

    inline LLVMPassManagerBuilderRef wrap(PassManagerBuilder *P) {
        return reinterpret_cast<LLVMPassManagerBuilderRef>(P);
    }
}
#endif // LLVM < 11


API_EXPORT(LLVMPassManagerBuilderRef)
LLVMPY_PassManagerBuilderCreate()
{
    return LLVMPassManagerBuilderCreate();
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderDispose(LLVMPassManagerBuilderRef PMB)
{
    LLVMPassManagerBuilderDispose(PMB);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderPopulateModulePassManager(
                            LLVMPassManagerBuilderRef PMB,
                            LLVMPassManagerRef PM)
{
    LLVMPassManagerBuilderPopulateModulePassManager(PMB, PM);
}

API_EXPORT(unsigned)
LLVMPY_PassManagerBuilderGetOptLevel(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->OptLevel;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetOptLevel(LLVMPassManagerBuilderRef PMB,
                                  unsigned OptLevel)
{
    LLVMPassManagerBuilderSetOptLevel(PMB, OptLevel);
}

API_EXPORT(unsigned)
LLVMPY_PassManagerBuilderGetSizeLevel(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->SizeLevel;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetSizeLevel(LLVMPassManagerBuilderRef PMB,
                                   unsigned SizeLevel)
{
    LLVMPassManagerBuilderSetSizeLevel(PMB, SizeLevel);
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->DisableUnrollLoops;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB,
                                            LLVMBool Value)
{
    LLVMPassManagerBuilderSetDisableUnrollLoops(PMB, Value);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderUseInlinerWithThreshold(LLVMPassManagerBuilderRef PMB,
                                                 unsigned Threshold)
{
    LLVMPassManagerBuilderUseInlinerWithThreshold(PMB, Threshold);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderPopulateFunctionPassManager(
                                        LLVMPassManagerBuilderRef PMB,
                                        LLVMPassManagerRef PM)
{
    LLVMPassManagerBuilderPopulateFunctionPassManager(PMB, PM);
}


API_EXPORT(void)
LLVMPY_PassManagerBuilderSetLoopVectorize(LLVMPassManagerBuilderRef PMB,
                                          int Value)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    pmb->LoopVectorize = Value;
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetLoopVectorize(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->LoopVectorize;
}


API_EXPORT(void)
LLVMPY_PassManagerBuilderSetSLPVectorize(LLVMPassManagerBuilderRef PMB,
                                          int Value)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    pmb->SLPVectorize = Value;
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetSLPVectorize(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->SLPVectorize;
}


} // end extern "C"

#endif // LLVM_VERSION_MAJOR >= 17
