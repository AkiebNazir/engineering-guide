# Day 92: Quantized Model Formats & Inference Engines (GPTQ, AWQ, GGUF, FP8, vLLM vs SGLang vs TensorRT-LLM)

Welcome to Day 92. Yesterday you took apart the LLaMA/Mistral/Gemma architecture. Open any of those models on the Hugging Face Hub and you will not find one file. You will find `-AWQ`, `-GPTQ-Int4`, `-FP8`, `-GGUF` and `Q4_K_M` variants, and a README that says "serve with vLLM or SGLang". Every open model you will ever deploy arrives in one of these formats and runs on one of these engines.

Day 78 taught the core idea of quantization (a scale factor maps floats to small integers). Today is the production version: **which quantization algorithm produced the file, what number format the GPU actually multiplies in, which engine runs it, and how you prove you did not break the model.** These are the concrete names interviewers expect you to know.

> **Where this fits:** Day 78 is the theory of quantization, Day 94 uses FP8/BF16 for *training*, Day 98 (QLoRA) fine-tunes on top of a 4-bit base, Day 111 derives speculative decoding, and Days 151–152 build the production serving stack. Today connects them: the artifact you download and the engine you run it on.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Two Bottlenecks, Two Kinds of Quantization
An LLM request has two phases (you will meet them again on Day 151):
- **Prefill** processes the whole prompt in one big matrix multiply. It is **compute-bound**: the tensor cores are the limit.
- **Decode** produces one token at a time and has to stream every weight from GPU memory for each step. At small batch sizes it is **memory-bandwidth-bound**: the GPU spends most of its time waiting for bytes.

That gives two families of quantization, and mixing them up is the most common interview mistake:

| Scheme | What is low-precision | Speeds up | Typical use |
|---|---|---|---|
| **Weight-only (W4A16, W8A16)** | Weights stored in INT4/INT8, unpacked to FP16/BF16 inside the kernel | Decode at small/medium batch (fewer bytes to read) | GPTQ, AWQ, GGUF: fitting a big model on fewer or cheaper GPUs |
| **Weight + activation (W8A8 INT8, FP8)** | Both operands of the matmul are 8-bit, so the tensor cores run at 8-bit speed | Prefill *and* high-batch decode (more FLOPs per second) | FP8 on H100/H200/Blackwell/MI300, SmoothQuant INT8 on A100 |

Analogy: weight-only quantization is shipping furniture flat-packed (less truck space, but someone has to assemble it at the door). W8A8/FP8 is building smaller furniture in the first place: you save truck space *and* assembly time, but only if the factory (the tensor cores) can build in that size.

One consequence: a W4A16 model is not faster everywhere. At large batch sizes the workload becomes compute-bound, the unpack step is pure overhead, and a W4A16 model can be *slower* than FP8. Pick the format for your traffic, not for the file size alone.

### 2. Granularity: Who Shares a Scale Factor?
Day 78's lab showed one outlier ruining a per-tensor scale. The fix is to give smaller groups of numbers their own scale:
- **Per-tensor:** one scale for the whole matrix. Cheap, fragile.
- **Per-channel (per output row):** one scale per row. Standard for INT8/FP8 weights.
- **Per-group:** one scale per block of, typically, **128** consecutive weights in a row. Standard for INT4 (GPTQ/AWQ). Costs about 16 bits per 128 weights for the scale (plus a zero point in asymmetric schemes), so "4-bit" is really ~4.1–4.25 bits per weight.
- **Per-token / dynamic (activations):** activations change every request, so their scales are computed on the fly per token.
- **Microscaling (MX) block formats:** hardware-native small blocks. **MXFP4/MXFP8** (OCP standard) share one 8-bit power-of-two scale per 32 values; NVIDIA's **NVFP4** uses 16-value blocks with an FP8 scale. Blackwell tensor cores run these directly. OpenAI's open-weight gpt-oss models (2025) shipped their MoE weights in MXFP4.

