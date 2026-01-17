import os

# ---------------- CRITICAL FIX (Docling CPU only) ----------------
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["NCCL_P2P_DISABLE"] = "1"
os.environ["NCCL_IB_DISABLE"] = "1"
# ---------------------------------------------------------------

import torch
import faiss
import gc
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
from docling.document_converter import DocumentConverter


class GraniteDoclingRAG:
    def __init__(
        self,
        pdf_path,
        k_retrieve=4,
        granite_model="ibm-granite/granite-3.0-8b-instruct"
    ):
        self.pdf_path = pdf_path
        self.k_retrieve = k_retrieve

        # ---------------- Device & dtype ----------------
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if self.device == "cuda":
            if torch.cuda.is_bf16_supported():
                self.dtype = torch.bfloat16
                print("[INFO] Using bfloat16")
            else:
                self.dtype = torch.float16
                print("[INFO] bfloat16 not supported, falling back to float16")
        else:
            self.dtype = torch.float32
            print("[INFO] Using float32 (CPU)")

        # ---------------- Granite LLM ----------------
        self.tokenizer = AutoTokenizer.from_pretrained(granite_model)

        self.model = AutoModelForCausalLM.from_pretrained(
            granite_model,
            torch_dtype=self.dtype,
            device_map="auto" if self.device == "cuda" else None
        )

        # ---------------- Embeddings (CPU) ----------------
        self.embedder = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device="cpu"
        )

        # ---------------- Docling (CPU ONLY) ----------------
        self.converter = DocumentConverter()

        # ---------------- Build index ----------------
        self.chunks = self.build_chunks()
        self.build_index()

    # ---------------- Docling Extraction ----------------
    def build_chunks(self):
        result = self.converter.convert(self.pdf_path)
        doc = result.document

        chunks = []

        for block in doc.text_blocks:
            if block.text.strip():
                chunks.append({
                    "text": block.text,
                    "type": "text",
                    "source": f"page_{block.page_no}"
                })

        for i, table in enumerate(doc.tables):
            chunks.append({
                "text": table.to_pandas().to_string(index=False),
                "type": "table",
                "source": f"table_{i}_page_{table.page_no}"
            })

        for i, fig in enumerate(doc.figures):
            caption = fig.caption or "Figure without caption"
            chunks.append({
                "text": caption,
                "type": "figure",
                "source": f"figure_{i}_page_{fig.page_no}"
            })

        print(f"[INFO] Extracted {len(chunks)} chunks")
        return chunks

    # ---------------- FAISS ----------------
    def build_index(self):
        texts = [c["text"] for c in self.chunks]
        embeddings = self.embedder.encode(texts, convert_to_numpy=True)
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def retrieve(self, query):
        q = self.embedder.encode([query], convert_to_numpy=True)
        _, idx = self.index.search(q, self.k_retrieve)
        return [self.chunks[i] for i in idx[0]]

    # ---------------- Granite Generation (bf16 safe) ----------------
    def answer(self, query):
        docs = self.retrieve(query)

        context = "\n\n".join(
            f"[{d['type'].upper()} | {d['source']}]\n{d['text']}"
            for d in docs
        )

        prompt = f"""
Use the context below to answer the question.
If the answer is not in the context, say "I don't know".

Context:
{context}

Question:
{query}

Answer:
"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            if self.device == "cuda" and self.dtype == torch.bfloat16:
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    output = self.model.generate(
                        **inputs,
                        max_new_tokens=300,
                        do_sample=False,
                        temperature=0.2
                    )
            else:
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=300,
                    do_sample=False,
                    temperature=0.2
                )

        return self.tokenizer.decode(output[0], skip_special_tokens=True)

    # ---------------- Cleanup ----------------
    def cleanup(self):
        del self.model
        gc.collect()

        if self.device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()


# ---------------- Run ----------------
if __name__ == "__main__":
    rag = GraniteDoclingRAG("/kaggle/input/sampledataset/sample.pdf")
    print(rag.answer("Summarize the key findings including tables and figures."))
    rag.cleanup()
