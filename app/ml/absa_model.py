import tensorflow as tf
import numpy as np
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
from tqdm import tqdm
from .config import (
    ABSA_MODEL_NAME, 
    MODEL_CACHE_DIR, 
    ASPECT_CATEGORIES, 
    CONFIDENCE_THRESHOLD, 
    BATCH_SIZE
)

class ABSAModel:
    def __init__(self):
        print(f"Loading ABSA model: {ABSA_MODEL_NAME}...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            ABSA_MODEL_NAME, 
            cache_dir=MODEL_CACHE_DIR
        )
        self.model = TFAutoModelForSequenceClassification.from_pretrained(
            ABSA_MODEL_NAME, 
            cache_dir=MODEL_CACHE_DIR,
            output_attentions=True
        )
        
        # Check for GPU
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f"GPU found: {gpus}. Using GPU for inference.")
        else:
            print("No GPU found. Using CPU.")
            
        # Inference mode
        self.model.trainable = False
        
        # Polarity mapping
        self.polarity_map = {0: "negative", 1: "neutral", 2: "positive"}

    @tf.function(input_signature=[{
        "input_ids": tf.TensorSpec(shape=[None, None], dtype=tf.int32),
        "attention_mask": tf.TensorSpec(shape=[None, None], dtype=tf.int32),
        "token_type_ids": tf.TensorSpec(shape=[None, None], dtype=tf.int32)
    }])
    def _forward_pass(self, inputs):
        return self.model(inputs, training=False)

    def extract_aspects(self, text: str) -> list[dict]:
        results = []
        
        for category in ASPECT_CATEGORIES:
            # Construct input: "[CLS] {text} [SEP] {category} [SEP]"
            # HF tokenizer handles special tokens automatically if we pass two sequences
            inputs = self.tokenizer(
                text, 
                category, 
                truncation=True, 
                max_length=512, 
                return_tensors="tf"
            )
            
            outputs = self._forward_pass(inputs)
            logits = outputs.logits
            probs = tf.nn.softmax(logits, axis=-1).numpy()[0]
            
            prediction = np.argmax(probs)
            confidence = float(probs[prediction])
            
            if confidence >= CONFIDENCE_THRESHOLD:
                # Aspect Term Extraction (ATE) via final layer attention weights
                # outputs.attentions is a tuple of (layers, batch, heads, seq, seq)
                # We want the last layer
                final_layer_attention = outputs.attentions[-1].numpy()[0] # (heads, seq, seq)
                
                # Mean across heads
                avg_attention = np.mean(final_layer_attention, axis=0) # (seq, seq)
                
                # Identify tokens for the category query (aspect)
                # In [CLS] text [SEP] category [SEP], category starts after the first [SEP]
                input_ids = inputs['input_ids'].numpy()[0]
                sep_indices = np.where(input_ids == self.tokenizer.sep_token_id)[0]
                
                if len(sep_indices) >= 2:
                    text_start = 1 # Skip [CLS]
                    text_end = sep_indices[0]
                    category_start = sep_indices[0] + 1
                    category_end = sep_indices[1]
                    
                    # Compute mean attention of text tokens towards category tokens
                    # avg_attention[query_idx, key_idx]
                    # We want tokens in text that are "attended to" by the category tokens
                    # or tokens in text that "attend to" the category tokens?
                    # Usually "attended to" means key_idx. 
                    # Prompt says: "identify token span with highest mean attention FOR the aspect query tokens"
                    # This usually means text tokens that the aspect query tokens are looking at.
                    
                    text_to_cat_att = avg_attention[category_start:category_end, text_start:text_end]
                    # Mean attention per text token from all category tokens
                    text_token_scores = np.mean(text_to_cat_att, axis=0)
                    
                    # Identify span with "highest mean attention"
                    # Simple heuristic: continuous tokens above some threshold or just the highest score token?
                    # Usually, ABSA term extraction is a bit more complex, but here we'll take the 
                    # contiguous span around the highest score or just the single highest if not specified.
                    # Prompt says: "identify token span with highest mean attention"
                    # I'll implement a simple sliding window or just take the top-N tokens that are contiguous.
                    # Let's take the single highest scoring token and its immediate high-scoring neighbors.
                    
                    if len(text_token_scores) > 0:
                        max_idx = np.argmax(text_token_scores)
                        # Expand to neighbors if they also have high attention (e.g. > 50% of max)
                        threshold = text_token_scores[max_idx] * 0.5
                        start_span = max_idx
                        while start_span > 0 and text_token_scores[start_span - 1] > threshold:
                            start_span -= 1
                        end_span = max_idx
                        while end_span < len(text_token_scores) - 1 and text_token_scores[end_span + 1] > threshold:
                            end_span += 1
                        
                        aspect_term_ids = input_ids[text_start + start_span : text_start + end_span + 1]
                        aspect_term = self.tokenizer.decode(aspect_term_ids).strip()
                    else:
                        aspect_term = None
                else:
                    aspect_term = None

                if not aspect_term:
                    aspect_term = None
                    
                results.append({
                    "aspect_category": category,
                    "polarity": self.polarity_map[prediction],
                    "confidence": confidence,
                    "aspect_term": aspect_term
                })
        
        return results

    def batch_extract(self, texts: list[str]) -> list[list[dict]]:
        all_results = []
        batch_size = BATCH_SIZE
        
        i = 0
        pbar = tqdm(total=len(texts), desc="Processing Batch ABSA")
        while i < len(texts):
            batch_texts = texts[i : i + batch_size]
            try:
                batch_results = []
                for text in batch_texts:
                    batch_results.append(self.extract_aspects(text))
                all_results.extend(batch_results)
                i += batch_size
                pbar.update(len(batch_texts))
            except (tf.errors.ResourceExhaustedError, MemoryError):
                if batch_size > 1:
                    print(f"Memory Error at batch size {batch_size}. Falling back to batch_size=1")
                    batch_size = 1
                    # Don't increment i, retry with smaller batch
                else:
                    print("Memory Error even at batch size 1. Skipping one sample.")
                    all_results.append([])
                    i += 1
                    pbar.update(1)
        pbar.close()
        return all_results