### 3. GPTQ: Round, Then Let the Other Weights Absorb the Error
**GPTQ** (Frantar et al., 2022) is a one-shot, post-training method. It needs no retraining, only a few hundred calibration sequences, and quantizes one layer at a time.
1. Run calibration text through the model and record each linear layer's inputs $X$.
2. The goal is not "keep each weight close". It is "keep the layer's **output** close": minimize $\|XW^\top - X\hat W^\top\|^2$.
3. That objective has a Hessian $H = 2X^\top X$ over the input dimensions. Its off-diagonal entries say which input channels move together.
4. Quantize the weight columns one at a time. After rounding column $i$, compute its error and **subtract a correction from every not-yet-quantized column**, weighted by the inverse Hessian (a Cholesky factor of $H^{-1}$, computed once). Because correlated channels can stand in for each other, the next columns cancel most of the damage.

The idea goes back to Optimal Brain Surgeon (1993). GPTQ made it fast enough for 175B models (a few GPU-hours) by processing columns in fixed order and in batches. The `act_order` / `desc_act` option quantizes the columns with the largest Hessian diagonal first, which helps accuracy at a small kernel-speed cost.

### 4. AWQ: Protect the Channels That Matter by Scaling, Not by Keeping Them in FP16
A common misconception (the Day 78 simplification): *"AWQ keeps the 1% outlier weights in FP16."* That describes **LLM.int8()** (Dettmers et al., 2022, the `bitsandbytes` 8-bit mode), which splits outlier *feature dimensions* out into an FP16 matmul. Mixed-precision layouts are slow on GPUs, so AWQ does something smarter.

**AWQ** (Activation-aware Weight Quantization, Lin et al., 2023):
1. Observation: weights are not equally important. The input channels that see **large activations** matter most (roughly the top 0.1–1%), because their rounding error gets multiplied by a big number.
2. Instead of keeping them in FP16, AWQ multiplies those weight columns by a scale $s > 1$ *before* quantization, and divides the corresponding activations by $s$ (folded into the previous LayerNorm or linear layer, so it costs nothing at runtime). The product $XW^\top$ is unchanged, but the important weights now use more of the INT4 grid, so their *relative* rounding error shrinks.
3. The scale is $s = s_X^{\alpha}$ where $s_X$ is the average activation magnitude per channel, and $\alpha \in [0,1]$ is grid-searched per layer to minimize output error on calibration data.

Every weight ends up INT4, the layout is uniform, and fast kernels apply. AWQ needs no backprop and no Hessian, uses little calibration data, and tends to overfit the calibration set less than GPTQ. In practice both reach similar quality at 4 bits on large models; kernel support and tooling usually decide.

### 5. SmoothQuant and FP8: Quantizing the Activations Too
Weights are easy to quantize; activations are hard because of those outlier channels. **SmoothQuant** (Xiao et al., 2022) uses the same trick as AWQ in the other direction: divide the outlier activation channels by $s$ and multiply the weights by $s$, "migrating" the difficulty into the weights so that both can be INT8 (W8A8).

**FP8** is the modern default for weight+activation quantization. It is a floating-point format, so it has an exponent and handles a wide range without much calibration:
- **E4M3** (4 exponent bits, 3 mantissa bits, max ±448): more precision. Used for weights and activations in inference.
- **E5M2** (max ±57,344): more range. Used mainly for gradients in FP8 training (Day 94).

FP8 tensor cores exist on NVIDIA Hopper (H100/H200), Ada (L4, L40S) and Blackwell, and on AMD MI300. They run roughly twice as many FLOPs per second as BF16. **A100 has no FP8 tensor cores**, so on A100 engines fall back to weight-only FP8 kernels (memory savings, no compute speed-up). With per-channel weight scales and dynamic per-token activation scales, FP8 W8A8 is close to lossless on most benchmarks, which is why many labs now publish an official `-FP8` checkpoint. DeepSeek-V3 went further and *trained* in FP8 with fine-grained block scaling.

### 6. GGUF and llama.cpp: The Local and CPU World
**GGUF** is the single-file format of `llama.cpp` (it replaced the older GGML format in 2023). One file holds the tensors, the tokenizer, the chat template and all metadata, and it is memory-mapped, so loading is near-instant. Ollama, LM Studio and many desktop apps run on it. It targets CPUs (AVX2/AVX-512/NEON), Apple Silicon (Metal), CUDA, ROCm and Vulkan, and can split layers between GPU and CPU RAM (`-ngl`, the number of GPU layers) when a model does not fit in VRAM.

