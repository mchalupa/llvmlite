#include "llvm-c/Core.h"
#include "llvm-c/Target.h"

#include "core.h"
#include "llvm/Config/llvm-config.h"

#if LLVM_VERSION_MAJOR >= 17
// llvm-c/Initialization.h was removed in LLVM 17, use the C++ API instead
#include "llvm/InitializePasses.h"
#include "llvm/PassRegistry.h"
#else
#include "llvm-c/Initialization.h"
#endif

extern "C" {

#if LLVM_VERSION_MAJOR >= 17

#define INIT(F) \
    API_EXPORT(void) LLVMPY_Initialize ## F() { \
            llvm::initialize ## F (*llvm::PassRegistry::getPassRegistry()); }

// ObjCARCOpts and IPA have no initializers anymore, keep them as no-ops
#define INIT_NOOP(F) \
    API_EXPORT(void) LLVMPY_Initialize ## F() { }

INIT(Core)
INIT(TransformUtils)
INIT(ScalarOpts)
INIT_NOOP(ObjCARCOpts)
INIT(Vectorization)
INIT(InstCombine)
INIT(IPO)
INIT(Analysis)
INIT_NOOP(IPA)
INIT(CodeGen)
INIT(Target)

#undef INIT_NOOP
#undef INIT

#else

#define INIT(F) \
    API_EXPORT(void) LLVMPY_Initialize ## F() { \
            LLVMInitialize ## F (LLVMGetGlobalPassRegistry()); }

INIT(Core)
INIT(TransformUtils)
INIT(ScalarOpts)
INIT(ObjCARCOpts)
INIT(Vectorization)
INIT(InstCombine)
INIT(IPO)
// INIT(Instrumentation)
INIT(Analysis)
INIT(IPA)
INIT(CodeGen)
INIT(Target)

#undef INIT

#endif // LLVM_VERSION_MAJOR >= 17

API_EXPORT(void)
LLVMPY_Shutdown(){
    LLVMShutdown();
}

// Target Initialization
#define INIT(F) API_EXPORT(void) LLVMPY_Initialize ## F() { LLVMInitialize ## F (); }

// NOTE: it is important that we don't export functions which we don't use,
// especially those which may pull in large amounts of additional code or data.

INIT(AllTargetInfos)
INIT(AllTargets)
INIT(AllTargetMCs)
INIT(AllAsmPrinters)
INIT(NativeTarget)
INIT(NativeAsmParser)
INIT(NativeAsmPrinter)
// INIT(NativeDisassembler)

#undef INIT

API_EXPORT(unsigned int)
LLVMPY_GetVersionInfo()
{
    unsigned int verinfo = 0;
    verinfo += LLVM_VERSION_MAJOR << 16;
    verinfo += LLVM_VERSION_MINOR << 8;
#ifdef LLVM_VERSION_PATCH
    /* Not available under Windows... */
    verinfo += LLVM_VERSION_PATCH << 0;
#endif
    return verinfo;
}

} // end extern "C"
