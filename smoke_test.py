import importlib
import os

modules = ["torch", "diffusers", "transformers", "accelerate", "safetensors", "huggingface_hub"]

print("Environment: ")
print("CWD:", os.getcwd())
print('HF_HUB_DISABLE_SYMLINKS_WARNING=', os.getenv('HF_HUB_DISABLE_SYMLINKS_WARNING'))
print()

for m in modules:
    try:
        mod = importlib.import_module(m)
        ver = getattr(mod, "__version__", "unknown")
        print(f"{m}: installed, version={ver}")
    except Exception as e:
        print(f"{m}: NOT installed ({e.__class__.__name__}: {e})")

# Check torch CUDA availability if torch is present
try:
    import torch
    print("\ntorch.cuda.is_available() ->", torch.cuda.is_available())
    try:
        print("torch.version.cuda ->", torch.version.cuda)
    except Exception:
        pass
except Exception:
    pass

print('\nSmoke test finished.')