Its quantization types are named `Q<bits>_<variant>`:
- `Q8_0`, `Q4_0`: the simple legacy block formats (32 weights share one scale).
- **K-quants** (`Q4_K_M`, `Q5_K_M`, `Q6_K`, ...): 256-weight super-blocks whose sub-block scales are themselves quantized. The `_S/_M/_L` suffix is a *mix*: `Q4_K_M` keeps some sensitive tensors (parts of attention and FFN down-projections) at higher precision, so its average is nearer 4.8 bits per weight (approximate). `Q4_K_M` and `Q5_K_M` are the usual sweet spots.
- **I-quants** (`IQ2_XS`, `IQ3_M`, ...): lattice-codebook formats for 2–3 bits. They need an **importance matrix** (`imatrix`), activation statistics from calibration text, which plays the same role as AWQ's activation awareness. An imatrix also improves the K-quants.

GGUF is the right answer for laptops, Macs, edge boxes and CPU servers. For multi-user GPU serving you normally use GPTQ/AWQ/FP8 in vLLM, SGLang or TensorRT-LLM, whose batching and kernels are built for concurrency.

### 7. The KV Cache Is Also Memory
Quantizing weights does nothing for the KV cache, and at high concurrency or long context the cache is the bigger number. For a LLaMA-3-70B-shaped model (80 layers, 8 KV heads via GQA, head dim 128) the cache costs $2 \times 80 \times 8 \times 128 \times 2 \text{ bytes} \approx 0.33$ MB per token in BF16. Thirty-two users at 8K tokens each is ~86 GB, more than the INT4 weights. Engines can store the cache in **FP8** (`--kv-cache-dtype fp8`), halving it with small quality loss; validate on long-context tasks, where errors accumulate.

### 8. Speculative Decoding in Production Engines
Day 111 derives speculative decoding: a cheap proposer guesses $k$ tokens, the big model verifies them in one forward pass, and the rejection-sampling rule keeps the output distribution identical to the big model's. What production engines actually ship in 2025–26:
- **Draft model:** a small model from the same family (same tokenizer). Simple, but it is a second model to host.
- **N-gram / prompt lookup:** propose tokens copied from the prompt. Free, and very effective for summarization, RAG answers and code edits, where the output repeats the input.
- **Medusa:** extra decoding heads on the target model, each predicting a token further ahead.
- **EAGLE / EAGLE-2 / EAGLE-3:** a small draft head that reads the target model's own hidden states. It has high acceptance rates and is the common default in vLLM, SGLang and TensorRT-LLM for supported models.
- **MTP (multi-token prediction):** some models (DeepSeek-V3, for example) are trained with extra next-next-token modules that double as a built-in drafter.

The speed-up depends on the **acceptance rate** and the **batch size**. At low batch the GPU has spare compute, so verifying 4 tokens costs about the same as generating 1 (typically ~1.5–3× faster decode, approximate and workload-dependent). At high batch the GPU is already compute-bound, the wasted work on rejected tokens costs real throughput, and speculation can make things *slower*. Engines let you cap it or switch it off under load.

### 9. The Engines: vLLM vs SGLang vs TensorRT-LLM (and Friends)
All serious engines share the same core ideas: continuous batching, paged KV cache, prefix caching, chunked prefill, tensor/pipeline/expert parallelism, quantized kernels (for example the Marlin INT4 kernels) and an OpenAI-compatible HTTP server. The differences are where they invest:

| Engine | From | Strengths | Trade-offs |
|---|---|---|---|
| **vLLM** | UC Berkeley → community (PyTorch Foundation) | PagedAttention originator; widest model and hardware coverage (NVIDIA, AMD, TPU, Intel, CPU); huge ecosystem; the de-facto default | Peak performance on a given NVIDIA model can trail a tuned TensorRT-LLM build |
| **SGLang** | LMSYS | **RadixAttention**: a radix tree over the KV cache that reuses any shared prefix across requests automatically (multi-turn chat, agents, few-shot, tree search); low-overhead scheduler; fast constrained JSON decoding; strong large-MoE (DeepSeek-style) serving | Smaller ecosystem than vLLM; fast-moving |
| **TensorRT-LLM** | NVIDIA | Best-tuned kernels on NVIDIA (FP8, NVFP4 on Blackwell), in-flight batching, deep integration with Triton and NVIDIA Dynamo | NVIDIA-only; historically required an ahead-of-time engine build per model/GPU/config (newer releases added a PyTorch-based workflow that reduces this) |
| **llama.cpp / Ollama** | Community | GGUF, CPU/Mac/edge, tiny footprint | Not built for high-concurrency GPU serving |
| **TGI, LMDeploy, MLX** | Hugging Face, Shanghai AI Lab, Apple | HF integration; TurboMind kernels; Apple Silicon | Narrower adoption for new deployments in 2025–26 |

How to choose, honestly: benchmark **your** model, **your** prompt/response lengths and **your** concurrency on each candidate, measuring TTFT, TPOT and throughput at your latency SLO (Day 151). Published "X is 3× faster than Y" charts go stale within months, because the projects copy each other's best ideas. Rules of thumb:
- Default to **vLLM** for breadth and ecosystem.
- Pick **SGLang** when requests share long prefixes (agents, multi-turn, structured outputs) or you run big MoE models.
- Pick **TensorRT-LLM** when you are all-NVIDIA, the model is stable, and the last 10–30% of cost per token justifies the build complexity.

At the largest scale, the frontier is **disaggregated serving**: prefill and decode run on separate GPU pools (they have opposite bottlenecks) and the KV cache moves between them over fast interconnects. NVIDIA Dynamo and llm-d orchestrate this on top of vLLM, SGLang or TensorRT-LLM (Day 154 covers multi-node serving).

### 10. Failure Modes to Name in an Interview
- **Calibration mismatch:** GPTQ/AWQ calibrated on English web text can degrade code, math or other languages. Calibrate on data that looks like your traffic.
- **Small models suffer more:** a 70B model at 4 bits usually loses little on benchmarks; a 1–3B model loses noticeably more. 3-bit and 2-bit need i-quants or quantization-aware training and still degrade.
- **Averages hide damage:** perplexity and MMLU can stay flat while long-context retrieval, tool-call JSON validity or rare-language quality drop. Evaluate on your tasks (Day 78's LLM-as-judge comparison).
- **Unofficial checkpoints:** a community `-AWQ` upload may use a different calibration set, an old tokenizer config or a broken chat template. Prefer the lab's own quantized release or produce your own.
- **Kernel availability:** a format is only fast if your engine has a kernel for your GPU (FP8 on A100, INT4 on AMD, MX formats before Blackwell). Otherwise the engine silently falls back to a slow path.
- **MoE specifics:** the router and shared experts are often left in higher precision. Aggressive quantization of the router changes which experts fire.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

### Part 1: GPTQ and AWQ From Scratch (NumPy)
We will build one linear layer whose input activations behave like a real LLM's (correlated channels plus a few huge outlier channels), then quantize it to INT4 four ways and measure the error of the layer's **output** on held-out tokens.

*(You only need NumPy: `pip install numpy`.)*

Create a file named `quant_lab.py`:

```python
import numpy as np

rng = np.random.default_rng(0)


# ---------- Part 1: the memory budget (why formats matter) ----------
BITS_PER_WEIGHT = {            # effective bits incl. scales; approximate
    "BF16": 16.0,
    "FP8 (E4M3, per-channel)": 8.0,
    "INT8 W8A8 (SmoothQuant)": 8.0,
    "GPTQ/AWQ INT4, group 128": 4.25,
    "GGUF Q4_K_M (mixed, ~)": 4.85,
}


def weight_gb(params_billion, bits):
    return params_billion * 1e9 * bits / 8 / 1e9


def kv_cache_gb(tokens, layers=80, kv_heads=8, head_dim=128, bytes_per=2):
    # 2 (K and V) x layers x kv_heads x head_dim x bytes, per token
    return 2 * layers * kv_heads * head_dim * bytes_per * tokens / 1e9


# ---------- Part 2: a layer with outlier input channels ----------
def make_layer(d_in=512, d_out=256, n_tokens=8192, n_factors=32, n_outliers=4):
    W = rng.normal(0, 0.02, size=(d_out, d_in))
    # Real activations are correlated (they live near a low-dimensional subspace) ...
    mix = rng.normal(0, 1, size=(n_factors, d_in)) / np.sqrt(n_factors)
    X = rng.normal(0, 1, size=(n_tokens, n_factors)) @ mix
    X += 0.2 * rng.normal(0, 1, size=(n_tokens, d_in))
    # ... and a handful of channels carry huge values (the LLM "outlier features")
    outlier_channels = rng.choice(d_in, n_outliers, replace=False)
    X[:, outlier_channels] *= 25.0
    return W, X


def quant_sym(w, scale, bits=4):
    qmax = 2 ** (bits - 1) - 1              # 7 for INT4
    return np.clip(np.round(w / scale), -qmax - 1, qmax) * scale


def rtn_per_tensor(W, bits=4):
    scale = np.abs(W).max() / (2 ** (bits - 1) - 1)
    return quant_sym(W, scale, bits)


def rtn_grouped(W, group=128, bits=4):
    Q = np.empty_like(W)
    for g in range(0, W.shape[1], group):
        blk = W[:, g:g + group]
        scale = np.abs(blk).max(axis=1, keepdims=True) / (2 ** (bits - 1) - 1)
        Q[:, g:g + group] = quant_sym(blk, scale, bits)
    return Q


def awq(W, X, group=128, bits=4):
    """Activation-aware scaling: protect the input channels that see big activations
    by scaling their weights UP before quantization (and folding 1/s into the input).
    Every weight is still INT4; no mixed precision."""
    s_x = np.abs(X).mean(axis=0)                          # per-input-channel activation size
    best = (None, np.inf, None)
    for alpha in np.linspace(0, 1, 21):
        s = s_x ** alpha
        s = s / np.sqrt(s.max() * s.min())
        Wq = rtn_grouped(W * s, group, bits) / s          # quantize scaled W, undo the scale
        err = output_error(W, Wq, X)
        if err < best[1]:
            best = (Wq, err, alpha)
    return best[0], best[2]


def gptq(W, X, group=128, bits=4, damp=0.01):
    """GPTQ: quantize one input column at a time and push the rounding error onto the
    columns not yet quantized, weighted by the inverse Hessian H = 2 X^T X / n."""
    W = W.copy()
    d_in = W.shape[1]
    H = 2 * X.T @ X / X.shape[0]
    H += damp * np.mean(np.diag(H)) * np.eye(d_in)
    Hinv = np.linalg.cholesky(np.linalg.inv(H)).T        # upper Cholesky of H^-1
    Q = np.zeros_like(W)
    scale = None
    for i in range(d_in):
        if i % group == 0:                                # group scale from the *updated* weights
            blk = W[:, i:i + group]
            scale = np.abs(blk).max(axis=1) / (2 ** (bits - 1) - 1)
        q = quant_sym(W[:, i], scale, bits)
        Q[:, i] = q
        err = (W[:, i] - q) / Hinv[i, i]
        W[:, i + 1:] -= np.outer(err, Hinv[i, i + 1:])    # compensate in later columns
    return Q


def output_error(W, Wq, X):
    """What matters is the layer OUTPUT on real activations, not the weight error."""
    Y, Yq = X @ W.T, X @ Wq.T
    return np.linalg.norm(Y - Yq) / np.linalg.norm(Y)


def main():
    print("== Memory budget: 70B dense model ==")
    for name, bits in BITS_PER_WEIGHT.items():
        print(f"  {name:<28} weights ~ {weight_gb(70, bits):6.1f} GB")
    per_tok_mb = kv_cache_gb(1) * 1e3
    print(f"  KV cache (BF16, GQA 8 KV heads): {per_tok_mb:.2f} MB/token -> "
          f"32 users x 8K tokens = {kv_cache_gb(32 * 8192):.0f} GB "
          f"(FP8 KV cache halves it: {kv_cache_gb(32 * 8192, bytes_per=1):.0f} GB)")

    print("\n== INT4 on a layer with 4 outlier activation channels ==")
    W, X = make_layer()
    X_cal, X_test = X[:4096], X[4096:]    # calibrate on one half, evaluate on the other
    results = {
        "RTN per-tensor": rtn_per_tensor(W),
        "RTN group-128": rtn_grouped(W),
    }
    W_awq, alpha = awq(W, X_cal)
    results[f"AWQ group-128 (alpha={alpha:.2f})"] = W_awq
    results["GPTQ group-128"] = gptq(W, X_cal)
    for name, Wq in results.items():
        print(f"  {name:<30} relative output error on held-out tokens: {output_error(W, Wq, X_test):.4f}")


if __name__ == "__main__":
    main()
```

Expected output (NumPy 2.x, fixed seed):
```text
== Memory budget: 70B dense model ==
  BF16                         weights ~  140.0 GB
  FP8 (E4M3, per-channel)      weights ~   70.0 GB
  INT8 W8A8 (SmoothQuant)      weights ~   70.0 GB
  GPTQ/AWQ INT4, group 128     weights ~   37.2 GB
  GGUF Q4_K_M (mixed, ~)       weights ~   42.4 GB
  KV cache (BF16, GQA 8 KV heads): 0.33 MB/token -> 32 users x 8K tokens = 86 GB (FP8 KV cache halves it: 43 GB)

== INT4 on a layer with 4 outlier activation channels ==
  RTN per-tensor                 relative output error on held-out tokens: 0.1941
  RTN group-128                  relative output error on held-out tokens: 0.1222
  AWQ group-128 (alpha=0.30)     relative output error on held-out tokens: 0.0717
  GPTQ group-128                 relative output error on held-out tokens: 0.0488
```

### Key Takeaways from Code:
1. **Granularity is the first free win:** moving from one scale per tensor to one scale per 128 weights cuts the output error by about 40% at a cost of ~0.1–0.25 bits per weight.
2. **AWQ wins by looking at activations:** it never touches the Hessian. It just notices which input channels carry big activations and gives their weights more of the INT4 grid. The grid search picked $\alpha = 0.3$; $\alpha = 0$ would be plain RTN.
3. **GPTQ wins by exploiting correlation:** the error of each rounded column is pushed onto correlated columns that have not been rounded yet. Try deleting the correlated part of `make_layer` (keep only the noise and the outliers): GPTQ's advantage over RTN almost disappears, because $X^\top X$ becomes nearly diagonal and there is nothing to compensate with.
4. **Always measure on held-out tokens:** both methods fit the calibration half. Evaluating on the other half is how you catch calibration overfitting, which is exactly what happens in production when the calibration set does not match the traffic.
5. **The KV cache line is the sobering one:** at realistic concurrency the cache outweighs the INT4 weights. Weight quantization gets the model *loaded*; KV-cache sizing decides how many users it *serves*.

### Part 2: Producing and Serving Quantized Models (GPU)
These are the real workflows. They need a GPU (or a Mac for llama.cpp) and change quickly, so check each project's docs for current flags.

**Produce a GPTQ or FP8 checkpoint** with `llm-compressor` (the vLLM project's quantization library, which superseded the older AutoGPTQ/AutoAWQ packages):
```python
# quantize_checkpoint.py  (pip install llmcompressor)
from llmcompressor import oneshot
from llmcompressor.modifiers.quantization import GPTQModifier, QuantizationModifier

MODEL = "Qwen/Qwen2.5-7B-Instruct"

# W4A16 with GPTQ: needs calibration data that looks like your traffic
oneshot(
    model=MODEL,
    dataset="open_platypus",
    recipe=GPTQModifier(targets="Linear", scheme="W4A16", ignore=["lm_head"]),
    max_seq_length=2048,
    num_calibration_samples=512,
    output_dir="qwen2.5-7b-w4a16-gptq",
)

# FP8 weights + dynamic per-token FP8 activations: no calibration data needed
oneshot(
    model=MODEL,
    recipe=QuantizationModifier(targets="Linear", scheme="FP8_DYNAMIC", ignore=["lm_head"]),
    output_dir="qwen2.5-7b-fp8-dynamic",
)
```

**Serve it** (all three expose an OpenAI-compatible API):
```bash
# vLLM: reads the quantization config from the checkpoint; FP8 KV cache; n-gram speculation
vllm serve ./qwen2.5-7b-w4a16-gptq --kv-cache-dtype fp8 \
  --speculative-config '{"method": "ngram", "num_speculative_tokens": 4, "prompt_lookup_max": 4}'

# SGLang: RadixAttention prefix reuse is on by default
python -m sglang.launch_server --model-path ./qwen2.5-7b-fp8-dynamic --port 30000

# llama.cpp: convert, build an importance matrix, quantize, serve
python convert_hf_to_gguf.py ./Qwen2.5-7B-Instruct --outfile qwen-f16.gguf --outtype f16
llama-imatrix -m qwen-f16.gguf -f calibration.txt -o imatrix.dat
llama-quantize --imatrix imatrix.dat qwen-f16.gguf qwen-Q4_K_M.gguf Q4_K_M
llama-server -m qwen-Q4_K_M.gguf -c 8192 -ngl 99
```

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Quantization Bake-Off
You will pick a production format with evidence instead of vibes. A laptop is enough if you use llama.cpp; use vLLM on a GPU if you have one.
1. Take a small instruct model (1–8B) and produce at least four variants: BF16 (or `Q8_0`), `Q4_K_M` without an imatrix, `Q4_K_M` with an imatrix, and one aggressive variant (`Q3_K_M` or `IQ3_M`). On a GPU, use BF16 / FP8 / GPTQ-W4A16 / AWQ instead.
2. Measure perplexity on held-out text (`llama-perplexity -f wiki.test.raw`) *and* on a sample of your own domain text (code, another language, or your company's documents).
3. Build a 50-item task eval that looks like real use: short answers with exact-match checking plus 10 tool-call prompts where you validate the JSON. Run it on every variant.
4. Measure speed with `llama-bench` (or vLLM's benchmark script): prompt-processing tokens/s, generation tokens/s, and peak memory.
5. Plot quality against bytes per parameter and against generation tokens/s. Mark which variants are within 1 point of baseline on your task eval.
6. Write a one-paragraph recommendation that names the format, the evidence, and the one metric that would make you revisit the choice.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"We need to serve an open 70B instruct model for an internal assistant: about 200 concurrent users, prompts around 3K tokens with a shared 2K-token system prompt, answers around 400 tokens, p95 time-to-first-token under 1 second. You have one node with 4× H100-80GB. Choose the precision, the quantization method, the serving engine and any speculative decoding, and explain how you would prove quality did not regress."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Does the math first:** BF16 weights are ~140 GB, so they fit across 4×80 GB, but leave ~180 GB for the KV cache. At ~0.33 MB/token and ~3.4K tokens per request, 200 users need roughly 220 GB of cache in BF16. So something has to shrink: FP8 weights (~70 GB) plus an FP8 KV cache (~110 GB) fits with headroom. They use tensor parallelism across the 4 GPUs.
2. **Picks FP8 W8A8 over INT4 on H100, with the reason:** H100 has FP8 tensor cores, so FP8 speeds up the compute-bound prefill that dominates TTFT with 3K-token prompts, and it is close to lossless. W4A16 (GPTQ/AWQ) would save more memory but helps mainly low-batch decode and can lose throughput at 200 concurrent users. They mention that INT4 becomes the right answer on fewer or smaller GPUs (A100, L40S, a single card).
3. **Exploits the shared prefix:** the 2K-token system prompt is identical for everyone, so prefix caching (vLLM automatic prefix caching or SGLang RadixAttention) turns most of each prefill into a cache hit, which is the biggest single TTFT win. This is a reason to shortlist SGLang, and they would benchmark it against vLLM and TensorRT-LLM on the real traffic shape.
4. **Treats speculative decoding as conditional:** EAGLE-style or n-gram speculation helps TPOT at low load, but at 200 concurrent users the GPUs are closer to compute-bound, so they would benchmark it and cap or disable it at high batch.
5. **Proves quality:** they compare the BF16 reference and the FP8 deployment on a task-specific eval set (real internal queries, LLM-as-judge with human spot checks), plus long-context retrieval and tool-call validity checks. They use the lab's official FP8 checkpoint or calibrate on in-domain data, then roll out behind a canary with TTFT/TPOT and quality dashboards (Days 159, 167).

---
**Task for the end of the day:** Commit `quant_lab.py` and your bake-off table to Git. Then read the model card of one official `-FP8` or `-AWQ` release and note which layers it left unquantized and why.

Tomorrow, in **Day 93**, we go back to training. A 70B model's weights, gradients and optimizer states will not fit on one GPU, even before quantization enters the picture. We will learn **Distributed Training (FSDP, Tensor Parallelism and Pipeline Parallelism)**!
